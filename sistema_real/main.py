"""
API REST de agendamiento de citas (sistema real que se despliega en Docker).
- Guarda cada trámite en SQLite  -> datos/citas.db        (persistencia)
- Guarda cada petición en un CSV -> datos/telemetry_log.csv (telemetría)
"""
import csv
import os
import sqlite3
import threading
import time
from contextlib import closing
from datetime import datetime

import psutil
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

DATOS = os.getenv("DATOS_DIR", "datos")
os.makedirs(DATOS, exist_ok=True)
DB = os.path.join(DATOS, "citas.db")
LOG = os.path.join(DATOS, "telemetry_log.csv")
CUPOS_TOTALES = 500
TIPOS = ["AGENDAR", "REPROGRAMAR", "CANCELAR"]

app = FastAPI(title="API Sistema Real - Agendamiento de Citas")
candado = threading.Lock()          # evita que dos peticiones modifiquen cupos a la vez
proceso = psutil.Process()


class SolicitudCita(BaseModel):
    paciente_id: int
    tipo_tramite: str  # AGENDAR, REPROGRAMAR, CANCELAR


def iniciar_db():
    with closing(sqlite3.connect(DB)) as con:
        con.execute("""CREATE TABLE IF NOT EXISTS citas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT, paciente_id INTEGER, tipo_tramite TEXT, status TEXT)""")
        con.commit()


def cupos_disponibles(con):
    """Cupos = totales - agendados + cancelados (calculado desde la BD)."""
    agendados = con.execute("SELECT COUNT(*) FROM citas WHERE tipo_tramite='AGENDAR' "
                            "AND status='COMPLETADO'").fetchone()[0]
    cancelados = con.execute("SELECT COUNT(*) FROM citas WHERE tipo_tramite='CANCELAR' "
                             "AND status='COMPLETADO'").fetchone()[0]
    return min(CUPOS_TOTALES, CUPOS_TOTALES - agendados + cancelados)


def registrar_telemetria(tipo, status, latencia_ms):
    """Una fila por petición: latencia, CPU y RAM del proceso."""
    nuevo = not os.path.exists(LOG)
    with open(LOG, "a", newline="") as f:
        w = csv.writer(f)
        if nuevo:
            w.writerow(["timestamp", "tipo_tramite", "status", "latencia_ms",
                        "cpu_pct", "ram_mb"])
        w.writerow([datetime.now().isoformat(), tipo, status, round(latencia_ms, 3),
                    psutil.cpu_percent(interval=None),
                    round(proceso.memory_info().rss / 1e6, 1)])


iniciar_db()


@app.get("/")
def health_check():
    return {"status": "ok", "mensaje": "API de Citas Médicas operando en contenedor"}


@app.get("/api/v1/cupos")
def consultar_disponibilidad():
    with closing(sqlite3.connect(DB)) as con:
        return {"cupos_restantes": cupos_disponibles(con)}


@app.post("/api/v1/citas")
def procesar_cita(solicitud: SolicitudCita):
    inicio = time.perf_counter()
    if solicitud.tipo_tramite not in TIPOS:
        raise HTTPException(status_code=400, detail="Tipo de trámite no válido")

    with candado, closing(sqlite3.connect(DB)) as con:
        cupos = cupos_disponibles(con)
        if solicitud.tipo_tramite == "AGENDAR" and cupos <= 0:
            status = "RECHAZADO_SIN_CUPO"
        else:
            status = "COMPLETADO"
        con.execute("INSERT INTO citas (fecha, paciente_id, tipo_tramite, status) "
                    "VALUES (?,?,?,?)",
                    (datetime.now().isoformat(), solicitud.paciente_id,
                     solicitud.tipo_tramite, status))
        con.commit()
        cupos = cupos_disponibles(con)

    latencia = (time.perf_counter() - inicio) * 1000
    registrar_telemetria(solicitud.tipo_tramite, status, latencia)
    return {"status": status, "latencia_ms": latencia, "cupos_restantes": cupos}
