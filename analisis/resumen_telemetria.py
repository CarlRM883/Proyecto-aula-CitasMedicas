"""
Resume datos/telemetry_log.csv:   python analisis/resumen_telemetria.py
Imprime la tabla de latencias, CPU y RAM para la sección 3.1 del informe.
"""
from pathlib import Path
import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
archivo = RAIZ / "datos" / "telemetry_log.csv"
if not archivo.exists():
    raise SystemExit("No existe datos/telemetry_log.csv: levante la API y genere tráfico con Locust.")

df = pd.read_csv(archivo)
print(f"Peticiones registradas: {len(df)}\n")
print("| Trámite | n | Latencia media (ms) | p95 (ms) | p99 (ms) | máx (ms) |")
print("|:---|:---:|:---:|:---:|:---:|:---:|")
for tipo, g in list(df.groupby("tipo_tramite")) + [("TODOS", df)]:
    l = g["latencia_ms"]
    print(f"| {tipo} | {len(g)} | {l.mean():.2f} | {l.quantile(.95):.2f} | "
          f"{l.quantile(.99):.2f} | {l.max():.2f} |")
print(f"\nCPU del contenedor: media {df['cpu_pct'].mean():.1f} %, máx {df['cpu_pct'].max():.1f} %")
print(f"RAM del proceso:    media {df['ram_mb'].mean():.1f} MB, máx {df['ram_mb'].max():.1f} MB")

# Ajuste lognormal de la latencia real (mu y sigma del logaritmo, en segundos)
seg = df["latencia_ms"] / 1000
seg = seg[seg > 0]
print(f"\nAjuste Lognormal de la latencia medida: mu = {np.log(seg).mean():.3f}, "
      f"sigma = {np.log(seg).std():.3f}  (en segundos)")
