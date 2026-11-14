# Sistema de agendamiento de citas médicas vía API — Grupo 5

Proyecto de Aula · Modelos y Simulación (2026-2) · I.U. Pascual Bravo

## Qué hay en cada carpeta
| Carpeta | Contenido |
|:---|:---|
| `sistema_real/` | API REST (FastAPI) con base de datos SQLite y telemetría en CSV |
| `simulacion/` | Modelo SimPy: `config.py` (parámetros), `modelo_simpy.py` (modelo), `main.py` (experimentos) |
| `analisis/` | `contraste_mmc.py` (M/M/c vs SimPy) y `resumen_telemetria.py` |
| `pruebas/` | `locustfile.py` (prueba de carga contra la API) |
| `datos/` | `citas.db` y `telemetry_log.csv` (los crea la API al correr) |
| `docs/` | `INFORME_FINAL.md`, figuras y tablas generadas |

## 1. Levantar la API (un comando)
```bash
docker compose up --build -d
```
Probar: `http://localhost:8000/docs` (Swagger) o
```bash
curl -X POST http://localhost:8000/api/v1/citas -H "Content-Type: application/json" \
     -d '{"paciente_id": 1, "tipo_tramite": "AGENDAR"}'
```

## 2. Generar telemetría (prueba de carga)
```bash
pip install -r requirements-sim.txt
locust -f pruebas/locustfile.py --headless -u 50 -r 10 -t 60s --host http://localhost:8000 --csv datos/locust
python analisis/resumen_telemetria.py
```

## 3. Ejecutar los experimentos SimPy (un comando)
```bash
pip install -r requirements-sim.txt
python simulacion/main.py            # políticas + sensibilidad -> docs/tablas_resultados.md y docs/figuras/
python analisis/contraste_mmc.py     # M/M/c vs SimPy         -> docs/tabla_contraste.md
```
Las semillas son fijas (42..71), así que los resultados se pueden reproducir.
