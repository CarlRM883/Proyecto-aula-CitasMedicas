import enum

class TipoTramite(enum.Enum):
    AGENDAR = "AGENDAR"
    REPROGRAMAR = "REPROGRAMAR"
    CANCELAR = "CANCELAR"

class EstadoPeticion(enum.Enum):
    EN_COLA = "EN_COLA"
    EN_PROCESO = "EN_PROCESO"
    COMPLETADA = "COMPLETADA"
    RECHAZADA = "RECHAZADA"

class PeticionCita:
    def __init__(self, id_peticion: int, tipo_tramite: TipoTramite, tiempo_llegada: float):
        self.id = id_peticion
        self.tipo_tramite = tipo_tramite
        self.tiempo_llegada = tiempo_llegada
        self.tiempo_inicio_servicio = 0.0
        self.tiempo_fin_servicio = 0.0
        self.estado = EstadoPeticion.EN_COLA

    def calcular_tiempo_espera(self) -> float:
        return self.tiempo_inicio_servicio - self.tiempo_llegada

    def calcular_tiempo_sistema(self) -> float:
        return self.tiempo_fin_servicio - self.tiempo_llegada