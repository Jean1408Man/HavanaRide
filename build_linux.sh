#!/bin/bash
# ============================================================
#  build_linux.sh — Corre y construye en Ubuntu/Linux
#  Uso: bash build_linux.sh
# ============================================================

set -e

echo ""
echo " === HAVANA RIDE — Build para Linux ==="
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 no encontrado. Instala con: sudo apt install python3 python3-pip"
    exit 1
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$ROOT_DIR/.venv"
PYTHON="$VENV_DIR/bin/python"

echo "[1/3] Preparando entorno virtual..."
if [ ! -x "$PYTHON" ]; then
    python3 -m venv "$VENV_DIR" || {
        echo "ERROR: No se pudo crear el entorno virtual."
        echo "Instala primero: sudo apt install python3-venv"
        exit 1
    }
fi

echo "[1/3] Instalando dependencias..."
"$PYTHON" -m pip install -r requirements.txt --quiet

# Optional: install SDL2 system deps for pygame
if command -v apt &> /dev/null; then
    sudo apt-get install -y python3-pygame libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev 2>/dev/null || true
fi

# Run directly (for testing)
echo ""
echo "[2/3] Opciones:"
echo "  1) Ejecutar directamente (para testear)"
echo "  2) Crear ejecutable portable"
echo ""
read -p "Elige [1/2]: " choice

if [ "$choice" = "1" ]; then
    echo "[3/3] Ejecutando juego..."
    "$PYTHON" "$ROOT_DIR/main.py"

elif [ "$choice" = "2" ]; then
    echo "[3/3] Creando ejecutable..."
    "$PYTHON" -m PyInstaller --onefile --windowed --name "HavanaRide" \
        --add-data "assets:assets" \
        "$ROOT_DIR/main.py"
    echo ""
    echo " Ejecutable listo en: dist/HavanaRide"
    echo " Puedes ejecutarlo con: ./dist/HavanaRide"
fi

echo ""
echo " ¡Listo! ❤️"
