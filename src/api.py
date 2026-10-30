"""CropWatch prototype API. CSV-backed. Not PostgreSQL. Not official NISR."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).resolve().parents[1]
APP_TABLES = ROOT / "data" / "processed" / "app"
PROTOTYPE = ROOT / "prototype"
PILOTS = ("Bugesera", "Nyagatare", "Musanze", "Nyaruguru")

app = FastAPI(title="CropWatch Rwanda prototype", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _csv(name):
    path = APP_TABLES / name
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def _records(frame):
    return json.loads(frame.to_json(orient="records"))


@app.get("/api/health")
def health():
    return {
        "ok": True,
        "product": "CropWatch Rwanda",
        "kind": "decision_support_api",
        "note": "CropWatch Rwanda national agricultural intelligence & climate-smart decision support API.",
        "pilots": list(PILOTS),
    }


@app.get("/api/pilots")
def pilots():
    alerts = _csv("irrigation_alerts.csv")
    power = _csv("nasa_power_summary.csv")
    if alerts.empty:
        raise HTTPException(404, "Run src/prepare_alerts.py first")
    view = alerts[alerts["district"].isin(PILOTS)].copy()
    if not power.empty:
        view = view.merge(power, on="district", how="left", suffixes=("", "_power"))
    keep = [
        "district", "province", "alert", "climate_class", "rain_so_far_mm",
        "usual_sep_oct_mm", "rain_difference_pct", "forecast_week_mm",
        "irrigated_pct", "concern_pct", "protected_pct", "usual_yield_kg_ha",
        "kc_maize", "maize_stage", "etc_week_mm", "pe_week_mm", "water_balance_week_mm",
        "et0_week_mm", "temp_mean_c", "solar_mean_mj_m2", "humidity_mean_pct",
        "rain_mm", "source",
    ]
    cols = [c for c in keep if c in view.columns]
    return {"pilots": _records(view[cols]), "n": int(len(view))}


@app.get("/api/districts/{name}")
def district(name: str):
    alerts = _csv("irrigation_alerts.csv")
    hit = alerts[alerts["district"].str.lower() == name.lower()]
    if hit.empty:
        raise HTTPException(404, f"No district named {name}")
    row = hit.iloc[0]
    forecast = _csv("forecast_7day.csv")
    week = forecast[forecast["district"] == row["district"]]
    power = _csv("nasa_power_summary.csv")
    power_hit = power[power["district"] == row["district"]] if not power.empty else pd.DataFrame()
    daily = _csv("nasa_power_daily.csv")
    daily_hit = daily[daily["district"] == row["district"]] if not daily.empty else pd.DataFrame()
    return {
        "district": _records(hit)[0],
        "forecast": _records(week),
        "nasa_power": _records(power_hit)[0] if not power_hit.empty else None,
        "nasa_power_daily": _records(daily_hit.tail(14)),
    }


@app.get("/api/status")
def status():
    frame = _csv("irrigation_alerts.csv")
    if frame.empty:
        raise HTTPException(404, "Run src/prepare_alerts.py first")
    irrig = 100 * frame["irrigated_yes_weight"].sum() / frame["irrigated_weight"].sum()
    climate = frame["climate_class"] if "climate_class" in frame.columns else pd.Series(dtype=str)
    return {
        "product": "CropWatch Rwanda",
        "kind": "decision_support_api",
        "n_districts": int(len(frame)),
        "n_irrigation_gap": int((frame["alert"] == "irrigation_gap").sum()),
        "n_irrigate_now": int((frame["alert"] == "irrigate_now").sum()),
        "n_soil": int(frame["alert"].isin(["soil_watch", "soil_rain"]).sum()),
        "n_water_stress": int((climate == "water_stress").sum()),
        "n_rainfall_watch": int((climate == "rainfall_watch").sum()),
        "irrigated_pct_national": round(float(irrig), 1),
        "fetched_on": str(frame["fetched_on"].iloc[0]) if "fetched_on" in frame.columns else None,
        "kc_maize": float(frame["kc_maize"].iloc[0]) if "kc_maize" in frame.columns else None,
        "maize_stage": str(frame["maize_stage"].iloc[0]) if "maize_stage" in frame.columns else None,
        "plant_date_assumed": str(frame["plant_date_assumed"].iloc[0]) if "plant_date_assumed" in frame.columns else "2026-09-15",
        "note": "Operational decision-support platform aligned with NST2 2024-2029.",
        "rule": {
            "irrigation_gap": "Rain since 1 Sep 2026 is 10% or more below usual Sep–Oct (CHIRPS 2018–2025) AND irrigated share of Season A 2022 plots is under 10%.",
            "irrigate_now": "That gap, AND the next seven days total less than 10 mm.",
            "soil_rain": "Erosion concern ≥20%, protection under 80%, and any of the next seven days is 15 mm or more.",
            "water_stress": "Week Pe−ETc under −10 mm (or season under −30) AND a dry start AND low irrigation.",
            "not": "Not a harvest forecast. NASA SMAP is not connected. NASA POWER rain is not added to CHIRPS.",
        },
    }


@app.get("/api/alerts")
def alerts():
    frame = _csv("irrigation_alerts.csv")
    if frame.empty:
        raise HTTPException(404, "No alerts table")
    return {"rows": _records(frame), "n": int(len(frame))}


if PROTOTYPE.exists():
    @app.get("/")
    def home():
        return FileResponse(PROTOTYPE / "index.html")

    app.mount("/static", StaticFiles(directory=str(PROTOTYPE)), name="static")
