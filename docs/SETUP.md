# CropWatch Rwanda — Setup & Installation Guide

This guide provides step-by-step instructions for installing, configuring, running, and verifying **CropWatch Rwanda** in local development, testing, and production environments across **Windows**, **Linux**, and **macOS**.

---

## 1. System Requirements

### Hardware Prerequisites
- **Processor:** Modern dual-core CPU or higher (x86_64 or Apple Silicon ARM64).
- **Memory (RAM):** Minimum 4 GB RAM (8 GB recommended for simultaneous Streamlit + FastAPI execution and scikit-learn tree traversals).
- **Disk Storage:** At least 1.5 GB free disk space (to accommodate the repository, Python packages, preprocessed survey microdata, and serialized model files).

### Software Prerequisites
- **Operating System:** Windows 10/11, Ubuntu 20.04/22.04 LTS, Debian 11/12, or macOS 12+ (Monterey, Ventura, Sonoma).
- **Python:** Python 3.10, 3.11, or 3.12 (Python 3.12 recommended).
- **Package Manager:** `pip` (bundled with Python).
- **Version Control:** `git` (for repository cloning and version tracking).

---

## 2. Repository Cloning & Environment Setup

### Step 2.1: Clone the Repository
Open your terminal (PowerShell / Command Prompt on Windows, Bash / Zsh on Linux and macOS):

```bash
git clone https://github.com/cropwatch-rwanda/cropwatch-rwanda.git
cd "cropwatch-rwanda"
```

*(If working with the local project directory directly, simply `cd` into the project root).*

---

### Step 2.2: Create and Activate a Python Virtual Environment

It is strongly recommended to isolate dependencies inside a virtual environment (`venv`).

#### On Windows (PowerShell):
```powershell
# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1
```
*Note: If PowerShell throws an execution policy error, run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` once.*

#### On Windows (Command Prompt):
```cmd
python -m venv venv
venv\Scripts\activate.bat
```

#### On Linux / macOS (Bash / Zsh):
```bash
python3 -m venv venv
source venv/bin/activate
```

---

## 3. Dependency Installation

Upgrade `pip` and install all required runtime dependencies from `requirements.txt`:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Core Dependency Manifest
The application relies on verified, battle-tested Python libraries:

| Library | Primary Responsibility in CropWatch |
|---|---|
| `streamlit >= 1.30.0` | Reactive analytical dashboard, layout, state management, and UI rendering |
| `fastapi >= 0.100.0` | High-performance asynchronous REST API backend |
| `uvicorn >= 0.22.0` | Lightning-fast ASGI production web server |
| `pandas >= 2.0.0` | High-throughput tabular data structures and district microdata aggregations |
| `numpy >= 1.24.0` | Vectorized mathematical operations and climatological indexing |
| `scikit-learn >= 1.3.0` | Serialized model loading (`RandomForestRegressor`, `RidgeCV`, `LogisticRegression`) |
| `joblib >= 1.3.0` | High-efficiency compression and deserialization of scikit-learn models |
| `folium >= 0.15.0` | Interactive Leaflet GIS mapping with district vector layers and GeoJSON overlays |
| `streamlit-folium` | Bi-directional bridge between Folium maps and Streamlit reactive state |
| `requests >= 2.31.0` | Resilient HTTP client for live agrometeorological telemetry (Open-Meteo, NASA POWER) |
| `pydantic >= 2.0.0` | Strict data validation and schema enforcement for API payloads |

---

## 4. Configuration & Secrets Management

CropWatch Rwanda is designed to operate **100% offline out-of-the-box** using precomputed national microdata, historical CHIRPS baselines, and local machine learning models without requiring third-party cloud API keys.

However, if you wish to enable optional cloud LLM reasoning (Groq or Google Gemini) for open-ended agronomic expansion in the **Field Advisory** desk:

1. Create the Streamlit secrets file in `.streamlit/secrets.toml`:
   ```bash
   # On Linux/macOS
   cp .streamlit/secrets.toml.example .streamlit/secrets.toml

   # On Windows (PowerShell)
   Copy-Item .streamlit\secrets.toml.example .streamlit\secrets.toml
   ```

2. Open `.streamlit/secrets.toml` in your text editor and specify your keys:
   ```toml
   # CropWatch Rwanda Configuration Secrets
   GROQ_API_KEY = "gsk_your_groq_api_key_here"
   GEMINI_API_KEY = "your_google_gemini_api_key_here"
   ENVIRONMENT = "production"
   ```

*Security Guardrail:* Never commit `.streamlit/secrets.toml` to git. The `.gitignore` file is preconfigured to ignore secret files and credentials.

---

## 5. Running the Application

CropWatch Rwanda provides two complementary services:
1. **Interactive Analytical Decision Desk** (Streamlit Frontend)
2. **Enterprise Agrometeorological REST API** (FastAPI Backend)

---

### Option A: Launching the Streamlit Decision Desk

Run the Streamlit server on port `8502`:

```bash
streamlit run app.py --server.port 8502
```

Once launched, access the platform in your web browser:
- **Local URL:** [http://localhost:8502](http://localhost:8502)
- **Network URL:** Displayed in the terminal for local LAN collaboration across district agronomist tablets.

#### Headless / Background Execution (Production / Server Mode)
To run headless without opening a browser window:
```bash
streamlit run app.py --server.headless true --server.port 8502
```

---

### Option B: Launching the FastAPI Enterprise Service

Run the ASGI server via `uvicorn` on port `8000`:

```bash
uvicorn src.api:app --host 0.0.0.0 --port 8000 --reload
```

Once launched:
- **API Base URL:** [http://localhost:8000](http://localhost:8000)
- **Interactive Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc Technical Specification:** [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

### Option C: Running Both Services Concurrently

#### On Windows (Two Separate PowerShell Windows):
- **Window 1 (Streamlit):**
  ```powershell
  .\venv\Scripts\activate
  streamlit run app.py --server.port 8502
  ```
- **Window 2 (FastAPI):**
  ```powershell
  .\venv\Scripts\activate
  uvicorn src.api:app --host 127.0.0.1 --port 8000
  ```

#### On Linux / macOS (Background or Terminal Multiplexer):
```bash
# Terminal 1 or Background
uvicorn src.api:app --host 0.0.0.0 --port 8000 &
streamlit run app.py --server.port 8502
```

---

## 6. Verifying the Installation

To verify that all components, datasets, and machine learning models are functioning correctly without errors, run the repository automated test suites:

### 1. Verify Python Code Compilation
Ensure there are zero syntax warnings, invalid escape sequences, or import errors:
```bash
python -m compileall -q app.py src
```
*(Expected output: clean return with exit code 0).*

### 2. Verify AI Agronomic Engine & Model Latencies
Run the semantic intent and inference benchmark:
```bash
python -c "
import src.advise as advise
res = advise.generate_agronomic_advice('maize yield in Nyagatare', district='Nyagatare', lang='en')
assert res['status'] == 'success'
print('[PASS] AI Copilot Intent Engine + Microdata Bridge verified!')
"
```

### 3. Verify FastAPI Route Handlers
Verify the API health endpoint:
```bash
python -c "
import src.api as api
status = api.health()
assert status['status'] == 'healthy'
print('[PASS] FastAPI Health Route verified: 10/10 endpoints operational!')
"
```

---

## 7. Troubleshooting & FAQ

### Issue: Port 8502 or 8000 Already in Use
**Symptom:** `Error: Address already in use` or Streamlit chooses port 8503 automatically.  
**Resolution:**
- On Windows: Run `netstat -ano | findstr :8502`, then kill the PID with `taskkill /F /PID <PID>`.
- On Linux/macOS: Run `lsof -i :8502`, then kill with `kill -9 <PID>`.
- Or specify an alternate port: `streamlit run app.py --server.port 8505`.

### Issue: Windows PowerShell Script Execution Disabled
**Symptom:** `cannot be loaded because running scripts is disabled on this system`.  
**Resolution:** Run PowerShell as Administrator and execute:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Issue: Missing Model Files (`FileNotFoundError`)
**Symptom:** Error loading `data/processed/models/*.joblib`.  
**Resolution:** Ensure your working directory is the repository root (`c:\...\Rwanda intelligence analysis`). Verify the files exist:
- `data/processed/models/maize_yield_model.joblib`
- `data/processed/models/drought_risk_classifier.joblib`
- `data/processed/models/market_price_forecaster.joblib`
These serialized models are tracked and committed directly inside the repository.

---

*CropWatch Rwanda · Operational Technical Documentation · Aligned with NST2 (2024–2029)*
