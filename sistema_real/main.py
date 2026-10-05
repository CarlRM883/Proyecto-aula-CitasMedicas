import time
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="API Sistema Real - Agendamiento de Citas")

class SolicitudCita(BaseModel):
    paciente_id: int
    tipo_tramite: str  # AGENDAR, REPROGRAMAR, CANCELAR

cupos_disponibles = 500

@app.get("/")
def health_check():
    return {"status": "ok", "mensaje": "API de Citas Médicas operando en contenedor"}

@app.post("/api/v1/citas")
def procesar_cita(solicitud: SolicitudCita):
    global cupos_disponibles
    start_time = time.time()
    
    if solicitud.tipo_tramite not in ["AGENDAR", "REPROGRAMAR", "CANCELAR"]:
        raise HTTPException(status_code=400, detail="Tipo de trámite no válido")

    if solicitud.tipo_tramite == "AGENDAR":
        if cupos_disponibles <= 0:
            status = "RECHAZADO_SIN_CUPO"
        else:
            cupos_disponibles -= 1
            status = "COMPLETADO"
    else:
        status = "COMPLETADO"

    latencia = (time.time() - start_time) * 1000

    return {
        "status": status, 
        "latencia_ms": latencia, 
        "cupos_restantes": cupos_disponibles
    }