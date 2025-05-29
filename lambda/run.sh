#!/bin/bash

# Asegura que se ejecuta desde lambda/
cd "$(dirname "$0")"

# Configuración
SCRIPT_NAME="main.py"
ENTRY_POINT="lambda_function.py"
ZIP_NAME="lambda_function.zip"
REQUIREMENTS_FILE="requirements.txt"
PACKAGE_DIR="package"

echo "📦 Empaquetando AWS Lambda desde $(pwd)..."

# Verifica que main.py exista
if [ ! -f "$SCRIPT_NAME" ]; then
  echo "❌ No se encontró $SCRIPT_NAME"
  exit 1
fi

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
# boto3 no se incluye porque ya está en AWS Lambda
EOF
fi

# Limpieza previa
rm -rf "$PACKAGE_DIR" "$ZIP_NAME"

# Crea carpeta temporal
mkdir -p "$PACKAGE_DIR"

# Instala dependencias
echo "⬇️  Instalando dependencias..."
pip install -r "$REQUIREMENTS_FILE" --target "$PACKAGE_DIR" >/dev/null

# Copia el script con nombre requerido por AWS Lambda
cp "$SCRIPT_NAME" "$PACKAGE_DIR/$ENTRY_POINT"

# Empaqueta en zip
echo "🗜️  Empaquetando en $ZIP_NAME..."
cd "$PACKAGE_DIR"
zip -r "../$ZIP_NAME" . >/dev/null
cd ..

# Limpieza
rm -rf "$PACKAGE_DIR"

echo "✅ Lambda empaquetada correctamente: $ZIP_NAME"
