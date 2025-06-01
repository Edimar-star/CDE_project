#!/bin/bash

# ---------------------- LAMBDA ------------------------------
cd "$(dirname "$0")"

SCRIPT_NAME="main.py"
ENTRY_POINT="lambda_function.py"
ZIP_NAME="lambda_function.zip"

echo "📦 Empaquetando Lambda desde $(pwd)..."

if [ ! -f "$SCRIPT_NAME" ]; then
  echo "❌ No se encontró $SCRIPT_NAME"
  exit 1
fi

# Limpieza previa
rm -f "$ZIP_NAME"

# Copia y empaqueta solo el código
cp "$SCRIPT_NAME" "$ENTRY_POINT"
zip "$ZIP_NAME" "$ENTRY_POINT" >/dev/null
rm "$ENTRY_POINT"

echo "✅ Lambda empaquetada: $ZIP_NAME"


# ------------------- LAYER -------------------------
# Variables
LAYER_DIR="layer"
ZIP_NAME="lambda_layer.zip"
REQUIREMENTS="requirements.txt"

echo "📦 Empaquetando Lambda Layer personalizada..."

# Limpieza
rm -rf "$LAYER_DIR" "$ZIP_NAME"

# Crear estructura
mkdir -p "$LAYER_DIR/python"

# Instalar todas las dependencias
pip install -r "$REQUIREMENTS" -t "$LAYER_DIR/python" >/dev/null

# Limpiar archivos innecesarios
find "$LAYER_DIR" -type d -name "__pycache__" -exec rm -rf {} +
find "$LAYER_DIR" -type d -name "tests" -exec rm -rf {} +
find "$LAYER_DIR" -name "*.pyc" -delete

# Empaquetar
cd "$LAYER_DIR"
zip -r9 "../$ZIP_NAME" . >/dev/null
cd ..

rm -rf "$LAYER_DIR"

echo "✅ Layer lista: $ZIP_NAME"
