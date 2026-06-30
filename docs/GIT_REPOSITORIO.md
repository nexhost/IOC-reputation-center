# Preparacion del repositorio Git

## Archivos incluidos

El proyecto esta preparado para subir a Git con:

- Codigo fuente en `app/`
- Documentacion en `README.md` y `docs/`
- Plantilla de configuracion en `.env.example`
- Dependencias en `requirements.txt`
- `.gitignore` para excluir secretos y archivos generados

## Archivos que no deben subirse

El `.gitignore` excluye:

- `.env`
- `.venv/`
- `venv/`
- Bases locales `*.db`, `*.sqlite`, `*.sqlite3`
- Logs
- Cache de Python
- Reportes generados en `reports/`
- Exportaciones generadas en `exports/`

## Inicializar repositorio

```bash
git init
git add .
git commit -m "Initial release of IOC Reputation Center"
```

## Conectar remoto

```bash
git branch -M main
git remote add origin <url-del-repositorio>
git push -u origin main
```

## Checklist antes del push

- Confirmar que `.env` no aparece en `git status`.
- Confirmar que `ioc_reputation.db` no aparece en `git status`.
- Revisar que no haya API keys reales en `README.md`, `docs/` o capturas.
- Ejecutar la aplicacion localmente y validar `/health`.
- Probar una consulta IOC desde `/consulta`.

## Mantenimiento recomendado

- Mantener `requirements.txt` actualizado.
- Documentar cambios relevantes en el README.
- No versionar reportes generados.
- Rotar API keys si se sospecha exposicion accidental.

## Autor

IOC Reputation Center fue desarrollado por:

Kendry Rosario  
Lic. en Tecnologia de la Informacion con maestria en Ciberseguridad  
kendry.rosario@gmail.com
