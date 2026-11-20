# Solar Generation Prediction Model (XGBoost)

## Model Specification
- **Algorithm**: XGBoost Regressor
- **Target Variable**: Hourly solar power output (kW) / Daily generation (kWh)
- **Input Features (Planned)**:
  - Solar irradiance (GHI - Global Horizontal Irradiance in W/m²)
  - Ambient temperature (°C)
  - Relative humidity (%)
  - Wind speed (m/s)
  - Hour of day (0-23, cyclic sine/cosine encoded)
  - Month of year (1-12, cyclic sine/cosine encoded)
  - System capacity rating (kWp)
  - Tilt angle & azimuth
- **File Format Expected**: `model.json` or `xgboost_solar.ubj` along with `features.json`

## Status
Awaiting dataset audit and chronological split training. In the meantime, `generation_service.py` computes verified engineering baseline yields for Bangladesh's solar irradiation levels (4.5–5.0 PSH/day).
