# RoofwiseBD REST API Documentation

Base URL: `http://localhost:8000/api/v1`  
Interactive Swagger UI: `http://localhost:8000/docs`  
ReDoc: `http://localhost:8000/redoc`

---

## 1. Health & System Status

### `GET /health`
Returns service availability status.
```json
{
  "status": "healthy",
  "service": "RoofwiseBD",
  "version": "1.0.0"
}
```

### `GET /models/status`
Returns status of connected ML models (`ml-1-generation` and `ml-2-dust`), weights file detection, and academic scope.

### `GET /datasets/status`
Returns real-time file counts, sizes in MB, and status for `data/raw/` subdirectories.

### `GET /system/status`
Consolidated report of backend runtime, active tariff schedules, model registry, and dataset audit readiness.

---

## 2. Solar Sizing & Assessment

### `POST /solar/recommendation`
Calculates optimal photovoltaic DC capacity ($kW_p$), inverter AC rating, panel layouts (550Wp), and SREDA 2025 net metering compliance.
- **Request Body**:
  ```json
  {
    "monthly_units_kwh": 350.0,
    "total_roof_area_sqft": 1200.0,
    "sanctioned_load_kw": 3.0,
    "division": "Dhaka",
    "roof_type": "concrete_flat",
    "shading_condition": "low"
  }
  ```
- **Response**: Returns `recommended_system`, `alternative_options` (Economical & Maximum Roof), `sreda_compliance`, and `tariff_breakdown`.

### `POST /solar/assessment`
Submits a complete 5-step user assessment, runs sizing calculation, and persists the record into the SQLite database.

---

## 3. Machine Learning Endpoints

### `POST /generation/predict`
Predicts monthly and diurnal solar electricity generation using regional NASA POWER irradiance data and decoupled XGBoost model interface.
- **Request Body**:
  ```json
  {
    "system_capacity_kwp": 3.5,
    "division": "Dhaka",
    "tilt_degrees": 23.0,
    "shading_factor": 0.95
  }
  ```

### `POST /dust/predict`
Uploads a solar panel photo to classify surface cleanliness as `Clean` or `Dusty` via MobileNetV2 architecture.
- **Content-Type**: `multipart/form-data`
- **Field**: `file` (JPG, PNG, or WEBP)

---

## 4. Electricity Bill & Battery Storage

### `POST /bill/analyze`
Accepts electricity bill image or PDF (DESCO, DPDC, BPDB, NESCO, BREB), extracts units, and validates against BERC 2026 tariff schedule.
- **Content-Type**: `multipart/form-data`
- **Fields**: `file`, `manual_units_kwh` (optional), `manual_bill_bdt` (optional).

### `POST /battery/recommendation`
Computes critical load, required backup energy, usable and nominal battery capacity, and a 24-hour dispatch schedule.
- **Request Body**:
  ```json
  {
    "appliances": [
      {"name": "Ceiling Fan", "wattage": 75, "quantity": 3, "daily_usage_hours": 8, "is_critical": true},
      {"name": "LED Bulb", "wattage": 15, "quantity": 5, "daily_usage_hours": 6, "is_critical": true}
    ],
    "required_backup_hours": 4.0,
    "battery_chemistry": "lifepo4",
    "custom_dod": 0.85,
    "custom_inverter_eff": 0.90
  }
  ```
