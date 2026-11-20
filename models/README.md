# RoofwiseBD ML Models Directory

This directory stores trained model artifacts, weights, and feature metadata for RoofwiseBD's AI components.

## Subdirectories
- `generation/`: Trained XGBoost solar electricity generation prediction model (`model.json` or `model.ubj`) and scaler/feature configuration.
- `dust/`: Trained MobileNetV2 solar panel dust classification model (`mobilenetv2_dust.keras` or `model.h5`) and class label mappings.

## Dynamic Status Detection
The backend API (`GET /api/v1/models/status`) dynamically scans this directory:
- When trained weight files are placed here, the service loads them automatically into memory for live inference.
- When weights are not yet present, the system operates in transparent `not_connected` / `demo_baseline` mode with clearly labeled engineering heuristics and a UI DEMO badge.
