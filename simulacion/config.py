"""
Parámetros del modelo. TODO el tiempo está en SEGUNDOS.
Si algo cambia en el informe, se cambia aquí y en ningún otro lado.
"""
import math

# --- Horizonte y demanda -------------------------------------------------
JORNADA = 28800          # 8 horas (7:00 a 15:00) en segundos
FIN_PICO = 7200          # el pico dura las primeras 2 horas (7:00-9:00)
LAMBDA_PICO = 1.5        # llegadas/seg en pico  (= 5400 sol/h)  -> sobrecarga
LAMBDA_VALLE = 0.2       # llegadas/seg en valle (= 720 sol/h)

# --- Mezcla de trámites ---------------------------------------------------
MEZCLA = {"AGENDAR": 0.60, "REPROGRAMAR": 0.25, "CANCELAR": 0.15}

# --- Tiempo de servicio: Lognormal (2 parámetros: media y CV) -------------
SERVICIO_MEDIA = {"AGENDAR": 3.5, "REPROGRAMAR": 3.0, "CANCELAR": 1.0}  # seg
SERVICIO_CV = 0.5                 # CV = desviación / media
SERVICIO_MEDIO_GLOBAL = 3.0       # media ponderada (0.6*3.5+0.25*3+0.15*1) = 3.0 s

def parametros_lognormal(media, cv):
    """Convierte (media, CV) a los (mu, sigma) que pide random.lognormvariate."""
    sigma2 = math.log(1 + cv ** 2)
    return math.log(media) - sigma2 / 2, math.sqrt(sigma2)

PARAMS_LOGNORMAL = {t: parametros_lognormal(m, SERVICIO_CV)
                    for t, m in SERVICIO_MEDIA.items()}

# --- Comportamiento del paciente (C7: abandono y reintento) ---------------
PACIENCIA = 40            # seg máx. esperando en cola (timeout del cliente)
PROB_REINTENTO = 0.30     # prob. de volver a intentar tras rechazo/abandono
ESPERA_REINTENTO = 20     # seg promedio antes de reintentar (exponencial)
MAX_REINTENTOS = 1        # solo un reintento por solicitud

# --- Experimento -----------------------------------------------------------
REPLICAS = 30
SEMILLA_BASE = 42         # semillas 42..71

# --- SLA (umbrales aceptables) ---------------------------------------------
SLA_ESPERA_P95 = 5.0      # seg, p95 del tiempo de espera en cola (pico)
SLA_PERDIDA = 5.0         # %, rechazo + abandono en pico
SLA_UTIL = (70.0, 85.0)   # %, utilización de servidores en pico
SLA_COLA_FINAL = 5        # solicitudes en cola al cierre

# --- Políticas a comparar (c = servidores, K = tamaño de cola) -------------
POLITICAS = [
    {"nombre": "Actual (c=4, K=60)", "c": 4, "K": 60},
    {"nombre": "Alt. 1 (c=5, K=60)", "c": 5, "K": 60},
    {"nombre": "Alt. 2 (c=6, K=60)", "c": 6, "K": 60},
]
