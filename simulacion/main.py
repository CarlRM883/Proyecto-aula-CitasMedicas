"""
Experimento principal:  python simulacion/main.py
 1) Compara las políticas (Actual vs Alternativas) con 30 réplicas.
 2) Análisis de sensibilidad (variando c y K).
 3) Guarda tablas en docs/tablas_resultados.md y gráficas en docs/figuras/.
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import config
import modelo_simpy as m
from estadisticas import media_ic

RAIZ = Path(__file__).resolve().parent.parent
FIG = RAIZ / "docs" / "figuras"
FIG.mkdir(parents=True, exist_ok=True)
SEMILLAS = range(config.SEMILLA_BASE, config.SEMILLA_BASE + config.REPLICAS)


def correr_politica(c, K):
    """Corre R réplicas y devuelve una lista de resultados (uno por réplica)."""
    resultados = []
    for semilla in SEMILLAS:
        s = m.correr_replica(c, K, semilla)
        pico = m.metricas(s, 0, config.FIN_PICO)
        dia = m.metricas(s, 0, config.JORNADA)
        serie_Q = np.array(s.hist_Q[:config.JORNADA]).reshape(-1, 60).mean(axis=1)
        resultados.append({"pico": pico, "dia": dia, "cola_final": s.en_cola,
                           "serie_Q": serie_Q})
    return resultados


def resumen(resultados, ventana, kpi):
    """(media, IC95) del KPI a través de las réplicas."""
    return media_ic([r[ventana][kpi] for r in resultados])


def fmt(media_ic_, marca=""):
    return f"{media_ic_[0]:.2f} ± {media_ic_[1]:.2f}{marca}"


def ok(cond):
    return " ✓" if cond else " ✗"


def main():
    print(f"Réplicas: {config.REPLICAS}, semillas {SEMILLAS[0]}..{SEMILLAS[-1]}")
    todo = {}
    for pol in config.POLITICAS:
        print("Simulando", pol["nombre"], "...")
        todo[pol["nombre"]] = correr_politica(pol["c"], pol["K"])

    nombres = list(todo.keys())
    out = []

    # ------------- Tabla 1: KPIs por política -------------------------------
    out.append("### Tabla de KPIs (media ± IC 95 % sobre "
               f"{config.REPLICAS} réplicas, ventana de PICO 7:00-9:00)\n")
    out.append("| KPI | SLA | " + " | ".join(nombres) + " |")
    out.append("|:---|:---:|" + ":---:|" * len(nombres))

    filas = [
        ("Espera en cola p95 (s)", f"≤ {config.SLA_ESPERA_P95}", "pico", "espera_p95",
         lambda v: v <= config.SLA_ESPERA_P95),
        ("Espera en cola p99 (s)", "—", "pico", "espera_p99", None),
        ("Rechazo por buffer lleno (%)", "—", "pico", "rechazo_pct", None),
        ("Abandono por paciencia (%)", "—", "pico", "abandono_pct", None),
        ("Pérdida total = rechazo + abandono (%)", f"≤ {config.SLA_PERDIDA}", "pico",
         "perdida_pct", lambda v: v <= config.SLA_PERDIDA),
        ("Utilización medida de servidores (%)",
         f"{config.SLA_UTIL[0]:.0f}-{config.SLA_UTIL[1]:.0f}", "pico", "util_pct",
         lambda v: config.SLA_UTIL[0] <= v <= config.SLA_UTIL[1]),
        ("Pérdida total en toda la jornada (%)", "—", "dia", "perdida_pct", None),
    ]
    cumple = {n: True for n in nombres}
    for etiqueta, sla, ventana, kpi, regla in filas:
        celdas = []
        for n in nombres:
            r = resumen(todo[n], ventana, kpi)
            marca = ""
            if regla:
                marca = ok(regla(r[0]))
                cumple[n] &= regla(r[0])
            celdas.append(fmt(r, marca))
        out.append(f"| {etiqueta} | {sla} | " + " | ".join(celdas) + " |")

    celdas = []
    for n in nombres:
        r = media_ic([x["cola_final"] for x in todo[n]])
        celdas.append(fmt(r, ok(r[0] < config.SLA_COLA_FINAL)))
        cumple[n] &= r[0] < config.SLA_COLA_FINAL
    out.append(f"| Cola al cierre de la jornada (solicitudes) | < {config.SLA_COLA_FINAL} | "
               + " | ".join(celdas) + " |")
    out.append("| **¿Cumple todo el SLA?** | | "
               + " | ".join("**Sí**" if cumple[n] else "**No**" for n in nombres) + " |")

    # ------------- Tabla 2: sensibilidad en c --------------------------------
    out.append("\n### Sensibilidad al número de servidores c (K = 60)\n")
    out.append("| c | ρ teórico pico = λ·E[S]/c | Utilización medida (%) | Pérdida pico (%) | Espera p95 (s) |")
    out.append("|:---:|:---:|:---:|:---:|:---:|")
    sens_c = {}
    for c in range(3, 9):
        res = todo[config.POLITICAS[0]["nombre"]] if c == 4 else correr_politica(c, 60)
        sens_c[c] = res
        rho = config.LAMBDA_PICO * config.SERVICIO_MEDIO_GLOBAL / c
        out.append(f"| {c} | {rho:.2f} | {fmt(resumen(res,'pico','util_pct'))} | "
                   f"{fmt(resumen(res,'pico','perdida_pct'))} | "
                   f"{fmt(resumen(res,'pico','espera_p95'))} |")

    # ------------- Tabla 3: sensibilidad en K --------------------------------
    out.append("\n### Sensibilidad al tamaño de cola K (c = 4)\n")
    out.append("| K | Rechazo (%) | Abandono (%) | Pérdida total (%) | Espera p95 (s) |")
    out.append("|:---:|:---:|:---:|:---:|:---:|")
    for K in (30, 60, 120, 240):
        res = todo[config.POLITICAS[0]["nombre"]] if K == 60 else correr_politica(4, K)
        out.append(f"| {K} | {fmt(resumen(res,'pico','rechazo_pct'))} | "
                   f"{fmt(resumen(res,'pico','abandono_pct'))} | "
                   f"{fmt(resumen(res,'pico','perdida_pct'))} | "
                   f"{fmt(resumen(res,'pico','espera_p95'))} |")

    texto = "\n".join(out)
    print("\n" + texto)
    (RAIZ / "docs" / "tablas_resultados.md").write_text(texto + "\n", encoding="utf-8")

    # ------------- Gráficas ---------------------------------------------------
    # Fig 2: evolución de la cola Q(t)
    plt.figure(figsize=(8, 4.5))
    minutos = np.arange(480)
    for n in nombres:
        serie = np.mean([r["serie_Q"] for r in todo[n]], axis=0)
        plt.plot(minutos, serie, label=n)
    plt.axhline(60, color="red", linestyle="--", label="Límite K = 60")
    plt.axvline(120, color="gray", linestyle=":", label="Fin del pico (9:00)")
    plt.xlabel("Minutos desde las 7:00"); plt.ylabel("Solicitudes en cola Q(t)")
    plt.title("Evolución de la cola (promedio de 30 réplicas)")
    plt.legend(); plt.grid(alpha=.3); plt.tight_layout()
    plt.savefig(FIG / "fig3_evolucion_cola.png", dpi=150); plt.close()

    # Fig 3 y 4: barras con IC y línea de SLA
    def barras(kpi, etiqueta, sla, archivo, titulo):
        vals = [resumen(todo[n], "pico", kpi) for n in nombres]
        plt.figure(figsize=(7, 4.5))
        plt.bar(range(len(nombres)), [v[0] for v in vals],
                yerr=[v[1] for v in vals], capsize=6, color="#4C72B0")
        plt.axhline(sla, color="red", linestyle="--", label=f"SLA = {sla}")
        plt.xticks(range(len(nombres)), nombres, fontsize=8)
        plt.ylabel(etiqueta); plt.title(titulo); plt.legend(); plt.grid(alpha=.3, axis="y")
        plt.tight_layout(); plt.savefig(FIG / archivo, dpi=150); plt.close()

    barras("perdida_pct", "Pérdida en pico (%)", config.SLA_PERDIDA,
           "fig4_perdida_pico.png", "Rechazo + abandono en el pico (IC 95 %)")
    barras("espera_p95", "Espera en cola p95 (s)", config.SLA_ESPERA_P95,
           "fig5_espera_p95.png", "Espera p95 en el pico (IC 95 %)")

    # Fig 5: sensibilidad a c
    cs = list(sens_c.keys())
    perd = [resumen(sens_c[c], "pico", "perdida_pct") for c in cs]
    plt.figure(figsize=(7, 4.5))
    plt.errorbar(cs, [p[0] for p in perd], yerr=[p[1] for p in perd], marker="o", capsize=4)
    plt.axhline(config.SLA_PERDIDA, color="red", linestyle="--", label="SLA = 5 %")
    plt.xlabel("Número de servidores c"); plt.ylabel("Pérdida en pico (%)")
    plt.title("Sensibilidad: pérdida vs. servidores (IC 95 %)")
    plt.legend(); plt.grid(alpha=.3); plt.tight_layout()
    plt.savefig(FIG / "fig6_sensibilidad_c.png", dpi=150); plt.close()
    print("\nListo: tablas en docs/tablas_resultados.md y gráficas en docs/figuras/")


if __name__ == "__main__":
    main()
