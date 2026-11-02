"""Control por voz: escuchar el microfono y entender ordenes en castellano.

Reconocimiento SIN internet con Vosk (modelo chico en espanol, ~40 MB, se
descarga solo la primera vez) y el microfono con sounddevice. Sin internet
importa: el wifi del aula no siempre ayuda.

Dos partes separadas a proposito:
  - interpretar(texto): texto -> orden. Funcion pura, se prueba sin microfono.
  - Oyente: microfono -> texto. Solo escucha mientras se le pide, asi no se
    escucha a si mismo cuando el robot habla o se mueve.

Seguridad: para que una charla en el aula no mueva al robot, las ordenes
empiezan con la palabra clave "robot" ("robot, avanza un metro"). Decir solo
"robot" tambien sirve: el robot contesta "¿Si?" y espera la orden.
"""

import json
import os
import queue
import re
import time
import unicodedata

PALABRA_CLAVE = "robot"
MAX_METROS_VOZ = 1.0          # por voz, como mucho 1 m por orden
METROS_POR_PASO = 0.2
DISTANCIA_POR_DEFECTO = 0.4
COSTADO_POR_DEFECTO = 0.2

AYUDA = ("Decí robot y después la orden. Por ejemplo: robot avanza un metro, "
         "robot gira a la izquierda, robot paso al costado, robot media vuelta, "
         "robot saluda, robot dame la mano, robot baila, robot zigzag, "
         "robot ocho, robot cangrejo, robot vigía, robot celebra, "
         "robot juguemos a piedra papel o tijera, o robot menú para volver.")

# Casos con nombre: palabra clave -> nombre del caso en la demo.
CASOS_POR_VOZ = [
    (("presentate", "presentacion", "quien sos"), "presentacion"),
    (("zigzag", "zig zag", "zig"), "zigzag"),
    (("ocho",), "ocho"),
    (("cangrejo",), "cangrejo"),
    (("vigia", "vigila", "alrededor", "explora"), "vigia"),
    (("celebra", "festeja", "festejo", "celebracion", "festejemos"), "celebracion"),
    (("baila", "baile", "bailar", "bailemos", "bailate"), "baile"),
    (("moonwalk", "lunar", "maicol"), "moonwalk"),
    (("cuadrado",), "cuadrado"),
    (("curva", "circulo"), "curva"),
    (("entrada", "entra"), "entrada"),
    (("despedida", "despedite", "chau", "adios"), "despedida"),
]

# Vocabulario para Vosk: limitarlo mejora MUCHO el reconocimiento.
# Va con y sin tilde porque el modelo puede escribir cualquiera de las dos;
# las que no conoce las ignora.
FRASES = [
    "robot", "robot avanza un metro", "robot avanzá dos pasos",
    "robot camina adelante", "robot hacia atrás", "robot retrocede medio metro",
    "robot gira a la izquierda", "robot girá a la derecha un poco",
    "robot dobla a la izquierda", "robot paso al costado a la derecha",
    "robot correte a la izquierda", "robot media vuelta", "robot vuelta entera",
    "robot vuelta completa", "robot para", "robot pará", "robot frena",
    "robot alto", "robot quieto", "robot saluda", "robot saludá", "robot hola",
    "robot saluda a todos", "robot saluda al aula", "robot dame la mano",
    "robot baila", "robot bailá", "robot moonwalk", "robot paso lunar",
    "robot cuadrado", "robot curva", "robot círculo", "robot ocho",
    "robot zigzag", "robot zig zag", "robot cangrejo", "robot vigía",
    "robot mira alrededor", "robot explora", "robot celebra", "robot festeja",
    "robot presentate", "robot quién sos", "robot entrada", "robot despedida",
    "robot chau", "robot adiós", "robot juguemos a piedra papel o tijera",
    "robot jugar", "piedra", "papel", "tijera", "sí", "si", "no", "otra",
    "basta", "robot ayuda", "robot qué sabés hacer", "robot menú",
    "robot salir", "robot terminar", "uno", "una", "dos", "tres", "cuatro",
    "cinco", "metros", "pasos", "poquito", "lado", "adelante", "atras",
    "seguí", "recto", "dale", "[unk]",
]


# --------------------------------------------------------------- interpretar
def normalizar(texto):
    """minusculas, sin tildes, sin signos: 'Avanzá 1 metro!' -> 'avanza 1 metro'."""
    texto = unicodedata.normalize("NFD", texto.lower())
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    texto = texto.replace("[unk]", " ")
    return " ".join(re.sub(r"[^a-z0-9 ]", " ", texto).split())


def quitar_palabra_clave(texto):
    """(tenia_la_palabra_clave, resto_del_texto) ya normalizado."""
    texto = normalizar(texto)
    palabras = texto.split()
    if PALABRA_CLAVE in palabras:
        i = palabras.index(PALABRA_CLAVE)
        return True, " ".join(palabras[i + 1:])
    return False, texto


NUMEROS = {"un": 1, "uno": 1, "una": 1, "dos": 2, "tres": 3, "cuatro": 4,
           "cinco": 5, "medio": 0.5, "media": 0.5}


def _numero(palabra):
    if palabra in NUMEROS:
        return NUMEROS[palabra]
    try:
        return float(palabra)
    except ValueError:
        return None


def _cantidad(palabras, unidades):
    """Numero escrito antes de una de las 'unidades', o None.

    'dos metros' -> 2 ; 'medio metro' -> 0.5 ; 'un metro y medio' -> 1.5
    """
    for i, palabra in enumerate(palabras):
        if palabra in unidades:
            n = _numero(palabras[i - 1]) if i > 0 else None
            n = 1 if n is None else n
            if palabras[i + 1:i + 3] == ["y", "medio"]:
                n += 0.5
            return n
    return None


def _distancia(palabras, por_defecto, metros_por_paso=METROS_POR_PASO):
    metros = _cantidad(palabras, ("metro", "metros"))
    if metros is None:
        pasos = _cantidad(palabras, ("paso", "pasos"))
        if pasos is not None and any(_numero(p) for p in palabras):
            metros = pasos * metros_por_paso
    if metros is None:
        metros = por_defecto / 2 if ("poco" in palabras or "poquito" in palabras) \
            else por_defecto
    return metros


def _texto_distancia(metros):
    if metros < 1:
        return f"{round(metros * 100)} centímetros"
    return f"{metros:g} metro" + ("" if metros == 1 else "s")


def interpretar(texto):
    """Texto (ya sin la palabra clave) -> orden, o None si no se entendio.

    Una orden es un dict con 'accion' y, segun el caso, 'valor' o 'nombre',
    mas 'confirmacion': lo que el robot dice antes de hacerlo.
    """
    t = normalizar(texto)
    palabras = t.split()
    if not palabras:
        return None
    hay = lambda *claves: any(  # noqa: E731
        (" " in c and f" {c} " in f" {t} ") or c in palabras for c in claves)

    if hay("salir", "menu", "terminar", "basta"):
        return {"accion": "salir", "confirmacion": "Vuelvo al menú"}
    if hay("ayuda", "que sabes", "que podes"):
        return {"accion": "ayuda", "confirmacion": AYUDA}
    if hay("frena", "alto", "quieto", "stop", "detenete", "detente"):
        return {"accion": "detener", "confirmacion": "Me detengo"}
    if hay("piedra", "papel", "tijera", "jugar", "juguemos", "juego", "jugamos"):
        return {"accion": "jugar", "confirmacion": "¡Juguemos!"}

    # Saludar al aula entera antes que el saludo comun
    if hay("saluda", "saludo", "hola") and hay("todos", "aula", "clase"):
        return {"accion": "caso", "nombre": "saludo_al_aula",
                "confirmacion": "Hola a todos"}
    for claves, nombre in CASOS_POR_VOZ:
        if hay(*claves):
            return {"accion": "caso", "nombre": nombre, "confirmacion": "¡Dale!"}
    if hay("mano"):
        return {"accion": "dar_la_mano", "confirmacion": "Acá va mi mano"}
    if hay("saluda", "saludo", "hola"):
        return {"accion": "saludar", "confirmacion": "¡Hola!"}

    # ---- movimiento
    if hay("vuelta"):
        if hay("media"):
            grados = -180 if hay("derecha") else 180
            return {"accion": "girar", "valor": grados, "confirmacion": "Media vuelta"}
        grados = -360 if hay("derecha") else 360
        return {"accion": "girar", "valor": grados, "confirmacion": "Una vuelta entera"}

    adelante = hay("adelante", "avanza", "avanzar", "avanzo", "camina", "segui",
                   "recto", "derecho")
    atras = hay("atras", "retrocede", "retroceder", "retrocedo")
    izquierda, derecha = hay("izquierda"), hay("derecha")
    lateral = hay("costado", "lado", "paso", "pasos", "correte", "corre", "lateral")
    girando = hay("gira", "girar", "dobla", "doblar", "gira")

    if (izquierda or derecha) and lateral and not girando:
        metros = min(_distancia(palabras, COSTADO_POR_DEFECTO, 0.15), MAX_METROS_VOZ)
        signo = 1 if izquierda else -1
        lado = "izquierda" if izquierda else "derecha"
        return {"accion": "costado", "valor": signo * metros,
                "confirmacion": f"Me corro {_texto_distancia(metros)} a la {lado}"}
    if izquierda or derecha:
        grados = 45 if hay("poco", "poquito") else 90
        lado = "izquierda" if izquierda else "derecha"
        return {"accion": "girar", "valor": grados if izquierda else -grados,
                "confirmacion": f"Giro a la {lado}"}
    if adelante or atras:
        pedido = _distancia(palabras, DISTANCIA_POR_DEFECTO)
        metros = min(pedido, MAX_METROS_VOZ)
        aviso = (f" Por seguridad, por voz me muevo como mucho "
                 f"{_texto_distancia(MAX_METROS_VOZ)}.") if pedido > MAX_METROS_VOZ else ""
        verbo = "Avanzo" if adelante else "Retrocedo"
        return {"accion": "avanzar", "valor": metros if adelante else -metros,
                "confirmacion": f"{verbo} {_texto_distancia(metros)}.{aviso}"}
    if palabras in (["para"], ["pare"]):
        return {"accion": "detener", "confirmacion": "Me detengo"}
    return None


def respuesta_si_no(texto):
    """True (si), False (no) o None (no se entendio)."""
    t = normalizar(texto).split()
    if any(p in t for p in ("si", "dale", "otra", "bueno", "obvio")):
        return True
    if any(p in t for p in ("no", "basta", "salir", "menu", "terminar")):
        return False
    return None


def jugada_dicha(texto):
    """'piedra', 'papel', 'tijera' o None."""
    t = normalizar(texto).split()
    for jugada in ("piedra", "papel", "tijera"):
        if jugada in t:
            return jugada
    return None


# -------------------------------------------------------------------- oyente
class VozNoDisponible(RuntimeError):
    """No hay reconocimiento de voz (falta libreria, modelo o microfono)."""


class Oyente:
    """Microfono -> texto, con Vosk. Escucha solo dentro de escuchar()."""

    def __init__(self, gramatica=None):
        try:
            import sounddevice as sd
            import vosk
        except ImportError as exc:
            raise VozNoDisponible(
                f"Falta la libreria '{exc.name}'. Instala 'vosk' y 'sounddevice' "
                "(lo hace INICIAR_VISITA.command; ver LEEME_VISITA.md).") from None
        except OSError as exc:              # sounddevice sin PortAudio (Linux)
            raise VozNoDisponible(
                f"No encuentro PortAudio ({exc}). En Linux: "
                "sudo apt install libportaudio2") from None
        self._sd = sd
        vosk.SetLogLevel(-1)
        try:
            dispositivo = sd.query_devices(kind="input")
        except Exception as exc:                              # noqa: BLE001
            raise VozNoDisponible(f"No encuentro un microfono ({exc}).") from None
        self._frecuencia = int(dispositivo["default_samplerate"])

        print("   Cargando el reconocimiento de voz "
              "(la primera vez descarga ~40 MB)...")
        ruta = os.environ.get("VOSK_MODELO")
        try:
            modelo = vosk.Model(ruta) if ruta else vosk.Model(lang="es")
        except Exception as exc:                              # noqa: BLE001
            raise VozNoDisponible(
                f"No pude cargar el modelo de voz en espanol ({exc}). "
                "La primera vez necesita internet.") from None
        if gramatica is None:
            gramatica = os.environ.get("VOZ_LIBRE") != "1"
        if gramatica:
            self._rec = vosk.KaldiRecognizer(modelo, self._frecuencia,
                                             json.dumps(FRASES, ensure_ascii=False))
        else:
            self._rec = vosk.KaldiRecognizer(modelo, self._frecuencia)
        self._cola = queue.Queue()

    def _al_recibir(self, datos, _frames, _tiempo, _estado):
        self._cola.put(bytes(datos))

    def escuchar(self, timeout=None):
        """Espera una frase. Devuelve el texto, o None si paso 'timeout' s."""
        self._rec.Reset()
        self._cola = queue.Queue()
        limite = None if timeout is None else time.monotonic() + timeout
        with self._sd.RawInputStream(samplerate=self._frecuencia,
                                     blocksize=self._frecuencia // 4,
                                     dtype="int16", channels=1,
                                     callback=self._al_recibir):
            while limite is None or time.monotonic() < limite:
                try:
                    datos = self._cola.get(timeout=0.3)
                except queue.Empty:
                    continue
                if self._rec.AcceptWaveform(datos):
                    texto = json.loads(self._rec.Result()).get("text", "")
                    texto = texto.replace("[unk]", "").strip()
                    if texto:
                        return texto
        return None
