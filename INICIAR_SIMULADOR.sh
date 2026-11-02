#!/usr/bin/env bash
# ============================================================
#   Programacion I - TP02
#   Levanta el simulador oficial de Unitree listo para el TP.
# ============================================================
cd "$(dirname "$0")" || exit 1

echo "============================================================"
echo "   Programacion I"
echo "   Simulador de robots Unitree"
echo "============================================================"
echo
echo "   Que robot queres usar?"
echo
echo "     1)  G1   - robot humanoide (camina en dos patas)"
echo "     2)  Go2  - robot perro     (camina en cuatro patas)"
echo
read -r -p "   Elegi 1 o 2 [1]: " OPCION

case "$OPCION" in
  2) ROBOT="go2" ;;
  *) ROBOT="g1"  ;;
esac
echo
echo "   Revisando que este todo instalado..."
echo "   (la primera vez puede tardar unos minutos)"
echo

# Buscamos un Python que ademas pueda abrir la ventana 3D. Una maquina puede
# tener varios Python y que solo uno tenga MuJoCo: si elegimos el primero que
# aparece, el simulador arranca sin ventana y parece roto.
# Se prueban en orden y gana el PRIMERO que tenga MuJoCo. Los nombres con
# version explicita estan porque en algunas distros `python3` apunta a una
# version vieja y la buena esta al lado.
CANDIDATOS="python3 python3.13 python3.12 python3.11 python3.10 python"
[ -x "$HOME/.venvs/unitree/bin/python" ] && CANDIDATOS="$HOME/.venvs/unitree/bin/python $CANDIDATOS"

PYTHON=""; PRIMERO=""
for PY in $CANDIDATOS; do
  command -v "$PY" >/dev/null 2>&1 || [ -x "$PY" ] || continue
  [ -z "$PRIMERO" ] && PRIMERO="$PY"
  if "$PY" -c "import mujoco" >/dev/null 2>&1; then PYTHON="$PY"; break; fi
done
[ -z "$PYTHON" ] && PYTHON="$PRIMERO"

if [ -z "$PYTHON" ]; then
  echo
  echo "   ============================================================"
  echo "   NO ENCUENTRO PYTHON"
  echo "   ============================================================"
  echo
  echo "   En Ubuntu o Debian:"
  echo "       sudo apt install python3 python3-pip"
  echo
  echo "   En Fedora:"
  echo "       sudo dnf install python3 python3-pip"
  echo
  echo "   En macOS (con Homebrew):"
  echo "       brew install python"
  echo "   ============================================================"
  echo
  read -r -p "   Enter para cerrar..."; exit 1
fi

# macOS: el visor 3D de MuJoCo (launch_passive) solo abre bajo `mjpython`, que
# viene con el paquete mujoco. Con python3 comun el simulador cae a modo
# consola. Buscamos el mjpython del MISMO Python que tiene MuJoCo.
SIMPY="$PYTHON"
if [ "$(uname)" = "Darwin" ]; then
  MJPY=$("$PYTHON" -c 'import os,sys,sysconfig
c=[os.path.join(os.path.dirname(sys.executable),"mjpython"),os.path.join(sysconfig.get_path("scripts"),"mjpython")]
for s in ("osx_framework_user","posix_user"):
    try: c.append(os.path.join(sysconfig.get_path("scripts",s),"mjpython"))
    except KeyError: pass
print(next((x for x in c if os.access(x,os.X_OK)),""))' 2>/dev/null)
  [ -z "$MJPY" ] && MJPY=$(command -v mjpython 2>/dev/null)
  if [ -n "$MJPY" ]; then
    SIMPY="$MJPY"
  else
    echo "   Aviso: no encuentro mjpython; el simulador va a abrir en modo consola."
    echo "   Reinstala MuJoCo con:  $PYTHON -m pip install --user --force-reinstall mujoco"
  fi
fi

cd entorno || exit 1
"$SIMPY" -m sim --robot "$ROBOT" --materia tp02

echo
read -r -p "El simulador se cerro. Enter para salir..."
