"""CropWatch Rwanda — National Agricultural Decision Support API.
FastAPI service exposing live agrometeorological alerts, 30-district telemetry,
trained machine learning inference models, and the AI Agronomic Copilot.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from src.advise import answer, get_models, pack

ROOT = Path(__file__).resolve().parents[1]
APP_TABLES = ROOT / "data" / "processed" / "app"
PROCESSED = ROOT / "data" / "processed"
PILOTS = ("Bugesera", "Nyagatare", "Musanze", "Nyaruguru")

app = FastAPI(
    title="CropWatch Rwanda National Agricultural Decision Support API",
    version="1.0.0",
    description="Institutional agrometeorological early warning, 30-district survey microdata, and machine learning advisory API.",
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
    y_bundle, _, _ = get_models()
    if y_bundle is None:
        raise HTTPException(503, "Yield model not loaded")
    rf = y_bundle["rf_model"]
    feats = y_bundle["feature_names"]
    x_base = pd.DataFrame([{
        "irrigated": int(profile["irrigated_pct"] > 5),
        "organic": 1,
        "organic_short": 0,
        "inorganic": 0,
        "protected": int(profile["protected_pct"] > 50),
        "erosion_moderate": 0,
        "erosion_severe": int(profile["concern_pct"] > 30),
        "rain_diff_pct": profile["rain_pct"],
        "vegetation_mean": profile["veg_now"],
    }])[feats]
    pred_base = float(rf.predict(x_base)[0])
    x_irrig = x_base.copy()
    x_irrig["irrigated"] = 1
    pred_irrig = float(rf.predict(x_irrig)[0])
    x_both = x_base.copy()
    x_both["irrigated"] = 1
    x_both["inorganic"] = 1
    x_both["protected"] = 1
    pred_both = float(rf.predict(x_both)[0])

    return {
        "district": profile["district"],
        "baseline_yield_kg_ha": round(pred_base, 1),
        "with_supplementary_irrigation_kg_ha": round(pred_irrig, 1),
        "with_full_climate_smart_package_kg_ha": round(pred_both, 1),
        "yield_uplift_kg_ha": round(pred_both - pred_base, 1),
        "price_rwf_per_kg": profile["price"],
        "revenue_uplift_rwf_ha": round((pred_both - pred_base) * profile["price"], 0),
        "model": "RandomForestRegressor (28,042 NISR SAS plots)",
    }


@app.get("/api/models/drought/{district}")
def model_drought(district: str):
    profile = _get_district_profile(district)
    _, d_bundle, _ = get_models()
    if d_bundle is None:
        raise HTTPException(503, "Drought model not loaded")
    clf = d_bundle["model"]
    feats = d_bundle["features"]
    x_clim = pd.DataFrame([{
        "rain_diff_pct": profile["rain_pct"],
        "water_balance_mm": profile["water_week"],
        "irrigated_pct": profile["irrigated_pct"],
        "concern_pct": profile["concern_pct"],
        "etc_mm": profile["etc_week"],
    }])[feats]
    probs = clf.predict_proba(x_clim)[0]
    p_crisis = float(probs[2]) * 100.0
    is_triggered = (p_crisis >= 30.0) or (profile["water_week"] <= -10.0 and profile["rain_pct"] <= -15.0)

    return {
        "district": profile["district"],
        "probability_crisis_pct": round(p_crisis, 1),
        "probability_watch_pct": round(float(probs[1]) * 100.0, 1),
        "probability_stable_pct": round(float(probs[0]) * 100.0, 1),
        "nais_parametric_insurance_payout_triggered": bool(is_triggered),
        "model": "RandomForestClassifier",
    }


@app.get("/api/models/prices/{district}")
def model_prices(district: str):
    profile = _get_district_profile(district)
    _, _, p_bundle = get_models()
    if p_bundle is None:
        raise HTTPException(503, "Price model not loaded")
    model = p_bundle["model"]
    cur_price = profile["price"]
    month = 10
    import numpy as np
    m_sin = float(np.sin(2 * np.pi * month / 12.0))
    m_cos = float(np.cos(2 * np.pi * month / 12.0))
    x_price = pd.DataFrame([{
        "month_sin": m_sin,
        "month_cos": m_cos,
        "lag1": float(cur_price),
        "lag2": float(cur_price * 0.98),
        "lag3": float(cur_price * 0.95),
    }])[p_bundle["features"]]
    proj_30d = float(model.predict(x_price)[0])

    return {
        "district": profile["district"],
        "current_price_rwf_kg": cur_price,
        "projected_price_30d_rwf_kg": round(proj_30d, 1),
        "projected_price_60d_rwf_kg": round(proj_30d * 1.042, 1),
        "projected_price_90d_rwf_kg": round(proj_30d * 1.085, 1),
        "hermetic_pics_bag_cost_rwf_kg": 28.0,
        "net_arbitrage_gain_90d_rwf_kg": round((proj_30d * 1.085 - cur_price) - 28.0, 1),
        "model": "Autoregressive RidgeCV (2,728 WFP records)",
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
