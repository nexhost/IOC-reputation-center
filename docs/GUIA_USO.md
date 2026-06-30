# Guia de uso

## Inicio de sesion

Abrir la aplicacion en el navegador:

```text
http://127.0.0.1:8000
```

Credenciales iniciales:

```text
Email: analista@soc.local
Password: admin123
```

## Consulta de IOC

Entrar a `/consulta` e ingresar uno de los siguientes indicadores:

- IP
- Dominio
- URL
- MD5
- SHA1
- SHA256

Cada IOC se consulta contra:

- ThreatFox
- URLHaus
- AbuseIPDB
- VirusTotal

La herramienta guarda un resultado por fuente. Si una fuente no aplica para el tipo de IOC, el resultado queda como `No aplica`. Si una fuente requiere API key y no esta configurada, queda como `Sin API key`.

## Interpretacion del score

- 0-20: Bajo
- 21-40: Moderado
- 41-60: Alto
- 61-80: Critico
- 81-100: Malicioso

El score final se calcula a partir de los resultados entregados por las fuentes de inteligencia.

## Fuentes

En `/fuentes` se pueden revisar y actualizar:

- URL base de cada API
- API key
- Estado de la integracion

ThreatFox y URLHaus pueden funcionar sin llave. AbuseIPDB y VirusTotal requieren credenciales para consultas reales.

## Historial

En `/historial` se pueden revisar las consultas realizadas, filtrar por IOC, tipo y veredicto, y eliminar registros cuando sea necesario.

## Casos

En `/casos` se pueden crear investigaciones, asociar IOC y registrar eventos de seguimiento.

## Reportes

En `/reportes` se pueden generar archivos:

- HTML
- PDF
- JSON
- CSV

Los reportes generados se guardan localmente en `reports/`.

## Seguridad operativa

- No subir `.env` al repositorio.
- No compartir API keys en capturas o reportes.
- Usar la herramienta para analisis defensivo.
- Validar hallazgos criticos con evidencia adicional del SIEM, EDR o firewall.

## Desarrollador

Kendry Rosario  
Lic. en Tecnologia de la Informacion con maestria en Ciberseguridad  
kendry.rosario@gmail.com
