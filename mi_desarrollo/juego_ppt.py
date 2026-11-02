"""Piedra, papel o tijera contra el robot: con teclado, con camara o con voz.

La ronda es la misma en los tres casos: el robot hace la cuenta regresiva
("piedra, papel, tijera" con un vaiven por palabra), elige al azar, muestra
las dos jugadas y reacciona: saluda si gana, da la mano si pierde y hace un
vaiven si empatan. Lo unico que cambia es COMO se lee la jugada del alumno.
"""

import random

from utilidades import decir

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


def nuevo_marcador():
    return {"vos": 0, "robot": 0, "empates": 0}


def _mostrar(jugada_alumno, jugada_robot):
    print()
    print(f"   {'VOS: ' + jugada_alumno.upper():<24}ROBOT: {jugada_robot.upper()}")
    izq, der = DIBUJOS[jugada_alumno], DIBUJOS[jugada_robot]
    ancho = max(len(linea) for linea in der)
    espejo = str.maketrans("()", ")(")
    for a, b in zip(izq, der):
        print(f"   {a:<24}{b.ljust(ancho)[::-1].translate(espejo)}")
    print()


def cuenta_regresiva(robot):
    """Un vaiven por palabra: simetrico, el robot no se desplaza."""
    w = min(0.5, robot.perfil.velocidad_angular_max)
    for palabra in ("Piedra", "papel", "tijera"):
        robot.mover(vyaw=w, tiempo=0.3)
        decir(palabra)
        robot.mover(vyaw=-w, tiempo=0.3)


def resolver_ronda(robot, jugada, puntos):
    """El robot elige, se muestra el resultado y reacciona."""
    robot_elige = random.choice(JUGADAS)
    _mostrar(jugada, robot_elige)
    decir(f"Yo elegí {robot_elige}")
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


# ------------------------------------------------------------------ teclado
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


def jugar_con_teclado(robot):
    puntos = nuevo_marcador()
    decir("Juguemos a piedra, papel o tijera")
    while True:
        jugada = _pedir_jugada()
        if jugada is None:
            break
        cuenta_regresiva(robot)
        resolver_ronda(robot, jugada, puntos)
    decir("Gracias por jugar")


def otra_por_teclado():
    try:
        return input("   Enter = otra ronda   q = salir: ").strip().lower() not in ("q", "salir")
    except EOFError:
        return False


# ------------------------------------------------------------------- camara
def jugar_con_camara(robot, otra_ronda=otra_por_teclado):
    """Lee la mano con la camara. Levanta CamaraNoDisponible si no hay."""
    from vision_ppt import Cancelado, abrir_camara

    print("   Abriendo la camara...")
    camara = abrir_camara()
    puntos = nuevo_marcador()
    try:
        decir("Mostrá tu mano a la cámara. Cuando diga tijera, hacé tu jugada.")
        while True:
            try:
                jugada = camara.jugar_ronda(lambda: cuenta_regresiva(robot))
            except Cancelado:
                break
            if jugada is None:
                decir("No vi bien tu mano. Repetimos.")
                continue
            print(f"   La camara vio: {jugada.upper()}")
            resolver_ronda(robot, jugada, puntos)
            if not otra_ronda():
                break
    finally:
        camara.cerrar()
    decir("Gracias por jugar")


# ---------------------------------------------------------------------- voz
def jugar_con_voz(robot, oyente, otra_ronda):
    """Sin camara: el alumno DICE su jugada justo despues de 'tijera'."""
    from voz import jugada_dicha

    puntos = nuevo_marcador()
    decir("Cuando diga tijera, decí tu jugada en voz alta.")
    while True:
        cuenta_regresiva(robot)
        texto = oyente.escuchar(timeout=5)
        jugada = jugada_dicha(texto or "")
        if jugada is None:
            decir("No te escuché. Repetimos.")
            if texto is None and not otra_ronda():
                break
            continue
        resolver_ronda(robot, jugada, puntos)
        if not otra_ronda():
            break
    decir("Gracias por jugar")
