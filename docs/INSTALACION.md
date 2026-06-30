# Guia de instalacion

## Requisitos

- Python 3.11 o superior
- Git
- Acceso a internet para instalar dependencias y consultar fuentes externas
- API keys opcionales para AbuseIPDB y VirusTotal

En Kali Linux / Ubuntu, instale tambien librerias del sistema usadas por dependencias como WeasyPrint:

```bash
sudo apt install build-essential python3-dev libffi-dev libcairo2 libpango-1.0-0 libpangoft2-1.0-0 libgdk-pixbuf-2.0-0 shared-mime-info -y
```

## Instalacion en Windows

```powershell
cd C:\xampp\htdocs\IOC-reputation-center
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python run.py
```

Si PowerShell bloquea el entorno virtual:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Abrir en el navegador:

```text
http://127.0.0.1:8000
```

## Instalacion en Kali Linux / Ubuntu

```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv git build-essential python3-dev libffi-dev libcairo2 libpango-1.0-0 libpangoft2-1.0-0 libgdk-pixbuf-2.0-0 shared-mime-info -y
git clone <url-del-repositorio>
cd IOC-reputation-center
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## Acceso desde otra maquina

Levantar el servidor escuchando en todas las interfaces:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Luego acceder desde otro equipo de la red:

```text
http://IP_DEL_SERVIDOR:8000
```

En Windows puede ser necesario permitir el puerto en el firewall:

```powershell
New-NetFirewallRule -DisplayName "IOC FastAPI 8000" -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow
```

## Variables de entorno

Copiar `.env.example` a `.env` y completar las llaves disponibles:

```env
APP_NAME=IOC Reputation Center
APP_ENV=development
SECRET_KEY=change-this-local-secret
DATABASE_URL=sqlite:///./ioc_reputation.db

THREATFOX_API_URL=https://threatfox-api.abuse.ch/api/v1/
URLHAUS_API_URL=https://urlhaus-api.abuse.ch/v1/
ABUSEIPDB_API_KEY=
VIRUSTOTAL_API_KEY=
OTX_API_KEY=
HIBP_API_KEY=
REQUEST_TIMEOUT=12
```

Para consultas IOC, las llaves importantes son:

- `ABUSEIPDB_API_KEY`
- `VIRUSTOTAL_API_KEY`

## Verificacion

Comprobar estado de la aplicacion:

```text
http://127.0.0.1:8000/health
```

Credenciales iniciales:

```text
Email: analista@soc.local
Password: admin123
```
