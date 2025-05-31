"""
sky_temperature.py
==================
Pure calculation helpers for **AAG CloudWatcher sky‑temperature correction**
(T_sky) *without* any configuration or I/O.  The **caller** must pass in the
needed coefficients / thresholds – nothing here touches environment variables,
settings models, or dicts.

Typical usage
-------------
```python
from sky_temperature import tsky, classify_cloud_state, CloudState

coeffs = self.skytemp          # <- 你的 WeatherSettings.skytemp

T_sky = tsky(raw_sky_temp, ambient_temp, coeffs)
state = classify_cloud_state(T_sky, clear_limit=-17, cloudy_limit=-8)
```

Only two public helpers are exposed:
* `tsky(ts, ta, coeffs)   -> float`
* `classify_cloud_state(tsky, clear_limit=-17, cloudy_limit=-8) -> CloudState`

Where *coeffs* is any object that provides attributes **K1 … K7** (e.g. your
`Skytemp` Pydantic model).
"""
from __future__ import annotations

import math
from enum import IntEnum
from typing import Protocol


class _HasCoeffs(Protocol):
    """Anything that exposes K1–K7 float attributes."""

    K1: float; K2: float; K3: float
    K4: float; K5: float; K6: float; K7: float


# ---------------------------------------------------------------------------
#   Core maths
# ---------------------------------------------------------------------------

def _td(ta: float, c: _HasCoeffs) -> float:
    """Drift‑compensation term T_d(T_a) as per Lunático's model."""
    term1 = (c.K1 / 100.0) * (ta - c.K2 / 10.0)

    term2 = 0.0
    if c.K3:
        try:
            term2 = (c.K3 / 100.0) * (math.exp(c.K4 / 1000.0 * ta)) ** (c.K5 / 100.0)
        except OverflowError:
            term2 = 0.0

    delta = abs(c.K2 / 10.0 - ta)
    if delta < 1:
        t67 = math.copysign(delta, c.K6)
    else:
        t67 = (c.K6 / 10.0) * math.copysign(1, ta - c.K2 / 10.0) * (
            math.log10(delta) + c.K7 / 100.0
        )

    return term1 + term2 + t67


def tsky(ts: float, ta: float, coeffs: _HasCoeffs) -> float:
    """Return corrected sky temperature *T_sky* (°C).

    Parameters
    ----------
    ts : float
        Raw sky temperature from IR sensor.
    ta : float
        Ambient / sensor housing temperature.
    coeffs : Any object exposing attributes K1..K7.
    """
    return ts - _td(ta, coeffs)


class CloudState(IntEnum):
    CLEAR = 0
    CLOUDY = 1
    VERY_CLOUDY = 2


def classify_cloud_state(
    tsky_val: float,
    *,
    clear_limit: float = -17.0,
    cloudy_limit: float = -8.0,
) -> CloudState:
    """Map *T_sky* to discrete cloud state.

    Parameters
    ----------
    tsky_val : float
        Corrected sky temperature.
    clear_limit : float, default -17°C
        Boundary below which sky is considered *clear*.
    cloudy_limit : float, default -8°C
        Boundary above which sky is *very cloudy*.
    """
    if tsky_val < clear_limit:
        return CloudState.CLEAR
    if tsky_val > cloudy_limit:
        return CloudState.VERY_CLOUDY
    return CloudState.CLOUDY


# ---------------------------------------------------------------------------
#   Quick CLI check (kept for convenience)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    from dataclasses import dataclass

    @dataclass
    class _D:
        K1: float = 33; K2: float = 0; K3: float = 0; K4: float = 0
        K5: float = 0; K6: float = 140; K7: float = 40

    if len(sys.argv) == 3:
        Ts, Ta = map(float, sys.argv[1:])
        s = tsky(Ts, Ta, _D())
        print(f"T_sky: {s:.2f} °C =>", classify_cloud_state(s).name)
    else:
        print("Usage: python -m sky_temperature <Ts> <Ta>")
