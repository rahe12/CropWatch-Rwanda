"""NASA POWER daily meteorology for the four proposal pilot districts.

Public point API, no key. This is a district-midpoint retrieval, not a farm
sensor. SMAP soil moisture is still not connected.
"""

from __future__ import annotations

import json
import time
from datetime import date
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "data" / "processed" / "app"
PILOTS = ("Bugesera", "Nyagatare", "Musanze", "Nyaruguru")
START = date(2026, 9, 1)
END = date(2026, 10, 29)
PARAMS = "T2M,T2M_MAX,T2M_MIN,RH2M,WS2M,ALLSKY_SFC_SW_DWN,PRECTOTCORR"


def http_json(url, tries=3):
    request = Request(url, headers={"User-Agent": "CropWatchRwanda/1.0"})
    last_error = None
    for attempt in range(tries):
        try:
            with urlopen(request, timeout=90) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception as error:
            last_error = error
            time.sleep(3 * (attempt + 1))
    raise RuntimeError(f"NASA POWER failed: {last_error}")


def fetch_point(lat, lon):
    query = urlencode(
        {
            "parameters": PARAMS,
            "community": "AG",
            "longitude": f"{lon:.4f}",
            "latitude": f"{lat:.4f}",
            "start": START.strftime("%Y%m%d"),
            "end": END.strftime("%Y%m%d"),
            "format": "JSON",
        }
    )
    url = f"https://power.larc.nasa.gov/api/temporal/daily/point?{query}"
    payload = http_json(url)
    properties = payload.get("properties", {}).get("parameter", {})
    dates = sorted(properties.get("T2M", {}).keys())
    rows = []
    for day in dates:
        rows.append(
            {
                "date": f"{day[:4]}-{day[4:6]}-{day[6:8]}",
                "temp_c": properties.get("T2M", {}).get(day),
                "temp_max_c": properties.get("T2M_MAX", {}).get(day),
                "temp_min_c": properties.get("T2M_MIN", {}).get(day),
                "humidity_pct": properties.get("RH2M", {}).get(day),
                "wind_ms": properties.get("WS2M", {}).get(day),
                "solar_mj_m2": properties.get("ALLSKY_SFC_SW_DWN", {}).get(day),
                "rain_mm": properties.get("PRECTOTCORR", {}).get(day),
            }
        )
    return pd.DataFrame(rows)


def main():
    APP.mkdir(parents=True, exist_ok=True)
    alerts = pd.read_csv(APP / "irrigation_alerts.csv")
    daily_parts = []
    summaries = []
    for name in PILOTS:
        hit = alerts[alerts["district"] == name]
        if hit.empty:
            print("Missing district", name)
            continue
        row = hit.iloc[0]
        print("NASA POWER", name, float(row["latitude"]), float(row["longitude"]))
        daily = fetch_point(float(row["latitude"]), float(row["longitude"]))
        daily.insert(0, "district", name)
        daily_parts.append(daily)
        keep = daily.copy()
        for column in ("temp_c", "temp_max_c", "temp_min_c", "humidity_pct", "wind_ms", "solar_mj_m2", "rain_mm"):
            keep[column] = pd.to_numeric(keep[column], errors="coerce")
            keep.loc[keep[column] <= -900, column] = pd.NA
        summaries.append(
            {
                "district": name,
                "start": START.isoformat(),
                "end": END.isoformat(),
                "n_days": int(len(keep)),
                "temp_mean_c": round(float(keep["temp_c"].mean()), 1),
                "temp_max_c": round(float(keep["temp_max_c"].max()), 1),
                "humidity_mean_pct": round(float(keep["humidity_pct"].mean()), 1),
                "solar_mean_mj_m2": round(float(keep["solar_mj_m2"].mean()), 2),
                "rain_mm": round(float(keep["rain_mm"].sum()), 1),
                "source": "NASA POWER daily point, community AG, district midpoint",
                "fetched_on": date(2026, 10, 30).isoformat(),
            }
        )
    if not daily_parts:
        raise SystemExit("No NASA POWER rows")
    pd.concat(daily_parts, ignore_index=True).to_csv(APP / "nasa_power_daily.csv", index=False)
    pd.DataFrame(summaries).to_csv(APP / "nasa_power_summary.csv", index=False)
    print(pd.DataFrame(summaries).to_string(index=False))


if __name__ == "__main__":
    main()
