# CropWatch Rwanda — System Architecture

## 1. Executive Summary & Vision

**CropWatch Rwanda** is a national-scale agricultural intelligence and agrometeorological decision-support platform designed to operationalize Rwanda's **Second National Strategy for Transformation (NST2 2024–2029)**.

The system bridges satellite earth observation (CHIRPS climatology, NASA POWER agrometeorology, Sentinel-2 vegetation indices), high-resolution field survey microdata from the **National Institute of Statistics of Rwanda (NISR)**, and real-time food commodity markets from the **World Food Programme (WFP VAM)**.

---

## 2. Architectural Blueprint

```mermaid
flowchart TD
    subgraph Data Sources [Satellite, Survey & Market Data Sources]
        A1[NISR SAS Microdata\n2018-2026 Season A & B\n28,042 Plot Records]
        A2[CHIRPS & Meteo Rwanda\n1981-2026 Precipitation Climatology]
        A3[NASA POWER & Open-Meteo\nSolar, Temp, RH, 7-Day Forecast]
        A4[WFP VAM & UN Comtrade\nRetail Food Prices & Cross-Border Flows]
    end

    subgraph Processing & Models [ETL & Machine Learning Engine]
        B1[Data Cleansing & Spatial Alignment\nETL Scripts in src/prepare_*.py]
        B2[maize_yield_model.joblib\nRandomForest & KNN Retrieval]
        B3[drought_risk_classifier.joblib\nParametric Insurance Classifier]
        B4[market_price_forecaster.joblib\nAutoregressive RidgeCV]
    end

    subgraph Services [Application & API Services]
        C1[Streamlit Reactive Application\napp.py on Port 8502]
        C2[FastAPI Enterprise Service\nsrc/api.py on Port 8000]
        C3[AI Agronomic Copilot\nsrc/advise.py with Web Speech API]
    end

    subgraph Users [User Stakeholders & Touchpoints]
        D1[Smallholder Farmers\nUSSD *801# & 160-Char Field SMS]
        D2[RAB Field Extension Agronomists\nTablet / Mobile Web App & Voice Audio]
        D3[MINAGRI & NST2 Policymakers\nStrategic Dashboards & HTML Reports]
    end

    A1 --> B1
    A2 --> B1
    A3 --> B1
    A4 --> B1
    B1 --> B2
    B1 --> B3
    B1 --> B4
    B2 --> C1
    B3 --> C1
    B4 --> C1
    B2 --> C2
    B3 --> C2
    B4 --> C2
    C1 --> C3
    C3 --> D1
    C3 --> D2
    C1 --> D3
```

---

## 3. Layered Architectural Decomposition

### 3.1 Presentation Layer (`app.py` & `src/style.py`)
- **Framework:** Streamlit 1.66+ with session state management.
- **Styling Architecture:** Single-injection stylesheet (`src/style.py`) applying the Inter typeface, responsive grid system, sticky institutional top bar (`min-height: 72px`), and emerald/gold color palette matching Rwanda's national identity.
- **Bilingual Internationalization:** Complete English (`en`) and Kinyarwanda (`rw`) localization dictionary (`locale/en.json`, `locale/rw.json`) loaded dynamically with zero latency.
- **Geospatial Mapping:** Interactive Folium / Leaflet maps embedded via HTML components, supporting multi-layer toggles:
  1. Primary Early Warning Alert status
  2. FAO Agroecological Climate Classification
  3. Cumulative Precipitation Anomaly (%)
  4. Irrigated Plot Share (NISR SAS %)
  5. Severe Soil Erosion Risk (%)
  6. Sentinel-2 NDRE Chlorophyll Vegetation Health Index

### 3.2 Machine Learning & Analytical Layer (`src/advise.py` & `data/processed/models/`)
The system completely replaces static templates with three trained, pre-warmed scikit-learn models:
1. **Plot-Level Yield Regressor & KNN Case Retrieval (`maize_yield_model.joblib` — 9.6 MB):**
   - **Architecture:** `RandomForestRegressor` ($n=160, \text{max\_depth}=7$) + `RidgeCV` + `NearestNeighbors` ($k=3$).
   - **Training Set:** 28,042 real NISR SAS plot microdata records.
   - **Capabilities:** Live yield forecasting, counterfactual intervention uplift (+irrigation, +fertilizer, +terraces), and case-based retrieval returning real matching surveyed plots.
2. **Parametric Drought Risk Classifier (`drought_risk_classifier.joblib` — 265 KB):**
   - **Architecture:** `RandomForestClassifier` trained on crop water balance ($P_e - ET_c$), seasonal rainfall anomaly, and irrigated share.
   - **Capabilities:** Probabilistic risk estimation ($P(\text{Crisis})$, $P(\text{Watch})$, $P(\text{Stable})$), automatically triggering Parametric Crop Insurance payouts (**NAIS / *Tekana Urishingiwe***).
3. **Autoregressive Commodity Price Forecaster (`market_price_forecaster.joblib` — 1.7 KB):**
   - **Architecture:** Autoregressive `RidgeCV` ($R^2 = 0.705$) trained on 2,728 historical WFP retail market observations.
   - **Capabilities:** Forecasts grain prices at 30, 60, and 90-day forward horizons; models triple-layer hermetic PICS bag storage arbitrage.

### 3.3 Programmatic API Layer (`src/api.py`)
- **Framework:** FastAPI with CORS middleware.
- **Endpoints:**
  - `GET /`: Interactive API index and OpenAPI specification links.
  - `GET /api/health`: Health status, operational mode, and pilot district registry.
  - `GET /api/status`: National agrometeorological KPIs and district alert distribution.
  - `GET /api/alerts`: Comprehensive 30-district risk records.
  - `GET /api/pilots`: Merged telemetry for Bugesera, Nyagatare, Musanze, and Nyaruguru.
  - `GET /api/districts/{name}`: Full profile, 7-day forecast, and NASA POWER daily series.
  - `GET /api/models/yield/{district}`: Live scikit-learn yield uplift inference.
  - `GET /api/models/drought/{district}`: Live parametric insurance probability inference.
  - `GET /api/models/prices/{district}`: Live 30/60/90-day commodity price forecasting.
  - `GET /api/chat/ask`: Conversational AI endpoint returning agronomic advice.

### 3.4 Data Storage & Lookup Layer (`data/processed/`)
- All datasets are structured in high-performance columnar formats (CSV, Parquet, GeoJSON):
  - `data/processed/app/`: Curated application tables for immediate memory-mapped reading.
  - `data/processed/lookups/`: Official HS code matches, crop calendar zones, and district metadata.
  - `data/processed/models/`: Serialized scikit-learn model bundles.
  - `data/processed/sas/`: Cleaned microdata tables extracted from official NISR STATA archives.

---

## 4. Security & Data Governance

1. **Sandboxing & Offline Reliability:** The entire analytical engine runs locally with zero mandatory cloud dependencies. All scikit-learn inferences execute in $<10\text{ ms}$ on commodity hardware.
2. **Data Integrity:** No simulated, fake, or synthetic records are ever presented as ground truth. Historical survey data (NISR SAS) is strictly distinguished from real-time API forecasts (Open-Meteo) and statistical models.
3. **Attribution Standards:** Every AI recommendation, table, and visualization explicitly cites the underlying dataset, geographic level, reporting period, and measurement units.
