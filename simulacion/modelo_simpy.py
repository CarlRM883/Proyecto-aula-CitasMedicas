import random
import simpy
import numpy as np
from clases_poo import PeticionCita, TipoTramite, EstadoPeticion

# Parámetros del modelo SimPy v0
CAPACIDAD_SERVIDORES = 4      # c = 4
CAPACIDAD_COLA = 60          # K = 60
TIEMPO_SERVICIO_MEDIO = 3.0  # 3 segundos por trámite
TIEMPO_SIMULACION = 28800     # 8 horas (7:00 AM - 3:00 PM)

LAMBDA_PICO = 1.0            # 3600 solicitudes/h (1 sol/segundo)
LAMBDA_VALLE = 0.2           # 720 solicitudes/h (0.2 sol/segundo)

class SistemaCitasSimPy:
    def __init__(self, env):
        self.env = env
        self.servidores = simpy.Resource(env, capacity=CAPACIDAD_SERVIDORES)
        self.cola_actual = 0
        self.rechazadas_buffer_lleno = 0
        self.total_llegadas = 0
        self.tiempos_espera = []

    def atender_peticion(self, peticion: PeticionCita):
        with self.servidores.request() as req:
            yield req
            self.cola_actual -= 1
            peticion.tiempo_inicio_servicio = self.env.now
            peticion.estado = EstadoPeticion.EN_PROCESO
            
            tiempo_servicio = random.expovariate(1.0 / TIEMPO_SERVICIO_MEDIO)
            yield self.env.timeout(tiempo_servicio)
            
            peticion.tiempo_fin_servicio = self.env.now
            peticion.estado = EstadoPeticion.COMPLETADA
            self.tiempos_espera.append(peticion.calcular_tiempo_espera())

def generador_llegadas(env, sistema):
    peticion_id = 0
    while True:
        # Horas pico primeras 2 horas (7200 s)
        lambda_actual = LAMBDA_PICO if env.now < 7200 else LAMBDA_VALLE
        
        yield env.timeout(random.expovariate(lambda_actual))
        
        peticion_id += 1
        sistema.total_llegadas += 1
        
        tipo = random.choices(
            [TipoTramite.AGENDAR, TipoTramite.REPROGRAMAR, TipoTramite.CANCELAR],
            weights=[0.60, 0.25, 0.15]
        )[0]
        
        peticion = PeticionCita(peticion_id, tipo, env.now)
        
        if sistema.cola_actual >= CAPACIDAD_COLA:
            sistema.rechazadas_buffer_lleno += 1
            peticion.estado = EstadoPeticion.RECHAZADA
        else:
            sistema.cola_actual += 1
            env.process(sistema.atender_peticion(peticion))

if __name__ == "__main__":
    print("Ejecución metricas modelo simpy v0")
    env = simpy.Environment()
    sistema = SistemaCitasSimPy(env)
    env.process(generador_llegadas(env, sistema))
    env.run(until=TIEMPO_SIMULACION)
    
    tasa_rechazo = (sistema.rechazadas_buffer_lleno / sistema.total_llegadas) * 100
    espera_promedio = np.mean(sistema.tiempos_espera) if sistema.tiempos_espera else 0
    
    print(f"Total solicitudes: {sistema.total_llegadas}")
    print(f"Rechazadas por Buffer Lleno (K={CAPACIDAD_COLA}): {sistema.rechazadas_buffer_lleno}")
    print(f"Tasa de rechazo: {tasa_rechazo:.2f}%")
    print(f"Tiempo de espera promedio: {espera_promedio:.2f} segundos")
    print("Fin de la simulación")