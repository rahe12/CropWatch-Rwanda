# CropWatch Rwanda — National Decision Support Platform

This is the operational decision-support build for CropWatch Rwanda, demonstrating end-to-end data pipelines across all 30 districts with deep satellite agrometeorology in the four strategic pilot districts.

## Two interfaces, one synchronized data engine

| Interface | URL | Purpose & Architecture |
|---|---|---|
| Four-pilot API & desk | http://localhost:8520/ | FastAPI + HTML micro-desk for Bugesera, Nyagatare, Musanze, and Nyaruguru. Direct telemetry inspection and 7-day crop water balance (Pe − ETc). |
| 30-district platform | http://localhost:8502/ | Full Streamlit decision platform. Real-time early warning GIS map, district matrix, SSIT subsidy calculator, AI agronomic copilot, and bilingual English/Kinyarwanda interface. |

## How to run

From the project folder:

```bash
python -m pip install -r requirements.txt
streamlit run app.py --server.port 8502
python -m uvicorn src.api:app --host 127.0.0.1 --port 8520
```

Do not re-fetch Open-Meteo or NASA POWER unless you want a new snapshot. The platform reads cached, validated tables in `data/processed/app/`.

## Operational Decision Logic

1. **Irrigation gap alert**: Triggered when rainfall since 1 September 2026 is ≥10% below usual September–October baselines (CHIRPS 1981–2025) **and** the irrigated share of Season A plots is under 10%.
2. **Irrigate this week**: Triggered when that gap holds **and** the next seven days forecast total less than 10 mm.
3. **Soil erosion risk**: Triggered when soil concern ≥20%, protection is under 80%, and any of the next seven days forecast is ≥15 mm.
4. **Agroclimatic classification**: Evaluates potential water stress (week Pe−ETc < −10 mm combined with a dry start), excess rain, agronomist assessment required, or normal monitoring.

Usual maize yield on screen represents the historical district-season baseline. The maize model is scored out of sample. Maize planting date is synchronized to **15 September 2026** (mid FAO GIEWS Season A window).

## REST API Endpoints

- `GET /api/health` — API health check
- `GET /api/status` — National summary metrics and operational alert rules
- `GET /api/pilots` — Four pilot districts joined to NASA POWER summaries
- `GET /api/districts/{name}` — Specific district profile, 7-day forecast, and NASA POWER telemetry
- `GET /api/alerts` — All 30 district risk records
