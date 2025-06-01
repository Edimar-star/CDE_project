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

# Limpieza previa
echo "🧹 Limpiando archivos anteriores..."
rm -rf "$LAYER_DIR" "$ZIP_NAME"

# Crear estructura esperada por Lambda
mkdir -p "$LAYER_DIR/python"

# Verificación de requirements
if [ ! -f "$REQUIREMENTS" ]; then
  echo "❌ No se encontró $REQUIREMENTS"
  exit 1
fi

# Instalar dependencias
echo "⬇️ Instalando dependencias desde $REQUIREMENTS..."
pip3 install -t "$LAYER_DIR/python" -r "$REQUIREMENTS" --no-cache-dir >/dev/null

# Limpiar archivos innecesarios
echo "🧽 Limpiando archivos innecesarios..."
find "$LAYER_DIR" -type d -name "__pycache__" -exec rm -rf {} +
find "$LAYER_DIR" -type d -name "tests" -exec rm -rf {} +
find "$LAYER_DIR" -name "*.pyc" -delete
find "$LAYER_DIR" -name "*.dist-info" -exec rm -rf {} +

# Empaquetar
echo "📦 Creando archivo ZIP..."
cd "$LAYER_DIR"
zip -r "../$ZIP_NAME" . >/dev/null
cd ..

# Limpieza opcional
rm -rf "$LAYER_DIR"

echo "✅ Layer empaquetado correctamente: $ZIP_NAME"
