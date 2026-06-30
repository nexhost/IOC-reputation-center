#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "[IOC Reputation Center] Instalando dependencias del sistema..."
if command -v apt >/dev/null 2>&1; then
    sudo apt update
    sudo apt install python3 python3-pip python3-venv git build-essential python3-dev libffi-dev libcairo2 libpango-1.0-0 libpangoft2-1.0-0 libgdk-pixbuf-2.0-0 shared-mime-info -y
else
    echo "Este instalador automatico esta preparado para Kali Linux / Ubuntu con apt."
    echo "Instale Python 3.11+, python3-venv y las dependencias graficas requeridas por WeasyPrint manualmente."
fi

cd "$PROJECT_DIR"

echo "[IOC Reputation Center] Creando entorno virtual..."
python3 -m venv .venv

echo "[IOC Reputation Center] Instalando paquetes Python..."
.venv/bin/python -m pip install --upgrade pip
.venv/bin/pip install -r requirements.txt

if [ ! -f .env ]; then
    cp .env.example .env
    echo "[IOC Reputation Center] Archivo .env creado desde .env.example."
else
    echo "[IOC Reputation Center] Archivo .env existente conservado."
fi

mkdir -p reports exports logs

echo
echo "Instalacion completada."
echo "Para iniciar la herramienta:"
echo "  source .venv/bin/activate"
echo "  uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"
echo
echo "Acceso local:"
echo "  http://127.0.0.1:8000"
