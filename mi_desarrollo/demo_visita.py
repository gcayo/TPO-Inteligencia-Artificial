"""Demo para la visita del humanoide G1 a clase.

Casos de uso pensados para mostrar en el aula, usando SOLO la API permitida
(avanzar, girar, mover, detenerse, saludar, dar_la_mano). No agrega acciones
nuevas al robot: combina las que ya estan en la lista blanca, asi que lo que
anda aca anda igual en el laboratorio fisico.

Uso (con el simulador ABIERTO y el G1 elegido):
    python3 mi_desarrollo/demo_visita.py          # menu interactivo
    python3 mi_desarrollo/demo_visita.py todo     # corre toda la secuencia
    python3 mi_desarrollo/demo_visita.py 2        # corre un solo caso

Todas las velocidades y tiempos se validan contra el perfil de la materia con
que se abrio el simulador. Los movimientos largos se parten en ordenes cortas
para no superar la duracion maxima por comando.
"""

import math
import sys

from robot import ErrorDeSeguridad, NoHaySimulador, Robot

VEL_LINEAL = 0.20    # m/s   (<= techo de 0.25)
VEL_ANGULAR = 0.50   # rad/s (<= techo de 1.0)


# ---------------------------------------------------------------- utilidades
def _en_tramos(robot, accion, velocidad, tiempo_total):
    """Ejecuta 'accion' en tramos que respetan la duracion maxima del perfil."""
    tope = robot.perfil.duracion_max
    restante = tiempo_total
    while restante > 1e-6:
        tramo = min(tope, restante)
        accion(velocidad=velocidad, tiempo=tramo)
        restante -= tramo


def avanzar_metros(robot, metros):
    """distancia = v x t  ->  t = distancia / v. Negativo = retrocede."""
    v = VEL_LINEAL if metros >= 0 else -VEL_LINEAL
    _en_tramos(robot, robot.avanzar, v, abs(metros) / VEL_LINEAL)


def girar_grados(robot, grados):
    """Positivo = izquierda, negativo = derecha."""
    w = VEL_ANGULAR if grados >= 0 else -VEL_ANGULAR
    _en_tramos(robot, robot.girar, w, math.radians(abs(grados)) / VEL_ANGULAR)


def anunciar(texto):
    print(f"\n>>> {texto}")


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
JUGADAS = ("piedra", "papel", "tijera")
LE_GANA_A = {"piedra": "tijera", "papel": "piedra", "tijera": "papel"}
DIBUJOS = {
    "piedra": ["    _______   ", "---'   ____)  ", "      (_____) ",
               "      (_____) ", "      (____)  ", "---.__(___)   "],
    "papel":  ["    _______        ", "---'   ____)____   ", "           ______) ",
               "          _______) ", "         _______)  ", "---.__________)    "],
    "tijera": ["    _______        ", "---'   ____)____   ", "           ______) ",
               "        __________)", "      (____)       ", "---.__(___)        "],
}


def _voz_en_castellano():
    """Una voz en castellano de macOS (comando 'say'), o None."""
    import shutil
    import subprocess
    if not shutil.which("say"):
        return None
    try:
        voces = subprocess.run(["say", "-v", "?"], capture_output=True,
                               text=True, timeout=5).stdout.splitlines()
    except Exception:                                      # noqa: BLE001
        return None
    for region in ("es_AR", "es_MX", "es_ES", "es_"):
        for linea in voces:
            if region in linea:
                return linea.split(region)[0].strip().split("  ")[0].strip()
    return None


_VOZ = _voz_en_castellano()


def decir(texto):
    """Lo dice en voz alta si hay voz en castellano (macOS); si no, solo imprime."""
    print(f"   🔊 {texto}")
    if _VOZ:
        import subprocess
        try:
            subprocess.run(["say", "-v", _VOZ, texto], timeout=10)
        except Exception:                                  # noqa: BLE001
            pass


def _mostrar(jugada_alumno, jugada_robot):
    print()
    print(f"   {'VOS: ' + jugada_alumno.upper():<24}ROBOT: {jugada_robot.upper()}")
    izq, der = DIBUJOS[jugada_alumno], DIBUJOS[jugada_robot]
    ancho = max(len(linea) for linea in der)
    espejo = str.maketrans("()", ")(")
    for a, b in zip(izq, der):
        print(f"   {a:<24}{b.ljust(ancho)[::-1].translate(espejo)}")
    print()


def _pedir_jugada():
    while True:
        texto = input("   Tu jugada: 1) piedra  2) papel  3) tijera  q) salir: ").strip().lower()
        if texto in ("q", "salir"):
            return None
        if texto in ("1", "2", "3"):
            return JUGADAS[int(texto) - 1]
        if texto in JUGADAS:
            return texto
        print("   No entendi. Escribi 1, 2, 3 o el nombre.")


def caso_piedra_papel_tijera(robot):
    """8. Piedra, papel o tijera contra el robot (interactivo)."""
    import random
    anunciar("Piedra, papel o tijera")
    decir("Juguemos a piedra, papel o tijera")
    w = min(0.5, robot.perfil.velocidad_angular_max)
    puntos = {"vos": 0, "robot": 0, "empates": 0}
    while True:
        jugada = _pedir_jugada()
        if jugada is None:
            break
        # Cuenta regresiva: un vaiven por palabra (simetrico, no se desplaza)
        for palabra in ("Piedra", "papel", "tijera"):
            robot.mover(vyaw=w, tiempo=0.3)
            decir(palabra)
            robot.mover(vyaw=-w, tiempo=0.3)
        robot_elige = random.choice(JUGADAS)
        _mostrar(jugada, robot_elige)
        decir(f"Yo elegi {robot_elige}")
        if jugada == robot_elige:
            puntos["empates"] += 1
            decir("Empate")
            robot.mover(vx=0.1, tiempo=0.5)
            robot.mover(vx=-0.1, tiempo=0.5)
        elif LE_GANA_A[robot_elige] == jugada:
            puntos["robot"] += 1
            decir("¡Gané yo!")
            robot.saludar()
        else:
            puntos["vos"] += 1
            decir("Ganaste vos. ¡Bien jugado!")
            robot.dar_la_mano()
        print(f"   Marcador -> vos {puntos['vos']}  |  robot {puntos['robot']}"
              f"  |  empates {puntos['empates']}\n")
    decir("Gracias por jugar")


def caso_despedida(robot):
    """9. Se despide y sale del centro de la escena."""
    anunciar("Despedida: saluda, da media vuelta y se aleja")
    robot.saludar()
    girar_grados(robot, 180)
    avanzar_metros(robot, 0.8)


CASOS = [caso_entrada, caso_saludo_al_aula, caso_dar_la_mano,
         caso_cuadrado, caso_curva, caso_baile, caso_moonwalk,
         caso_piedra_papel_tijera, caso_despedida]
# Los juegos esperan respuestas del alumno: en "todo" se saltean si nadie
# puede escribir (por ejemplo, si la salida esta redirigida).
INTERACTIVOS = (caso_piedra_papel_tijera,)


def correr_todo(robot):
    for caso in CASOS:
        if caso in INTERACTIVOS and not sys.stdin.isatty():
            print(f"\n(salteo '{caso.__doc__.split('. ', 1)[1]}': necesita teclado)")
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
            print(f"  {i}. {caso.__doc__.split('. ', 1)[1]}")
        print("  t. Toda la secuencia      q. Salir")
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
