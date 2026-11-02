"""Utilidades compartidas por la demo: moverse en metros/grados y hablar.

Todo usa SOLO la API permitida del robot (avanzar, girar, mover, detenerse,
saludar, dar_la_mano). Los movimientos largos se parten en ordenes cortas para
no superar la duracion maxima por comando del perfil de la materia.
"""

import math
import shutil
import subprocess
import sys

VEL_LINEAL = 0.20    # m/s   (<= techo de 0.25)
VEL_ANGULAR = 0.50   # rad/s (<= techo de 1.0)
VEL_LATERAL = 0.15   # m/s   paso al costado, un poco mas lento


# ------------------------------------------------------------- movimiento
def en_tramos(robot, accion, velocidad, tiempo_total):
    """Ejecuta 'accion' en tramos que respetan la duracion maxima del perfil."""
    tope = robot.perfil.duracion_max
    restante = tiempo_total
    while restante > 1e-6:
        tramo = min(tope, restante)
        accion(velocidad=velocidad, tiempo=tramo)
        restante -= tramo


def mover_en_tramos(robot, tiempo_total, vx=0.0, vy=0.0, vyaw=0.0):
    """Como en_tramos, pero con mover() (las tres velocidades a la vez)."""
    tope = robot.perfil.duracion_max
    restante = tiempo_total
    while restante > 1e-6:
        tramo = min(tope, restante)
        robot.mover(vx=vx, vy=vy, vyaw=vyaw, tiempo=tramo)
        restante -= tramo


def avanzar_metros(robot, metros):
    """distancia = v x t  ->  t = distancia / v. Negativo = retrocede."""
    v = VEL_LINEAL if metros >= 0 else -VEL_LINEAL
    en_tramos(robot, robot.avanzar, v, abs(metros) / VEL_LINEAL)


def girar_grados(robot, grados):
    """Positivo = izquierda, negativo = derecha."""
    w = VEL_ANGULAR if grados >= 0 else -VEL_ANGULAR
    en_tramos(robot, robot.girar, w, math.radians(abs(grados)) / VEL_ANGULAR)


def costado_metros(robot, metros):
    """Paso lateral sin girar. Positivo = izquierda, negativo = derecha."""
    v = VEL_LATERAL if metros >= 0 else -VEL_LATERAL
    mover_en_tramos(robot, abs(metros) / VEL_LATERAL, vy=v)


def anunciar(texto):
    print(f"\n>>> {texto}")


# ------------------------------------------------------------------ voz
def _voz_mac():
    """Una voz en castellano de macOS (comando 'say'), o None."""
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


def _elegir_sintetizador():
    """Devuelve una funcion texto -> lista de argumentos, o None si no hay voz."""
    voz = _voz_mac()
    if voz:
        return lambda t: ["say", "-v", voz, t]
    for programa in ("espeak-ng", "espeak"):           # Linux
        if shutil.which(programa):
            return lambda t, p=programa: [p, "-v", "es-419", t]
    if sys.platform.startswith("win") and shutil.which("powershell"):
        def windows(t):
            t = t.replace("'", "''")
            return ["powershell", "-NoProfile", "-Command",
                    "Add-Type -AssemblyName System.Speech; "
                    "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
                    f"$s.Speak('{t}')"]
        return windows
    return None


_SINTETIZADOR = _elegir_sintetizador()


def decir(texto):
    """Lo dice en voz alta si hay voz en castellano; si no, solo lo imprime.

    Espera a terminar de hablar: asi el microfono (modo voz) no escucha al
    propio robot.
    """
    print(f"   🔊 {texto}")
    if _SINTETIZADOR:
        try:
            subprocess.run(_SINTETIZADOR(texto), timeout=15,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:                                  # noqa: BLE001
            pass
