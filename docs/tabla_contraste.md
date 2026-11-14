Capacidad máxima del sistema: c·μ = 4×0.3333 = 1.333 sol/s = 4800 sol/h  (cuello de botella: los 4 servidores)

Pico del escenario: λ=1.5/s -> ρ = 1.125 > 1 (M/M/4 NO tiene estado estacionario; la cola crece hasta K).


### PICO de validación (λ=1.0/s, ρ=0.75)

P(esperar) teórica (Erlang C) = 0.5094; P0 = 0.0377

| Métrica | M/M/4 analítico | SimPy modo markoviano (media ± IC95) | Dif. relativa (%) |
|:---|:---:|:---:|:---:|
| Utilización ρ | 0.7500 | 0.7482 ± 0.0041 | -0.2 |
| Lq (solicitudes en cola) | 1.5283 | 1.4995 ± 0.0722 | -1.9 |
| Wq (s) | 1.5283 | 1.5012 ± 0.0691 | -1.8 |
| W (s) | 4.5283 | 4.5020 ± 0.0758 | -0.6 |

**Ley de Little (SimPy, λ=1.0):** L medido = 4.492 ± 0.086  vs  λ·W = 4.491 ± 0.085  (dif. -0.04 %)

### VALLE (λ=0.2/s, ρ=0.15)

P(esperar) teórica (Erlang C) = 0.0035; P0 = 0.5487

| Métrica | M/M/4 analítico | SimPy modo markoviano (media ± IC95) | Dif. relativa (%) |
|:---|:---:|:---:|:---:|
| Utilización ρ | 0.1500 | 0.1491 ± 0.0018 | -0.6 |
| Lq (solicitudes en cola) | 0.0006 | 0.0006 ± 0.0001 | -7.3 |
| Wq (s) | 0.0031 | 0.0028 ± 0.0006 | -9.2 |
| W (s) | 3.0031 | 2.9965 ± 0.0244 | -0.2 |

### Divergencia al activar la dinámica real (λ=1.0 fijo, K=60, servicio lognormal por trámite, abandono y reintento)

| Métrica | M/M/4 analítico | SimPy real (media ± IC95) | Dif. relativa (%) |
|:---|:---:|:---:|:---:|
| Utilización ρ | 0.7500 | 0.7482 ± 0.0038 | -0.2 |
| Lq | 1.5283 | 1.0564 ± 0.0480 | -30.9 |
| Wq (s) | 1.5283 | 1.0572 ± 0.0451 | -30.8 |
| W (s) | 4.5283 | 4.0580 ± 0.0481 | -10.4 |

Pérdida (rechazo+abandono) en SimPy real: 0.000 ± 0.000 % (M/M/c con cola infinita predice 0 %).
