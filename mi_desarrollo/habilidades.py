"""Habilidades nuevas del robot.

Igual que el resto de la demo, usan SOLO la API permitida (mover, avanzar,
girar, detenerse, saludar, dar_la_mano) y respetan los limites del perfil de
la materia. No hay saltos, acrobacias ni cambios de postura: estan prohibidos
en entorno/sim/acciones.py y lo que anda aca tiene que andar igual en el robot
real.

Casi todas las figuras son cerradas: el robot termina donde empezo, asi se
pueden encadenar en el aula sin que se vaya de la escena.
"""

import math

from utilidades import (VEL_LATERAL, anunciar, avanzar_metros, costado_metros,
                        decir, girar_grados, mover_en_tramos)


def _v(robot, deseada):
    """La velocidad deseada, sin pasarse del perfil."""
    return min(deseada, robot.perfil.velocidad_max)


def _w(robot, deseada):
    return min(deseada, robot.perfil.velocidad_angular_max)


# ----------------------------------------------------------------- figuras
def caso_presentacion(robot):
    """10. Presentacion: el robot se presenta y cuenta lo que sabe hacer."""
    anunciar("Presentacion")
    robot.saludar()
    decir("Hola, soy el robot humanoide G1. Hoy vine a visitarlos.")
    decir("Sé caminar, bailar, hacer figuras, obedecer órdenes de voz "
          "y jugar a piedra, papel o tijera mirando la cámara.")
    robot.dar_la_mano()
    decir("Mucho gusto.")


def caso_zigzag(robot):
    """11. Zigzag: avanza esquivando conos imaginarios y vuelve."""
    anunciar("Zigzag: cuatro diagonales y vuelta al lugar")
    vx, vy, t = _v(robot, 0.15), _v(robot, 0.12), 1.5
    # Lateral +, -, -, +  ->  termina centrado (y = 0)
    for signo in (1, -1, -1, 1):
        robot.mover(vx=vx, vy=signo * vy, tiempo=t)
    avanzar_metros(robot, -vx * t * 4)


def caso_ocho(robot):
    """12. Figura de ocho: un circulo a la izquierda y otro a la derecha."""
    anunciar("Ocho: dos circulos de 30 cm de radio")
    v, w = _v(robot, 0.15), _w(robot, 0.5)
    vuelta = 2 * math.pi / w                     # tiempo de un circulo entero
    mover_en_tramos(robot, vuelta, vx=v, vyaw=w)
    mover_en_tramos(robot, vuelta, vx=v, vyaw=-w)


def caso_cangrejo(robot):
    """13. Cangrejo: pasos al costado, saludando a cada lado."""
    anunciar("Cangrejo: izquierda, derecha y vuelta al centro")
    costado_metros(robot, 0.3)
    robot.saludar()
    costado_metros(robot, -0.6)
    robot.saludar()
    costado_metros(robot, 0.3)


def caso_vigia(robot):
    """14. Vigia: mira a su alrededor en cuatro direcciones."""
    anunciar("Vigia: un cuarto de vuelta por vez")
    for frase in ("Al frente, despejado.", "A la izquierda, despejado.",
                  "Atrás, despejado.", "A la derecha, todo en orden."):
        girar_grados(robot, 90)
        decir(frase)


def caso_celebracion(robot):
    """15. Celebracion: festeja con un giro, vaiven y saludos."""
    anunciar("Celebracion")
    decir("¡Vamos!")
    w = _w(robot, 0.5)
    robot.saludar()
    for _ in range(3):                            # vaiven corto, simetrico
        robot.mover(vyaw=w, tiempo=0.4)
        robot.mover(vyaw=-w, tiempo=0.4)
    girar_grados(robot, 360)
    robot.saludar()


# --------------------------------------------------------- control manual
TECLAS = {
    "w": ("Adelante 20 cm", lambda r: avanzar_metros(r, 0.2)),
    "s": ("Atras 20 cm", lambda r: avanzar_metros(r, -0.2)),
    "a": ("Girar 45 grados a la izquierda", lambda r: girar_grados(r, 45)),
    "d": ("Girar 45 grados a la derecha", lambda r: girar_grados(r, -45)),
    "z": ("Paso al costado izquierdo", lambda r: costado_metros(r, VEL_LATERAL)),
    "c": ("Paso al costado derecho", lambda r: costado_metros(r, -VEL_LATERAL)),
    "h": ("Saludar", lambda r: r.saludar()),
    "m": ("Dar la mano", lambda r: r.dar_la_mano()),
}


def caso_control_manual(robot):
    """16. Control manual: manejalo con el teclado (w a s d)."""
    anunciar("Control manual")
    print("   Escribi una o varias letras y Enter (ej: 'wwa' = adelante, "
          "adelante, izquierda).")
    for tecla, (texto, _) in TECLAS.items():
        print(f"     {tecla}  {texto}")
    print("     q  Volver al menu")
    while True:
        try:
            entrada = input("   Orden: ").strip().lower()
        except EOFError:
            return
        if entrada in ("q", "salir"):
            return
        for tecla in entrada:
            if tecla in TECLAS:
                print(f"   -> {TECLAS[tecla][0]}")
                TECLAS[tecla][1](robot)
            elif tecla != " ":
                print(f"   '{tecla}' no es una orden.")
        robot.detenerse()
        print(f"   Estado: {robot.verificar_estado()}")


HABILIDADES = [caso_presentacion, caso_zigzag, caso_ocho, caso_cangrejo,
               caso_vigia, caso_celebracion]
