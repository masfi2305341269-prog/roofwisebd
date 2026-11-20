# RoofwiseBD — AI-Powered Rooftop Solar Platform for Bangladesh

**RoofwiseBD** is a modern, responsive web application and engineering recommendation platform tailored for residential energy consumers in Bangladesh. It calculates rooftop solar potential, forecasts daily and monthly generation, classifies solar panel dust using deep learning, optimizes battery storage for load shedding, and generates multi-tier solar system recommendations compliant with the **SREDA Net Metering Guideline 2025** and **BERC 2026 Electricity Tariff Schedule** (June 4, 2026 revision).

---

## 1. Key Capabilities & Features

- **5-Step Solar Assessment Wizard**: Location (8 Bangladesh divisions & 64 districts), consumption (monthly kWh units & sanctioned load), bill upload/manual verification, rooftop characteristics (flat RCC, tin shed, tiled, shading), and review.
- **SREDA Net Metering Guideline 2025 Compliance**: Enforces that inverter AC output does not exceed the customer's sanctioned load ($kW_{AC} \le kW_{sanctioned}$), and flags three-phase requirements for systems $>10\text{ kW}$.
- **BERC 2026 Residential Tariff Engine**: Models the official progressive multi-tier slabs (Lifeline Tk 4.63, 0-75 Tk 5.26, 76-200 Tk 8.50, 201-300 Tk 9.10, 301-400 Tk 9.62, 401-600 Tk 15.01, >600 Tk 17.03) with demand charges and configurable utility VAT to compute real financial savings in BDT (৳).
- **Solar Generation Forecasting (ML 1)**: Physics-based NASA POWER agroclimatology baseline paired with a decoupled XGBoost machine learning model interface.
- **Solar Panel Dust Detection AI (ML 2)**: Image classification tool built with MobileNetV2 architecture to classify module cleanliness (Clean vs Dusty) and recommend scheduled cleaning intervals.
- **Battery Backup Optimizer**: Critical load calculator based on real household appliances (fans, LED lights, refrigerators, routers, TVs), configurable Depth-of-Discharge (LiFePO4 85% vs Lead-Acid 50%), and 24-hour dispatch simulation.
- **Downloadable & Printable Report**: Formatted assessment report ready for PDF export or printing.
- **Live Model Registry & Dataset Audit**: Transparent dynamic reporting of model weights detection, academic scope limitations, and raw dataset directory stats.

---

## 2. Technology Stack

- **Frontend**:
  - React 18
  - TypeScript
  - Vite
  - Tailwind CSS
  - Lucide React (Clean, modern iconography)
  - Recharts (Diurnal power curves, monthly generation bars, battery dispatch lines)
  - React Router DOM v6
- **Backend**:
  - Python 3.12+ (tested on Python 3.12 and 3.14)
  - FastAPI (REST API with automatic OpenAPI Swagger docs)
  - Pydantic v2 (Input validation & typed schemas)
  - SQLAlchemy & SQLite (Database persistence)
  - Pillow & NumPy (Image inspection and arrays)
  - Pytest & HTTPX (Automated unit & API testing)
- **Machine Learning**:
  - XGBoost 2.0+ (PV Generation regression)
  - TensorFlow / Keras 2.15+ (MobileNetV2 dust classification)
  - Scikit-learn (Model evaluation)

---

## 3. Project Folder Structure

```
RoofWiseBD Web/
├── frontend/                     # React 18 + TypeScript + Vite frontend
│   ├── src/
│   │   ├── components/common/    # Navbar, Footer, DemoBadge, ModelStatusBadge
│   │   ├── pages/                # Home, Assessment, Recommendation, Generation, Dust, Battery, Status
│   │   ├── services/api.ts       # Centralized REST API client
│   │   ├── types/index.ts        # TypeScript interfaces
│   │   ├── App.tsx               # Route configurations
│   │   └── main.tsx              # Application entry point
│   ├── package.json
│   ├── vite.config.ts
│   └── tailwind.config.js
├── backend/                      # FastAPI Python REST backend
│   ├── app/
│   │   ├── api/v1/               # Health, Solar, Bill, Generation, Dust, Battery, Status endpoints
│   │   ├── core/                 # Config, Bangladesh solar constants, BERC 2026 tariff engine
│   │   ├── database/             # SQLite connection & SQLAlchemy assessment models
│   │   ├── schemas/              # Pydantic request/response schemas
│   │   └── services/             # Sizing, tariff, battery, dust, rooftop, generation services
│   ├── tests/                    # Pytest test suite (12 automated tests)
│   ├── main.py                   # FastAPI server entry point
│   ├── requirements.txt          # Lightweight backend dependencies
│   └── requirements-ml.txt       # ML training dependencies for Python 3.12
├── data/
│   ├── raw/                      # Raw dataset directory structure
│   │   ├── bangladesh_pv/
│   │   ├── solnet/ (clean & dusty)
│   │   ├── nasa_power/
│   │   └── dhaka_rooftop/ (csv, shp, metadata, research)
│   ├── processed/
│   └── README.md
├── models/
│   ├── generation/               # XGBoost model weights (model.json / model.ubj)
│   ├── dust/                     # MobileNetV2 model weights (mobilenetv2_dust.keras)
│   └── README.md
├── docs/                         # Architecture, API specs, ML integration, Dataset audit plan
├── scripts/
│   └── audit_datasets.py         # Automated dataset verification CLI tool
├── README.md
├── .gitignore
└── .env.example
```

---

## 4. Installation & Startup Instructions (Windows)

### Prerequisites
- Node.js (v18+ or v24+)
- Python 3.12 or 3.14

### Step 1: Backend Setup
1. Open PowerShell in the project directory:
   ```powershell
   cd "f:\RoofWiseBD Web"
   ```
2. Install backend dependencies:
   ```powershell
   python -m pip install -r backend/requirements.txt
   ```
3. Run the automated backend test suite:
   ```powershell
   $env:PYTHONPATH="backend"
   python -m pytest backend/tests/
   ```
4. Start the FastAPI backend server:
   ```powershell
   $env:PYTHONPATH="backend"
   python backend/main.py
   ```
   The backend will start at **`http://localhost:8000`**.  
   Access interactive Swagger API documentation at **`http://localhost:8000/docs`**.

---

### Step 2: Frontend Setup
1. In a new PowerShell terminal, navigate to the frontend folder:
   ```powershell
   cd "f:\RoofWiseBD Web\frontend"
   ```
2. Install frontend packages:
   ```powershell
   npm.cmd install
   ```
3. Start the Vite development server:
   ```powershell
   npm.cmd run dev
   ```
   The web application will be accessible at **`http://localhost:5173`**.

---

## 5. Dataset Placement & Audit Protocol

1. Place downloaded raw datasets in their respective folders:
   - Bangladesh PV sensor CSVs $\rightarrow$ `data/raw/bangladesh_pv/`
   - Clean panel photos $\rightarrow$ `data/raw/solnet/clean/`
   - Dusty panel photos $\rightarrow$ `data/raw/solnet/dusty/`
   - NASA POWER CSV records $\rightarrow$ `data/raw/nasa_power/`
   - Dhaka rooftop polygons and metadata $\rightarrow$ `data/raw/dhaka_rooftop/`
2. Run the audit script to inspect file counts, columns, nulls, image resolutions, and corrupt files:
   ```powershell
   python scripts/audit_datasets.py
   ```

---

## 6. Machine Learning Model Integration

- **Generation Predictor**: Export your trained XGBoost regressor as `model.json` or `model.ubj` into `models/generation/`.
- **Dust Classifier**: Export your trained MobileNetV2 model as `mobilenetv2_dust.keras` into `models/dust/`.
- When weights are present, the backend services automatically detect them and switch from heuristic/baseline mode to live inference without modifying any code. Check status at **`/status`** in the web UI.

---

## 7. Legal & Engineering Disclaimers

- **Advisory Sizing**: RoofwiseBD provides preliminary engineering estimates. A formal civil structural survey and local utility sanction verification (DESCO, DPDC, BPDB, NESCO, BREB) are mandatory before physical installation.
- **SREDA 2025 Notice**: Inverter AC capacity must not exceed the sanctioned load for net-metered residential connections.
- **BERC 2026 Notice**: Savings calculations utilize the latest verified BERC 2026 tariff schedule (June 4, 2026 revision).
