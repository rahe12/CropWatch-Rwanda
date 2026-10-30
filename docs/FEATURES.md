# CropWatch Rwanda — Operational Features & Desks Guide

CropWatch Rwanda provides 11 cohesive operational desks designed to serve smallholder farmers, sector agronomists, and national agricultural policymakers.

---

## Desk Inventory

| Desk Key | Operational Name (English) | Izina ry'Ikiciro (Kinyarwanda) | Core Functionality | Primary Data Source |
| :--- | :--- | :--- | :--- | :--- |
| **`home`** | National Overview | Gahunda Nkuru | Strategic briefing, live commodity prices, national KPI counters | NISR, WFP, CHIRPS |
| **`alerts`** | Early Warning Alerts | Iburira ry'Ikirere | 30-district interactive map, 6 layers, 7-day forecast, USSD emulator | Open-Meteo, CHIRPS |
| **`dashboard`** | 30 Districts Survey | Ikoranabuhanga mu Turere | NISR SAS baseline explorer, district profiles, CSV/HTML exports | NISR SAS 2018–2026 |
| **`pilot`** | 4 Pilot Districts | Uturere 4 tw'Icyitegererezo | Deep telemetry merge for Bugesera, Nyagatare, Musanze, Nyaruguru | NASA POWER, FAO-56 |
| **`soil`** | Terraces & Soil Health | Amaterasi n'Ubutaka | Slope erosion severity rankings, terracing target tracker | Rwanda Water Portal, SAS |
| **`watch`** | Seasonal Watch | Ikirere n'Amasoko | Multi-season comparison, retail price trends, Sentinel-2 NDRE | WFP VAM, Sentinel-2 |
| **`simulator`** | What-If Yield & SSIT | Kugereranya & SSIT | Counterfactual yield uplift modeling and 50% SSIT pump sizing | NISR SAS, MINAGRI SSIT |
| **`advise`** | AI Agronomic Copilot | Umujyanama wa AI | Live ML inference (<5ms), real plot retrieval, native voice speech | Trained Scikit-Learn |
| **`data`** | Open Data Registry | Amakuru Fatizo | Data dictionaries, crop price matching tables, seasonal calendars | NISR, FAO, UN Comtrade |
| **`method`** | Methodology & Benchmarks | Uko Bikora | FAO-56 Penman-Monteith formulas, ML benchmarks, glossary | FAO-56, NISR SAS |
| **`about`** | Governance & Partners | Ibyerekeye | NST2 alignment, partner directory, user role manuals | MINAGRI, RAB, NISR |

---

## Detailed Desk Specifications

### 1. National Overview (`home`)
- **Executive Hero:** High-contrast photographic banner with the official title, national objective, and immediate calls-to-action.
- **Live 4-District Price & Rain Anomaly Preview:** Real-time table displaying current cumulative precipitation vs. normal and current market status.
- **National Strategic KPI Counters:**
  - Districts with active irrigation-gap warnings.
  - National weighted irrigated plot share ($1.5\%$).
  - Driest district seasonal anomaly ($-37\%$).
- **NST2 Challenge Framework:** Structural transformation goals, food security priorities, and user role pathways (Farmer, Extension Officer, National Planner).

### 2. Early Warning Alerts (`alerts`)
- **Interactive Leaflet/Folium Map:** 30-district interactive polygon map supporting 6 layer visualizations:
  1. *Operational Alert Status* (Stable, Watch, Dry Watch, Soil Watch, Irrigation Gap, Irrigate Now, Soil Rain)
  2. *Agroclimatic Class* (Stable, Rainfall Watch, Water Stress)
  3. *Rainfall Anomaly (%)* (CHIRPS vs 1981–2025 norm)
  4. *Irrigated Plot Share (%)* (NISR SAS 2022)
  5. *Soil Erosion Concern (%)* (NISR SAS 2022)
  6. *Sentinel-2 NDRE Vegetation Health Index (2026)*
- **7-Day Numerical Forecast Panel:** Daily breakdown of forecasted rainfall ($mm$), maximum temperature ($^\circ\text{C}$), and crop evapotranspiration ($ET_c$).
- **Rural USSD & SMS Simulator (`*801#`):** Interactive feature phone mockup testing SMS broadcasts and USSD menus for rural smallholders without smartphones.

### 3. 30 Districts Survey Baseline (`dashboard`)
- **Macro Distribution Tables:** Tabulation of districts by risk level and agroclimatic stress status.
- **Data Freshness Tracker:** Live validation of last reporting dates across prices, satellite rainfall, and trade records.
- **District Deep-Dive Profile:** Comprehensive agrometeorological briefing with why-boxes explaining the physical causes of moisture gaps.
- **One-Click Export Engine:** Direct export to verified CSV files and styled, printable HTML situation notes.

### 4. 4 Focus Pilot Districts (`pilot`)
- Intensive agrometeorological telemetry monitoring for Bugesera (East), Nyagatare (East), Musanze (North), and Nyaruguru (South).
- Merges NASA POWER solar radiation ($MJ/m^2$), 2-meter air temperature ($^\circ\text{C}$), relative humidity ($\%$), and Penman-Monteith reference evapotranspiration ($ET_0$).

### 5. Terraces & Soil Health (`soil`)
- **District Erosion Severity Ranking:** Ordered table ranking districts by percentage of cultivated plots suffering moderate to severe erosion.
- **Soil Protection & Amendment Audit:** Tracks bench terracing coverage, hedgerow vetiver planting, organic manure usage, and agricultural lime requirements for acidic highland soils.

### 6. Seasonal Watch & Commodity Markets (`watch`)
- **Season A vs. Season B Multi-Year Analysis:** Comparative agrometeorological metrics across agricultural seasons.
- **Retail Grain Price Tracking:** Historical and current retail maize prices across Rwandan markets from the World Food Programme (WFP VAM).
- **Multi-Year Sentinel-2 NDRE Vegetation Trends:** Longitudinal line chart (2018–2026) contrasting district-level chlorophyll absorption with the national mean.
- **UN Comtrade Trade Flow Analysis:** Annual maize export value ($USD$) and top bilateral trading partners.

### 7. What-If Simulator & SSIT Calculator (`simulator`)
- **What-If Yield Uplift Simulator:** Interactive sliders allowing agronomists to model the impact of expanding supplementary irrigation ($+0\text{ to }30\%$) and eliminating organic fertilizer deficits ($+0\text{ to }50\%$) using coefficients fit on 28,042 surveyed plots.
- **Small-Scale Irrigation Technology (SSIT) Sizing:**
  - Input: Farm acreage ($0.2\text{ to }5.0\text{ ha}$), water source (marshland, shallow well, rainwater tank), and crop choice.
  - Sizing Output: Recommends foot treadle pump, 1.5 kW solar pump with drip kit, or 5.5 HP high-flow motor pump.
  - Financial Output: Models protected harvest ($kg$) and protected gross crop value ($RWF$) under MINAGRI's official 50% capital subsidy.

### 8. AI Agronomic Copilot (`advise`)
- **Production ML Inference:** In-memory scikit-learn models delivering answers in $<10\text{ ms}$:
  - *Yield Prediction:* Baseline harvest, counterfactual uplifts, and KNN retrieval of matching real farmer plots.
  - *Drought Classifier:* Calculates drought probability distribution and triggers automated Parametric Insurance (**NAIS / *Tekana Urishingiwe***) Mobile Money payouts.
  - *Market Price Forecaster:* Projects prices 30, 60, and 90 days out; calculates triple-layer hermetic PICS bag storage arbitrage.
- **Conversational Intelligence:** Answers questions regarding crops, definitions, charts, and trends.
- **Native Web Speech API Voice Synthesis:** Inline audio playback ("🔊 Listen Aloud" / "🔊 Umva Inama Mu Majwi") for field extension with non-literate farmers.
- **160-Character Rural SMS Engine:** Prepares GSM-7 compliant field SMS alerts ready for telecom SMS gateways.

### 9. Open Data Registry (`data`)
- **5 Organized Repositories:**
  1. *Data Sources:* Complete data dictionary, update frequency, and provider registry.
  2. *Overview:* Survey plot records matrix across all seasons (2018–2026).
  3. *Crops & Pricing:* Verified mapping between NISR survey crop names, HS product codes, and WFP commodities.
  4. *Crop Calendar:* Official FAO planting, weeding, and harvesting windows by agroecological zone.
  5. *Rainfall Explorer:* Historical monthly rainfall and anomalies across all 30 districts since 1981.

### 10. Methodology & Benchmarks (`method`)
- **10-Step Operational Methodology:** Detailed explanation from raw data ingestion to field advisory dispatch.
- **Physical Agronomic Formulas:** Formal definitions of FAO-56 Penman-Monteith reference evapotranspiration ($ET_0$), crop water requirement ($ET_c = K_c \times ET_0$), and effective rainfall ($P_e$).
- **Machine Learning Benchmark Table:** Out-of-sample validation metrics (MAE, RMSE, $R^2$) comparing Ordinary Least Squares, Ridge Regression, and Random Forest on 28,042 plots.
- **Feature Importance Breakdown:** Quantifies the relative contribution of inorganic fertilizer ($44.1\%$), rainfall anomaly ($16.8\%$), vegetation index ($11.7\%$), and irrigation ($3.8\%$).
- **Bilingual Technical Glossary:** Authoritative definitions of 12 critical agricultural and meteorological terms.

### 11. Governance & Institutional Partners (`about`)
- Strategic alignment with **Rwanda Vision 2050** and **NST2 2024–2029 Strategic Priority 1**.
- Detailed operational responsibilities and guidelines for smallholder farmers, RAB sector agronomists, and national agricultural policymakers.
- Partner directory and data governance notices.
