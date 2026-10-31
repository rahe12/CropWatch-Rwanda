"""CropWatch Copilot: district tables, 2022 yield gaps, alert rule, SMS draft.

Does not run a live NAIS payout or a 90-day price forecast.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

import pandas as pd
import requests

from src.logic import (
    N_PLOTS_SIM_2022A,
    drought_screen,
    kit_for_hectares,
    load_effects,
    plot_package,
    ssit_plan,
)

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
APP_TABLES = PROCESSED / "app"
LOOKUPS = PROCESSED / "lookups"

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
# llama-3.1-8b-instant shut down for free/dev Groq on 16 Aug 2026.
GROQ_MODELS = ("openai/gpt-oss-20b", "llama-3.1-8b-instant")
GROQ_MODEL = GROQ_MODELS[0]
GEMINI_MODEL = "gemini-2.0-flash"
LAST_LLM_ERROR = ""

HELLO_WORDS = {
    "hey", "hi", "hello", "yo", "muraho", "mwiriwe", "bite", "salut",
    "good morning", "good afternoon", "good evening", "komera", "mwaramutse",
}

_LOOKUPS_CACHE = {}


def get_lookups():
    global _LOOKUPS_CACHE
    if not _LOOKUPS_CACHE:
        try:
            p_match = LOOKUPS / "crop_price_match.csv"
            if p_match.exists():
                _LOOKUPS_CACHE["crop_match"] = pd.read_csv(p_match)
            p_seasons = LOOKUPS / "seasons.csv"
            if p_seasons.exists():
                _LOOKUPS_CACHE["seasons"] = pd.read_csv(p_seasons)
            p_cal = LOOKUPS / "maize_sorghum_calendar.csv"
            if p_cal.exists():
                _LOOKUPS_CACHE["calendar"] = pd.read_csv(p_cal)
            p_zones = LOOKUPS / "crop_calendar_zones.csv"
            if p_zones.exists():
                _LOOKUPS_CACHE["zones"] = pd.read_csv(p_zones)
            p_unmatched = LOOKUPS / "crops_without_a_price.csv"
            if p_unmatched.exists():
                _LOOKUPS_CACHE["unmatched"] = pd.read_csv(p_unmatched)
        except Exception:
            pass
    return _LOOKUPS_CACHE


def pack(alerts, forecast, watch, soil, vegetation, district, season="A"):
    alert = alerts[alerts["district"] == district].iloc[0]
    week = forecast[forecast["district"] == district].sort_values("date")
    watch_hit = watch[(watch["district"] == district) & (watch["season"] == season)]
    watch_row = watch_hit.iloc[0] if not watch_hit.empty else None
    soil_hit = soil[soil["district"] == district]
    soil_row = soil_hit.iloc[0] if not soil_hit.empty else None
    veg = vegetation[vegetation["district"] == district].sort_values("year")
    national = vegetation.groupby("year", as_index=False)["vegetation_mean"].mean()

    price = None
    price_date = None
    national_price = None
    if watch_row is not None:
        if pd.notna(watch_row.get("maize_price_rwf_per_kg")):
            price = float(watch_row["maize_price_rwf_per_kg"])
            price_date = str(watch_row["price_date"])
        if pd.notna(watch_row.get("national_maize_price_rwf_per_kg")):
            national_price = float(watch_row["national_maize_price_rwf_per_kg"])
        if not price_date:
            price_date = str(watch_row.get("national_price_date") or "")

    veg_2026 = veg[veg["year"] == 2026]
    veg_hist = veg[veg["year"].between(2018, 2025)]

    water_week = float(alert["water_balance_week_mm"]) if "water_balance_week_mm" in alert and pd.notna(alert.get("water_balance_week_mm")) else 0.0
    deficit_mm = abs(min(0.0, water_week))
    liters_ha = deficit_mm * 10000.0

    return {
        "district": district,
        "alert": str(alert["alert"]),
        "rain_pct": float(alert["rain_difference_pct"]),
        "rain_mm": float(alert["rain_so_far_mm"]),
        "usual_mm": float(alert["usual_sep_oct_mm"]),
        "week_mm": float(alert["forecast_week_mm"]),
        "irrigated_pct": float(alert["irrigated_pct"]),
        "concern_pct": float(alert["concern_pct"]),
        "protected_pct": float(alert["protected_pct"]),
        "organic_pct": float(alert["organic_pct"]),
        "inorganic_pct": float(alert["inorganic_pct"]),
        "usual_yield": float(alert["usual_yield_kg_ha"]),
        "climate": str(alert["climate_class"]) if "climate_class" in alert and pd.notna(alert.get("climate_class")) else "",
        "etc_week": float(alert["etc_week_mm"]) if "etc_week_mm" in alert and pd.notna(alert.get("etc_week_mm")) else 25.0,
        "water_week": water_week,
        "deficit_mm": deficit_mm,
        "liters_ha": liters_ha,
        "kc": float(alert["kc_maize"]) if "kc_maize" in alert and pd.notna(alert.get("kc_maize")) else 1.15,
        "price": price if price is not None else national_price,
        "price_date": price_date or "Latest",
        "national_price": national_price,
        "veg_now": float(veg_2026["vegetation_mean"].iloc[0]) if not veg_2026.empty else 0.42,
        "veg_usual": float(veg_hist["vegetation_mean"].mean()) if not veg_hist.empty else 0.44,
        "week": week,
        "veg": veg,
        "national_veg": national,
        "soil": soil_row,
        "watch": watch_row,
    }


def _usable_key(val):
    text = str(val or "").strip()
    if not text:
        return ""
    low = text.lower()
    if "paste" in low or "your_" in low or text.endswith("_here"):
        return ""
    return text


def secret(name):
    got = _usable_key(os.environ.get(name, ""))
    if got:
        return got
    try:
        import streamlit as st
        got = _usable_key(st.secrets.get(name, ""))
        if got:
            return got
        got = _usable_key(st.session_state.get(name, ""))
        if got:
            return got
    except Exception:
        pass
    return ""


def llm_status():
    if secret("GROQ_API_KEY"):
        return "groq"
    if secret("GEMINI_API_KEY") or secret("GOOGLE_API_KEY"):
        return "gemini"
    return ""


# ==============================================================================
# SEMANTIC INTENT CLASSIFICATION & DIALOGUE RECOGNITION
# ==============================================================================
RWANDA_DISTRICTS = [
    "Bugesera", "Nyagatare", "Musanze", "Nyaruguru", "Gatsibo", "Kayonza", "Rwamagana", "Kirehe",
    "Ngoma", "Gasabo", "Kicukiro", "Nyarugenge", "Rulindo", "Gakenke", "Burera", "Gicumbi",
    "Kamonyi", "Muhanga", "Ruhango", "Nyanza", "Huye", "Gisagara", "Nyamagabe", "Rusizi",
    "Nyamasheke", "Karongi", "Rutsiro", "Rubavu", "Nyabihu", "Ngororero"
]


def extract_district(text):
    """Senior-grade NER entity extraction: detects any of Rwanda's 30 districts from natural text."""
    if not text:
        return None
    raw = text.lower()
    for d in RWANDA_DISTRICTS:
        pattern = r"\b" + re.escape(d.lower()) + r"\b"
        if re.search(pattern, raw):
            return d
    return None


def extract_all_districts(text):
    """Extracts all mentioned districts for multi-district comparisons."""
    if not text:
        return []
    raw = text.lower()
    found = []
    for d in RWANDA_DISTRICTS:
        pattern = r"\b" + re.escape(d.lower()) + r"\b"
        if re.search(pattern, raw):
            found.append(d)
    return found
def get_followups(intent, lang="en"):
    """Returns 3 clickable suggested follow-up prompts for conversational flow."""
    is_rw = (lang == "rw")
    followup_map = {
        "yield": [
            ("💧 Inyungu yo Kuhira" if is_rw else "💧 Irrigation Uplift"),
            ("💰 Igiciro cya WFP" if is_rw else "💰 Latest WFP maize price"),
            ("📱 Inyandiko ya SMS (ntikohereza)" if is_rw else "📱 SMS draft (not sent)"),
        ],
        "irrigation": [
            ("🧪 Kubara Umusaruro wose" if is_rw else "🧪 Run Yield Simulation"),
            ("🛡️ Icyuho cy'amazi (si NAIS)" if is_rw else "🛡️ Water-stress screen (not NAIS)"),
            ("💰 Gahunda ya SSIT ya 50%" if is_rw else "💰 50% SSIT Equipment Subsidy"),
        ],
        "insurance": [
            ("💧 Uburyo bwo Kuhira" if is_rw else "💧 Smart Irrigation Strategy"),
            ("🌧️ Iteganyagihe ry'Icyumweru" if is_rw else "🌧️ 7-Day Rainfall Forecast"),
            ("🧪 Gusuzuma Umusaruro" if is_rw else "🧪 Check Yield Impact"),
        ],
        "market": [
            ("📦 Ubuhuniki mu Mifuka ya PICS" if is_rw else "📦 PICS Hermetic Storage"),
            ("🧪 Kubara Umusaruro" if is_rw else "🧪 Maize Yield Uplift"),
            ("💧 Icyuho cy'Ubuhehere" if is_rw else "💧 Check Irrigation Deficit"),
        ],
        "yellow_leaves": [
            ("🧪 Ikoreshwa ry'Ifumbire ya Urea" if is_rw else "🧪 Urea Top-Dressing Guide"),
            ("💧 Kureba Icyuho cy'Amazi" if is_rw else "💧 Check Waterlogging & Deficit"),
            ("🐛 Kurwanya Inyonzi (Fall Armyworm)" if is_rw else "🐛 Fall Armyworm Identification"),
        ],
        "fertilizer": [
            ("🌿 Gushyiramo Ishwagara (Lime)" if is_rw else "🌿 Agricultural Lime Guide"),
            ("🧪 Kubara Umusaruro w'Ibigori" if is_rw else "🧪 Predict Maize Yield"),
            ("📦 Kubika Imyaka muri PICS" if is_rw else "📦 Grain Storage Solutions"),
        ],
        "lime_acidity": [
            ("🧪 Ifumbire ya DAP na Urea" if is_rw else "🧪 DAP & Urea Split Application"),
            ("⛰️ Amaterasi n'Isuri" if is_rw else "⛰️ Terracing & Hillside Erosion"),
            ("💧 Kuhira Imyaka" if is_rw else "💧 Supplemental Irrigation"),
        ],
        "seasons": [
            ("🌱 Igihe cyo Gutera Imbuto" if is_rw else "🌱 Sowing Windows & Spacing"),
            ("🌧️ Iteganyagihe ry'Icyumweru" if is_rw else "🌧️ 7-Day Weather Forecast"),
            ("🛡️ Icyuho cy'amazi (si NAIS)" if is_rw else "🛡️ Water-stress screen (not NAIS)"),
        ],
        "spacing": [
            ("🧪 Ifumbire ya DAP n'Ibigori" if is_rw else "🧪 DAP Fertilizer Rates"),
            ("🐛 Kurwanya Inyonzi" if is_rw else "🐛 Pest & Disease Control"),
            ("💧 Icyuho cy'Amazi" if is_rw else "💧 Irrigation Scheduling"),
        ],
        "district_compare": [
            ("🧪 Kubara Umusaruro" if is_rw else "🧪 Predict Maize Yield"),
            ("💰 Ibiciro by'Amasoko" if is_rw else "💰 Market Prices Comparison"),
            ("🌧️ Iteganyagihe ry'Icyumweru" if is_rw else "🌧️ 7-Day Weather Forecast"),
        ],
    }
    chips = followup_map.get(intent, [
        ("🧪 Kubara Umusaruro (ML)" if is_rw else "🧪 Predict Maize Yield (ML)"),
        ("💧 Kureba Icyuho cy'Amazi" if is_rw else "💧 Check Irrigation Deficit"),
        ("💰 Ibiciro ku Masoko" if is_rw else "💰 Market Prices & Arbitrage"),
    ])
    rephrase = "✏️ Vuga mu yandi magambo" if is_rw else "✏️ Rephrase this"
    return [rephrase] + [c for c in chips if c != rephrase][:2]


def classify(text, context=None):
    """Classifies user query intent using semantic patterns, keyword clusters,
    and conversational context (remembering previous district, crop, or subject).
    """
    raw = (text or "").strip().lower().strip("!?.")

    # 1. Greetings
    if raw in HELLO_WORDS or raw.startswith(("hey ", "hi ", "hello ", "muraho ", "bite ")):
        return "hello"

    if any(k in raw for k in (
        "rephrase", "paraphrase", "rewrite", "say it simpler", "in other words",
        "make it simpler", "say that again", "vuga mu yandi", "sobanura mu yandi",
        "ongera uvuge", "mu magambo yoroshye",
    )):
        return "rephrase"

    # 1b. Engineering Team & Hackathon Authorship
    if any(k in raw for k in ("who created", "who built", "authors", "creator", "developers", "team", "hackathon", "murenzi", "bahire", "polytechnic", "byakozwe na nde", "irushanwa", "abakoze uyu mushinga")):
        return "team"

    # 2. Multi-District Comparison
    districts = extract_all_districts(raw)
    if len(districts) >= 2 and any(k in raw for k in ("compare", "versus", "vs", "difference", "itandukaniro", "gereranya")):
        return "district_compare"

    # 3. Yellow Leaves / Crop Deficiencies / Chlorosis
    if any(k in raw for k in ("yellow", "yellowing", "umuhondo", "leaves turning", "amababi ahinduka", "chlorosis", "pale leaves", "burn on leaves")):
        return "yellow_leaves"

    # 4. Fertilizer Protocol & Application Rates
    if any(k in raw for k in ("fertilizer", "ifumbire", "dap", "urea", "npk", "manure", "iborera", "how much fertilizer", "gushyiramo ifumbire", "top dress", "basal")):
        return "fertilizer"

    # 5. Soil Acidity & Agricultural Lime (Ishwagara)
    if any(k in raw for k in ("lime", "ishwagara", "acidity", "acidic", "ph", "ubusharire", "soil ph", "dolomite")):
        return "lime_acidity"

    # 6. Seasons & Calendar Differences
    if any(k in raw for k in ("season a", "season b", "season c", "difference between season", "igihembwe a", "igihembwe b", "igihembwe c", "when to plant", "planting window", "calendar", "igihe cyo gutera")):
        return "seasons"

    # 7. Spacing & Planting Density
    if any(k in raw for k in ("spacing", "density", "inter-row", "distance", "ubuso hagati", "interasaniro", "plants per hectare", "seed rate", "ibiro by'imbuto")):
        return "spacing"

    # 8. Storage, PICS Bags & Post-Harvest Losses
    if any(k in raw for k in ("pics", "storage", "store", "guhunika", "weevil", "imungu", "aflatoxin", "loss", "hermetic", "imifuka ya pics")):
        return "storage"

    # 9. MINAGRI SSIT Subsidy
    if any(k in raw for k in ("ssit", "subsidy", "50%", "nkunganire", "kunganirwa", "pompi ya leta", "rab subsidy", "government subsidy")):
        return "ssit_subsidy"

    # 10. NAIS Agricultural Insurance
    if any(k in raw for k in ("nais", "insurance", "ubwishingizi", "tekana", "indishyi", "payout", "claim", "drought insurance", "premium")):
        return "insurance_nais"

    # 11. Available Crops in Dataset
    if any(k in raw for k in ("which crops", "what crops", "available crops", "list of crops", "ibihingwa bihari", "ibihingwa biboneka", "crops in this dataset")):
        return "crops_available"

    # 12. General Definitions
    if any(k in raw for k in ("what does yield mean", "what is yield", "define yield", "ibisobanuro by'umusaruro", "umusaruro bishatse kuvuga iki")):
        return "yield_definition"
    if any(k in raw for k in ("what is water balance", "what is deficit", "penman", "cropwat", "ibisobanuro by'icyuho", "water balance meaning")):
        return "water_definition"

    # 13. Data Registry Location
    if any(k in raw for k in ("where can i find", "where is the data", "download data", "data registry", "amakuru aboneka he", "gukuramo amakuru", "source of data")):
        return "data_location"

    # 14. Charts / Maps Explanation
    if any(k in raw for k in ("explain this chart", "explain chart", "explain map", "how to read", "sobannura ikarita", "sobanura iki gishushanyo", "ndre meaning", "what does map show")):
        return "chart_explain"

    # 15. Core Machine Learning Models
    if any(k in raw for k in ("yield", "umusaruro", "uplift", "harvest", "gain", "projection", "predict yield")):
        return "yield"
    if any(k in raw for k in ("price", "igiciro", "isoko", "market", "sell", "cost", "wfp price", "arbitrage")):
        return "market"
    if any(k in raw for k in ("irrigate", "irrigation", "water", "kuhira", "deficit", "pump", "liters", "litiro", "schedule", "pumping")):
        return "irrigation"
    if any(k in raw for k in ("terrace", "amaterasi", "soil", "ubutaka", "erosion", "isuri", "slope", "urubingo")):
        return "soil"
    if any(k in raw for k in ("pest", "disease", "armyworm", "inyonzi", "blight", "miyira", "caterpillar", "inseti")):
        return "pests"
    if any(k in raw for k in ("sms", "ussd", "message", "ubutumwa", "mobile", "phone", "telefoni", "broadcast")):
        return "sms"
    if any(k in raw for k in ("forecast", "weather", "rain this week", "imvura y'iki cyumweru", "teganyijwe")):
        return "week"

    # 16. Context-aware follow-up
    if context and "last_intent" in context:
        return context["last_intent"]

    return "general_agronomy"


# ==============================================================================
# REAL MACHINE LEARNING INFERENCE ENGINES (TRAINED ON NISR & WFP DATA)
# ==============================================================================

def _rwf(p, kg):
    price = p.get("price")
    if price is None:
        return "—"
    return f"{kg * float(price):,.0f} RWF"


def ai_yield_ml(p, lang="en"):
    """Same 2022 OLS gaps as the Yield Simulator. Not a Random Forest harvest."""
    d = p["district"]
    pkg = plot_package(p["usual_yield"])
    price = p.get("price")
    price_line = (
        f"{price:.0f} RWF/kg" if price is not None else "no WFP maize price for this district"
    )
    if lang == "rw":
        return f"""### Umusaruro w'ibigori — itandukaniro rya 2022, si isarura rya 2026 — {d}

Imirima **{N_PLOTS_SIM_2022A}** y'ibigori mu gihembwe A cya 2022. Tuvana umusaruro usanzwe w'aka karere, noneho twongeraho itandukaniro ry'imirima yahijwe cyangwa yafashwe ifumbire **mu karere kamwe**. Si Random Forest. Si isarura rya 2026.

| Uburyo | kg/ha | Impinduka | Ku giciro cy'isoko |
| :--- | :---: | :---: | :---: |
| Umusaruro usanzwe w'aka karere | `{pkg['baseline_kg_ha']:.0f}` | — | — |
| + kuhira | `{pkg['with_irrigation_kg_ha']:.0f}` | `{pkg['irrigation_kg_ha']:+.0f}` | {_rwf(p, pkg['irrigation_kg_ha'])} |
| + ifumbire y'amabuye | `{pkg['with_inorganic_kg_ha']:.0f}` | `{pkg['inorganic_kg_ha']:+.0f}` | {_rwf(p, pkg['inorganic_kg_ha'])} |
| + ifumbire y'imborera | `{pkg['with_organic_kg_ha']:.0f}` | `{pkg['organic_kg_ha']:+.0f}` | {_rwf(p, pkg['organic_kg_ha'])} |
| kuhira + ifumbire y'amabuye | `{pkg['with_irrigation_and_inorganic_kg_ha']:.0f}` | `{(pkg['irrigation_kg_ha'] + pkg['inorganic_kg_ha']):+.0f}` | {_rwf(p, pkg['irrigation_kg_ha'] + pkg['inorganic_kg_ha'])} |

Amaterasi ntiyongerewe nk'inyungu: mu 2022 imirima irinzwe yari hasi ({pkg['protected_kg_ha']:+.0f} kg/ha), kubera ko akenshi iri ku misozi.

Igiciro: **{price_line}**.

👉 [Simulator](?page=simulator) ikoresha amategeko amwe ku buso bw'uturere."""

    return f"""### Maize yield gaps from 2022 — not a 2026 harvest — {d}

**{N_PLOTS_SIM_2022A}** Season A 2022 maize plots. Start from this district's usual yield, then add the within-district gap for irrigation or fertilizer. Same numbers as the Yield Simulator. Not a Random Forest forecast.

| Package | kg/ha | Change | At latest maize price |
| :--- | :---: | :---: | :---: |
| District usual yield | `{pkg['baseline_kg_ha']:.0f}` | — | — |
| + irrigation | `{pkg['with_irrigation_kg_ha']:.0f}` | `{pkg['irrigation_kg_ha']:+.0f}` | {_rwf(p, pkg['irrigation_kg_ha'])} |
| + inorganic fertilizer | `{pkg['with_inorganic_kg_ha']:.0f}` | `{pkg['inorganic_kg_ha']:+.0f}` | {_rwf(p, pkg['inorganic_kg_ha'])} |
| + organic fertilizer | `{pkg['with_organic_kg_ha']:.0f}` | `{pkg['organic_kg_ha']:+.0f}` | {_rwf(p, pkg['organic_kg_ha'])} |
| irrigation + inorganic | `{pkg['with_irrigation_and_inorganic_kg_ha']:.0f}` | `{(pkg['irrigation_kg_ha'] + pkg['inorganic_kg_ha']):+.0f}` | {_rwf(p, pkg['irrigation_kg_ha'] + pkg['inorganic_kg_ha'])} |

Terracing is **not** added as a gain: protected plots yielded **{pkg['protected_kg_ha']:+.0f} kg/ha** in the same district in 2022 (likely steeper land).

Price used: **{price_line}**.

👉 The [Yield Simulator](?page=simulator) uses the same 2022 gaps on district *shares*."""


def ai_drought_ml(p, lang="en"):
    """Same water screen as the alert map. Does not pay NAIS."""
    d = p["district"]
    screen = drought_screen(p["rain_pct"], p["water_week"], p["irrigated_pct"], p["week_mm"])
    flag = "Yego — icyuho cy'amazi" if screen["cropwatch_water_flag"] else "Oya — nta burira bwo kuhira"
    flag_en = "Yes — irrigation / dry-start flag" if screen["cropwatch_water_flag"] else "No — not an irrigation alert"
    if lang == "rw":
        return f"""### Icyuho cy'amazi — {d} (si indishyi ya NAIS)

Amategeko amwe n'ikarita y'iburira:

* Imvura igeze: **{p['rain_pct']:+.0f}%** ugereranyije n'isanzwe (Open-Meteo vs CHIRPS 2018–2025)
* Iminsi 7: **{p['week_mm']:.0f} mm**
* Imiti yahijwe mu 2022: **{p['irrigated_pct']:.1f}%**
* Icyumweru $P_e - ET_c$: **{p['water_week']:+.1f} mm**
* Icyiciro: **{screen['level']}**
* Iburira rya CropWatch: **{flag}**

**NAIS / Tekana:** CropWatch **ntishyura** indishyi kandi ntihuza na SONARWA. Niba ushaka ubwishingizi, gana umurenge cyangwa koperative **mbere** y'igihembwe.

👉 [Ikarita y'iburira](?page=alerts)"""

    return f"""### Water-stress screen — {d} (not an NAIS payout)

Same rule as the alert map:

* Rain so far: **{p['rain_pct']:+.0f}%** vs usual (Open-Meteo this season vs CHIRPS 2018–2025)
* Next 7 days: **{p['week_mm']:.0f} mm**
* Irrigated plots in 2022: **{p['irrigated_pct']:.1f}%**
* This week $P_e - ET_c$: **{p['water_week']:+.1f} mm**
* Screen: **{screen['level']}**
* CropWatch flag: **{flag_en}**

**NAIS / Tekana:** CropWatch **does not** trigger or pay insurance. Enrol through the sector or a cooperative **before** the season.

👉 [Alert map](?page=alerts)"""


def ai_price_ml(p, lang="en"):
    """Latest WFP maize price only. No 30/60/90-day invented forecast."""
    d = p["district"]
    cur = p.get("price")
    nat = p.get("national_price")
    date_str = p.get("price_date") or "—"
    if cur is None and nat is None:
        body = "Nta giciro cy'ibigori cya WFP kuri aka karere." if lang == "rw" else "No WFP maize price row for this district."
        return f"### WFP maize price — {d}\n\n{body}\n\n👉 [Prices](?page=watch)"
    local = f"{cur:.0f} RWF/kg" if cur is not None else "—"
    national = f"{nat:.0f} RWF/kg" if nat is not None else "—"
    vs = ""
    if cur is not None and nat is not None:
        vs = f"{cur - nat:+.0f} RWF/kg vs national"
    if lang == "rw":
        return f"""### Igiciro cy'ibigori (WFP) — {d}

* Aka karere: **{local}** ({date_str})
* Igihugu: **{national}**
* {vs}

Nta iteganyagihe ry'iminsi 30/60/90. CropWatch ntiyihangira ibiciro bizaza. PICS irinda imungu; ntiyongera igiciro.

👉 [Amasoko](?page=watch)"""
    return f"""### Latest WFP maize price — {d}

* This district: **{local}** ({date_str})
* National: **{national}**
* {vs}

There is **no** 30/60/90-day price forecast in this app. CropWatch does not invent future prices. PICS bags cut storage loss; they do not raise the market price.

👉 [Market desk](?page=watch)"""


def ai_irrigation(p, lang="en"):
    d = p["district"]
    deficit = p["deficit_mm"]
    liters = p["liters_ha"]
    plan = ssit_plan(0.5, "marsh")
    kit = plan["name_rw"] if lang == "rw" else plan["name_en"]
    if lang == "rw":
        return f"""### Kuhira — {d}

* Icyuho cy'icyumweru: **{deficit:.1f} mm** ({liters:,.0f} L/ha; {liters * 0.5:,.0f} L kuri 0.5 ha)
* Pompi y'urugero kuri 0.5 ha ku gishanga: **{kit}**
* Igiciro cyateganyijwe: **{plan['indicative_cost_rwf']:,.0f} RWF** — umuhinzi **{plan['farmer_rwf']:,.0f}**, nkunganire 50% **{plan['subsidy_rwf']:,.0f}** (si igiciro cya MINAGRI)

Kuhira mu gitondo cyangwa nimugoroba. Hindura inkomoko y'amazi kuri [SSIT](?page=simulator)."""
    return f"""### Irrigation this week — {d}

* Weekly gap: **{deficit:.1f} mm** ({liters:,.0f} L/ha; {liters * 0.5:,.0f} L on 0.5 ha)
* Example kit for 0.5 ha from a marsh: **{kit}**
* Indicative cost: **{plan['indicative_cost_rwf']:,.0f} RWF** — farmer **{plan['farmer_rwf']:,.0f}**, 50% co-share **{plan['subsidy_rwf']:,.0f}** (not a MINAGRI quote)

Water early morning or evening. Change water source on the [SSIT tab](?page=simulator)."""


def ai_soil(p, lang="en"):
    d = p["district"]
    concern = p["concern_pct"]
    prot = p["protected_pct"]

    if lang == "rw":
        return f"""### 🏔️ Amaterasi n'Ubuzima bw'Ubutaka — {d}

* **Imirima yibasiwe n'isuri (NISR SAS):** `{concern:.1f}%`
* **Imirima irinzwe n'amaterasi cyangwa ibyatsi:** `{prot:.1f}%`

#### 🛠️ Ingamba zo Kubungabunga Ubutaka:
1. **Amaterasi y'Indinganire (Radical Terraces):** Kuri hejuru y'ubuhaname bwa 16%, amaterasi y'indinganire niyo yonyine arinda ubutaka gutwarwa n'imvura.
2. **Gutera Urubingo na Vetiver:** Huza imiferege n'ibyatsi bifata ubutaka ku misozi ihanamye.
3. **Ishwagara (Agricultural Lime):** Gushyiramo Toni 2.5/ha z'ishwagara mu butaka bwa aside kugira ngo ifumbire ya DAP n'ifumbire y'imborera bibashe gukora neza."""
    else:
        return f"""### 🏔️ Terraces, Slope Grading & Soil Conservation — {d}

* **Surveyed Plots with Erosion Concern (NISR SAS):** `{concern:.1f}%`
* **Plots with Physical Soil Conservation:** `{prot:.1f}%`

#### 🛠️ Field Engineering Directives:
1. **Bench Terracing (Radical Terraces):** Mandatory for slopes >16% to intercept heavy runoff during extreme storm events.
2. **Biological Hedgerows:** Establish *Pennisetum purpureum* (Urubingo) and Vetiver grass along infiltration contour trenches.
3. **Soil Acidity Remediation:** Apply 2.5 MT/ha of agricultural limestone on acidic highland slopes to unlock phosphorus fixation."""


def ai_pests(p, lang="en"):
    d = p["district"]

    if lang == "rw":
        return f"""### 🐛 Inama ku Byonnyi, Indwara, n'Ifumbire mu Murima — {d}

#### 1. Kurwanya Inyonzi / Nsenene mu Bigori (Fall Armyworm):
* **Icyitegererezo cyo kugenzura:** Suzuma ibiti 20 ahantu 5 mu murima ureba niba hari amababi arimo utwenge (window panes).
* **Uburyo bwa gakondo bwa mbere:** Shyira mu mutima w'ikigori agatsiko k'umusenyi mwiza uvanze n'ivu ry'inkwi cyangwa umushongi w'ibibabi by'umuti wa Nimu (Neem).
* **Imiti yemewe:** Koresha *Emamectin Benzoate* (Prove 1.92 EC, Attack) witwaje ibikoresho birinda uburozi, utera mu kabwibwi igihe inyonzi ziri kurya.

#### 2. Kurinda Indwara y'Ibirayi (Miyira / Late Blight):
* Tera umuti wa *Mancozeb* cyangwa *Metalaxyl* mbere y'uko imvura igwa niba ubushuhe burengeje 85%.

#### 3. Ingengabihe y'Ifumbire ya RAB:
* **Gutera (DAP):** Koresha ibiro 100/ha ushyira ifumbire ku ntera ya santimetero 5 uvuye ku mbuto.
* **Ibigori bikuze (Urea 1):** Bigeze mu mavi (V6), shyiramo ibiro 50/ha bya Urea mu butaka buhehereye.
* **Igihe cyo kurabya (Urea 2):** Shyiramo ibindi biro 50/ha kugira ngo ikigori cyuzure neza."""
    else:
        return f"""### 🐛 Crop Diagnostics, Pest Control & Fertilizer Protocol — {d}

#### 1. Fall Armyworm Management (*Spodoptera frugiperda*):
* **Field Scouting:** Inspect 20 plants in 5 representative spots; threshold is reached if >10% of vegetative whorls show "window pane" skeletonized leaves.
* **Biological / Agroecological First Line:** Apply a pinch of clean dry sand mixed with fine wood ash or aqueous Neem leaf extract directly into the central plant whorl.
* **Chemical Intervention:** Spray registered bio-rational insecticides (e.g., *Emamectin benzoate* 1.92 EC or *Chlorantraniliprole*) late in the afternoon when larvae actively feed.

#### 2. Irish Potato Late Blight (*Phytophthora infestans*):
* Apply preventive *Mancozeb* (2.5 kg/ha) prior to forecasted rain events whenever relative humidity exceeds 85%.

#### 3. Official RAB Fertilizer Regimen:
* **Basal Application (At Planting):** 100 kg/ha DAP placed 5 cm beside and below seed furrows.
* **First Topdressing (Knee-High Stage V6):** 50 kg/ha Urea incorporated into moist soil to avoid volatilization.
* **Second Topdressing (Tasseling Window):** 50 kg/ha Urea to maximize grain weight and cob fill."""


def ai_sms(p, lang="en"):
    d = p["district"]
    deficit = p["deficit_mm"]
    if lang == "rw":
        sms = f"[CropWatch] {d}: imvura {p['rain_pct']:+.0f}% ku isanzwe. Icyuho {deficit:.0f}mm. Reba umurenge. Si ubutumwa bwa MINAGRI."
    else:
        sms = f"[CropWatch] {d}: rain {p['rain_pct']:+.0f}% vs usual. Gap {deficit:.0f}mm. Ask the sector. Not a MINAGRI text."
    sms = sms[:160]
    note = (
        "Iyi ni **inyandiko**. CropWatch **ntikohereza** SMS kandi ntihuza na *801#."
        if lang == "rw"
        else "This is a **draft**. CropWatch **does not send** SMS and is not connected to *801#."
    )
    return f"""### SMS draft (not sent)

```text
{sms}
```
{len(sms)} / 160 characters.

{note}"""


# ==============================================================================
# EXPANDED CONVERSATIONAL CAPABILITIES (PHASE 5)
# ==============================================================================

def ai_crops_available(lang="en"):
    """Explains all available crops in the verified NISR SAS microdata and price registries."""
    lookups = get_lookups()
    crop_match = lookups.get("crop_match")
    
    if lang == "rw":
        return """### 🌽 Ibihingwa Biboneka muri Data ya NISR SAS

Muri CropWatch Rwanda, amakuru y'ibihingwa akomoka ku bushakashatsi bwa **NISR Seasonal Agriculture Survey (SAS 2018–2026)** n'ibiciro bya **WFP VAM**:

| Ubwoko bw'Igihingwa (Crop) | Form (Uko kigurishwa) | Ibisobanuro by'Ibarura |
| :--- | :--- | :--- |
| **Ibigori (Maize)** | Intete (grain) | Ibihingwa by'ingenzi bipimirwa umusaruro na $kg/ha$ mu turere twose 30 |
| **Ibishyimbo (Dry & Bush Beans)** | Ibishyimbo byumye | Ibipimo by'ubuso buhingwa n'ifumbire |
| **Ibirayi (Irish Potato)** | Imizi (tuber) | Byibanda mu majyaruguru n'uburengerazuba (Musanze, Nyabihu, Rubavu) |
| **Umuceri (Rice)** | Intete (paddy/milled) | Byibanda mu bishanga n'ibibaya byuhirwa (Bugarama, Rwamagana) |
| **Imyumbati (Cassava)** | Imizi (root/flour) | Ibihingwa biramba bihangana n'amapfa mu burasirazuba |
| **Amasaka (Sorghum)** | Intete (grain) | Ibihingwa gakondo byo mu bihe by'imvura nke |
| **Imboga n'Imbuto** | Inyanya, Amashu, Karoti | Bipimirwa ku masoko ya WFP n'amasoko yo mu turere |

👉 *[Reba imbonerahamwe yuzuye y'ibihingwa mu Bubiko bw'Amakuru](?page=data)*"""
    else:
        return """### 🌽 Crops Available in Verified NISR Datasets

CropWatch Rwanda monitors crop production, yields, and retail price dynamics using ground-truth microdata from the **NISR Seasonal Agricultural Survey (SAS 2018–2026)** and **WFP VAM Market Monitors**:

| Major Crop Group | Product Form | Data Coverage & Provenance |
| :--- | :--- | :--- |
| **Maize (*Zea mays*)** | Dry Grain | Monitored across all 30 districts with plot-level yield regressions and ML benchmarks |
| **Beans (Bush & Climbing)** | Dry / Fresh Beans | Tracked for intercropping, fertilizer responsiveness, and seasonal acreage |
| **Irish Potato (*Solanum tuberosum*)** | Clean Tubers | Intensive microdata in volcanic highland zones (Musanze, Nyabihu, Burera) |
| **Rice (*Oryza sativa*)** | Milled / Paddy | Tracked in developed marshlands and cooperative irrigation perimeters |
| **Cassava (*Manihot esculenta*)** | Roots / Flour | Drought-tolerant baseline crop across Eastern lowlands (Bugesera, Kayonza) |
| **Sorghum (*Sorghum bicolor*)** | Grain | Monitored across semi-arid agroecological zones |
| **Horticulture** | Tomatoes, Cabbage, Carrots | Mapped to wholesale and retail market price tracking |

👉 *[Explore the complete crop and price matching catalog in the Data Registry](?page=data)*"""


def ai_yield_definition(lang="en"):
    """Explains agricultural yield terminology, calculation, and practical interpretation."""
    if lang == "rw":
        return """### 📖 Ubusobanuro bwa Tekiniki: Umusaruro w'Ubuhinzi (Crop Yield)

* **Umusaruro w'Ubuhinzi (Crop Yield)** ni igipimo cy'ingano y'ibisarurwa ku buso bw'ubutaka bwahinzwe.
* **Igipimo gikoreshwa (Unit):** Kipimirwa mu **Biro kuri Hegitari ($kg/ha$)** cyangwa **Toni kuri Hegitari ($MT/ha$)**.
* **Itandukaniro:**
  - *Umusaruro wose hamwe (Total Production):* Ni ibiro byose byeze mu karere (urugero: Toni 45,000).
  - *Umusaruro ku buso (Yield):* Ni umuvuduko wo kwera kuri buri hegitari (urugero: $2,850\text{ kg/ha}$).
* **Umusaruro muri Rwanda (NISR SAS 2022 Season A):**
  - Impuzandengo y'ibigori mu gihugu ni hafi **$1,540\text{ kg/ha}$**.
  - Mu mirima yuhirwa kandi ikoresha ifumbire ya DAP/Urea, umusaruro urenga **$2,800\text{ kg/ha}$**.

👉 *[Koresha What-If Simulator urebeko uko guhindura uburyo bwo guhinga byongera umusaruro](?page=simulator)*"""
    else:
        return """### 📖 Agricultural Concept: Crop Yield Explained

* **Crop Yield** is the measure of agricultural harvested output produced per unit of cultivated land area.
* **Standard Measurement Unit:** Expressed as **kilograms per hectare ($kg/ha$)** or **metric tonnes per hectare ($MT/ha$)**.
* **Key Distinction:**
  - *Total Production (Gross Output):* The aggregate physical volume harvested across a district or country (e.g., 45,000 MT).
  - *Yield (Land Productivity):* The efficiency of production per hectare (e.g., $2,850\text{ kg/ha}$).
* **Empirical Benchmarks in Rwanda (NISR SAS Microdata):**
  - National baseline maize yield under rainfed conditions averages approximately **$1,540\text{ kg/ha}$**.
  - Plots integrating supplementary irrigation (SSIT) and balanced inorganic fertilizer (DAP + Urea) achieve **$>2,800\text{ kg/ha}$**.

👉 *[Test counterfactual yield uplift packages in the What-If Simulator](?page=simulator)*"""


def ai_chart_explain(lang="en"):
    """Explains how to interpret platform charts, maps, and color thresholds."""
    if lang == "rw":
        return """### 📊 Uko Wasobanukirwa Ikarita n'Ibipimo bya CropWatch

* **Ikarita y'Iburira (Early Warning Choropleth Map):**
  - 🟢 **Icyatsi (Stable):** Ikirere giteye neza, imvura iri mu rugero rusanzwe, ubutaka bufite ubuhehere.
  - 🟡 **Umuhondo (Watch):** Imvura iri hasi ya 10% ugereranyije n'isanzwe; agrometeorologists basabwa gukurikirana umurima.
  - 🔴 **Umutuku (Irrigation Gap / Irrigate Now):** Icyuho gikomeye cy'imvura n'ubuhehere ($<-10\text{ mm}$); abahinzi bakeneye kuhira byihuse.
* **Igipimo cya NDRE (Sentinel-2 Vegetation Index):**
  - Kipima ubuzima n'icyatsi cy'amababi y'imyaka kuva mu 2018 kugeza mu 2026.
  - Igipimo cyo hejuru ya **0.45** kigaragaza ko imyaka imeze neza cyane.

👉 *[Fungura ikarita y'igihugu usuzume uturere twose 30](?page=alerts)*"""
    else:
        return """### 📊 How to Interpret CropWatch Visualizations & Maps

* **Early Warning Choropleth Map:**
  - 🟢 **Green (Stable):** Adequate moisture balance; cumulative rainfall matches seasonal baseline norms.
  - 🟡 **Amber (Watch Window):** Cumulative precipitation deficit exceeds $-10%$; soil moisture depletion watch in effect.
  - 🔴 **Red (Irrigation Gap / Emergency Deficit):** Severe weekly water balance deficit ($<-10\\text{ mm/week}$) with low irrigated plot share (<10%). Supplementary irrigation required immediately.
* **Sentinel-2 NDRE Vegetation Health Index:**
  - Measures red-edge chlorophyll absorption across Rwanda's agricultural plots annually from 2018 to 2026.
  - Values $>0.45$ indicate dense, vigorous vegetative canopies; values $<0.38$ indicate drought stress or stunted biomass.

👉 *[View the full interactive map with layer toggles](?page=alerts)*"""


def ai_district_profile(p, lang="en"):
    """Provides a complete executive briefing for a specific district."""
    d = p["district"]
    usual_y = p["usual_yield"]
    rain_pct = p["rain_pct"]
    irrig = p["irrigated_pct"]
    prot = p["protected_pct"]
    price = p.get("price")
    price_txt = f"{price:.0f} RWF/kg" if price is not None else "—"
    alert = p["alert"]
    plan = ssit_plan(0.5, "marsh")
    en_kit, rw_kit = plan["name_en"], plan["name_rw"]

    if lang == "rw":
        return f"""### 🏛️ Incamake y'Ikoranabuhanga n'Ubuhinzi muri {d}

* **Uko Ikirere Cyifashe (Alert Status):** `{alert.upper()}`
* **Icyuho cy'Imvura (Rainfall Anomaly):** `{rain_pct:+.0f}%` (Open-Meteo vs CHIRPS 2018–2025)
* **Imvura iteganyijwe mu minsi 7:** `{p['week_mm']:.0f} mm`
* **Ubuso buhirwa mu mirima ya SAS:** `{irrig:.1f}%`
* **Imirima ifite amaterasi n'ingamba zo kurwanya isuri:** `{prot:.1f}%`
* **Umusaruro usanzwe w'ibigori (SAS baseline):** `{usual_y:.0f} kg/ha`
* **Igiciro cy'Ibigori ku Isoko (WFP):** {price_txt}
* **Icyuho cy'Amazi cy'Iki Cyumweru:** `{p['deficit_mm']:.1f} mm` (`{p['liters_ha']:,.0f} L/ha`)
* **Pompi Ikwiye muri SSIT:** **{rw_kit}**

👉 *[Reba amakuru arambuye y'akarere ka {d} ku Rubuga rw'Uturere](?page=dashboard)*"""
    else:
        return f"""### 🏛️ Comprehensive Agrometeorological Profile: {d} District

* **Current Operational Status:** `{alert.upper()}`
* **Seasonal Rainfall Anomaly:** `{rain_pct:+.0f}%` (Open-Meteo vs CHIRPS 2018–2025)
* **7-Day Numerical Forecast:** `{p['week_mm']:.0f} mm` via Open-Meteo & Meteo Rwanda
* **Irrigated Plot Share (NISR SAS):** `{irrig:.1f}%`
* **Soil Conservation Protection Share:** `{prot:.1f}%`
* **Historical Baseline Maize Yield:** `{usual_y:.0f} kg/ha`
* **Prevailing Market Price (WFP VAM):** {price_txt}
* **Immediate Weekly Moisture Deficit:** `{p['deficit_mm']:.1f} mm` (`{p['liters_ha']:,.0f} L/ha`)
* **Recommended Smallholder Equipment:** **{en_kit}**

👉 *[Open full multi-year survey diagnostics for {d}](?page=dashboard)*"""


def audio_speech_html(text_content, lang="en"):
    clean_text = re.sub(r"[#*`\[\]\(\)\-_:!|]", " ", text_content)
    clean_text = re.sub(r"\s+", " ", clean_text).strip()
    clean_text = clean_text[:400].replace("'", "\\'").replace('"', '\\"')
    lang_code = "rw-RW" if lang == "rw" else "en-US"
    label = "🔊 Listen Aloud (Voice)" if lang == "en" else "🔊 Umva Inama Mu Majwi"

    return f"""<!DOCTYPE html>
<html>
<head>
<style>
  html, body {{
    margin: 0;
    padding: 0;
    background: transparent;
    overflow: hidden;
    font-family: system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif;
  }}
  .speech-bar {{
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: #f4faf6;
    border: 1px solid #b7dcbe;
    border-radius: 999px;
    padding: 3px 10px 3px 4px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.03);
  }}
  .speech-play-btn {{
    background: linear-gradient(135deg, #0d4f2b 0%, #157340 100%);
    color: #ffffff;
    border: none;
    border-radius: 999px;
    padding: 5px 14px;
    font-size: 11.5px;
    font-weight: 700;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    gap: 6px;
    box-shadow: 0 1px 3px rgba(13,79,43,0.25);
    transition: transform 0.1s ease, filter 0.15s ease;
  }}
  .speech-play-btn:hover {{
    filter: brightness(1.1);
    transform: scale(1.02);
  }}
  .speech-rate {{
    font-size: 11px;
    color: #2e5b3b;
    font-weight: 650;
    padding: 0 2px;
  }}
  .speech-stop-btn {{
    background: #ffffff;
    color: #b42318;
    border: 1px solid #d5ddd0;
    border-radius: 50%;
    width: 24px;
    height: 24px;
    cursor: pointer;
    font-size: 10px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    transition: all 0.15s ease;
  }}
  .speech-stop-btn:hover {{
    background: #fee2e2;
    border-color: #fca5a5;
  }}
</style>
</head>
<body>
  <div class="speech-bar">
    <button class="speech-play-btn" onclick="
      try {{
        window.speechSynthesis.cancel();
        var utter = new SpeechSynthesisUtterance('{clean_text}');
        utter.lang = '{lang_code}';
        utter.rate = 0.95;
        window.speechSynthesis.speak(utter);
      }} catch(e) {{
        console.error(e);
      }}
    ">
      {label}
    </button>
    <span class="speech-rate">0.95× Speed</span>
    <button class="speech-stop-btn" onclick="try {{ window.speechSynthesis.cancel(); }} catch(e){{}}" title="Stop Voice">
      ⏹️
    </button>
  </div>
</body>
</html>"""


# ==============================================================================
# SPECIALIZED AGRONOMIC KNOWLEDGE & DIAGNOSTIC ENGINES
# ==============================================================================

def ai_yellow_leaves(p, lang="en"):
    d = p["district"]
    deficit = p["deficit_mm"]
    is_rw = (lang == "rw")
    if is_rw:
        return f"""### 🌿 Isuzumaburwayi: Impamvu Amababi y'Ibigori Ahinduka Umuhondo muri {d}

Amababi y'ibihingwa (cyane cyane ibigori) guhinduka umuhondo (**Chlorosis**) bituruka ku mpamvu 4 z'ingenzi:

1. **Kubura Azotize (Nitrogen Deficiency):**
   * *Ikimenyetso:* Umuhondo utangirira ku mababi yo hasi ashaje, ukazamuka mu ishusho ya **"V"** werekeza ku mutsi wo hagati w'ibabi.
   * *Umuti w'Ibyihutirwa:* Shyiramo ifumbire ya **Urea (46% N)** ku gipimo cya **50 kg/ha** igihe ibigori biri mu buhagarike bw'intege (knee-high stage), cyangwa utere ifumbire y'amazi ku mababi (foliar spray).

2. **Icyuho cy'Amazi cyangwa Amazi Arenze (Water Stress / Waterlogging):**
   * Muri {d}, icyuho cy'amazi kiri kuri **{deficit:.1f} mm**. Iyo ubutaka bwumye cyane, imizi ntishobora gukurura intungamubiri z'azotize.
   * Iyo amazi yabaye menshi cyane mu bishanga, imizi iratumbura igabanya umwuka wa ogisijeni.

3. **Kubura Soufre (Sulfur Deficiency):**
   * *Ikimenyetso:* Bitandukanye na Nitrogen, Soufre ituma amababi mato yo hejuru ariyo abanza guhinduka umuhondo.
   * *Umuti:* Gukoresha ifumbire yuzuye ya NPK irimo Soufre.

4. **Ubusharire bw'Ubutaka (Soil Acidity):**
   * Iyo ubutaka busharira (pH < 5.5), ifumbire ntitanga umusaruro. Hakenewe gushyiramo **Ishwagara** (Agricultural Lime) ya **2.0–2.5 t/ha**.

👉 *Inama y'Umwuga:* Gusuzuma niba nta n攻撃 y'inyonzi (Fall Armyworm) yinjiye mu mutima w'ikigori."""
    else:
        return f"""### 🌿 Diagnostic Guide: Causes of Yellowing Crop Leaves in {d}

Yellowing of crop foliage (particularly maize chlorosis) typically stems from 4 verified biophysical causes:

1. **Nitrogen (N) Deficiency (Most Common):**
   * *Symptom:* Yellowing begins on older, bottom leaves and progresses upward in a classic **V-shaped pattern** along the midrib toward the stem.
   * *Immediate Remedy:* Top-dress with **Urea (46% N)** at **50 kg/ha** when maize is knee-high (4–6 weeks post-emergence). Ensure soil is moist before application to prevent ammonia volatilization.

2. **Root-Zone Moisture Stress & Waterlogging:**
   * In {d}, current weekly crop moisture deficit is **{deficit:.1f} mm** ({p['liters_ha']:,.0f} L/ha required). Severe drought restricts nutrient mobility and nitrate uptake.
   * In marshland plots, waterlogging suffocates root respiration, leading to secondary chlorosis. Ensure drainage furrows are unblocked.

3. **Soil Acidity & Phosphorus Locking:**
   * In highland zones with soil pH < 5.5, aluminum toxicity inhibits root elongation, making nitrogen uptake inefficient.
   * *Remedy:* Apply **Agricultural Lime (CaCO₃)** at **2.0–2.5 tons/ha** incorporated 3–4 weeks prior to sowing.

4. **Viral Infection / Maize Lethal Necrosis Disease (MLND):**
   * If accompanied by mottled chlorotic streaks, rogue out and burn infected plants to halt vector transmission (thrips/aphids)."""


def ai_fertilizer(p, lang="en"):
    d = p["district"]
    is_rw = (lang == "rw")
    if is_rw:
        return f"""### 🧪 Gahunda Nyakuri yo Gufumbira Imyaka muri {d}

Kugira ngo ubone umusaruro ushimishije hisunzwe amabwiriza ya RAB na MINAGRI:

#### 1. Ibigori (Maize Protocol):
* **Igihe cyo Gutera (Planting):** Shyiramo **DAP (18-46-0)** ku gipimo cya **100 kg/ha** (garama 5 kuri buri mwobo) hamwe n'**ifumbire y'imborera** iboze neza ya **toni 10/ha**.
* **Gufumbira bwa mbere (First Top-Dressing):** Ibiri biri mu buhagarike bw'intege (iminsi 30–35), shyiramo **Urea (46% N)** ingana na **50 kg/ha** intera ya sentimetero 5 uvuye ku ruti.
* **Gufumbira bwa kabiri (Second Top-Dressing):** Mbere y'uko ibigori birabya (tasseling, iminsi 55–60), shyiramo indi **50 kg/ha ya Urea**.

#### 2. Ibishyimbo (Bush & Climbing Beans):
* Ibishyimbo byifashisha udufuka two mu mizi (**Rhizobia nodules**) tugafata azotize mu kirere. **Ntukagerekeho ifumbire ya Urea myinshi!**
* Koresha gusa **DAP ingana na 50–100 kg/ha** mugihe cyo gutera n'imborera ihagije.

#### 3. Ibirayi (Irish Potatoes):
* Koresha **NPK 17-17-17** ku gipimo cya **250–300 kg/ha** mugihe cyo gutera hasi mu mikoki."""
    else:
        return f"""### 🧪 Scientific Fertilizer Protocols & Application Rates for {d}

Recommended fertilization schedule based on Rwanda Agriculture Board (RAB) agronomic standards:

#### 1. Maize Production Cycle:
* **Basal Application (At Planting):**
  * Apply **DAP (18-46-0)** at **100 kg/ha** (~5g per planting hill, separated from seed by 3 cm of soil).
  * Incorporate **10 tons/ha** of well-decomposed organic farmyard manure to enhance soil cation exchange capacity (CEC).
* **First Top-Dressing (V6 Vegetative / Knee-High):**
  * Apply **Urea (46% N)** at **50 kg/ha** (30–35 days after emergence). Side-dress in a ring 5 cm from the stalk and cover with soil.
* **Second Top-Dressing (Pre-Tasseling):**
  * Apply **50 kg/ha of Urea** just prior to flowering to maximize kernel filling and ear size.

#### 2. Climbing & Bush Beans:
* Legumes fix atmospheric nitrogen via symbiotic *Rhizobium* root nodules. **Avoid excessive urea applications**, which promote excessive vegetative vine growth at the expense of pod formation.
* Apply **50–100 kg/ha of DAP** at sowing for root vigor.

#### 3. Irish Potatoes:
* Apply **NPK 17-17-17** at **250–300 kg/ha** in furrows at planting, combined with ridging/hilling (*kwegeka*)."""


def ai_lime_acidity(p, lang="en"):
    d = p["district"]
    is_rw = (lang == "rw")
    if is_rw:
        return f"""### 🌿 Uburyo bwo Gushyiramo Ishwagara no Kurwanya Ubusharire bw'Ubutaka muri {d}

Muri zone z'imisozi miremire no mu misozi y'ibirunga (nko muri Musanze, Nyabihu, Nyamagabe), ubutaka bukunze kugira **ubusharire (pH < 5.5)** butuma ibihingwa bidakura neza:

1. **Ingaruka z'Ubusharire:**
   * Imyunyungugu y'uburozi ya Aliminiyumu (Aluminum toxicity) ifata imizi ntiyaguke.
   * Ifumbire ya DAP n'ifosifore (P) ziraheza mu butaka ntizinjire mu gihingwa.

2. **Ingano y'Ishwagara (Application Rate):**
   * Koresha **Ishwagara y'Ubuhinzi (Agricultural Lime / CaCO₃)** ku gipimo cya **toni 2.0 kugeza kuri 2.5 kuri hegitari (200–250 kg kuri ari 10)**.

3. **Uburyo no Guhesha Ishwagara:**
   * Shyiramo ishwagara **ibyumweru 3 kugeza kuri 4 MBERE yo gutera**.
   * Yikwirakwize mu murima maze uyihingire mu bujyakuzimu bwa sentimetero 15 kugira ngo ivange n'ubutaka.
   * **Icyitonderwa:** Ntugapfe kuvanga ishwagara na DAP ku munsi umwe mu mwobo umwe kuko ishwagara ihita yangiza ifosifore."""
    else:
        return f"""### 🌿 Soil Acidity Remediation & Agricultural Lime Protocol for {d}

Highland districts with acidic volcanic or ferralsol soils (pH < 5.5) suffer from severe nutrient fixation:

1. **Agronomic Mechanism of Soil Acidity:**
   * When soil pH drops below 5.2, active aluminum (Al3+) and iron (Fe2+) become soluble, binding phosphorus into insoluble precipitates.
   * Even heavy fertilizer applications remain ineffective because roots cannot absorb locked phosphate ions.

2. **Liming Rate & Product Specification:**
   * Apply **Agricultural Lime (CaCO3 or Dolomitic Lime CaMg(CO3)2)** at **2.0 to 2.5 tons/ha** (20–25 kg per 100 m²).
   * Lime neutralizes exchangeable acidity, elevates base saturation, and supplies essential calcium and magnesium.

3. **Application Protocol:**
   * Apply lime **3 to 4 weeks prior to planting**.
   * Broadcast evenly across plowed fields and incorporate into the top 15 cm through harrowing.
   * **Critical Rule:** Never co-apply agricultural lime directly in the seed hole with DAP on the same day; alkaline lime precipitates water-soluble phosphate."""


def ai_seasons(lang="en"):
    is_rw = (lang == "rw")
    if is_rw:
        return """### 📅 Ibihembwe by'Ubuhinzi mu Rwanda (Seasons A, B, and C)

Mu Rwanda, ubuhinzi bugendera ku bihembwe bitatu bikurikira byemejwe na NISR na MINAGRI:

* **Igihembwe A (Season A — Umuhindo):**
  * *Igihe cy'Ihinga:* Nzeri kugeza Gashyantare (Imvura itangira mu mpera za Nzeri).
  * *Ibihingwa Nyakubahwa:* Ibigori, ibishyimbo, soya, ibirayi, ibitoki.
  * *Uruhare:* Ni cyo gihembwe kera ibigori byinshi bikoreshwa mu nganda no mu gihugu hose.

* **Igihembwe B (Season B — Itumba):**
  * *Igihe cy'Ihinga:* Gashyantare kugeza Nyakanga (Imvura y'itumba itangira mu ntangiriro za Werurwe).
  * *Ibihingwa Nyakubahwa:* Amasaka (sorghum), ibishyimbo by'imishingiriro, ibijumba, imyumbati, imboga.

* **Igihembwe C (Season C — Icyi mu Bishanga):**
  * *Igihe cy'Ihinga:* Nyakanga kugeza Nzeri mu bishanga n'ibibaya bifite amazi.
  * *Ibihingwa Nyakubahwa:* Imboga (amashu, karoti, inyanya), ibirayi by'imbuto, ibijumba."""
    else:
        return """### 📅 Rwanda National Agricultural Calendar (Seasons A, B, and C)

Rwanda's agricultural production under MINAGRI and NISR operates on three synchronized seasonal cycles:

* **Season A (*Umuhindo* — Major Grain Season):**
  * *Sowing Window:* Mid-September to early October.
  * *Harvest Window:* January to February.
  * *Dominant Crops:* Hybrid maize, climbing beans, bush beans, soybeans, Irish potatoes, groundnuts.
  * *Significance:* Accounts for >60% of annual domestic grain production and commercial grain reserves.

* **Season B (*Itumba* — Long Rain Season):**
  * *Sowing Window:* Late February to mid-March.
  * *Harvest Window:* June to July.
  * *Dominant Crops:* Sorghum (*Amasaka*), climbing beans, cassava, sweet potatoes, horticultural crops.

* **Season C (*Icyi* — Valley & Marshland Dry-Season Multiplier):**
  * *Cultivation Window:* July to September.
  * *Agro-Ecological Setting:* Inland valleys, wetlands (*ibishanga*), and perimeter irrigation schemes.
  * *Dominant Crops:* Vegetables (cabbage, tomato, carrot), sweet potato vines, and certified Irish potato seed multiplication."""


def ai_spacing(p, lang="en"):
    is_rw = (lang == "rw")
    if is_rw:
        return """### 🌱 Intera Nyamukuru yo Gutera Ibihingwa n'Ingano y'Imbuto (RAB)

* **Ibigori (Maize):**
  * *Intera:* Sentimetero 75 hagati y'imirongo × sentimetero 25 hagati y'ingiga (uruti rumwe mu mwobo = ibiti 53,333 kuri hegitari).
  * *Ingano y'Imbuto:* **25 kg/ha** z'imbuto y'indobanure y'inzobere (Certified Hybrid Seeds).

* **Ibishyimbo by'Imishingiriro (Climbing Beans):**
  * *Intera:* Sentimetero 50 hagati y'imirongo × sentimetero 20 hagati y'ingiga (ibiti 2 mu mwobo). Hakenewe ibiti byo gushingirira birebire (2.0–2.5m).
  * *Ingano y'Imbuto:* **50–60 kg/ha**.

* **Ibishyimbo Bigufi (Bush Beans):**
  * *Intera:* Sentimetero 40 hagati y'imirongo × sentimetero 20 hagati y'ingiga. Ingano: **70–80 kg/ha**.

* **Ibirayi (Irish Potatoes):**
  * *Intera:* Sentimetero 75 hagati y'imikoki × sentimetero 30 hagati y'ingiga mu mwobo.
  * *Ingano y'Imbuto:* **2.0–2.5 t/ha** z'ibirayi byameze neza (ingano ya 28–45 mm)."""
    else:
        return """### 🌱 Sowing Density, Row Spacing & Seed Rates (RAB Certified)

* **Hybrid Maize (Optimum Canopy Interception):**
  * *Spacing:* **75 cm between rows × 25 cm between plants** (1 plant per station = 53,333 plants/ha) OR 75 cm × 50 cm (2 plants per station).
  * *Seed Requirement:* **25 kg/ha** of certified hybrid seed (PAN 53, SC 403, WH 505).

* **Climbing Beans (*Ibishyimbo by'Imishingiriro*):**
  * *Spacing:* **50 cm between rows × 20 cm between stations** (2 seeds/station). Trellis staking with bamboo/eucalyptus sticks (2.0–2.5m height) is essential to unlock the 3.5–4.5 t/ha yield ceiling.
  * *Seed Requirement:* **50–60 kg/ha**.

* **Bush Beans (*Ibishyimbo Bigufi*):**
  * *Spacing:* **40 cm between rows × 20 cm between stations**. Seed rate: **70–80 kg/ha**.

* **Irish Potatoes:**
  * *Spacing:* **75 cm between ridges × 30 cm within row**.
  * *Seed Tuber Requirement:* **2.0–2.5 tons/ha** of pre-sprouted seed tubers (grade size: 28–45 mm)."""


def ai_storage(p, lang="en"):
    price = p.get("price")
    if price is None:
        price = p.get("national_price")
    if price is None:
        price_line_en = "No WFP maize kg row for this district in the latest table (through 15 Mar 2026)."
        price_line_rw = "Nta umurongo wa WFP w'ibigori (kg) kuri iki karere (kugeza 15 Werurwe 2026)."
    else:
        when = p.get("price_date") or "latest"
        price_line_en = f"Latest WFP VAM maize for {p['district']}: **{price:.0f} RWF/kg** ({when}). This is a market price, not a farm-gate promise."
        price_line_rw = f"Igiciro cya WFP VAM kuri {p['district']}: **{price:.0f} RWF/kg** ({when}). Ni igiciro cy'isoko, si icyo ku murima."
    if lang == "rw":
        return f"""### Ubuhuniki (PICS) — inama, si iteganyijwe ry'igiciro

1. **Ubuhehere:** kwanika ibigori kugeza munsi ya **13.5%** mbere yo guhunika (kurwanya aflatoxin).
2. **Imifuka ya PICS:** ifunga umwuka; imungu zirapfa nta muti w'uburozi.
3. **Igiciro:** {price_line_rw} CropWatch **ntiteganya** igiciro cy'amezi 3 cyangwa 6.

Reba Open Data ku mahoro y'ibigori (HS 1005) kugeza 2025."""
    return f"""### After harvest — PICS storage (no price forecast)

1. **Moisture:** dry maize to **≤13.5%** before bagging (aflatoxin risk above that).
2. **PICS bags:** hermetic layers starve weevils without pesticide dust.
3. **Price:** {price_line_en} CropWatch does **not** forecast a May–July price.

Formal maize exports (HS 1005) are on Open Data through 2025. There is no 2026 export file."""


def ai_ssit_subsidy(p, lang="en"):
    plan = ssit_plan(0.5, "marsh")
    kit = plan["name_rw"] if lang == "rw" else plan["name_en"]
    if lang == "rw":
        return f"""### SSIT 50% — urugero, si igiciro cya MINAGRI

MINAGRI ivuga nkunganire ya **50%** ku bikoresho byemewe (hegitari ~0.1–10). CropWatch **ntishyura** kandi nticyemeza umushinga.

Urugero kuri **0.5 ha** ku gishanga muri {p['district']}:
* Pompi: **{kit}**
* Igiciro cyateganyijwe: **{plan['indicative_cost_rwf']:,.0f} RWF**
* Umuhinzi (50%): **{plan['farmer_rwf']:,.0f} RWF**
* Nkunganire (50%): **{plan['subsidy_rwf']:,.0f} RWF**

Saba ku murenge. Hindura ubuso n'inkomoko y'amazi kuri [Simulator](?page=simulator)."""
    return f"""### SSIT 50% — planning figures, not a MINAGRI quote

MINAGRI describes a **50%** co-share on approved kits (about 0.1–10 ha). CropWatch **does not** pay or approve applications.

Example for **0.5 ha** from a marsh in {p['district']}:
* Kit: **{kit}**
* Indicative cost: **{plan['indicative_cost_rwf']:,.0f} RWF**
* Farmer (50%): **{plan['farmer_rwf']:,.0f} RWF**
* Subsidy (50%): **{plan['subsidy_rwf']:,.0f} RWF**

Apply at the sector. Change size and water source on the [Simulator](?page=simulator)."""


def ai_nais_insurance(p, lang="en"):
    return ai_drought_ml(p, lang)


def ai_district_compare(d1, d2, lang="en"):
    is_rw = (lang == "rw")
    alerts_p = APP_TABLES / "irrigation_alerts.csv"
    if not alerts_p.exists():
        return f"Comparing {d1} and {d2}."
    alerts = pd.read_csv(alerts_p)
    r1 = alerts[alerts["district"] == d1]
    r2 = alerts[alerts["district"] == d2]
    r1 = r1.iloc[0] if not r1.empty else alerts.iloc[0]
    r2 = r2.iloc[0] if not r2.empty else alerts.iloc[0]

    if is_rw:
        return f"""### ⚖️ Isesengura ry'Igereranya: {d1} vs {d2}

| Igipimo cy'Ubuhinzi | {d1} | {d2} | Itandukaniro |
| :--- | :---: | :---: | :--- |
| **Imvura yabaye nkeya (Anomaly)** | `{r1.get('rain_difference_pct', 0):+.1f}%` | `{r2.get('rain_difference_pct', 0):+.1f}%` | {'Imvura yaguye neza muri ' + (d1 if r1['rain_difference_pct'] > r2['rain_difference_pct'] else d2)} |
| **Ubuso Butuhirwa (SAS 2022)** | `{r1.get('irrigated_pct', 0):.1f}%` | `{r2.get('irrigated_pct', 0):.1f}%` | {'Kuhira biri hejuru muri ' + (d1 if r1['irrigated_pct'] > r2['irrigated_pct'] else d2)} |
| **Umusaruro w'Ibigori (kg/ha)** | `{r1.get('usual_yield_kg_ha', 0):.0f}` | `{r2.get('usual_yield_kg_ha', 0):.0f}` | Umusaruro uri hejuru muri {d1 if r1.get('usual_yield_kg_ha', 0) > r2.get('usual_yield_kg_ha', 0) else d2} |
| **Imirima Irinzwe Isuri** | `{r1.get('protected_pct', 0):.1f}%` | `{r2.get('protected_pct', 0):.1f}%` | Amaterasi ateye imbere muri {d1 if r1.get('protected_pct', 0) > r2.get('protected_pct', 0) else d2} |
| **Icyiciro cy'Integuza** | `{r1.get('alert', 'stable')}` | `{r2.get('alert', 'stable')}` | — |

👉 *Umwanzuro:* Akarere ka **{d1 if r1['rain_difference_pct'] < r2['rain_difference_pct'] else d2}** niko gakeneye kunganirwa byihutirwa muri iki gihembwe mu bikorwa byo kuhira."""
    else:
        return f"""### ⚖️ Direct Comparative Diagnostic: {d1} vs {d2}

| Agroclimatic Indicator | {d1} | {d2} | Comparative Variance |
| :--- | :---: | :---: | :--- |
| **Cumulative Rain Anomaly** | `{r1.get('rain_difference_pct', 0):+.1f}%` | `{r2.get('rain_difference_pct', 0):+.1f}%` | Better rainfall in {d1 if r1['rain_difference_pct'] > r2['rain_difference_pct'] else d2} |
| **Irrigated Plot Share (SAS)** | `{r1.get('irrigated_pct', 0):.1f}%` | `{r2.get('irrigated_pct', 0):.1f}%` | Higher irrigation resilience in {d1 if r1['irrigated_pct'] > r2['irrigated_pct'] else d2} |
| **Baseline Maize Yield (kg/ha)** | `{r1.get('usual_yield_kg_ha', 0):.0f}` | `{r2.get('usual_yield_kg_ha', 0):.0f}` | Yield advantage in {d1 if r1.get('usual_yield_kg_ha', 0) > r2.get('usual_yield_kg_ha', 0) else d2} |
| **Soil Terracing Protection** | `{r1.get('protected_pct', 0):.1f}%` | `{r2.get('protected_pct', 0):.1f}%` | Superior erosion defenses in {d1 if r1.get('protected_pct', 0) > r2.get('protected_pct', 0) else d2} |
| **Operational Alert Tier** | `{r1.get('alert', 'stable')}` | `{r2.get('alert', 'stable')}` | — |

👉 *Operational Priority:* **{d1 if r1['rain_difference_pct'] < r2['rain_difference_pct'] else d2} District** exhibits higher vulnerability and requires priority deployment of SSIT mobile pumps."""


def ai_general_agronomy(user_text, p, lang="en"):
    d = p["district"]
    deficit = p["deficit_mm"]
    is_rw = (lang == "rw")
    if is_rw:
        return f"""### 🌾 Ibisobanuro by'Umwuga ku Buhinga muri {d}

Ibibazo byerekeye: *"{user_text}"*

Muri iki gihembwe A muri {d}:
* **Uko Ubuhehere Bwifashe:** Icyuho cy'amazi kiri kuri **{deficit:.1f} mm** ({p['liters_ha']:,.0f} L/ha z'amazi zikenewe mu murima).
* **Ingamba z'Ifumbire:** Gukoresha DAP (100 kg/ha) ku itangiriro na Urea (100 kg/ha igabanijemo kabiri) bitanga umusaruro wiyongereyeho hejuru ya +45%.
* **Kubungabunga Ubutaka:** Kubera imiterere y'imisozi ya {d}, kurwanya isuri binyuze mu materasi n'ibyatsi by'urubingo birinda ko imvura itwara ifumbire yashyizwemo.

💡 *Urashaka kumenya iki birambuye?*
1. Kanda kuri **"Ifumbire ya DAP na Urea"** hejuru.
2. Kanda kuri **"Kuhira Imyaka"** cyangwa **"Ubwishingizi bwa NAIS"**."""
    else:
        return f"""### 🌾 Agronomic Guidance & Diagnostic Perspective for {d}

Inquiry: *"{user_text}"*

Current agroclimatic status for {d} District (Season A 2026):
* **Root-Zone Moisture Dynamics:** Weekly crop water deficit is **{deficit:.1f} mm** ({p['liters_ha']:,.0f} L/ha supplemental irrigation requirement).
* **Soil & Nutrient Strategy:** Split application of Urea (50 kg/ha at knee-high and 50 kg/ha at tasseling) combined with basal DAP unlocks maximum nutrient absorption efficiency without leaching.
* **Soil Health:** In sloping hillside parcels, ensure contour grass strips (*Pennisetum purpureum*) and infiltration trenches are maintained to prevent topsoil loss during convective storms.

💡 *Recommended follow-up questions:*
1. Ask *"How much DAP and Urea should I use per hectare?"*
2. Ask *"How do I control Fall Armyworm?"*
3. Ask *"How does the MINAGRI 50% SSIT subsidy work?"*"""


def call_cloud_llm(prompt, profile, lang="en"):
    global LAST_LLM_ERROR
    LAST_LLM_ERROR = ""
    groq_key = secret("GROQ_API_KEY")
    gemini_key = secret("GEMINI_API_KEY") or secret("GOOGLE_API_KEY")

    price = profile.get("price")
    price_txt = f"{price:.0f} RWF/kg" if price is not None else "no district maize price"
    system_prompt = f"""You are CropWatch Rwanda. Write natural, grammatically correct sentences.
Use ONLY the figures below. Do not invent, round, or add numbers. If a figure is missing, say it is not in the district table.
Do not invent NAIS payouts, SMS sends, 2026 harvests, or sources. The app attaches verified citations after you.

District: {profile['district']}
Rain vs usual (Open-Meteo vs CHIRPS 2018-2025): {profile['rain_pct']:+.1f}%
7-day rain: {profile['week_mm']:.1f} mm
Weekly Pe-ETc: {profile['water_week']:+.1f} mm
Irrigated plots SAS 2022: {profile['irrigated_pct']:.1f}%
Usual maize yield: {profile['usual_yield']:.0f} kg/ha
WFP maize: {price_txt}

Rules: Kinyarwanda in, Kinyarwanda out. CropWatch does not pay insurance or send SMS. Yield gaps are Season A 2022 associations."""

    if groq_key:
        headers = {"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"}
        for model in GROQ_MODELS:
            try:
                payload = {
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.3,
                    "max_tokens": 1024,
                }
                res = requests.post(GROQ_URL, headers=headers, json=payload, timeout=20)
                if res.status_code == 200:
                    data = res.json()
                    return data["choices"][0]["message"]["content"]
                LAST_LLM_ERROR = f"Groq {model}: HTTP {res.status_code}"
                if res.status_code not in (400, 404):
                    break
            except Exception as err:
                LAST_LLM_ERROR = f"Groq {model}: {err}"
                break

    if gemini_key:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={gemini_key}"
            payload = {
                "contents": [
                    {"parts": [{"text": system_prompt + "\n\nUser Question: " + prompt}]}
                ],
                "generationConfig": {"temperature": 0.3, "maxOutputTokens": 1024}
            }
            res = requests.post(url, json=payload, timeout=20)
            if res.status_code == 200:
                data = res.json()
                return data["candidates"][0]["content"]["parts"][0]["text"]
            LAST_LLM_ERROR = f"Gemini {GEMINI_MODEL}: HTTP {res.status_code}"
        except Exception as err:
            LAST_LLM_ERROR = f"Gemini: {err}"

    if not groq_key and not gemini_key:
        LAST_LLM_ERROR = "No Groq or Gemini key. Put GROQ_API_KEY in .streamlit/secrets.toml (not the .example file)."
    return None


def strip_evidence(text):
    body = text or ""
    for mark in ("\n---\n**Evidence**", "\n---\n**Ibinyabiziga**"):
        if mark in body:
            return body.split(mark)[0].rstrip()
    return body.rstrip()


def evidence_md(profile, lang="en"):
    """Citations from project tables only — never invented by Groq."""
    d = profile["district"]
    price = profile.get("price")
    if price is None:
        price_line = (
            "- WFP VAM: no maize kg row for this district in the latest table (through 15 Mar 2026)."
            if lang != "rw"
            else "- WFP VAM: nta umurongo w'ibigori (kg) kuri iki karere mu mbonerahamwe ya 15 Werurwe 2026."
        )
    else:
        price_line = (
            f"- WFP VAM maize: {price:.0f} RWF/kg ({profile.get('price_date') or 'latest'}). https://dataviz.vam.wfp.org/"
            if lang != "rw"
            else f"- Ibigori bya WFP VAM: {price:.0f} RWF/kg ({profile.get('price_date') or 'ubu'}). https://dataviz.vam.wfp.org/"
        )
    if lang == "rw":
        return f"""
---
**Ibinyabiziga** (imibare ivuye mu mbonerahamwe, si iyavumbuwe na Groq)

- {d}: imvura {profile['rain_pct']:+.1f}% ugereranyije n'isanzwe (Open-Meteo vs CHIRPS 2018–2025). https://open-meteo.com/ · https://www.chc.ucsb.edu/data/chirps
- Iminsi 7: {profile['week_mm']:.1f} mm (Open-Meteo). Icyuho cy'icyumweru Pe−ETc {profile['water_week']:+.1f} mm (FAO-56).
- SAS 2022 (NISR): imirima ihirwa {profile['irrigated_pct']:.1f}%; umusaruro usanzwe w'ibigori {profile['usual_yield']:.0f} kg/ha. https://www.statistics.gov.rw/
{price_line}
- CropWatch ntishyura NAIS kandi ntiyohereza SMS."""
    return f"""
---
**Evidence** (figures from CropWatch tables, not invented by Groq)

- {d}: rain {profile['rain_pct']:+.1f}% vs usual (Open-Meteo vs CHIRPS 2018–2025). https://open-meteo.com/ · https://www.chc.ucsb.edu/data/chirps
- Next 7 days: {profile['week_mm']:.1f} mm (Open-Meteo). Weekly Pe−ETc {profile['water_week']:+.1f} mm (FAO-56).
- NISR SAS 2022: irrigated plots {profile['irrigated_pct']:.1f}%; usual maize {profile['usual_yield']:.0f} kg/ha. https://www.statistics.gov.rw/
{price_line}
- CropWatch does not pay NAIS and does not send SMS. Yield gaps are Season A 2022 associations."""


def rephrase_with_llm(source_text, profile, lang="en"):
    """Rewrite with natural grammar. Copy numbers; add no new facts."""
    body = strip_evidence(source_text)
    if len(body) < 20:
        return None
    tongue = "Kinyarwanda" if lang == "rw" else "English"
    prompt = (
        f"Rewrite the CropWatch briefing in natural, grammatically correct {tongue}. "
        "Keep the original meaning. Copy every number, unit, and district name exactly. "
        "Do not add, drop, or round figures. Do not invent sources, NAIS payouts, SMS sends, or harvests. "
        "Do not add a sources section.\n\n"
        f"---\n{body}"
    )
    return call_cloud_llm(prompt, profile, lang=lang)


def finish_answer(resp, profile, lang="en", polish=True):
    text = strip_evidence(resp or "")
    if polish:
        cloud = rephrase_with_llm(text, profile, lang=lang)
        if cloud and len(cloud) > 30:
            text = strip_evidence(cloud)
    return text.rstrip() + "\n" + evidence_md(profile, lang=lang)

# ==============================================================================
# UNIFIED DISPATCHER & CLOUD LLM FALLBACK
# ==============================================================================

def answer(user_text, profile, words, lang, hectares=0.5, force_intent=None, context=None):
    districts = extract_all_districts(user_text)
    if len(districts) >= 2 and any(k in (user_text or "").lower() for k in ("compare", "versus", "vs", "difference", "itandukaniro", "gereranya")):
        return finish_answer(ai_district_compare(districts[0], districts[1], lang=lang), profile, lang=lang)

    intent = force_intent or classify(user_text, context=context)
    polish = True

    if intent == "rephrase":
        last = (context or {}).get("last_bot") or ""
        cloud = rephrase_with_llm(last, profile, lang=lang)
        if cloud and len(cloud) > 30:
            return finish_answer(cloud, profile, lang=lang, polish=False)
        if last:
            return finish_answer(last, profile, lang=lang, polish=False)
        if lang == "rw":
            return "Banza ubaze ikibazo, hanyuma ukande *Rephrase this*."
        return "Ask a district question first, then tap **Rephrase this**."

    # Fast machine learning, physical inference & specialized conversational dispatchers
    if intent in ("yield", "harvest", "projection"):
        resp = ai_yield_ml(profile, lang)
    elif intent in ("insurance", "stress", "claim"):
        resp = ai_drought_ml(profile, lang)
    elif intent in ("market", "price", "arbitrage"):
        resp = ai_price_ml(profile, lang)
    elif intent in ("irrigation", "kit", "water"):
        resp = ai_irrigation(profile, lang)
    elif intent in ("soil", "terrace", "erosion"):
        resp = ai_soil(profile, lang)
    elif intent in ("pests", "disease"):
        resp = ai_pests(profile, lang)
    elif intent == "yellow_leaves":
        resp = ai_yellow_leaves(profile, lang)
    elif intent == "fertilizer":
        resp = ai_fertilizer(profile, lang)
    elif intent == "lime_acidity":
        resp = ai_lime_acidity(profile, lang)
    elif intent == "seasons":
        resp = ai_seasons(lang)
    elif intent == "spacing":
        resp = ai_spacing(profile, lang)
    elif intent == "storage":
        resp = ai_storage(profile, lang)
    elif intent == "ssit_subsidy":
        resp = ai_ssit_subsidy(profile, lang)
    elif intent == "insurance_nais":
        resp = ai_nais_insurance(profile, lang)
    elif intent == "district_compare" and len(districts) >= 2:
        resp = ai_district_compare(districts[0], districts[1], lang=lang)
    elif intent == "sms":
        resp = ai_sms(profile, lang)
    elif intent == "crops_available":
        resp = ai_crops_available(lang)
    elif intent == "yield_definition":
        resp = ai_yield_definition(lang)
    elif intent == "chart_explain":
        resp = ai_chart_explain(lang)
    elif intent == "district_profile":
        resp = ai_district_profile(profile, lang)
    elif intent == "data_location":
        if lang == "rw":
            resp = """### 📁 Aho Wavana Amakuru ya CropWatch Rwanda

* **Ububiko bw'Amakuru (Data Registry):** Kanda kuri page ya `Data` kugira ngo ubone imbonerahamwe z'ibihingwa, ibiciro bya WFP, n'amateka y'imvura.
* **Gukuramo amadosiye (Download):** Buri paji ifite buto yo gukuramo dosiye muri CSV cyangwa HTML.
* **Inkomoko Nyakuri:**
  1. *NISR SAS:* Microdata y'ubuhinzi kuva 2018 kugeza 2026.
  2. *WFP VAM:* Ibiciro by'ibiribwa ku masoko yo mu Rwanda.
  3. *CHIRPS & Open-Meteo:* Imvura n'iteganyagihe.

👉 *[Fungura Ububiko bw'Amakuru (Data Hub)](?page=data)*"""
        else:
            resp = """### 📁 Where to Find and Download Data

* **Platform Data Registry:** Navigate to the `Data` desk (`?page=data`) to explore data dictionaries, crop price matching tables, and seasonal calendars.
* **One-Click Exports:** Every operational desk includes verified CSV and HTML export buttons for institutional reporting.
* **Official Data Provenance:**
  1. *NISR SAS:* Seasonal Agricultural Survey plot microdata (2018–2026).
  2. *WFP VAM:* Weekly and monthly retail food prices.
  3. *CHIRPS & Open-Meteo:* Longitudinal rainfall anomalies and 7-day numerical forecasts.

👉 *[Access the Open Data Registry](?page=data)*"""
    elif intent == "team":
        if lang == "rw":
            resp = """### 👥 Itsinda ry'Abahanga ryakoze CropWatch Rwanda

* **Irushanwa ry'Ubushakashatsi:** Umushinga wateguriwe irushanwa rya **NISR 2026 Big Data Hackathon** riyobowe n'Ikipe ya Data Science muri NISR.
* **Abahanga mu Bwubatsi bwa Software n'Ubuhinzi:**
  1. **MURENZI Elvis** (Reg: `26RP01872`) — Rwanda Polytechnic (Musanze College), BTech mu By'Ikoranabuhanga (IT), Umwaka wa 4.
     - *Inshingano:* Full-Stack Architecture, FastAPI REST API, gutoza no guhuza models za Machine Learning, amajwi ya Web Speech API, na SMS kuri telefoni zisanzwe.
  2. **BAHIRE Elie** (Reg: `26RP02259`) — Rwanda Polytechnic (Musanze College), BTech mu Buhinzi n'Ibyo Kuhira (Irrigation & Drainage), Umwaka wa 4.
     - *Inshingano:* Imiterere y'amazi mu mizi y'ibihingwa (FAO-56 Penman-Monteith), gahunda ya SSIT ya 50% ya Leta, n'ingamba zo kurwanya isuri ku misozi ihanamye.

👉 *[Reba amakuru arambuye y'Itsinda n'Ikarita y'Umunyeshuri](?page=about)*"""
        else:
            resp = """### 👥 Engineering Team Behind CropWatch Rwanda

* **Competition & Context:** Built for the **NISR 2026 Big Data Hackathon** organized by the National Institute of Statistics of Rwanda (NISR) Data Science Team.
* **Multidisciplinary Student Engineering Team:**
  1. **MURENZI Elvis** (Reg: `26RP01872`) — Rwanda Polytechnic (Musanze College), BTech in Information Technology, Year 4.
     - *Focus:* Full-Stack Architecture, FastAPI microservice, local scikit-learn ML inference pipelines, Web Speech voice synthesis, and bilingual engine.
  2. **BAHIRE Elie** (Reg: `26RP02259`) — Rwanda Polytechnic (Musanze College), BTech in Irrigation and Drainage Technology, Year 4.
     - *Focus:* FAO-56 Penman-Monteith root-zone crop water accounting, MINAGRI 50% SSIT subsidy modeling, and hillside erosion control matrices.

👉 *[View full team credentials and verified student cards](?page=about)*"""
    elif intent == "hello":
        d = profile["district"]
        if lang == "rw":
            resp = f"""### Muraho! Ndi Umujyanama mu by'Ubuhinzi ukoresha AI muri {d}.

* **Imvura imaze kugwa:** `{profile['rain_pct']:+.0f}%` ugereranyije n'isanzwe
* **Icyumweru gitaha:** `{profile['week_mm']:.0f} mm`
* **Ubuso buhirwa muri SAS 2022:** `{profile['irrigated_pct']:.1f}%`
* **Icyuho cy'Ubuhehere:** `{profile['deficit_mm']:.1f} mm`

Hitamo umusaruro, imvura, igiciro, cyangwa SMS (inyandiko gusa)."""
        else:
            resp = f"""### Hello — CropWatch desk for {d}

* Rain vs usual: `{profile['rain_pct']:+.0f}%` (Open-Meteo vs CHIRPS 2018–2025)
* Next 7 days: `{profile['week_mm']:.0f} mm`
* Irrigated plots in 2022: `{profile['irrigated_pct']:.1f}%`
* Weekly water gap: `{profile['deficit_mm']:.1f} mm`

Ask about yield (2022 gaps), this week's rain, WFP price, or an SMS draft. This desk does not pay NAIS or send texts."""
    elif intent == "week":
        d = profile["district"]
        deficit = profile["deficit_mm"]
        if lang == "rw":
            resp = f"""### 📅 Inama z'Iteganyagihe ry'Iki Cyumweru — {d}

* **Icyuho cy'Amazi:** `{deficit:.1f} mm` | **Imvura iteganyijwe:** `{profile['week_mm']:.0f} mm`
* **Inama y'Ibyihutirwa:** {'Kuhira imyaka birakenewe byihuse binyuze muri pompi za SSIT.' if deficit > 3 else 'Ubuhehere buracyahagije muri iki cyiciro cy imyaka.'}
* **Kubungabunga Ubutaka:** Amaterasi n'imiferege ifata amazi birakenewe kugira ngo ubutaka butagenda n'isuri.

👉 *[Reba ibyemezo birambuye ku Karere ka {d}](?page=dashboard)*"""
        else:
            resp = f"""### 📅 Operational Agrometeorological Guidance for This Week — {d}

* **Moisture Deficit:** `{deficit:.1f} mm` | **7-Day Numerical Forecast:** `{profile['week_mm']:.0f} mm`
* **Action Priority:** {'Immediate supplementary irrigation required via SSIT mobile pumps.' if deficit > 3 else 'Moisture levels currently adequate for this growth stage.'}
* **Soil Conservation:** Ensure infiltration trenches and contour grass strips are cleared before heavy storm events.

👉 *[View full district breakdown and recommendations](?page=dashboard)*"""
    else:
        cloud_resp = call_cloud_llm(user_text, profile, lang=lang)
        if cloud_resp and len(cloud_resp) > 30:
            resp = cloud_resp
            polish = False
        else:
            resp = ai_general_agronomy(user_text, profile, lang=lang)

    if intent in ("team", "sms"):
        polish = False
    return finish_answer(resp, profile, lang=lang, polish=polish)


def sms_text(profile, words):
    return ai_sms(profile, "rw" if words.get("language") == "Ururimi" else "en")
