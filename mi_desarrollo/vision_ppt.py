"""Vision por camara para jugar a piedra, papel o tijera.

Usa OpenCV para la camara y MediaPipe Hands para encontrar los 21 puntos de
la mano. Con esos puntos se cuenta que dedos estan estirados:

    ningun dedo estirado            -> piedra
    indice y medio (los demas no)   -> tijera
    tres o cuatro dedos estirados   -> papel

Un dedo esta "estirado" si su punta esta bastante mas lejos de la muneca que
su nudillo del medio. Comparar distancias (y no alturas) hace que funcione
aunque la mano este inclinada o de costado.

MediaPipe no siempre tiene version para el Python mas nuevo. Por eso este
archivo se puede usar de dos formas, con la misma interfaz:

  - importado, si el Python de la demo tiene cv2 y mediapipe (Camara);
  - como proceso aparte con OTRO Python que si los tenga (CamaraRemota).
    El instalador arma ese Python en ~/.venvs/unitree-vision si hace falta.

Este archivo NO importa nada de la demo: el proceso aparte no tiene el robot.

Probar solo la camara (sin robot):
    python3 mi_desarrollo/vision_ppt.py
"""

import json
import math
import os
import queue
import subprocess
import sys
import threading
import time
from collections import Counter
from pathlib import Path

JUGADAS = ("piedra", "papel", "tijera")

# Puntos de MediaPipe Hands: 0 = muneca; por dedo (punta, nudillo medio).
DEDOS = {
    "indice": (8, 6),
    "medio": (12, 10),
    "anular": (16, 14),
    "menique": (20, 18),
}
CONEXIONES = [(0, 1), (1, 2), (2, 3), (3, 4), (0, 5), (5, 6), (6, 7), (7, 8),
              (5, 9), (9, 10), (10, 11), (11, 12), (9, 13), (13, 14), (14, 15),
              (15, 16), (13, 17), (17, 18), (18, 19), (19, 20), (0, 17)]

UMBRAL_ESTIRADO = 1.15     # punta / nudillo medio, medidos desde la muneca
SEGUNDOS_CAPTURA = 1.2     # despues de "tijera", cuanto tiempo se mira la mano
MODELO_URL = ("https://storage.googleapis.com/mediapipe-models/hand_landmarker/"
              "hand_landmarker/float16/1/hand_landmarker.task")
CACHE = Path.home() / ".cache" / "visita_g1"
VENTANA = "Piedra, papel o tijera"


class CamaraNoDisponible(RuntimeError):
    """No se puede usar la camara (falta una libreria, permiso o dispositivo)."""


class FaltanLibrerias(CamaraNoDisponible):
    pass


class Cancelado(Exception):
    """El jugador cerro la ventana (tecla q o Esc)."""


# ------------------------------------------------------------- clasificador
def _dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def dedos_estirados(puntos):
    """Dict dedo -> True/False. 'puntos' son 21 pares (x, y) en pixeles."""
    muneca = puntos[0]
    return {nombre: _dist(muneca, puntos[punta]) >
            _dist(muneca, puntos[nudillo]) * UMBRAL_ESTIRADO
            for nombre, (punta, nudillo) in DEDOS.items()}


def clasificar_mano(puntos):
    """'piedra', 'papel', 'tijera' o None si el gesto no es claro."""
    if not puntos or len(puntos) < 21:
        return None
    e = dedos_estirados(puntos)
    n = sum(e.values())
    if n == 0:
        return "piedra"
    if e["indice"] and e["medio"] and not e["anular"] and not e["menique"]:
        return "tijera"
    if n >= 3:
        return "papel"
    return None


# ------------------------------------------------------------------ detector
def _modelo_tasks():
    """Descarga (una sola vez) el modelo de la API nueva de MediaPipe."""
    destino = CACHE / "hand_landmarker.task"
    if not destino.exists():
        import urllib.request
        CACHE.mkdir(parents=True, exist_ok=True)
        print("   Descargando el modelo de manos (solo la primera vez)...",
              file=sys.stderr)
        tmp = destino.with_suffix(".tmp")
        urllib.request.urlretrieve(MODELO_URL, tmp)
        tmp.replace(destino)
    return str(destino)


class _Detector:
    """MediaPipe Hands, con la API vieja (solutions) o la nueva (tasks)."""

    def __init__(self):
        import mediapipe as mp
        self._mp = mp
        soluciones = getattr(mp, "solutions", None)
        if soluciones is not None and hasattr(soluciones, "hands"):
            self._hands = soluciones.hands.Hands(
                model_complexity=0, max_num_hands=1,
                min_detection_confidence=0.6, min_tracking_confidence=0.5)
            self._tasks = None
        else:
            from mediapipe.tasks import python as mp_python
            from mediapipe.tasks.python import vision
            opciones = vision.HandLandmarkerOptions(
                base_options=mp_python.BaseOptions(model_asset_path=_modelo_tasks()),
                running_mode=vision.RunningMode.VIDEO, num_hands=1,
                min_hand_detection_confidence=0.6)
            self._tasks = vision.HandLandmarker.create_from_options(opciones)
            self._t0 = time.monotonic()
            self._ultimo_ms = -1

    def detectar(self, rgb):
        """Los 21 puntos de la primera mano, en pixeles, o None."""
        alto, ancho = rgb.shape[:2]
        if self._tasks is None:
            r = self._hands.process(rgb)
            if not r.multi_hand_landmarks:
                return None
            marcas = r.multi_hand_landmarks[0].landmark
        else:
            ms = max(int((time.monotonic() - self._t0) * 1000), self._ultimo_ms + 1)
            self._ultimo_ms = ms
            imagen = self._mp.Image(image_format=self._mp.ImageFormat.SRGB, data=rgb)
            r = self._tasks.detect_for_video(imagen, ms)
            if not r.hand_landmarks:
                return None
            marcas = r.hand_landmarks[0]
        return [(p.x * ancho, p.y * alto) for p in marcas]


# ------------------------------------------------------- camara (en proceso)
def _hay_pantalla():
    """En Linux sin pantalla, imshow() de OpenCV aborta el proceso entero."""
    if sys.platform.startswith("linux"):
        return bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))
    return True


class Camara:
    """Camara + detector en este mismo proceso."""

    def __init__(self, indice=0):
        try:
            import cv2
            import mediapipe  # noqa: F401
        except ImportError as exc:
            raise FaltanLibrerias(f"Falta una libreria: {exc.name}") from None
        self._cv2 = cv2
        try:
            self._detector = _Detector()
        except Exception as exc:                              # noqa: BLE001
            raise CamaraNoDisponible(
                f"No pude preparar el detector de manos ({exc}). La primera "
                "vez necesita internet para bajar el modelo.") from None
        self._cap = cv2.VideoCapture(indice)
        ok = self._cap.isOpened() and self._cap.read()[0]
        if not ok:
            self._cap.release()
            raise CamaraNoDisponible(
                "No pude abrir la camara. Revisa que este conectada y que la "
                "Terminal tenga permiso (macOS: Configuracion del Sistema > "
                "Privacidad y seguridad > Camara).")
        self._con_ventana = _hay_pantalla()

    # -- dibujo
    def _dibujar(self, frame, puntos, titulo, detalle=""):
        cv2 = self._cv2
        if puntos:
            p = [(int(x), int(y)) for x, y in puntos]
            for a, b in CONEXIONES:
                cv2.line(frame, p[a], p[b], (255, 255, 255), 2)
            for punto in p:
                cv2.circle(frame, punto, 4, (0, 140, 255), -1)
        cv2.rectangle(frame, (0, 0), (frame.shape[1], 70), (0, 0, 0), -1)
        cv2.putText(frame, titulo, (15, 45), cv2.FONT_HERSHEY_SIMPLEX, 1.2,
                    (255, 255, 255), 3)
        if detalle:
            cv2.putText(frame, detalle, (15, frame.shape[0] - 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

    def _mostrar(self, frame):
        """Muestra el cuadro; devuelve la tecla apretada (o -1)."""
        if not self._con_ventana:
            return -1
        try:
            self._cv2.imshow(VENTANA, frame)
            return self._cv2.waitKey(1) & 0xFF
        except self._cv2.error:
            # OpenCV sin ventanas (paquete "headless"): juega igual, sin vista
            self._con_ventana = False
            return -1

    def _cerrar_ventana(self):
        if self._con_ventana:
            try:
                self._cv2.destroyWindow(VENTANA)
                for _ in range(5):
                    self._cv2.waitKey(1)
            except self._cv2.error:
                pass

    # -- juego
    def capturar_jugada(self, esta_listo, segundos_captura=SEGUNDOS_CAPTURA):
        """Muestra la camara hasta que esta_listo() sea True ("¡tijera!") y
        despues mira la mano 'segundos_captura' s. Devuelve la jugada que mas
        se vio, o None si no se vio ninguna mano clara."""
        cv2 = self._cv2
        votos = Counter()
        fin = None
        ultimo = None
        while True:
            ok, frame = self._cap.read()
            if not ok:
                raise CamaraNoDisponible("La camara dejo de responder.")
            frame = cv2.flip(frame, 1)                       # efecto espejo
            puntos = self._detector.detectar(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            jugada = clasificar_mano(puntos)
            ahora = time.monotonic()
            if fin is None and esta_listo():
                fin = ahora + segundos_captura
            if fin is None:
                titulo = "Prepara tu mano..."
            elif ahora < fin:
                titulo = "YA!"
                if jugada:
                    votos[jugada] += 1
            else:
                break
            detalle = f"Veo: {jugada.upper()}" if jugada else (
                "Mostra la mano a la camara" if not puntos else "Gesto poco claro")
            self._dibujar(frame, puntos, titulo, detalle)
            ultimo = frame
            if self._mostrar(frame) in (ord("q"), 27):
                self._cerrar_ventana()
                raise Cancelado()
        elegida = votos.most_common(1)[0][0] if votos else None
        if ultimo is not None:                                # resultado 1 s
            self._dibujar(ultimo, None, f"Tu jugada: {elegida.upper()}" if elegida
                          else "No vi tu mano")
            fin = time.monotonic() + 1.0
            while time.monotonic() < fin and self._con_ventana:
                self._mostrar(ultimo)
                time.sleep(0.03)
        self._cerrar_ventana()
        return elegida

    def jugar_ronda(self, cuenta_regresiva):
        """Corre cuenta_regresiva() (robot + voz) mientras muestra la camara.

        La ventana tiene que vivir en el hilo principal (macOS lo exige), asi
        que la cuenta regresiva del robot va en un hilo aparte.
        """
        error = []

        def correr():
            try:
                cuenta_regresiva()
            except BaseException as exc:                     # noqa: BLE001
                error.append(exc)

        hilo = threading.Thread(target=correr, daemon=True)
        hilo.start()
        try:
            jugada = self.capturar_jugada(lambda: not hilo.is_alive())
        finally:
            hilo.join()
        if error:
            raise error[0]
        return jugada

    def cerrar(self):
        self._cap.release()
        self._cerrar_ventana()


# -------------------------------------------- camara (en otro proceso Python)
def python_vision():
    """El Python aparte con mediapipe, si el instalador lo armo."""
    propio = os.environ.get("VISITA_PYTHON_VISION")
    if propio and Path(propio).exists():
        return propio
    base = Path.home() / ".venvs" / "unitree-vision"
    for candidato in (base / "bin" / "python", base / "Scripts" / "python.exe"):
        if candidato.exists():
            return str(candidato)
    return None


class CamaraRemota:
    """Misma interfaz que Camara, pero la camara corre en otro proceso."""

    def __init__(self, python, indice=0):
        self._proc = subprocess.Popen(
            [python, str(Path(__file__).resolve()), "--servidor", str(indice)],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, text=True, bufsize=1)
        respuesta = self._leer()
        if "error" in respuesta:
            self.cerrar()
            raise CamaraNoDisponible(respuesta["error"])

    def _leer(self):
        linea = self._proc.stdout.readline()
        if not linea:
            raise CamaraNoDisponible("El proceso de la camara se cerro.")
        return json.loads(linea)

    def _enviar(self, texto):
        self._proc.stdin.write(texto + "\n")
        self._proc.stdin.flush()

    def jugar_ronda(self, cuenta_regresiva):
        self._enviar("ronda")
        try:
            cuenta_regresiva()
        finally:
            self._enviar("ya")
        respuesta = self._leer()
        if "error" in respuesta:
            raise CamaraNoDisponible(respuesta["error"])
        if respuesta.get("cancelado"):
            raise Cancelado()
        return respuesta.get("jugada")

    def cerrar(self):
        try:
            self._enviar("salir")
            self._proc.wait(timeout=3)
        except Exception:                                    # noqa: BLE001
            self._proc.kill()


def abrir_camara(indice=0):
    """La mejor camara disponible. Levanta CamaraNoDisponible si no hay."""
    try:
        return Camara(indice)
    except FaltanLibrerias as exc:
        python = python_vision()
        if python:
            return CamaraRemota(python, indice)
        raise CamaraNoDisponible(
            f"{exc}. Para jugar con la camara instala 'mediapipe' y "
            "'opencv-python' (lo hace INICIAR_VISITA.command; ver LEEME_VISITA.md)."
        ) from None


# ------------------------------------------------- modo servidor (otro proceso)
def _servidor(indice):
    def responder(datos):
        print(json.dumps(datos), flush=True)

    try:
        camara = Camara(indice)
    except Exception as exc:                                  # noqa: BLE001
        responder({"error": str(exc)})
        return
    ordenes = queue.Queue()

    def leer_stdin():
        for linea in sys.stdin:
            ordenes.put(linea.strip())
        ordenes.put("salir")

    threading.Thread(target=leer_stdin, daemon=True).start()
    responder({"listo": True})

    def llego_ya():
        try:
            orden = ordenes.get_nowait()
        except queue.Empty:
            return False
        if orden == "salir":
            ordenes.put("salir")
            raise Cancelado()
        return orden == "ya"

    while True:
        orden = ordenes.get()
        if orden == "salir":
            break
        if orden != "ronda":
            continue                       # un "ya" suelto despues de cancelar
        try:
            responder({"jugada": camara.capturar_jugada(llego_ya)})
        except Cancelado:
            responder({"cancelado": True})
        except Exception as exc:                              # noqa: BLE001
            responder({"error": str(exc)})
    camara.cerrar()


def _probar():
    """Prueba sin robot: 3 rondas con una cuenta regresiva en la terminal."""
    camara = abrir_camara()
    try:
        for _ in range(3):
            def cuenta():
                for palabra in ("Piedra...", "papel...", "tijera!"):
                    print(f"   {palabra}")
                    time.sleep(0.8)
            print(f"   -> {camara.jugar_ronda(cuenta)}")
    except Cancelado:
        print("   Cancelado.")
    finally:
        camara.cerrar()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--servidor":
        _servidor(int(sys.argv[2]) if len(sys.argv) > 2 else 0)
    else:
        _probar()
