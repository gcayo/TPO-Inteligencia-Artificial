"""Demo para la visita del humanoide G1 a clase.

Casos de uso pensados para mostrar en el aula, usando SOLO la API permitida
(avanzar, girar, mover, detenerse, saludar, dar_la_mano). No agrega acciones
nuevas al robot: combina las que ya estan en la lista blanca, asi que lo que
anda aca anda igual en el laboratorio fisico.

Ademas del menu, el robot se puede manejar POR VOZ (opcion 'v' del menu): se
le dice "robot, avanza un metro", "robot, baila", "robot, juguemos"... Los dos
modos conviven: desde el modo voz se vuelve al menu diciendo "robot, menu".

Uso (con el simulador ABIERTO y el G1 elegido):
    python3 mi_desarrollo/demo_visita.py          # menu interactivo
    python3 mi_desarrollo/demo_visita.py todo     # corre toda la secuencia
    python3 mi_desarrollo/demo_visita.py 2        # corre un solo caso
    python3 mi_desarrollo/demo_visita.py voz      # arranca en modo voz

Todas las velocidades y tiempos se validan contra el perfil de la materia con
que se abrio el simulador. Los movimientos largos se parten en ordenes cortas
para no superar la duracion maxima por comando.

Archivos de la demo (todos en mi_desarrollo/):
    utilidades.py   moverse en metros/grados y hablar
    habilidades.py  figuras nuevas (zigzag, ocho, cangrejo...) y control manual
    juego_ppt.py    piedra, papel o tijera (teclado, camara o voz)
    vision_ppt.py   la camara: detecta la mano con MediaPipe
    voz.py          el microfono: entiende ordenes en castellano con Vosk
"""

import math
import sys

import juego_ppt
import voz
from habilidades import HABILIDADES, caso_control_manual
from robot import ErrorDeSeguridad, NoHaySimulador, Robot
from utilidades import (VEL_ANGULAR, VEL_LINEAL, anunciar, avanzar_metros,  # noqa: F401
                        costado_metros, decir, en_tramos as _en_tramos,
                        girar_grados)
from vision_ppt import CamaraNoDisponible


# ----------------------------------------------------------- casos de uso
def caso_entrada(robot):
    """1. Entra al aula y saluda."""
    anunciar("Entrada: avanza 0.8 m y saluda")
    avanzar_metros(robot, 0.8)
    robot.saludar()


def caso_saludo_al_aula(robot):
    """2. Saluda a la izquierda, al centro y a la derecha del aula."""
    anunciar("Saludo al aula: izquierda, centro, derecha")
    girar_grados(robot, 45)
    robot.saludar()
    girar_grados(robot, -45)
    robot.saludar()
    girar_grados(robot, -45)
    robot.saludar()
    girar_grados(robot, 45)


def caso_dar_la_mano(robot):
    """3. Se acerca a un alumno y le da la mano."""
    anunciar("Dar la mano: se acerca 0.4 m, extiende la mano y vuelve")
    avanzar_metros(robot, 0.4)
    robot.dar_la_mano()
    avanzar_metros(robot, -0.4)


def caso_cuadrado(robot):
    """4. Recorre un cuadrado de 0.4 m (el ejemplo de los TP de programacion)."""
    anunciar("Cuadrado de 0.40 m de lado")
    for _ in range(4):
        avanzar_metros(robot, 0.4)
        girar_grados(robot, 90)


def caso_curva(robot):
    """5. Una curva: avanza y gira a la vez con mover() (lo que usa la app TP04)."""
    anunciar("Curva: medio circulo combinando vx y vyaw")
    # Medio circulo = pi rad a 0.4 rad/s -> 7.85 s, en tramos.
    w = 0.4
    tope = robot.perfil.duracion_max
    restante = math.pi / w
    while restante > 1e-6:
        tramo = min(tope, restante)
        robot.mover(vx=0.15, vyaw=w, tiempo=tramo)
        restante -= tramo


def caso_baile(robot):
    """6. Baile: coreografia con movimientos permitidos (vuelve al mismo lugar)."""
    # NO usa Dance1/Dance2 del SDK: estan PROHIBIDAS en acciones.py (movimientos
    # bruscos e impredecibles). Esta coreografia usa solo mover() y saludar(),
    # dentro de los limites de la materia, asi que corre igual en el robot real.
    # Cada figura es simetrica: el robot termina donde empezo.
    anunciar("Baile: balanceo, pasos al costado, vaiven, saludos y giro")
    tiempo = 0.5                     # un "tiempo" de la musica, en segundos
    v = min(0.15, robot.perfil.velocidad_max)
    w = min(0.5, robot.perfil.velocidad_angular_max)

    def paso(vx=0.0, vy=0.0, vyaw=0.0, tiempos=1):
        robot.mover(vx=vx, vy=vy, vyaw=vyaw, tiempo=tiempo * tiempos)

    # 1. Balanceo de cadera: gira a un lado y al otro
    for _ in range(2):
        paso(vyaw=w)
        paso(vyaw=-w, tiempos=2)
        paso(vyaw=w)
    # 2. Paso al costado: izquierda, derecha, derecha, izquierda
    paso(vy=v, tiempos=2)
    paso(vy=-v, tiempos=4)
    paso(vy=v, tiempos=2)
    # 3. Vaiven adelante y atras
    for _ in range(2):
        paso(vx=v)
        paso(vx=-v)
    robot.saludar()
    # 4. Rombo: adelante-izquierda, atras-izquierda, atras-derecha, adelante-derecha
    for vx, vy in ((v, v), (-v, v), (-v, -v), (v, -v)):
        paso(vx=vx, vy=vy, tiempos=2)
    # 5. Giro completo en dos medias vueltas y saludo final
    media_vuelta = math.pi / w
    for _ in range(2):
        _en_tramos(robot, robot.girar, w, media_vuelta)
    robot.saludar()


def caso_moonwalk(robot):
    """7. Moonwalk: se desliza hacia atras con las piernas 'caminando' adelante."""
    # En el simulador la animacion de las piernas siempre avanza, sin importar
    # el sentido: al retroceder, el robot "camina" hacia adelante mientras se
    # desliza hacia atras. Eso ES el moonwalk. En el robot real es caminar hacia
    # atras, lento y dentro de los limites.
    anunciar("Moonwalk: deslizamiento hacia atras, glide lateral y vuelta")
    decir("Moonwalk")
    v = min(0.15, robot.perfil.velocidad_max)
    _en_tramos(robot, robot.avanzar, -v, 0.6 / v)          # atras 0.6 m
    robot.mover(vy=-0.12, tiempo=1.5)                       # glide a la derecha
    robot.mover(vy=0.12, tiempo=1.5)                        # y vuelve
    _en_tramos(robot, robot.avanzar, -v, 0.3 / v)           # otro tramo atras
    robot.saludar()
    avanzar_metros(robot, 0.9)                              # vuelve a su lugar


# ------------------------------------------------- piedra, papel o tijera
def caso_piedra_papel_tijera(robot):
    """8. Piedra, papel o tijera contra el robot (con el teclado)."""
    anunciar("Piedra, papel o tijera")
    juego_ppt.jugar_con_teclado(robot)


def caso_ppt_camara(robot):
    """17. Piedra, papel o tijera con la camara (el robot ve tu mano)."""
    anunciar("Piedra, papel o tijera con camara")
    try:
        juego_ppt.jugar_con_camara(robot)
    except CamaraNoDisponible as exc:
        print(f"   Camara no disponible: {exc}")
        print("   Jugamos con el teclado.")
        juego_ppt.jugar_con_teclado(robot)


def caso_despedida(robot):
    """9. Se despide y sale del centro de la escena."""
    anunciar("Despedida: saluda, da media vuelta y se aleja")
    robot.saludar()
    girar_grados(robot, 180)
    avanzar_metros(robot, 0.8)


# La secuencia original de la visita (opciones 1 a 9 y "toda la secuencia").
SECUENCIA = [caso_entrada, caso_saludo_al_aula, caso_dar_la_mano,
             caso_cuadrado, caso_curva, caso_baile, caso_moonwalk,
             caso_piedra_papel_tijera, caso_despedida]
# Lo nuevo: opciones 10 en adelante.
NUEVOS = HABILIDADES + [caso_control_manual, caso_ppt_camara]
CASOS = SECUENCIA + NUEVOS
# Los juegos esperan respuestas del alumno: en "todo" se saltean si nadie
# puede escribir (por ejemplo, si la salida esta redirigida).
INTERACTIVOS = (caso_piedra_papel_tijera,)

# Para el modo voz: nombre que devuelve voz.interpretar() -> caso
CASOS_POR_NOMBRE = {
    "entrada": caso_entrada, "saludo_al_aula": caso_saludo_al_aula,
    "cuadrado": caso_cuadrado, "curva": caso_curva, "baile": caso_baile,
    "moonwalk": caso_moonwalk, "despedida": caso_despedida,
}
CASOS_POR_NOMBRE.update({c.__name__.removeprefix("caso_"): c for c in HABILIDADES})


def _titulo(caso):
    return caso.__doc__.split(". ", 1)[1]


def correr_todo(robot):
    for caso in SECUENCIA:
        if caso in INTERACTIVOS and not sys.stdin.isatty():
            print(f"\n(salteo '{_titulo(caso)}': necesita teclado)")
            continue
        correr(robot, caso)


# --------------------------------------------------------------- modo voz
def _otra_por_voz(oyente):
    def preguntar():
        for _ in range(2):
            decir("¿Otra?")
            texto = oyente.escuchar(timeout=6)
            if texto:
                print(f"   🎤 {texto}")
            respuesta = voz.respuesta_si_no(texto or "")
            if respuesta is not None:
                return respuesta
        return False
    return preguntar


def _jugar_por_voz(robot, oyente):
    """Con camara si hay; si no, el alumno dice su jugada."""
    try:
        juego_ppt.jugar_con_camara(robot, otra_ronda=_otra_por_voz(oyente))
    except CamaraNoDisponible as exc:
        print(f"   Camara no disponible ({exc}): jugamos de palabra.")
        juego_ppt.jugar_con_voz(robot, oyente, _otra_por_voz(oyente))


def ejecutar_orden(robot, orden, oyente):
    """Hace lo que pide una orden de voz.interpretar()."""
    accion = orden["accion"]
    if accion == "avanzar":
        avanzar_metros(robot, orden["valor"])
    elif accion == "costado":
        costado_metros(robot, orden["valor"])
    elif accion == "girar":
        girar_grados(robot, orden["valor"])
    elif accion == "saludar":
        robot.saludar()
    elif accion == "dar_la_mano":
        robot.dar_la_mano()
    elif accion == "detener":
        robot.detenerse()
    elif accion == "caso":
        CASOS_POR_NOMBRE[orden["nombre"]](robot)
    elif accion == "jugar":
        _jugar_por_voz(robot, oyente)
    # "ayuda": la confirmacion ya es la explicacion, no hay que moverse


def modo_voz(robot):
    """Escucha ordenes que empiezan con 'robot'. 'robot, menu' vuelve al menu."""
    try:
        oyente = voz.Oyente()
    except voz.VozNoDisponible as exc:
        print(f"\n   Control por voz no disponible: {exc}")
        print("   Seguis con el menu.")
        return
    anunciar("Modo voz (Ctrl+C o 'robot, menu' para volver al menu)")
    print(f"   {voz.AYUDA}")
    decir("Te escucho. Decí robot y después la orden.")
    esperando = False                  # dijeron solo "robot": espero la orden
    try:
        while True:
            print("   🎤 Escuchando..." if not esperando else "   🎤 Esperando la orden...")
            texto = oyente.escuchar(timeout=8 if esperando else None)
            if texto is None:
                esperando = False
                continue
            print(f"   🎤 Escuche: \"{texto}\"")
            tenia_clave, resto = voz.quitar_palabra_clave(texto)
            if not tenia_clave and not esperando:
                continue               # charla del aula: no es para el robot
            esperando = False
            if not resto:
                decir("¿Sí?")
                esperando = True
                continue
            orden = voz.interpretar(resto)
            if orden is None:
                decir("No te entendí. Decí robot ayuda.")
                continue
            decir(orden["confirmacion"])
            if orden["accion"] == "salir":
                return
            correr(robot, lambda r: ejecutar_orden(r, orden, oyente))
    except KeyboardInterrupt:
        robot.detenerse()
        print("\n   Salgo del modo voz.")


# --------------------------------------------------------------- principal
def correr(robot, caso):
    try:
        caso(robot)
    except ErrorDeSeguridad as exc:
        print(f"   RECHAZADO por seguridad: {exc}")
    except NotImplementedError as exc:
        print(f"   No disponible en este robot: {exc}")
    finally:
        robot.detenerse()
    print(f"   Estado: {robot.verificar_estado()}")


def menu(robot):
    while True:
        print("\n=== Visita del humanoide: casos de uso ===")
        for i, caso in enumerate(CASOS, 1):
            if i == len(SECUENCIA) + 1:
                print("  --- Habilidades nuevas ---")
            print(f"  {i:>2}. {_titulo(caso)}")
        print("   v. Hablarle al robot (control por voz)")
        print("   t. Toda la secuencia (1 a 9)      q. Salir")
        opcion = input("Elegi: ").strip().lower()
        if opcion == "q":
            return
        if opcion == "t":
            correr_todo(robot)
        elif opcion == "v":
            modo_voz(robot)
        elif opcion.isdigit() and 1 <= int(opcion) <= len(CASOS):
            correr(robot, CASOS[int(opcion) - 1])
        else:
            print("Opcion invalida.")


def main():
    try:
        robot = Robot()
        robot.conectar()
    except NoHaySimulador as exc:
        print(exc)
        return 1
    print(f"Conectado. Perfil: {robot.perfil.nombre} "
          f"(max {robot.perfil.velocidad_max} m/s, "
          f"{robot.perfil.duracion_max} s por orden)")
    if robot.modelo != "g1":
        print("Aviso: esta demo esta pensada para el G1 (humanoide).")
    try:
        arg = sys.argv[1].lower() if len(sys.argv) > 1 else ""
        if arg == "todo":
            correr_todo(robot)
        elif arg == "voz":
            modo_voz(robot)
            menu(robot)
        elif arg.isdigit() and 1 <= int(arg) <= len(CASOS):
            correr(robot, CASOS[int(arg) - 1])
        else:
            menu(robot)
    except KeyboardInterrupt:
        print("\nInterrumpido.")
    finally:
        robot.detenerse()
        robot.desconectar()
    return 0


if __name__ == "__main__":
    sys.exit(main())
