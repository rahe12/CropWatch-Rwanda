"""One set of rules used by the app, the API, and the Copilot.

Yield what-if = Season A 2022 within-district OLS (not a 2026 harvest).
Drought flag = same idea as the alert table (not an NAIS payout).
SSIT kit = plot size + water source, with an indicative 50/50 cost split.
Price = latest WFP maize row (no invented 60- and 90-day forecasts).
"""

from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
APP_TABLES = ROOT / "data" / "processed" / "app"

# Season A 2022 maize plots after the 1–99 yield window (model_benchmark.json).
N_PLOTS_SIM_2022A = 11148
# Pooled maize plots that actually joined: 2022, 2023, 2025 seasons A and B.
N_PLOTS_POOLED = 28042

# Season A 2022 within-district OLS (kg/ha). Same numbers as model_benchmark.json.
EFFECTS_2022 = {
    "irrigated": 365.3,
    "organic": 304.6,
    "organic_short": -190.7,
    "inorganic": 523.7,
    "protected": -106.9,
    "erosion_moderate": -182.0,
    "erosion_severe": -374.5,
}

# Planning figures only — not a MINAGRI quote.
KIT_COST_RWF = {
    "treadle": 180_000,
    "solar": 2_800_000,
    "motor": 1_450_000,
}
TANK_EXTRA_RWF = 650_000


def season_a_dates(today: date | None = None):
    """Season A starts 1 September. Plant date is mid-window (assumed, not a field visit)."""
    today = today or date.today()
    if today.month >= 9:
        start = date(today.year, 9, 1)
        plant = date(today.year, 9, 15)
    else:
        start = date(today.year - 1, 9, 1)
        plant = date(today.year - 1, 9, 15)
    archive_end = today - timedelta(days=1)
    if archive_end < start:
        archive_end = start
    return start, plant, today, archive_end


def load_effects():
    path = APP_TABLES / "model_benchmark.json"
    if not path.exists():
        return dict(EFFECTS_2022)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        raw = data.get("within_district_kg_ha") or {}
        out = dict(EFFECTS_2022)
        for key in out:
            if key in raw and raw[key] is not None:
                out[key] = float(raw[key])
        return out
    except Exception:
        return dict(EFFECTS_2022)


def district_share_whatif(base_yield, current_irrig_pct, current_short_pct, add_irrig_pp, cut_short_pp, effects=None):
    """District-level sliders: change plot *shares*, apply 2022 kg/ha gaps."""
    effects = effects or load_effects()
    irrig_gap = float(effects.get("irrigated", 0))
    short_gap = abs(float(effects.get("organic_short", 0)))
    new_irrig = min(100.0, float(current_irrig_pct) + float(add_irrig_pp))
    new_short = max(0.0, float(current_short_pct) - float(cut_short_pp))
    gain = ((new_irrig - current_irrig_pct) / 100.0) * irrig_gap + (
        (current_short_pct - new_short) / 100.0
    ) * short_gap
    base = float(base_yield)
    return {
        "base_kg_ha": base,
        "projected_kg_ha": base + gain,
        "gain_kg_ha": gain,
        "gain_pct": (100.0 * gain / base) if base else 0.0,
        "new_irrig_pct": new_irrig,
        "new_short_pct": new_short,
        "irrig_gap": irrig_gap,
        "short_gap": short_gap,
        "note": "Season A 2022 within-district OLS on plot shares. Not this season's harvest. Terracing is not used as a gain.",
    }


def plot_package(usual_yield, effects=None):
    """One rainfed-style plot: add practices one at a time. Do not add terracing as a plus."""
    effects = effects or load_effects()
    base = float(usual_yield)
    irrig = float(effects["irrigated"])
    inorganic = float(effects["inorganic"])
    organic = float(effects["organic"])
    return {
        "baseline_kg_ha": round(base, 1),
        "with_irrigation_kg_ha": round(base + irrig, 1),
        "with_inorganic_kg_ha": round(base + inorganic, 1),
        "with_organic_kg_ha": round(base + organic, 1),
        "with_irrigation_and_inorganic_kg_ha": round(base + irrig + inorganic, 1),
        "irrigation_kg_ha": round(irrig, 1),
        "inorganic_kg_ha": round(inorganic, 1),
        "organic_kg_ha": round(organic, 1),
        "protected_kg_ha": round(float(effects["protected"]), 1),
        "n_plots": N_PLOTS_SIM_2022A,
        "year": 2022,
        "season": "A",
        "note": (
            f"Adds Season A 2022 within-district gaps ({N_PLOTS_SIM_2022A} maize plots) "
            "to this district's usual maize yield. Not a 2026 harvest. "
            "Terracing is reported separately because its OLS sign is negative (likely slope)."
        ),
    }


def drought_screen(rain_pct, water_week_mm, irrigated_pct, forecast_week_mm):
    """Same thresholds as src/prepare_alerts.py classify(), without claiming NAIS."""
    dry = float(rain_pct) <= -10
    low_irrigation = float(irrigated_pct) < 10
    dry_week = float(forecast_week_mm) < 10
    week_deficit = float(water_week_mm) < -10

    if dry and low_irrigation and dry_week:
        level = "irrigate_now"
        flag = True
    elif dry and low_irrigation:
        level = "irrigation_gap"
        flag = True
    elif week_deficit and dry:
        level = "rainfall_watch"
        flag = True
    else:
        level = "watch_or_stable"
        flag = False

    return {
        "level": level,
        "cropwatch_water_flag": flag,
        "nais_payout_triggered": False,
        "note": (
            "CropWatch screen from Open-Meteo this season vs CHIRPS 2018–2025 usual rain, "
            "and Season A 2022 irrigation share. Not an official NAIS / Tekana trigger. "
            "CropWatch does not pay claims."
        ),
    }


def ssit_plan(hectares, source="marsh"):
    """Kit class from size and water source. Indicative RWF, 50% farmer / 50% subsidy split."""
    ha = float(hectares)
    source = (source or "marsh").lower()
    warning = ""

    if source == "tank":
        if ha > 0.5:
            key = "treadle"
            en = "Rainwater tank is usually too small for maize on this area — size the tank first, then a treadle or drip kit"
            rw = "Igikoresho cy'imvura gikunze kuba gito ku bigori kuri ubu buso — banza ubure igikoresho, hanyuma pompi y'amaguru"
            warning = "Tank volume, not pump size, is the limit here."
        else:
            key = "treadle"
            en = "Rainwater tank plus a foot treadle pump (small bed / nursery)"
            rw = "Igikoresho cy'imvura n'ipompi y'amaguru (ubusohoke buto)"
    elif source == "well":
        if ha < 0.5:
            key = "solar"
            en = "Shallow-well solar pump (about 1.5 kW) with drip on a small plot"
            rw = "Pompi y'izuba ku iriba (hafi 1.5 kW) n'uburyo bwa drip ku murima muto"
        elif ha <= 2.0:
            key = "solar"
            en = "Solar surface or submersible pump (about 1.5 kW) with a drip kit"
            rw = "Pompi y'izuba (hafi 1.5 kW) n'uburyo bwa drip"
        else:
            key = "motor"
            en = "Motor pump from a high-yield borehole (check yield before buying)"
            rw = "Pompi y'imashini ku iriba rikomeye (suzuma amazi mbere yo kugura)"
            warning = "A well must yield enough litres per hour for this area."
    else:
        if ha < 0.5:
            key = "treadle"
            en = "Manual foot treadle pump from a marsh or river"
            rw = "Pompi ikoreshwa n'amaguru ku gishanga cyangwa uruzi"
        elif ha <= 2.0:
            key = "solar"
            en = "Solar surface pump (about 1.5 kW) with a 2 ha drip kit"
            rw = "Pompi y'izuba (hafi 1.5 kW) n'uburyo bwa drip bwa hegitari 2"
        else:
            key = "motor"
            en = "Portable motor pump (about 5.5 HP) with rain-gun or hose from marsh/river"
            rw = "Pompi y'imashini (hafi 5.5 HP) ku gishanga cyangwa uruzi"

    cost = KIT_COST_RWF[key]
    if source == "tank":
        cost += TANK_EXTRA_RWF
    subsidy = round(cost * 0.5)
    farmer = cost - subsidy
    return {
        "key": key,
        "name_en": en,
        "name_rw": rw,
        "source": source,
        "hectares": ha,
        "indicative_cost_rwf": cost,
        "subsidy_rwf": subsidy,
        "farmer_rwf": farmer,
        "warning": warning,
        "note": "Indicative kit class and a 50/50 split for planning. Not an official MINAGRI quote.",
    }


def kit_for_hectares(hectares):
    plan = ssit_plan(hectares, "marsh")
    return plan["key"], plan["name_en"], plan["name_rw"]


def maize_value(hectares, irrig_gap_kg_ha, price_rwf):
    if price_rwf is None:
        return None, None
    kg = float(irrig_gap_kg_ha) * float(hectares)
    return kg, kg * float(price_rwf)


def _clip(value, lo, hi):
    return max(lo, min(hi, float(value)))


def track1_need_score(row):
    """Planning need for SSIT and hillside care. Not a hackathon judge score."""
    rain = float(row.get("rain_difference_pct") or 0)
    irrig = float(row.get("irrigated_pct") or 0)
    soil = float(row.get("concern_pct") or 0)
    week = float(row.get("water_balance_week_mm") or 0)
    return {
        "rain_pts": round(_clip(-rain, 0, 40), 1),
        "irrig_pts": round(_clip((10.0 - irrig) * 3.0, 0, 30), 1),
        "soil_pts": round(_clip(soil * 0.4, 0, 20), 1),
        "week_pts": round(_clip(-week * 0.5, 0, 10), 1),
        "track1_score": round(
            _clip(-rain, 0, 40)
            + _clip((10.0 - irrig) * 3.0, 0, 30)
            + _clip(soil * 0.4, 0, 20)
            + _clip(-week * 0.5, 0, 10),
            1,
        ),
    }


def national_ranking(alerts):
    """30 districts ordered by irrigation/soil/water need. Not the NISR team mark sheet."""
    cols = [
        "district",
        "province",
        "alert",
        "rain_difference_pct",
        "forecast_week_mm",
        "water_balance_week_mm",
        "irrigated_pct",
        "concern_pct",
        "usual_yield_kg_ha",
    ]
    have = [c for c in cols if c in alerts.columns]
    out = alerts[have].copy()
    parts = out.apply(track1_need_score, axis=1, result_type="expand")
    out = pd.concat([out, parts], axis=1)
    out["track1_score"] = (
        out["rain_pts"] + out["irrig_pts"] + out["soil_pts"] + out["week_pts"]
    )
    out = out.sort_values(["track1_score", "rain_difference_pct"], ascending=[False, True]).reset_index(drop=True)
    out.insert(0, "rank", range(1, len(out) + 1))
    kit = ssit_plan(0.5, "marsh")
    out["ssit_kit_0_5ha_marsh"] = kit["key"]
    out["note"] = (
        "Planner order only. Not the NISR 2026 evaluation criteria for the team."
    )
    return out

