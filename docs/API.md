# CropWatch Rwanda — Enterprise REST API Documentation

## 1. Overview & Service Architecture

The **CropWatch Rwanda REST API** (`src/api.py`) is an asynchronous, high-throughput microservice built on **FastAPI** and **Uvicorn**. It exposes programmatic interfaces to:
- 30-district early warning agrometeorological alerts.
- Live Open-Meteo 7-day numerical forecasts and NASA POWER solar/temperature telemetry.
- Serialized machine learning models (`maize_yield_model`, `drought_risk_classifier`, `market_price_forecaster`).
- The bilingual **AI Agronomic Copilot** inference engine (`src/advise.py`).

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
| `GET` | `/api/models/yield/{district}` | Multi-factor maize yield simulation & revenue uplift | `district` (path, string) |
| `GET` | `/api/models/drought/{district}` | Climate crisis probability & NAIS parametric insurance payout trigger | `district` (path, string) |
| `GET` | `/api/models/prices/{district}` | WFP retail price forecast & post-harvest hermetic storage arbitrage | `district` (path, string) |
| `GET` | `/api/chat/ask` | AI Agronomic Copilot semantic inference in English or Kinyarwanda | `q` (query), `district` (query), `lang` (query) |

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

### 3.7 Machine Learning Maize Yield Simulator
`GET /api/models/yield/{district}`

Executes the Random Forest regressor trained on 28,042 NISR SAS plot microdata. Computes counterfactual simulations comparing rainfed production against supplementary irrigation and a full climate-smart package (irrigation + inorganic fertilizer + progressive terracing).

**Path Parameters:**
- `district` *(string, required)*: Target district.

**Example Response (200 OK):**
```json
{
  "district": "Bugesera",
  "baseline_yield_kg_ha": 1342.5,
  "with_supplementary_irrigation_kg_ha": 1728.3,
  "with_full_climate_smart_package_kg_ha": 2380.1,
  "yield_uplift_kg_ha": 1037.6,
  "price_rwf_per_kg": 460.0,
  "revenue_uplift_rwf_ha": 477296.0,
  "model": "RandomForestRegressor (28,042 NISR SAS plots)"
}
```

---

### 3.8 Parametric Drought Insurance Trigger
`GET /api/models/drought/{district}`

Evaluates the multi-class Drought Classifier against current root-zone moisture deficits, triggering official payouts for the National Agricultural Insurance Scheme (**NAIS / Tekana Urishingiwe Muhinzi**).

**Example Response (200 OK):**
```json
{
  "district": "Nyagatare",
  "probability_crisis_pct": 38.4,
  "probability_watch_pct": 45.2,
  "probability_stable_pct": 16.4,
  "nais_parametric_insurance_payout_triggered": true,
  "model": "RandomForestClassifier"
}
```

---

### 3.9 Post-Harvest Market Price Arbitrage
`GET /api/models/prices/{district}`

Uses the autoregressive harmonic `RidgeCV` model trained on 2,728 historical WFP market observations to forecast maize prices 30, 60, and 90 days post-harvest. Evaluates whether investing in hermetic storage bags (PICS bags at 28 RWF/kg equivalent amortization) generates positive economic arbitrage.

**Example Response (200 OK):**
```json
{
  "district": "Musanze",
  "current_price_rwf_kg": 480.0,
  "projected_price_30d_rwf_kg": 492.4,
  "projected_price_60d_rwf_kg": 513.1,
  "projected_price_90d_rwf_kg": 534.2,
  "hermetic_pics_bag_cost_rwf_kg": 28.0,
  "net_arbitrage_gain_90d_rwf_kg": 26.2,
  "model": "Autoregressive RidgeCV (2,728 WFP records)"
}
```

---

### 3.10 AI Agronomic Copilot Query
`GET /api/chat/ask`

Executes the semantic conversational intelligence engine. Classifies intent across 16 categories, retrieves empirical district microdata, and formats natural bilingual responses.

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
