"""
Contraste M/M/c (fórmulas) vs SimPy:   python analisis/contraste_mmc.py
Genera docs/tabla_contraste.md
"""
import math
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "simulacion"))

import config
import modelo_simpy as m
from estadisticas import media_ic

C = 4
MU = 1.0 / config.SERVICIO_MEDIO_GLOBAL      # 1/3 por segundo
T, WARMUP = 10800, 1800                       # 3 h simuladas, 30 min de calentamiento
SEMILLAS = range(config.SEMILLA_BASE, config.SEMILLA_BASE + config.REPLICAS)


def erlang_c(lam, mu, c):
    """Fórmulas M/M/c en estado estacionario (solo válidas si ρ < 1)."""
    a = lam / mu                      # carga ofrecida
    rho = a / c
    suma = sum(a ** k / math.factorial(k) for k in range(c))
    termino = a ** c / (math.factorial(c) * (1 - rho))
    P0 = 1 / (suma + termino)
    Pw = termino * P0                 # prob. de esperar (Erlang C)
    Lq = Pw * rho / (1 - rho)
    Wq = Lq / lam
    W = Wq + 1 / mu
    return {"rho": rho, "P0": P0, "Pw": Pw, "Lq": Lq, "Wq": Wq, "W": W, "L": lam * W}


def simular(lam, markoviano, K):
    filas = []
    for s in SEMILLAS:
        sis = m.correr_replica(C, K, s, horizonte=T, markoviano=markoviano, lam_const=lam)
        filas.append(m.metricas(sis, WARMUP, T))
    return filas


def dif(teo, sim):
    return 100 * (sim - teo) / teo if teo else float("nan")


def main():
    out = []
    out.append(f"Capacidad máxima del sistema: c·μ = {C}×{MU:.4f} = {C*MU:.3f} sol/s "
               f"= {C*MU*3600:.0f} sol/h  (cuello de botella: los {C} servidores)\n")
    rho_pico = config.LAMBDA_PICO / (C * MU)
    out.append(f"Pico del escenario: λ={config.LAMBDA_PICO}/s -> ρ = {rho_pico:.3f} > 1 "
               "(M/M/4 NO tiene estado estacionario; la cola crece hasta K).\n")

    for lam, nombre in ((1.0, "PICO de validación (λ=1.0/s, ρ=0.75)"),
                        (0.2, "VALLE (λ=0.2/s, ρ=0.15)")):
        teo = erlang_c(lam, MU, C)
        sim = simular(lam, True, float("inf"))
        out.append(f"\n### {nombre}\n")
        out.append(f"P(esperar) teórica (Erlang C) = {teo['Pw']:.4f}; P0 = {teo['P0']:.4f}\n")
        out.append("| Métrica | M/M/4 analítico | SimPy modo markoviano (media ± IC95) | Dif. relativa (%) |")
        out.append("|:---|:---:|:---:|:---:|")
        for etiqueta, clave_t, clave_s, esc in (
                ("Utilización ρ", "rho", "util_pct", 0.01),
                ("Lq (solicitudes en cola)", "Lq", "Lq", 1),
                ("Wq (s)", "Wq", "espera_media", 1),
                ("W (s)", "W", "sistema_media", 1)):
            mu_, ic = media_ic([f[clave_s] * esc for f in sim])
            out.append(f"| {etiqueta} | {teo[clave_t]:.4f} | {mu_:.4f} ± {ic:.4f} | "
                       f"{dif(teo[clave_t], mu_):+.1f} |")

        if lam == 1.0:   # verificación de la Ley de Little: L = λ_ef · W
            L = media_ic([f["L"] for f in sim])
            LW = media_ic([f["lambda_ef"] * f["sistema_media"] for f in sim])
            out.append(f"\n**Ley de Little (SimPy, λ=1.0):** L medido = {L[0]:.3f} ± {L[1]:.3f}  "
                       f"vs  λ·W = {LW[0]:.3f} ± {LW[1]:.3f}  "
                       f"(dif. {dif(L[0], LW[0]):+.2f} %)")

    # Divergencia: mismo λ=1.0 pero con las reglas reales activadas
    teo = erlang_c(1.0, MU, C)
    real = simular(1.0, False, config.POLITICAS[0]["K"])
    out.append("\n### Divergencia al activar la dinámica real (λ=1.0 fijo, K=60, "
               "servicio lognormal por trámite, abandono y reintento)\n")
    out.append("| Métrica | M/M/4 analítico | SimPy real (media ± IC95) | Dif. relativa (%) |")
    out.append("|:---|:---:|:---:|:---:|")
    for etiqueta, ct, cs, esc in (("Utilización ρ", "rho", "util_pct", 0.01),
                                  ("Lq", "Lq", "Lq", 1),
                                  ("Wq (s)", "Wq", "espera_media", 1),
                                  ("W (s)", "W", "sistema_media", 1)):
        mu_, ic = media_ic([f[cs] * esc for f in real])
        out.append(f"| {etiqueta} | {teo[ct]:.4f} | {mu_:.4f} ± {ic:.4f} | "
                   f"{dif(teo[ct], mu_):+.1f} |")
    rp = media_ic([f["perdida_pct"] for f in real])
    out.append(f"\nPérdida (rechazo+abandono) en SimPy real: {rp[0]:.3f} ± {rp[1]:.3f} % "
               "(M/M/c con cola infinita predice 0 %).")

    texto = "\n".join(out)
    print(texto)
    (RAIZ / "docs" / "tabla_contraste.md").write_text(texto + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
