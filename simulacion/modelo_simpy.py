"""
Modelo SimPy del sistema de citas.

Entidad ........ PeticionCita
Recurso ........ servidores (c). La cola es la sala de espera del recurso.
Variables de estado: Q(t)=en_cola, B(t)=servidores ocupados,
                     rechazadas, abandonadas, completadas
Eventos ........ llegada, inicio de servicio, fin de servicio, rechazo
"""
import random
import numpy as np
import simpy

import config
from clases_poo import PeticionCita, TipoTramite, EstadoPeticion
from estadisticas import percentil


class SistemaCitas:
    def __init__(self, env, c, K, rng, markoviano=False):
        self.env = env
        self.rng = rng
        self.c = c
        self.K = K
        self.markoviano = markoviano
        self.servidores = simpy.Resource(env, capacity=c)

        # Variables de estado
        self.en_cola = 0          # Q(t)
        self.llegadas = 0
        self.rechazadas = 0
        self.abandonadas = 0
        self.completadas = 0
        self.peticiones = []      # todas las solicitudes (para calcular KPIs)
        self.hist_Q = []          # Q(t) medido cada 1 s
        self.hist_B = []          # B(t) medido cada 1 s

        if markoviano:            # modo "teórico": sin abandono ni reintento
            self.paciencia = 1e12
            self.prob_reintento = 0.0
        else:
            self.paciencia = config.PACIENCIA
            self.prob_reintento = config.PROB_REINTENTO

    # ---- tiempo de servicio ------------------------------------------------
    def tiempo_servicio(self, tipo):
        if self.markoviano:       # exponencial, igual para todos (supuesto M/M/c)
            return self.rng.expovariate(1.0 / config.SERVICIO_MEDIO_GLOBAL)
        mu, sigma = config.PARAMS_LOGNORMAL[tipo.value]
        return self.rng.lognormvariate(mu, sigma)

    # ---- EVENTO: llegada ---------------------------------------------------
    def recibir(self, tipo, intento=0):
        self.llegadas += 1
        p = PeticionCita(self.llegadas, tipo, self.env.now, intento)
        self.peticiones.append(p)

        if self.en_cola >= self.K:                 # buffer lleno -> RECHAZO
            p.estado = EstadoPeticion.RECHAZADA
            self.rechazadas += 1
            self.posible_reintento(p)
        else:                                      # entra a la cola
            self.en_cola += 1
            self.env.process(self.atender(p))

    # ---- EVENTOS: inicio y fin de servicio (o abandono) ---------------------
    def atender(self, p):
        with self.servidores.request() as req:
            # Espera turno, pero solo hasta agotar la paciencia
            resultado = yield req | self.env.timeout(self.paciencia)
            self.en_cola -= 1

            if req not in resultado:               # ABANDONO
                p.estado = EstadoPeticion.ABANDONADA
                self.abandonadas += 1
                self.posible_reintento(p)
                return

            p.tiempo_inicio_servicio = self.env.now            # inicio servicio
            p.estado = EstadoPeticion.EN_PROCESO
            yield self.env.timeout(self.tiempo_servicio(p.tipo_tramite))
            p.tiempo_fin_servicio = self.env.now               # fin servicio
            p.estado = EstadoPeticion.COMPLETADA
            self.completadas += 1

    # ---- Reintento (C7) -----------------------------------------------------
    def posible_reintento(self, p):
        if p.intento < config.MAX_REINTENTOS and self.rng.random() < self.prob_reintento:
            self.env.process(self.reintentar(p))

    def reintentar(self, p):
        yield self.env.timeout(self.rng.expovariate(1.0 / config.ESPERA_REINTENTO))
        self.recibir(p.tipo_tramite, p.intento + 1)


def generador_llegadas(env, sistema, lam_const=None):
    """Llegadas Poisson NO homogéneas: λ pico las primeras 2 h, luego λ valle."""
    tipos = list(config.MEZCLA.keys())
    pesos = list(config.MEZCLA.values())
    while True:
        if lam_const is not None:
            lam = lam_const                      # λ fijo (para validar M/M/c)
        else:
            lam = config.LAMBDA_PICO if env.now < config.FIN_PICO else config.LAMBDA_VALLE
        yield env.timeout(sistema.rng.expovariate(lam))
        tipo = TipoTramite(sistema.rng.choices(tipos, weights=pesos)[0])
        sistema.recibir(tipo)


def monitor(env, sistema):
    """Cada segundo guarda Q(t) y B(t). Sirve para utilización real y Little."""
    while True:
        sistema.hist_Q.append(sistema.en_cola)
        sistema.hist_B.append(sistema.servidores.count)
        yield env.timeout(1)


def correr_replica(c, K, semilla, horizonte=config.JORNADA,
                   markoviano=False, lam_const=None):
    env = simpy.Environment()
    rng = random.Random(semilla)               # semilla fija -> reproducible
    sistema = SistemaCitas(env, c, K, rng, markoviano)
    env.process(generador_llegadas(env, sistema, lam_const))
    env.process(monitor(env, sistema))
    env.run(until=horizonte)
    return sistema


def metricas(s, t_ini, t_fin):
    """KPIs de las solicitudes que llegaron entre t_ini y t_fin (segundos)."""
    ps = [p for p in s.peticiones if t_ini <= p.tiempo_llegada < t_fin]
    n = len(ps)
    rech = sum(p.estado == EstadoPeticion.RECHAZADA for p in ps)
    aban = sum(p.estado == EstadoPeticion.ABANDONADA for p in ps)
    hechas = [p for p in ps if p.estado == EstadoPeticion.COMPLETADA]
    esperas = [p.calcular_tiempo_espera() for p in hechas]
    en_sistema = [p.calcular_tiempo_sistema() for p in hechas]
    Q = np.array(s.hist_Q[int(t_ini):int(t_fin)])
    B = np.array(s.hist_B[int(t_ini):int(t_fin)])
    return {
        "llegadas": n,
        "rechazo_pct": 100 * rech / n if n else 0.0,
        "abandono_pct": 100 * aban / n if n else 0.0,
        "perdida_pct": 100 * (rech + aban) / n if n else 0.0,
        "espera_media": float(np.mean(esperas)) if esperas else 0.0,
        "espera_p95": percentil(esperas, 95),
        "espera_p99": percentil(esperas, 99),
        "sistema_media": float(np.mean(en_sistema)) if en_sistema else 0.0,
        "util_pct": 100 * float(B.mean()) / s.c,      # utilización MEDIDA
        "Lq": float(Q.mean()),
        "L": float((Q + B).mean()),
        "lambda_ef": (n - rech) / (t_fin - t_ini),     # llegadas que sí entraron
    }
