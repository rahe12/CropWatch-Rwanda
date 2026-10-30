# 🌾 CropWatch Rwanda — Season Intelligence & Decision Support System

> **NISR 2026 Big Data Hackathon Submission**  
> **Track 1: Agricultural Productivity**  
> **National Alignment:** National Strategy for Transformation 2 (NST2) & Vision 2050  
> **Live App Deployment:** *(Add your deployed Streamlit URL here, e.g. https://cropwatch-rwanda.streamlit.app)*  
> **Public GitHub Repository:** *(Add your GitHub repository URL here)*  

---

## 📌 Executive Summary

Rwanda's agricultural sector is predominantly rain-fed, with fewer than **2% of sampled plots equipped with irrigation infrastructure**. In drought-prone seasons, smallholder farmers face severe harvest vulnerabilities. While weather forecasts and survey microdata exist, they are often siloed, heavily aggregated, or published long after planting decisions have already been made.

**CropWatch Rwanda** is an end-to-end decision-support and early-warning intelligence platform. It fuses **NISR Seasonal Agriculture Survey (SAS)** microdata with **CHIRPS climatological baselines**, **Open-Meteo live precipitation forecasts**, **Sentinel NDRE satellite vegetation indices**, and **WFP retail food market prices**. Rather than making ungrounded predictions, CropWatch delivers actionable, bilingual (**English & Kinyarwanda**) alerts and policy simulation tools to target small-scale irrigation, mitigate soil erosion, and optimize crop yields.

---

## 🎯 Alignment with NST2 & Vision 2050 Priorities

CropWatch directly targets core national development pillars outlined in the **Second National Strategy for Transformation (NST2)** and **Vision 2050**:

1. **Expanding Small-Scale Irrigation Technology (SSIT):**
   * *NST2 Objective:* Accelerate climate resilience by expanding irrigated agricultural land.
   * *CropWatch Delivery:* Automatically flags deficit districts where rainfall is $\ge 10\%$ below usual and plot irrigation adoption is $<10\%$, prioritizing low-cost interventions (watering cans, treadle pumps, marshland water retention) supported by MINAGRI's 50% SSIT subsidy.
2. **Soil Conservation & Land Husbandry:**
   * *NST2 Objective:* Scale progressive and radical terracing and reverse land degradation.
   * *CropWatch Delivery:* Translates weighted survey plot data on moderate vs. severe erosion (rills, gullies, landslides) and combines it with real-time heavy rainfall warnings to trigger pre-storm drainage and grass strip maintenance.
3. **Evidence-Based Agricultural Policy & Resource Allocation:**
   * *Vision 2050 Objective:* Data-driven modern agriculture and market integration.
   * *CropWatch Delivery:* Interactive What-If simulation engine enabling district agronomists to model yield impacts of expanding irrigation and resolving organic fertilizer shortages.

---

## 🚀 Key System Features

### 1. 🚨 Smart Climate & Irrigation Alert Engine
* Combines **CHIRPS historical rainfall** (2018–2025 normal) with **Open-Meteo live rainfall since 1 Sept 2026** and **7-day forecasts** per district centroid.
* Generates tiered, transparent operational alerts:
  * **Irrigate this week (`irrigate_now`):** Rainfall deficit + low irrigation infrastructure + dry 7-day outlook.
  * **Irrigation gap (`irrigation_gap`):** Rain deficit with incoming precipitation—prompting rainwater harvesting and supplemental watering plans.
  * **Soil and rain alert (`soil_rain`):** High plot erosion risk combined with forecasted heavy precipitation ($\ge 15\text{ mm}$ daily).
  * **Dry watch / Soil watch / Stable.**

### 2. 🗺️ Interactive National Risk Map
* Visualizes all 30 districts of Rwanda on a geospatial deck map powered by Pydeck.
* Color-coded pins (Red: Irrigate Now, Orange: Irrigation Gap, Yellow: Soil/Rain, Green: Stable) with interactive tooltips showing real-time precipitation, 7-day forecast, and irrigation rates.

### 3. 🧪 "What-If" Policy Simulator & AI/ML Yield Optimization
* Allows policymakers and agronomists to simulate the impact of:
  * Expanding Small-Scale Irrigation Technology (SSIT) (+% adoption)
  * Reducing organic fertilizer shortages (+% manure availability)
  * Strengthening anti-erosion terracing and ditches (+% slope protection)
* Predicts projected yield uplift ($\text{kg/ha}$ and $\%$ gain) calibrated against historical SAS microdata and MINAGRI trial benchmarks.

### 4. 📊 Data Hub & Commodity Harmonization
* **Crop Matchmaking:** Rigorous harmonization between NISR survey crop names, WFP market prices, and international HS trade codes (distinguishing safe commodity pairs from misleading homonyms like grain vs. flour).
* **Farming Seasons & FAO Calendars:** Detailed planting, vegetative, and harvest spans for maize, sorghum, and 12 major crops across Rwanda's 6 agroecological zones.
* **District Rainfall Anomaly Explorer:** Monthly rainfall anomalies from 2018 to 2026 across all 30 districts.

### 5. 🌍 Grassroots Accessibility: Native Bilingual Localization
* Full toggle between **English** and **Kinyarwanda** for all metrics, alerts, tables, and explanations.

---

## 🔬 Data Sources & Engineering Architecture

| Dataset | Source Agency | Frequency / Window | Purpose in CropWatch |
| :--- | :--- | :--- | :--- |
| **Seasonal Agriculture Survey (SAS)** | National Institute of Statistics of Rwanda (NISR) | 2018–2026 (Seasons A, B, C) | Plot-level microdata: crop yields, irrigation adoption, erosion severity, fertilizer application, and survey weights (`plot_weight`). |
| **Administrative Boundaries** | NISR / MINALOC | 2018 GIS Shapefiles | Official 30-district polygon geometries and centroid coordinates. |
| **CHIRPS Climatology** | Climate Hazards Group (UCSB) | 2018–2026 (Monthly) | Climatological precipitation normals for all 30 districts. |
| **Live Weather & Forecast** | Open-Meteo API | Daily (Real-time + 7-Day) | Live season rainfall archive and 7-day precipitation forecast per district. |
| **NDRE Vegetation Index** | Sentinel-2 Remote Sensing | 2018–2026 (Yearly) | Canopy greenness, chlorophyll concentration, and crop vigor. |
| **Retail Food Market Prices** | World Food Programme (WFP) / NISR | 2018–March 2026 | Real-time market retail price series (RWF/kg). |
| **Export Trade Statistics** | UN Comtrade / NISR | 2018–2025 (Annual) | Formal agricultural trade flows by commodity, partner country, and USD value. |

---

## 📈 AI / Machine Learning Methodology & Benchmarks

To adhere to rigorous data science principles, we evaluated predictive modeling architectures across **300 district-season-year historical trials** (covering Seasons A and B across 30 districts from 2020 to 2025):

```
                        Model Comparison Benchmark
┌──────────────────────────────────────┬─────────────┬──────────────┬──────────┐
│ Model Architecture                   │ MAE (kg/ha) │ RMSE (kg/ha) │ R² Score │
├──────────────────────────────────────┼─────────────┼──────────────┼──────────┤
│ 1. Naive Rain Model (Linear Reg)     │   334.2     │    435.7     │  0.093   │
│ 2. Historical District Baseline      │   340.9     │    425.8     │  0.134   │
│ 3. Multi-Factor Random Forest (AI)   │   215.5     │    270.7     │  0.650   │
└──────────────────────────────────────┴─────────────┴──────────────┴──────────┘
```

### Key Analytical Insight:
* **Why naive rainfall models fail:** In Rwanda's topography, total rainfall volume explains only 9.3% of yield variance ($R^2 = 0.093$). Yield is heavily moderated by soil protection, terracing, and fertilizer inputs.
* **Why multi-factor ML wins:** By combining seasonal precipitation with **plot irrigation shares, organic and inorganic fertilizer adoption, erosion vulnerability, and Sentinel NDRE vegetation indices**, the Random Forest model achieves an **$R^2$ of 0.650** and reduces Mean Absolute Error by **36%** (from $340.9\text{ kg/ha}$ down to $215.5\text{ kg/ha}$).

### Feature Importance Breakdown:
1. **Seasonal Rainfall Volume (`rain_mm`):** $39.1\%$
2. **Rainfall Anomaly vs Normal (`rain_diff_pct`):** $18.7\%$
3. **Sentinel NDRE Vegetation Health (`vegetation_mean`):** $11.5\%$
4. **Organic Fertilizer Adoption (`organic_pct`):** $11.3\%$
5. **Inorganic Fertilizer Utilization (`inorganic_pct`):** $6.8\%$
6. **Small-Scale Irrigation Share (`irrigated_pct`):** $5.3\%$
7. **Soil Terracing / Anti-Erosion Ditches (`protected_pct`):** $4.1\%$
8. **Severe Soil Erosion Exposure (`concern_pct`):** $3.1\%$

---

## 💻 Local Installation & Setup

### Prerequisites
* Python 3.10, 3.11, or 3.12
* Git

### Step-by-Step Instructions

1. **Clone the repository:**
   ```bash
   git clone https://github.com/<your-username>/cropwatch-rwanda.git
   cd cropwatch-rwanda
   ```

2. **Create and activate a virtual environment:**
   ```bash
   # Windows (PowerShell)
   python -m venv .venv
   .venv\Scripts\Activate.ps1

   # Linux / macOS
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **(Optional) Re-train the ML models:**
   ```bash
   python src/model_yield.py
   ```

5. **Run the Streamlit application:**
   ```bash
   streamlit run app.py
   ```
   Open your browser at `http://localhost:8501`.

---

## ☁️ Deployment Instructions

This repository is optimized for one-click deployment on **Streamlit Community Cloud**:
1. Push this repository to GitHub.
2. Sign in to [Streamlit Community Cloud](https://share.streamlit.io).
3. Select this repository, branch `main`, and main file `app.py`.
4. Click **Deploy**.

---

## 📜 Declarations & Disclosures

### 1. Mandatory AI Tools Disclosure
*In compliance with the official NISR Big Data Hackathon guidelines:*
* **Disclosure:** Generative AI tools (including Claude and Gemini) were utilized as assistants during the development of this project. Specifically, AI tools supported data pipeline refactoring, CSS layout styling, bilingual translation verification (English to Kinyarwanda), and Scikit-learn model benchmark scripting. All methodologies, analyses, code logic, and data interpretations were designed, reviewed, validated, and tested by the team participants, who assume full responsibility for this submission.

### 2. Originality Declaration
* The authors declare that this submission is an original project created for the **2026 NISR Big Data Hackathon** and has not been previously submitted to any other competition or entity. All external datasets, references, and toolkits are cited in full.

### 3. Team Composition
* The participating team is composed of university students meeting all eligibility requirements, including Rwandan citizenship representation.
