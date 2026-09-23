"""Placeholder solar endpoints: fixed synthetic data, no external API calls."""

from fastapi import APIRouter, Query
from datetime import date, timedelta
import math

router = APIRouter()

@router.get("/forecast")
def forecast(location: str = Query(...), system_size: float = Query(..., gt=0)):
  """Return a 7-day PV energy forecast in kWh.

  Placeholder: a fixed sine pattern scaled by ``system_size``; ``location``
  is accepted but not used, and no weather data is involved.
  """
  today = date.today()
  daily = []
  for i in range(7):
      d = today + timedelta(days=i)
      base = 4.5 + 1.5 * math.sin(i / 6 * math.pi)  # simple seasonality-ish wave
      kwh = round(max(0, base) * system_size, 1)
      daily.append({"date": d.isoformat(), "kwh": kwh})
  return {"daily": daily}


@router.get("/weather")
def weather(lat: float, lon: float):
    """Return fixed placeholder weather; ``lat``/``lon`` are ignored."""
    # Safe fake weather for now
    return {
        "weather": [{"main": "Clouds"}],
        "clouds": {"all": 40},
        "wind": {"speed": 3.5},
        "rain": {"1h": 0},
    }
