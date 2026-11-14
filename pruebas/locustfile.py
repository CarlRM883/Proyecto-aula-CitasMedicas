"""
Prueba de carga contra la API en Docker.
  locust -f pruebas/locustfile.py --headless -u 50 -r 10 -t 60s \
         --host http://localhost:8000 --csv datos/locust
Mismo reparto de trámites que el modelo: 60 % / 25 % / 15 %.
"""
import random
from locust import HttpUser, task, between


class Paciente(HttpUser):
    wait_time = between(0.05, 0.2)

    @task
    def pedir_cita(self):
        tipo = random.choices(["AGENDAR", "REPROGRAMAR", "CANCELAR"],
                              weights=[60, 25, 15])[0]
        self.client.post("/api/v1/citas",
                         json={"paciente_id": random.randint(1, 100000),
                               "tipo_tramite": tipo})
