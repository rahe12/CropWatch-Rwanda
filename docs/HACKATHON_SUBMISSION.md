# NISR 2026 Big Data Hackathon — Official Submission & Team Eligibility

## 1. Project Information & Metadata

- **Project Title:** **CropWatch Rwanda** — National Agricultural Intelligence & Climate-Smart Decision Support Platform
- **Competition:** **NISR 2026 Big Data Hackathon**
- **Organizing Institution:** **National Institute of Statistics of Rwanda (NISR)** — Data Science Team
- **Submission Deadline:** **30 October 2026**
- **Public GitHub Repository:** [https://github.com/cropwatch-rwanda/cropwatch-rwanda](https://github.com/cropwatch-rwanda/cropwatch-rwanda)
- **Deployed Web Application:** [http://localhost:8502](http://localhost:8502) *(or public cloud deployment URL)*
- **Enterprise REST API:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Video Demonstration:** [`demo/`](file:///demo/README.md) (Screen recording $\le 3$ minutes)

---

## 2. Engineering Team & Verified Student Eligibility

In strict accordance with **NISR Big Data Hackathon Rule 6** (*"A team must be composed of 2 students with at least one Rwandan citizen. Students must have a student card or other official document confirming eligibility"*):

```mermaid
classDiagram
    class StudentTeam {
        +String institution: "Rwanda Polytechnic (RP)"
        +String campus: "RP Musanze College"
        +String academic_year: "2026 - 2027"
    }
    class MurenziElvis {
        +String name: "MURENZI Elvis"
        +String reg_no: "26RP01872"
        +String program: "BTech in Information Technology"
        +Int year_of_study: 4
        +String role: "Full-Stack Software Architecture & ML Engineering"
        +String citizenship: "Rwandan"
    }
    class BahireElie {
        +String name: "BAHIRE Elie"
        +String reg_no: "26RP02259"
        +String program: "BTech in Irrigation and Drainage Technology"
        +Int year_of_study: 4
        +String role: "Agrometeorology & Irrigation Engineering"
        +String citizenship: "Rwandan"
    }
    StudentTeam --> MurenziElvis
    StudentTeam --> BahireElie
```

### Team Member 1: Lead Software Architect & Data Science Engineer
- **Full Legal Name:** **MURENZI Elvis**
- **Institution:** **Rwanda Polytechnic (RP)** — Musanze College
- **Registration Number:** `26RP01872`
- **Academic Degree:** Bachelor of Technology in Information Technology
- **Year of Study:** Year 4 (Academic Year 2026–2027)
- **Citizenship:** Rwandan Citizen 🇷🇼
- **Official Student Card Document:** [`docs/team/student_id_murenzi_elvis_26RP01872.pdf`](file:///docs/team/student_id_murenzi_elvis_26RP01872.pdf)
- **Core Engineering Contributions:**
  - Full-stack Streamlit reactive architecture and modern institutional design system.
  - Production FastAPI microservice with 10 asynchronous REST endpoints.
  - Integration of serialized scikit-learn models (`RandomForestRegressor`, `RidgeCV`, `LogisticRegression`).
  - Web Speech API spoken audio engine and 160-character GSM-7 rural SMS generator.
  - Complete English-Kinyarwanda bilingual synchronization engine.

---

### Team Member 2: Lead Agrometeorologist & Irrigation Engineer
- **Full Legal Name:** **BAHIRE Elie**
- **Institution:** **Rwanda Polytechnic (RP)** — Musanze College
- **Registration Number:** `26RP02259`
- **Academic Degree:** Bachelor of Technology in Irrigation and Drainage Technology
- **Year of Study:** Year 4 (Academic Year 2026–2027)
- **Citizenship:** Rwandan Citizen 🇷🇼
- **Official Student Card Document:** [`docs/team/student_id_bahire_elie_26RP02259.pdf`](file:///docs/team/student_id_bahire_elie_26RP02259.pdf)
- **Core Engineering Contributions:**
  - Root-zone crop water balance accounting using FAO-56 Penman-Monteith physics ($Pe - ET_c$).
  - Calibration of maize crop coefficients ($K_c = 0.85$ for stem elongation / vegetative stage).
  - Formulation of the MINAGRI 50% Small-Scale Irrigation Technology (SSIT) equipment subsidy model.
  - Slope-weighted hillside erosion risk indexing and radical vs progressive terracing priority matrices.
  - Agricultural lime application requirements for acidic volcanic and tea-zone soils.

---

## 3. Compliance with Hackathon Judging Criteria

### 1. Problem Understanding & Relevance (NST2 Priority 1 Alignment)
- **The Challenge:** Rwandan agriculture employs over 60% of the workforce, yet only **2.2% of Season A plots are irrigated**, and over 75% of cultivated lands sit on steep slopes ($>16^\circ$) vulnerable to catastrophic topsoil erosion.
- **Strategic Policy Alignment:** Directly advances **Second National Strategy for Transformation (NST2 2024–2029) Priority Area 1: Agriculture Modernization and Commercialization**, scaling small-scale irrigation up to 10 ha, expanding radical terracing, and enhancing national food security.

### 2. Data Use & Methodology
- **Verified Primary Microdata:** Joined **28,042 surveyed plot records** across 2018–2026 from the National Institute of Statistics of Rwanda (NISR) Seasonal Agricultural Surveys (SAS).
- **Multi-Source Satellite Fusion:** Integrated 44-year CHIRPS precipitation baselines (1981–2025), NASA POWER solar radiation/temperature telemetry, and Copernicus Sentinel-2 Red-Edge vegetation vigor (NDRE).
- **Rigorous Data Preprocessing:** Cleaned using 1st–99th percentile outlier filtering and spatial harmonization to official 2026 NISR 30-district shapefiles.

### 3. Tangible Real-World Impact
- **Smallholder Farmers:** Automated 160-character USSD/SMS alerts delivered directly to 2G feature phones via MINAGRI's Smart Nkunganire infrastructure (`*801#`).
- **Field Extension Agronomists:** Tablet-optimized decision desks featuring spoken voice audio ("🔊 Listen Aloud") in English and Kinyarwanda for hands-free fieldwork.
- **MINAGRI / RAB / NAEB Policymakers:** National 30-district risk maps, irrigation gap rankings, and parametric drought insurance payout triggers for NAIS (*Tekana Urishingiwe Muhinzi*).

### 4. Technical Innovation
- **Sub-10ms Machine Learning Inference:** Local serialized Random Forest models evaluate counterfactual agronomic packages in real time ($<10\text{ ms}$).
- **Production REST API:** Asynchronous FastAPI microservice exposing 10 endpoints with automatic OpenAPI/Swagger documentation.
- **Client-Side Voice Synthesis:** Zero-latency Web Speech API text-to-speech embedded directly into the browser without recurring third-party cloud costs.

### 5. Usability & Professional Design
- **Institutional UI/UX:** Bespoke institutional design system featuring the Rwandan national crest, 72px navigation bar, accessible typography, zero horizontal scrolling, and a 4-column institutional footer.
- **100% Bilingual Parity:** Symmetrical English and Kinyarwanda translation across every label, chart tooltip, and AI advisory response.

---

## 4. Repository Structure Verification (Slide 20 Compliance)

The repository strictly conforms to the structure prescribed in NISR Webinar Slide 20:

```text
my-hackathon-project/ (CropWatch Rwanda)
├── README.md               # Comprehensive user manual, data docs, and quickstart
├── app.py                  # Reactive 11-desk decision support platform (Streamlit)
├── data/                   # Preprocessed NISR SAS microdata and satellite tables
│   ├── processed/app/      # Cleaned 30-district analytical tables
│   └── processed/models/   # Serialized machine learning models (.joblib)
├── demo/                   # Video demonstration directory and script
│   └── README.md           # 3-minute video guide
├── docs/                   # Complete 8-document technical library
│   ├── team/               # Verified Student Cards (Elvis Murenzi & Elie Bahire)
│   ├── ARCHITECTURE.md     # System architecture & data flow
│   ├── FEATURES.md         # 11-desk user & feature guide
│   ├── SETUP.md            # Installation & execution manual
│   ├── API.md              # FastAPI OpenAPI reference
│   ├── DATA_SOURCES.md     # Data provenance & limitations
│   ├── CHATBOT.md          # AI Copilot specification
│   ├── TESTING.md          # QA protocols & test outputs
│   └── HACKATHON_SUBMISSION.md # This official submission declaration
├── src/                    # Core engineering modules
│   ├── api.py              # FastAPI REST service (Port 8000)
│   ├── advise.py           # AI Agronomic Copilot & Web Speech API
│   ├── style.py            # Design system, 72px top bar, & footer
│   └── geo.py              # Leaflet / Folium GIS mapping engine
└── requirements.txt        # Exact runtime Python dependencies
```

---

*CropWatch Rwanda · NISR 2026 Big Data Hackathon · Rwanda Polytechnic (RP Musanze College)*
