"""CropWatch Rwanda API.

Same district packages as the Streamlit desk: alerts, 2022 OLS yield gaps,
FAO-56 water screen, latest WFP maize row, Advice from local tables.
Does not load joblib models, pay NAIS, or forecast 30/60/90-day prices.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from src.advise import answer, pack
from src.logic import drought_screen, plot_package

ROOT = Path(__file__).resolve().parents[1]
APP_TABLES = ROOT / "data" / "processed" / "app"
PROCESSED = ROOT / "data" / "processed"
PILOTS = ("Bugesera", "Nyagatare", "Musanze", "Nyaruguru")

app = FastAPI(
    title="CropWatch Rwanda National Agricultural Decision Support API",
    version="1.0.0",
    description="Season A water desk API: SAS 2022 shares, Open-Meteo vs CHIRPS, 2022 OLS yield gaps. Not an NAIS payout service.",
)

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


@app.get("/")
def api_root():
    return {
        "product": "CropWatch Rwanda",
        "description": "National Agricultural Decision Support API aligned with NST2 2024–2029",
        "version": "1.0.0",
        "status": "operational",
        "documentation": "/docs",
        "openapi_schema": "/openapi.json",
        "endpoints": [
            "/api/health",
            "/api/status",
            "/api/alerts",
            "/api/pilots",
            "/api/districts/{name}",
            "/api/models/yield/{district}",
            "/api/models/drought/{district}",
            "/api/models/prices/{district}",
            "/api/chat/ask",
        ],
    }


@app.get("/api/health")
def health():
    return {
        "ok": True,
        "product": "CropWatch Rwanda",
        "kind": "decision_support_api",
        "note": "CropWatch Rwanda national agricultural intelligence & climate-smart decision support API.",
        "pilots": list(PILOTS),
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
    }


@app.get("/api/alerts")
def alerts():
    frame = _csv("irrigation_alerts.csv")
    if frame.empty:
        raise HTTPException(404, "No alerts table found")
    return {"rows": _records(frame), "n": int(len(frame))}


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


def _get_district_profile(district_name: str):
    alerts = _csv("irrigation_alerts.csv")
    forecast = _csv("forecast_7day.csv")
    watch = _csv("season_watch.csv")
    soil = _csv("soil_season_a_2022.csv")
    veg_path = PROCESSED / "vegetation" / "district_year.csv"
    vegetation = pd.read_csv(veg_path) if veg_path.exists() else pd.DataFrame()
    hit = alerts[alerts["district"].str.lower() == district_name.lower()]
    if hit.empty:
        raise HTTPException(404, f"No district named '{district_name}'")
    exact_name = hit.iloc[0]["district"]
    return pack(alerts, forecast, watch, soil, vegetation, exact_name)


@app.get("/api/models/yield/{district}")
def model_yield(district: str):
    profile = _get_district_profile(district)
    pkg = plot_package(profile["usual_yield"])
    price = profile.get("price")
    irrig_rev = None if price is None else round(pkg["irrigation_kg_ha"] * float(price), 0)
    return {
        "district": profile["district"],
        "baseline_yield_kg_ha": pkg["baseline_kg_ha"],
        "with_supplementary_irrigation_kg_ha": pkg["with_irrigation_kg_ha"],
        "with_inorganic_kg_ha": pkg["with_inorganic_kg_ha"],
        "with_irrigation_and_inorganic_kg_ha": pkg["with_irrigation_and_inorganic_kg_ha"],
        "yield_uplift_irrigation_kg_ha": pkg["irrigation_kg_ha"],
        "price_rwf_per_kg": price,
        "irrigation_revenue_uplift_rwf_ha": irrig_rev,
        "model": "Season A 2022 within-district OLS (11,148 maize plots). Not a 2026 harvest.",
        "note": pkg["note"],
    }


@app.get("/api/models/drought/{district}")
def model_drought(district: str):
    profile = _get_district_profile(district)
    screen = drought_screen(
        profile["rain_pct"],
        profile["water_week"],
        profile["irrigated_pct"],
        profile["week_mm"],
    )
    return {
        "district": profile["district"],
        "level": screen["level"],
        "cropwatch_water_flag": screen["cropwatch_water_flag"],
        "nais_parametric_insurance_payout_triggered": False,
        "model": "Same alert rule as prepare_alerts.classify (not NAIS)",
        "note": screen["note"],
    }


@app.get("/api/models/prices/{district}")
def model_prices(district: str):
    profile = _get_district_profile(district)
    return {
        "district": profile["district"],
        "current_price_rwf_kg": profile.get("price"),
        "price_date": profile.get("price_date"),
        "national_price_rwf_kg": profile.get("national_price"),
        "forecast": None,
        "note": "Latest WFP maize row only. No 30/60/90-day forecast is computed.",
    }


@app.get("/api/chat/ask")
def chat_ask(
    q: str = Query(..., description="User query or agronomic question"),
    district: str = Query("Bugesera", description="District context"),
    lang: str = Query("en", description="Language: 'en' or 'rw'"),
):
    profile = _get_district_profile(district)
    words = {"language": "Ururimi" if lang == "rw" else "Language"}
    resp_text = answer(q, profile, words, lang=lang)
    return {
        "district": profile["district"],
        "language": lang,
        "query": q,
        "response": resp_text,
    }
