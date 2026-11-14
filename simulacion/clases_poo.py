import enum


class TipoTramite(enum.Enum):
    AGENDAR = "AGENDAR"
    REPROGRAMAR = "REPROGRAMAR"
    CANCELAR = "CANCELAR"


class EstadoPeticion(enum.Enum):
    EN_COLA = "EN_COLA"
    EN_PROCESO = "EN_PROCESO"
    COMPLETADA = "COMPLETADA"
    RECHAZADA = "RECHAZADA"      # buffer lleno (cola = K)
    ABANDONADA = "ABANDONADA"    # se cansó de esperar (paciencia agotada)


class PeticionCita:
    """La ENTIDAD del modelo: una solicitud de un paciente."""

    def __init__(self, id_peticion: int, tipo_tramite: TipoTramite,
                 tiempo_llegada: float, intento: int = 0):
        self.id = id_peticion
        self.tipo_tramite = tipo_tramite
        self.tiempo_llegada = tiempo_llegada
        self.intento = intento                # 0 = primer intento, 1 = reintento
        self.tiempo_inicio_servicio = 0.0
        self.tiempo_fin_servicio = 0.0
        self.estado = EstadoPeticion.EN_COLA

    def calcular_tiempo_espera(self) -> float:
        return self.tiempo_inicio_servicio - self.tiempo_llegada

    def calcular_tiempo_sistema(self) -> float:
        return self.tiempo_fin_servicio - self.tiempo_llegada
