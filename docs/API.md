# CropWatch Rwanda — Enterprise REST API Documentation

## 1. Overview & Service Architecture

The **CropWatch Rwanda REST API** (`src/api.py`) is the same district pack as the Streamlit desk, served with FastAPI:
- 30-district alerts (SAS 2022 irrigation share, Open-Meteo vs CHIRPS, FAO-56 week).
- District profile and 7-day Open-Meteo forecast.
- Yield: Season A 2022 OLS on 11,148 maize plots (not a loaded Random Forest).
- Drought: same water screen as the map. Payout flag is always false.
- Prices: latest WFP maize row only.
- Advice: local tables first (`src/advise.py`).

### Base Server Specifications
- **Framework:** FastAPI `0.100+` / Python `3.12`
- **Default Port:** `8000` (or `8520`)
- **Interactive OpenAPI Documentation (Swagger UI):** `http://localhost:8000/docs`
- **Machine-Readable OpenAPI Specification:** `http://localhost:8000/openapi.json`
- **Alternative Specification (ReDoc):** `http://localhost:8000/redoc`
- **Cross-Origin Resource Sharing (CORS):** Fully enabled (`allow_origins=["*"]`) for integration with mobile apps, USSD gateways, and external partner dashboards.

---

## 2. API Endpoints Catalog

| Method | Endpoint | Description | Query / Path Parameters |
|---|---|---|---|
| `GET` | `/` | API root discovery metadata and service catalog | None |
| `GET` | `/api/health` | Operational health check & active pilot districts | None |
| `GET` | `/api/status` | National executive summary of all 30 districts | None |
| `GET` | `/api/alerts` | Complete 30-district irrigation, soil, and climate alert table | None |
| `GET` | `/api/pilots` | High-resolution telemetry for Bugesera, Nyagatare, Musanze, Nyaruguru | None |
| `GET` | `/api/districts/{name}` | Comprehensive profile, 7-day forecast & NASA telemetry for a district | `name` (path, string) |
| `GET` | `/api/models/yield/{district}` | 2022 OLS plot package (not a 2026 harvest) | `district` (path, string) |
| `GET` | `/api/models/drought/{district}` | Same water screen as the map; NAIS payout always false | `district` (path, string) |
| `GET` | `/api/models/prices/{district}` | Latest WFP maize kg; no 30/60/90-day forecast | `district` (path, string) |
| `GET` | `/api/chat/ask` | Advice from local tables (EN / RW) | `q` (query), `district` (query), `lang` (query) |

---

## 3. Detailed Endpoint Specifications

### 3.1 Service Root
`GET /`

Returns service metadata, version, and endpoint manifest.

**Response (200 OK):**
```json
{
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
    "/api/chat/ask"
  ]
}
```

---

### 3.2 Health Check
`GET /api/health`

Verifies that the API process is responsive and lists the 4 designated agrometeorological pilot districts.

**Response (200 OK):**
```json
{
  "ok": true,
  "product": "CropWatch Rwanda",
  "kind": "decision_support_api",
  "note": "CropWatch Rwanda national agricultural intelligence & climate-smart decision support API.",
  "pilots": ["Bugesera", "Nyagatare", "Musanze", "Nyaruguru"]
}
```

---

### 3.3 National Status Summary
`GET /api/status`

Aggregates real-time national statistics across all 30 districts, including irrigation deficits, soil erosion alerts, and national weighted irrigation adoption.

**Response (200 OK):**
```json
{
  "product": "CropWatch Rwanda",
  "kind": "decision_support_api",
  "n_districts": 30,
  "n_irrigation_gap": 11,
  "n_irrigate_now": 6,
  "n_soil": 8,
  "n_water_stress": 4,
  "n_rainfall_watch": 7,
  "irrigated_pct_national": 2.2,
  "fetched_on": "2026-10-30",
  "kc_maize": 0.85,
  "maize_stage": "Vegetative / Stem Elongation",
  "plant_date_assumed": "2026-09-15",
  "note": "Operational decision-support platform aligned with NST2 2024-2029."
}
```

---

### 3.4 30-District Alerts Matrix
`GET /api/alerts`

Returns the full table of all 30 administrative districts with crop water balances, CHIRPS rainfall anomalies, and active alert classifications.

**Response (200 OK):**
```json
{
  "rows": [
    {
      "district": "Bugesera",
      "province": "Eastern",
      "alert": "irrigate_now",
      "climate_class": "water_stress",
      "rain_so_far_mm": 94.2,
      "usual_sep_oct_mm": 138.5,
      "rain_difference_pct": -32.0,
      "forecast_week_mm": 3.8,
      "irrigated_pct": 3.4,
      "concern_pct": 14.2,
      "protected_pct": 72.1,
      "usual_yield_kg_ha": 1420.0,
      "kc_maize": 0.85,
      "maize_stage": "Vegetative / Stem Elongation",
      "etc_week_mm": 24.8,
      "pe_week_mm": 2.8,
      "water_balance_week_mm": -22.0
    }
  ],
  "n": 30
}
```

---

### 3.5 High-Resolution Pilots Telemetry
`GET /api/pilots`

Fetches joined satellite agrometeorology and weather forecasts for Rwanda's 4 distinct agroecological pilot zones:
1. **Bugesera:** Eastern semi-arid savannah drought zone.
2. **Nyagatare:** Eastern livestock & grain corridor.
3. **Musanze:** Northern volcanic volcanic soils & Irish potato belt.
4. **Nyaruguru:** Southern high-altitude acidic tea & terraced hillside zone.

---

### 3.6 District Deep Profile
`GET /api/districts/{name}`

**Path Parameters:**
- `name` *(string, required)*: The case-insensitive district name (e.g., `Bugesera`, `Musanze`, `Huye`).

**Response Includes:**
- District baseline microdata from NISR SAS surveys.
- 7-day numerical precipitation forecast from Open-Meteo.
- NASA POWER daily surface solar radiation ($MJ/m^2$), 2m temperature ($^\circ C$), and relative humidity.

---

### 3.7 Yield what-if (2022 OLS)
`GET /api/models/yield/{district}`

Returns the Season A 2022 within-district OLS package (11,148 maize plots). Associations, not a 2026 harvest forecast.

**Example Response (200 OK):**
```json
{
  "district": "Bugesera",
  "baseline_yield_kg_ha": 1342.0,
  "with_supplementary_irrigation_kg_ha": 1707.0,
  "yield_uplift_irrigation_kg_ha": 365.0,
  "model": "Season A 2022 within-district OLS (11,148 maize plots). Not a 2026 harvest."
}
```

---

### 3.8 Water screen (not an NAIS payout)
`GET /api/models/drought/{district}`

Same alert rule as the map. CropWatch does not pay NAIS / Tekana.

**Example Response (200 OK):**
```json
{
  "district": "Nyagatare",
  "cropwatch_water_flag": true,
  "nais_parametric_insurance_payout_triggered": false,
  "model": "Same alert rule as prepare_alerts.classify (not NAIS)"
}
```

---

### 3.9 Latest WFP maize (no forecast)
`GET /api/models/prices/{district}`

Returns the latest WFP VAM maize kg if a row exists. `forecast` is always null.

**Example Response (200 OK):**
```json
{
  "district": "Musanze",
  "current_price_rwf_kg": 480.0,
  "forecast": null,
  "note": "Latest WFP maize row only. No 30/60/90-day forecast is computed."
}
```

---

### 3.10 Advice query
`GET /api/chat/ask`

Answers from district tables. Groq is optional grammar rewrite when a key is present.

**Query Parameters:**
- `q` *(string, required)*: The agronomic or platform query (e.g., `"Should I irrigate maize this week in Bugesera?"`, `"Ese imvura irahagije muri Musanze?"`).
- `district` *(string, optional, default: "Bugesera")*: Context district.
- `lang` *(string, optional, default: "en")*: Target language (`en` for English, `rw` for Kinyarwanda).

**Example Request:**
```bash
curl -X GET "http://localhost:8000/api/chat/ask?q=maize%20yield%20Nyagatare&district=Nyagatare&lang=en"
```

**Example Response (200 OK):**
```json
{
  "district": "Nyagatare",
  "language": "en",
  "query": "maize yield Nyagatare",
  "response": "In Nyagatare, baseline Season A maize yield is approximately 1,650 kg/ha. Applying supplementary Small-Scale Irrigation Technology (SSIT) unlocks an estimated uplift of +385 kg/ha, while combining irrigation with balanced mineral fertilizers (NPK/DAP) elevates potential output to 2,420 kg/ha."
}
```

---

## 4. Client Code Examples

### 4.1 Python Client (`requests`)
```python
import requests

BASE_URL = "http://localhost:8000"

# 1. Fetch national early warning summary
status_res = requests.get(f"{BASE_URL}/api/status").json()
print(f"National Irrigation Gaps: {status_res['n_irrigation_gap']} districts")

# 2. Query ML Yield Uplift for Bugesera
yield_res = requests.get(f"{BASE_URL}/api/models/yield/Bugesera").json()
print(f"Bugesera Revenue Uplift: {yield_res['revenue_uplift_rwf_ha']:,} RWF/ha")

# 3. Query AI Copilot in Kinyarwanda
chat_res = requests.get(
    f"{BASE_URL}/api/chat/ask",
    params={"q": "Hakenewe kuhira iki cyumweru?", "district": "Bugesera", "lang": "rw"}
).json()
print("AI Copilot Advice:", chat_res["response"])
```

### 4.2 JavaScript / TypeScript (`fetch`)
```typescript
async function checkDroughtTrigger(district: string) {
  const res = await fetch(`http://localhost:8000/api/models/drought/${district}`);
  const data = await res.json();
  if (data.nais_parametric_insurance_payout_triggered) {
    console.warn(`[ALERT] NAIS Payout Triggered for ${district}! Crisis Prob: ${data.probability_crisis_pct}%`);
  }
}
```

---

## 5. Error Handling & HTTP Status Codes

The API enforces standard HTTP error codes:
- **`200 OK`**: Request processed successfully.
- **`400 Bad Request`**: Malformed request syntax or invalid parameters.
- **`404 Not Found`**: Target district or table not found (e.g., `No district named 'Atlantis'`).
- **`503 Service Unavailable`**: Serialized model artifact not loaded or missing from disk.

---

*CropWatch Rwanda · Enterprise REST API Specification · Aligned with NST2 (2024–2029)*
