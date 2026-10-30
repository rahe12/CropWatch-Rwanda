# CropWatch Rwanda
### National Agricultural Intelligence & Climate-Smart Decision Support Platform
**Republic of Rwanda · Aligned with NST2 (2024–2029) Priority Area 1: Agriculture Modernization**

---

CropWatch Rwanda is an operational agrometeorological decision-support platform designed for the Ministry of Agriculture and Animal Resources (MINAGRI), the Rwanda Agriculture and Animal Resources Development Board (RAB), district agronomists, and agricultural cooperatives. 

By integrating Seasonal Agricultural Survey (SAS) microdata from the National Institute of Statistics of Rwanda (NISR), high-resolution NASA POWER agrometeorological telemetry, Copernicus Sentinel-2 satellite indices, and CHIRPS precipitation baselines, CropWatch Rwanda provides continuous 30-district early warning intelligence, plot-level machine learning yield simulations, and offline-compatible field advisories.

Available in full bilingual synchronization (**English & Kinyarwanda**).

---

## Strategic Policy & NST2 Alignment

Rwanda's Second National Strategy for Transformation (**NST2 2024–2029**) designates agricultural modernization and climate resilience as national economic priorities:

1. **Small-Scale Irrigation Technology (SSIT) Expansion:** Only 2.2% of sampled Season A agricultural plots nationwide are irrigated. CropWatch calculates real-time root-zone water deficits and models MINAGRI's 50% government equipment subsidy program to accelerate smallholder irrigation adoption up to 10 hectares.
2. **Hillside Soil Conservation & Radical Terracing:** With over 75% of Rwanda's cultivated land on slopes exceeding 16°, CropWatch identifies vulnerable hillside sectors requiring radical terracing, progressive terracing, and agroforestry hedgerows to halt topsoil loss.
3. **Agrometeorological Early Warning:** Combining historical CHIRPS 1981–2025 precipitation baselines with live numerical weather forecasts enables agronomists and irrigation engineers to detect drought stress before crop wilting occurs.
4. **Last-Mile Rural Access:** Translates complex satellite and machine learning analytics into 160-character mobile messages compatible with USSD and SMS push notifications for smallholders using feature phones.

---

## Platform Architecture & Pages

The platform organizes agricultural intelligence into a natural, intuitive 4-tier operational pipeline:

| Module / Page | Operational Focus | Key Data Sources & Capabilities |
|---|---|---|
| **Home** (`home`) | Executive Briefing | National crisis snapshot, live pilot cards, 3-stage decision workflow, and NST2 strategic objectives. |
| **Alerts & Warnings** (`alerts`) | Early Warning & Water Deficit | Interactive 30-district Folium GIS map with layer toggles (Alerts, Rain Deficit, Irrigation, Soil Risk, NDRE), 7-day weather forecast, and automated irrigation triggers. |
| **National Dashboard** (`dashboard`) | 30-District Agricultural Matrix | Longitudinal analysis across 2018–2026 SAS data, district-level productivity benchmarks, input adoption shares, and downloadable executive briefing notes. |
| **Climate Pilot** (`pilot`) | High-Resolution Agrometeorology | Direct NASA POWER daily telemetry for Bugesera, Nyagatare, Musanze, and Nyaruguru. Solar radiation (MJ/m²), 2m air temperature, ET₀, and Penman-Monteith crop water balance. |
| **Soil & Terraces** (`soil`) | Land Conservation & Acidity | Slope-weighted erosion risks, radical vs progressive terracing priority rankings, and agricultural lime subsidy targets for acidic highland soils. |
| **Season Watch** (`watch`) | Multi-Season Climate Chronology | Rainfall anomalies across Seasons A, B, and C (2018–2026), Copernicus Sentinel-2 NDRE vegetation health, and WFP VAM retail food market price tracking. |
| **Yield Simulator** (`simulator`) | Predictive Modeling & SSIT Subsidy | Ridge regression & Random Forest yield predictions trained on 28,000+ SAS plot microdata, paired with an interactive MINAGRI SSIT 50% equipment subsidy calculator. |
| **Field Advisory & USSD** (`advise`) | Extension Copilot & Mobile Gateway | Bilingual agronomic AI assistant for crop diagnostics and fertilizer management, with automated 160-character SMS/USSD packaging for offline mobile networks. |
| **Open Data** (`data`) | Data Catalog & Governance | Transparent catalog of all cleaned district tables, seasonal crop calendars, price match indices, GeoJSON shapefiles, and direct CSV/JSON downloads. |
| **Methodology** (`method`) | Scientific Validation & Glossary | Mathematical formulations (FAO-56 Penman-Monteith, Hargreaves), out-of-sample machine learning cross-validation metrics (RMSE, MAE, R²), and agrometeorological glossary. |
| **Institutional Charter** (`about`) | Governance & NST2 Alignment | Institutional provenance (MINAGRI, NISR, RAB, Meteo Rwanda), ethical AI guardrails, and decision-support transparency standards. |

---

## Agrometeorological & Alert Logic

CropWatch applies transparent, explainable physical rules:

1. **Irrigation Gap Alert:** Triggered when cumulative rainfall since 1 September 2026 is ≥10% below the long-term September–October baseline (CHIRPS 1981–2025) **and** the district's irrigated plot share is under 10%.
2. **Irrigate This Week:** Triggered when an irrigation gap is active **and** the 7-day numerical forecast totals less than 10 mm.
3. **Soil Erosion Risk:** Triggered when district erosion concern is ≥20%, soil protection coverage is under 80%, and the 7-day forecast predicts daily rainfall ≥15 mm on steep slopes.
4. **Crop Water Accounting (FAO-56):**
   - Reference Evapotranspiration ($ET_0$) calculated via Penman-Monteith physics.
   - Crop Water Demand ($ET_c = ET_0 \times K_c$) calibrated to tropical maize growth stages.
   - Root-Zone Water Balance ($Pe - ET_c$) where negative balances identify moisture stress.

---

## Machine Learning Yield Benchmarks

Trained on **11,148 Season A maize plots** from NISR microdata (1st–99th yield percentile filter):

- **Features:** Irrigation status, organic fertilizer, inorganic fertilizer (DAP/NPK), organic shortage, erosion severity, soil protection structures, CHIRPS rainfall anomaly, Sentinel-2 NDRE vegetation index.
- **Validation:** 5-fold cross-validation on held-out plots using survey plot weights.

| Model | MAE (kg/ha) | RMSE (kg/ha) | R² | Operational Verdict |
|---|---:|---:|---:|---|
| Naive Rain-Only Linear | 979 | 1,203 | −0.009 | Underperforms historical district baseline |
| Historical District Baseline | 943 | 1,175 | 0.038 | Baseline geographic mean |
| Multi-Factor Random Forest | 918 | 1,136 | 0.101 | Beats geographic baseline across all folds |
| Multi-Factor Gradient Boosting | 911 | 1,126 | 0.117 | Top predictive accuracy |

**Empirical Within-District Plot Effects:**
- Irrigation Access: **+365.3 kg/ha**
- Balanced Inorganic Fertilizer: **+524.1 kg/ha**
- Organic Manure Application: **+305.2 kg/ha**
- Severe Slope Erosion: **−375.0 kg/ha**

---

## Technical Stack & Execution

### System Requirements
- Python 3.12+
- Dependencies listed in `requirements.txt`

### Quickstart

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Launch Streamlit Decision Platform:**
   ```bash
   streamlit run app.py --server.port 8502
   ```
   Access in browser: `http://localhost:8502`

3. **Launch Micro-Desk & Telemetry API (Optional):**
   ```bash
   uvicorn src.api:app --host 127.0.0.1 --port 8520
   ```
   Access in browser: `http://localhost:8520`

### Optional LLM Integration for Advisory
For extended conversational natural language processing on the **Advise** desk:
1. Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml`
2. Add your Groq API key: `GROQ_API_KEY = "gsk_..."` or Gemini key: `GEMINI_API_KEY = "..."`
3. If no API key is provided, the platform operates offline using its built-in deterministic agronomic rule engine.

---

## Institutional Provenance & Data Partners

- **NISR (National Institute of Statistics of Rwanda):** Seasonal Agricultural Survey (SAS) microdata, district shapefiles, and agricultural census records.
- **MINAGRI & RAB:** Agricultural policy frameworks, SSIT guidelines, and crop production targets.
- **Meteo Rwanda & CHIRPS (UCSB CHC):** Historical gridded precipitation baselines (1981–2025) and daily rainfall monitoring.
- **NASA POWER:** High-resolution surface solar radiation, air temperature, relative humidity, and wind telemetry.
- **Copernicus Sentinel-2:** Red-edge vegetation indices (NDRE) for crop vigor tracking.
- **WFP VAM & UN Comtrade:** Market retail commodity prices and formal cross-border grain flows.

---
*© 2026 Republic of Rwanda · CropWatch Rwanda · National Agricultural Intelligence & Climate-Smart Decision Support Platform*
