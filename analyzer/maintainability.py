"""
Maintainability Index (MI).

Standard derived-metric formula (Microsoft / Visual Studio variant,
normalised to 0-100):

    MI = max(0, (171 - 5.2*ln(V) - 0.23*G - 16.2*ln(L)) * 100 / 171)

where V is Halstead Volume, G is average cyclomatic complexity across
the file's functions, and L is logical lines of code.
"""

import math


def compute_maintainability_index(volume: float, avg_complexity: float, logical_loc: int) -> float:
    v = max(volume, 1.0)
    g = max(avg_complexity, 1.0)
    l = max(logical_loc, 1)

    raw = 171 - 5.2 * math.log(v) - 0.23 * g - 16.2 * math.log(l)
    mi = max(0.0, raw * 100 / 171)
    return round(min(mi, 100.0), 2)


def rating_for(mi: float) -> str:
    if mi >= 85:
        return "High"
    if mi >= 65:
        return "Moderate"
    return "Low"
