"""Demo para la visita del humanoide G1 a clase.

Casos de uso pensados para mostrar en el aula, usando SOLO la API permitida
(avanzar, girar, mover, detenerse, saludar, dar_la_mano). No agrega acciones
nuevas al robot: combina las que ya estan en la lista blanca, asi que lo que
anda aca anda igual en el laboratorio fisico.

Uso (con el simulador ABIERTO y el G1 elegido):
    python3 mi_desarrollo/demo_visita.py          # menu interactivo
    python3 mi_desarrollo/demo_visita.py todo     # corre toda la secuencia
    python3 mi_desarrollo/demo_visita.py 2        # corre el caso 2 y sigue con el menu

Todas las velocidades y tiempos se validan contra el perfil de la materia con
que se abrio el simulador. Los movimientos largos se parten en ordenes cortas
para no superar la duracion maxima por comando.

Archivos de la demo (todos en mi_desarrollo/):
    utilidades.py   moverse en metros/grados y hablar
    habilidades.py  figuras nuevas (zigzag, ocho...) y control manual
    juego_ppt.py    piedra, papel o tijera (teclado o camara)
    vision_ppt.py   la camara: detecta la mano con MediaPipe
"""

import math
import sys

import juego_ppt
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
    """4. Recorre un cuadrado de 0.4 m."""
    anunciar("Cuadrado de 0.40 m de lado")
    for _ in range(4):
        avanzar_metros(robot, 0.4)
        girar_grados(robot, 90)


def caso_curva(robot):
    """5. Una curva: avanza y gira a la vez con mover()."""
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
    """6. Baile: coreografia con movimientos permitidos."""
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


# ------------------------------------------------- piedra, papel o tijera
def caso_piedra_papel_tijera(robot):
    """7. Piedra, papel o tijera contra el robot con el teclado."""
    anunciar("Piedra, papel o tijera")
    juego_ppt.jugar_con_teclado(robot)


def caso_ppt_camara(robot):
    """14. Piedra, papel o tijera con la camara: el robot ve tu mano."""
    anunciar("Piedra, papel o tijera con camara")
    try:
        juego_ppt.jugar_con_camara(robot)
    except CamaraNoDisponible as exc:
        print(f"   Camara no disponible: {exc}")
        print("   Jugamos con el teclado.")
        juego_ppt.jugar_con_teclado(robot)


def caso_despedida(robot):
    """8. Se despide y sale del centro de la escena."""
    anunciar("Despedida: saluda, da media vuelta y se aleja")
    robot.saludar()
    girar_grados(robot, 180)
    avanzar_metros(robot, 0.8)


# La secuencia original de la visita (opciones 1 a 8 y "toda la secuencia").
SECUENCIA = [caso_entrada, caso_saludo_al_aula, caso_dar_la_mano,
             caso_cuadrado, caso_curva, caso_baile,
             caso_piedra_papel_tijera, caso_despedida]
# Lo nuevo: opciones 9 en adelante.
NUEVOS = HABILIDADES + [caso_control_manual, caso_ppt_camara]
CASOS = SECUENCIA + NUEVOS
# Los juegos esperan respuestas del alumno: en "todo" se saltean si nadie
# puede escribir (por ejemplo, si la salida esta redirigida).
INTERACTIVOS = (caso_piedra_papel_tijera,)

def _titulo(caso):
    return caso.__doc__.split(". ", 1)[1]


def correr_todo(robot):
    for caso in SECUENCIA:
        if caso in INTERACTIVOS and not sys.stdin.isatty():
            print(f"\n(salteo '{_titulo(caso)}': necesita teclado)")
            continue
        correr(robot, caso)


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
            print(f"  {i:>2}. {_titulo(caso)}")
        print("   t. Toda la secuencia            q. Salir")
        opcion = input("Elegi: ").strip().lower()
        if opcion == "q":
            return
        if opcion == "t":
            correr_todo(robot)
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
        elif arg.isdigit() and 1 <= int(arg) <= len(CASOS):
            correr(robot, CASOS[int(arg) - 1])        # esa opcion y despues el menu
            menu(robot)
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
