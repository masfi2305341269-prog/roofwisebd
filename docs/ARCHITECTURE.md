# RoofwiseBD System Architecture Document

## 1. Overview
RoofwiseBD is a university Software Engineering project implementing an AI-powered rooftop solar assessment and energy recommendation platform tailored specifically to the residential solar energy needs and regulatory policies of Bangladesh.

## 2. Technical Stack
- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS, Lucide React, Recharts, React Router v6.
- **Backend**: Python 3.12+ (tested on Python 3.12 and 3.14), FastAPI, Pydantic v2, SQLAlchemy, SQLite, Pillow, NumPy.
- **Machine Learning**:
  - ML 1: XGBoost PV Electricity Generation Predictor with NASA POWER multi-year agroclimatology baseline.
  - ML 2: MobileNetV2 Solar Panel Dust & Soiling Classifier (Clean vs Dusty).
- **Standards & Policies**:
  - SREDA Net Metering Guideline 2025 (Inverter AC output capacity $\le$ Sanctioned load).
  - BERC 2026 Residential Electricity Tariff Schedule (incorporating June 4, 2026 tier revision).

## 3. High-Level System Architecture

```
+---------------------------------------------------------------------------------+
|                                React Frontend                                   |
|  [Home]  [Assessment Wizard]  [Dashboard]  [Gen AI]  [Dust AI]  [Battery]       |
+---------------------------------------------------------------------------------+
                                       |
                               REST API Requests
                                       |
+---------------------------------------------------------------------------------+
|                               FastAPI Backend                                   |
|   /api/v1/health          /api/v1/solar/recommendation   /api/v1/generation/predict|
|   /api/v1/dust/predict    /api/v1/battery/recommendation /api/v1/models/status    |
+---------------------------------------------------------------------------------+
          |                      |                   |                  |
   +--------------+      +--------------+     +--------------+   +--------------+
   |   Tariffs    |      |   Rooftop    |     |  XGBoost ML1 |   | MobileNetV2  |
   | Engine (BERC)|      |   Service    |     | & NASA POWER |   |   Dust ML2   |
   +--------------+      +--------------+     +--------------+   +--------------+
          |                      |                   |                  |
          +----------------------+-------------------+------------------+
                                       |
                              SQLite Database (roofwise.db)
```

## 4. Key Calculation Engines

### 4.1. BERC 2026 Progressive Slab Tariff Calculation
Electricity bills and monetary savings are calculated using the official progressive multi-tier formula:
- **Lifeline (0–50 kWh)**: Tk 4.63 / kWh
- **Step 1 (0–75 kWh)**: Tk 5.26 / kWh
- **Slab 2 (76–200 kWh)**: Tk 8.50 / kWh
- **Slab 3 (201–300 kWh)**: Tk 9.10 / kWh
- **Slab 4 (301–400 kWh)**: Tk 9.62 / kWh
- **Slab 5 (401–600 kWh)**: Tk 15.01 / kWh
- **Slab 6 (>600 kWh)**: Tk 17.03 / kWh
- Demand charge: Sanctioned load ($kW$) $\times$ Tk 35 / kW
- Utility VAT: 5% on taxable charges.

### 4.2. SREDA Net Metering Guideline 2025 Compliance
Under Section 5 of the 2025 guideline:
$$\text{Inverter AC Capacity } (kW_{AC}) \le \text{Customer Sanctioned Load } (kW_{sanctioned})$$
For residential installations, RoofwiseBD verifies whether:
1. $kW_{AC} \le kW_{sanctioned}$ (Compliant)
2. $kW_{AC} > 10\text{ kW}$ (Three-phase distribution infrastructure and utility sanction check required).

### 4.3. Usable Rooftop Spatial Analysis
$$\text{Usable Area} = \text{Gross Roof Area} \times R_{usable}$$
Where $R_{usable} = 0.70$ for Flat RCC (allowing 30% for parapet walls, staircase headrooms, and water tanks), and $0.78$ for sloped tin shed roofs.

### 4.4. Battery Optimization
$$\text{Backup Energy (Wh)} = \text{Critical Load (Watts)} \times \text{Backup Hours} \times 1.15$$
$$\text{Usable Battery Capacity (kWh)} = \frac{\text{Backup Energy (Wh)}}{\eta_{inverter} \times 1000}$$
$$\text{Nominal Battery Capacity (kWh)} = \frac{\text{Usable Capacity (kWh)}}{\text{Depth of Discharge (DoD)}}$$
Where $DoD = 0.85$ for LiFePO4 and $0.50$ for Lead-Acid.
