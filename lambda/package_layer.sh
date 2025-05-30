#!/bin/bash

cd "$(dirname "$0")"

LAYER_DIR="layer"
REQUIREMENTS_FILE="requirements.txt"
ZIP_NAME="lambda_layer.zip"

echo "📦 Empaquetando Lambda Layer desde $(pwd)..."

# Crea requirements.txt si no existe
if [ ! -f "$REQUIREMENTS_FILE" ]; then
  echo "📝 Generando $REQUIREMENTS_FILE..."
  cat <<EOF > $REQUIREMENTS_FILE
scipy
netCDF4
sodapy
pandas
numpy
requests
EOF
fi

# Limpieza previa
rm -rf "$LAYER_DIR" "$ZIP_NAME"

# Crear estructura esperada por AWS para un Layer
mkdir -p "$LAYER_DIR/python"

echo "⬇️  Instalando dependencias en $LAYER_DIR/python..."
pip install -r "$REQUIREMENTS_FILE" -t "$LAYER_DIR/python" >/dev/null

# Elimina archivos innecesarios
find "$LAYER_DIR" -type d -name "__pycache__" -exec rm -rf {} +
find "$LAYER_DIR" -type d -name "tests" -exec rm -rf {} +
find "$LAYER_DIR" -name "*.pyc" -delete

# Empaquetar el layer
cd "$LAYER_DIR"
zip -r9 "../$ZIP_NAME" . >/dev/null
cd ..

# Limpieza
rm -rf "$LAYER_DIR"

echo "✅ Lambda Layer empaquetado: $ZIP_NAME"
