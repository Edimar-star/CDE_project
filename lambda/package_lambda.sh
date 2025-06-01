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
PACKAGE="sodapy"

echo "📦 Empaquetando Lambda Layer para '${PACKAGE}'..."

# Limpieza previa
rm -rf "$LAYER_DIR" "$ZIP_NAME"

# Crear estructura esperada por AWS
mkdir -p "$LAYER_DIR/python"

# Instalar la librería en el directorio adecuado
echo "⬇️  Instalando ${PACKAGE} en ${LAYER_DIR}/python..."
pip install "${PACKAGE}" -t "${LAYER_DIR}/python" >/dev/null

# Limpieza de archivos innecesarios
echo "🧹 Limpiando archivos no necesarios..."
find "$LAYER_DIR" -type d -name "__pycache__" -exec rm -rf {} +
find "$LAYER_DIR" -type d -name "tests" -exec rm -rf {} +
find "$LAYER_DIR" -name "*.pyc" -delete

# Empaquetar en .zip
echo "📦 Creando archivo ZIP: $ZIP_NAME..."
cd "$LAYER_DIR"
zip -r9 "../$ZIP_NAME" . >/dev/null
cd ..

# Limpiar carpeta temporal
rm -rf "$LAYER_DIR"

echo "✅ Layer generado: $ZIP_NAME"