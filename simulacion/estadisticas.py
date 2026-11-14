import numpy as np
from scipy import stats


def media_ic(valores):
    """Devuelve (media, semiancho del IC 95%) usando la t de Student."""
    v = np.array(valores, dtype=float)
    n = len(v)
    if n < 2:
        return float(v.mean()), 0.0
    semiancho = stats.t.ppf(0.975, n - 1) * v.std(ddof=1) / np.sqrt(n)
    return float(v.mean()), float(semiancho)


def percentil(lista, q):
    return float(np.percentile(lista, q)) if len(lista) else 0.0
