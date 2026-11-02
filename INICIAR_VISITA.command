#!/usr/bin/env bash
# ============================================================
#   Visita del humanoide G1 - Demo en simulador (macOS / Linux)
#   Doble clic (macOS) o:  bash INICIAR_VISITA.command
#   Instala lo que falte, abre el simulador y arranca la demo.
# ============================================================
cd "$(dirname "$0")" || exit 1
VENV="$HOME/.venvs/unitree"
LOG="$PWD/simulador.log"
pausa() { echo; read -r -p "   Enter para cerrar..." _; }

echo "============================================================"
echo "   Visita del humanoide G1 - UADE"
echo "============================================================"

# 1) Python
if [ ! -x "$VENV/bin/python" ]; then
  BASE=""
  # Ademas del PATH, las carpetas donde instalan python.org y Homebrew: el
  # Python de Apple (3.9) suele aparecer primero y no sirve.
  CANDIDATOS="python3.14 python3.13 python3.12 python3.11 python3.10 python3"
  for D in /Library/Frameworks/Python.framework/Versions/3.*/bin /opt/homebrew/bin /usr/local/bin; do
    for V in 3.14 3.13 3.12 3.11 3.10; do
      [ -x "$D/python$V" ] && CANDIDATOS="$CANDIDATOS $D/python$V"
    done
  done
  for PY in $CANDIDATOS; do
    if { command -v "$PY" >/dev/null 2>&1 || [ -x "$PY" ]; } && "$PY" -c 'import sys; exit(sys.version_info < (3,10))' 2>/dev/null; then
      BASE="$PY"; break
    fi
  done
  if [ -z "$BASE" ]; then
    echo "   No encuentro Python 3.10 o mas nuevo."
    echo "   (el que trae macOS es 3.9 y MuJoCo no funciona con ese)"
    echo
    echo "   1. Entra a https://www.python.org/downloads/ y baja el instalador"
    echo "   2. Instalalo y despues abri 'Install Certificates.command'"
    echo "   3. Cerra la Terminal (Cmd+Q) y volve a abrir este archivo"
    command -v open >/dev/null 2>&1 && open "https://www.python.org/downloads/"
    pausa; exit 1
  fi
  echo "   Creando entorno en $VENV (solo la primera vez)..."
  "$BASE" -m venv "$VENV" || { echo "   No pude crear el entorno."; pausa; exit 1; }
fi
PY="$VENV/bin/python"

# 2) MuJoCo
if ! "$PY" -c "import mujoco" >/dev/null 2>&1; then
  echo "   Instalando MuJoCo (solo la primera vez, puede tardar)..."
  "$PY" -m pip install -q --upgrade pip >/dev/null 2>&1
  "$PY" -m pip install -q mujoco \
    || "$PY" -m pip install -q mujoco --trusted-host pypi.org --trusted-host files.pythonhosted.org \
    || { echo "   No pude instalar MuJoCo. Revisa la conexion a internet."; pausa; exit 1; }
fi
echo "   [OK] MuJoCo $("$PY" -c 'import mujoco; print(mujoco.__version__)')"

# 2b) Extras: voz y camara. Son OPCIONALES: si no se instalan, la demo anda
#     igual con el menu y el juego se juega con el teclado.
if ! "$PY" -c "import vosk, sounddevice" >/dev/null 2>&1; then
  echo "   Instalando el control por voz (solo la primera vez)..."
  "$PY" -m pip install -q vosk sounddevice >/dev/null 2>&1 \
    && echo "   [OK] Voz" \
    || echo "   Aviso: no pude instalar la voz. Queda el menu."
fi
VISION="$HOME/.venvs/unitree-vision"
if ! "$PY" -c "import cv2, mediapipe" >/dev/null 2>&1 && [ ! -x "$VISION/bin/python" ]; then
  echo "   Instalando la vision por camara (solo la primera vez, puede tardar)..."
  # (si mediapipe no trae OpenCV, se agrega opencv-python)
  if "$PY" -m pip install -q mediapipe >/dev/null 2>&1 \
     && { "$PY" -c "import cv2" >/dev/null 2>&1 || "$PY" -m pip install -q opencv-python >/dev/null 2>&1; } \
     && "$PY" -c "import cv2, mediapipe" >/dev/null 2>&1; then
    echo "   [OK] Camara"
  else
    # MediaPipe tarda en salir para cada Python nuevo. Si no hay para este,
    # armamos un entorno aparte con un Python compatible (3.12 a 3.10).
    VPY=""
    for V in 3.12 3.11 3.10; do
      for C in "python$V" /Library/Frameworks/Python.framework/Versions/$V/bin/python$V \
               /opt/homebrew/bin/python$V /usr/local/bin/python$V; do
        if command -v "$C" >/dev/null 2>&1 || [ -x "$C" ]; then VPY="$C"; break 2; fi
      done
    done
    if [ -n "$VPY" ] && "$VPY" -m venv "$VISION" >/dev/null 2>&1 \
       && "$VISION/bin/python" -m pip install -q mediapipe >/dev/null 2>&1 \
       && { "$VISION/bin/python" -c "import cv2" >/dev/null 2>&1 || "$VISION/bin/python" -m pip install -q opencv-python >/dev/null 2>&1; } \
       && "$VISION/bin/python" -c "import cv2, mediapipe" >/dev/null 2>&1; then
      echo "   [OK] Camara (con $VPY aparte)"
    else
      rm -rf "$VISION"
      echo "   Aviso: no pude instalar la camara (MediaPipe necesita Python 3.10 a 3.12)."
      echo "          Piedra, papel o tijera se juega con el teclado."
    fi
  fi
fi

# 3) En macOS la ventana 3D solo abre con mjpython
SIMPY="$PY"
if [ "$(uname)" = "Darwin" ]; then
  if [ -x "$VENV/bin/mjpython" ]; then SIMPY="$VENV/bin/mjpython"
  else echo "   Aviso: falta mjpython; el simulador abrira en modo consola."; fi
fi

# 4) Simulador en segundo plano
if "$PY" -c "import socket; socket.create_connection(('127.0.0.1', 8765), 1)" >/dev/null 2>&1; then
  echo "   Ya hay un simulador abierto: lo uso."
  SIM_PID=""
else
  echo "   Abriendo el simulador (G1)... la ventana 3D puede quedar detras de la Terminal."
  ( cd entorno && exec "$SIMPY" -m sim --robot g1 --materia tp02 ) > "$LOG" 2>&1 < /dev/null &
  SIM_PID=$!
  trap '[ -n "$SIM_PID" ] && kill "$SIM_PID" 2>/dev/null' EXIT
  for _ in $(seq 1 60); do
    "$PY" -c "import socket; socket.create_connection(('127.0.0.1', 8765), 1)" >/dev/null 2>&1 && break
    if ! kill -0 "$SIM_PID" 2>/dev/null; then
      echo "   El simulador se cerro al arrancar. Detalle:"; tail -20 "$LOG"; pausa; exit 1
    fi
    sleep 0.5
  done
  sleep 1
fi

# 5) Demo
echo
"$PY" mi_desarrollo/demo_visita.py "$@"
echo
echo "   Al cerrar esta ventana se cierra tambien el simulador."
pausa
