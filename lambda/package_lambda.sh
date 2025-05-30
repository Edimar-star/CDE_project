#!/bin/bash

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
