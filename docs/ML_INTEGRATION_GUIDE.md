# RoofwiseBD Machine Learning Integration Guide

This guide details how to train, evaluate, and integrate the machine learning models into the RoofwiseBD production services.

## Python Runtime & Environment Setup
To ensure compatibility with TensorFlow/Keras and XGBoost wheels:
1. Create a dedicated virtual environment with Python 3.12:
   ```powershell
   python -m venv .venv-ml
   .venv-ml\Scripts\activate
   pip install -r backend/requirements-ml.txt
   ```

---

## 1. ML 1 — Solar Generation Prediction (XGBoost)

### Dataset Sources
1. `data/raw/bangladesh_pv/`: Experimental photovoltaic sensor logs.
2. `data/raw/nasa_power/`: Hourly solar irradiance (GHI, DNI), ambient temperature, relative humidity, and wind speed for Bangladesh coordinates.

### Preprocessing Protocol & Data Leakage Prevention
- **Resampling**: Align timestamp intervals between PV sensor logs and NASA POWER hourly records using backward/forward time-window matching.
- **Leakage Prevention**: Never use actual inverter voltage, current, or energy generated as input features when forecasting future generation.
- **Chronological Splitting**: Use chronological train/validation/test splits (e.g. Train on Months 1–8, Validation on Months 9–10, Test on Months 11–12). Do NOT use random shuffle splitting on time-series data.

### Model Export & Deployment
After training XGBoost regressor, save the model artifact to:
```
models/generation/model.json
```
or
```
models/generation/model.ubj
```
The backend `generation_service.py` dynamically checks for this file on startup and will switch from the physics baseline to live inference automatically.

---

## 2. ML 2 — Solar Dust Detection (MobileNetV2)

### Dataset Source
- `data/raw/solnet/clean/`: Images of clean panel surfaces.
- `data/raw/solnet/dusty/`: Images with particulate dust, sand, and pollen accumulation.

### Architecture & Transfer Learning
- Base Model: `tf.keras.applications.MobileNetV2(weights='imagenet', include_top=False, input_shape=(224, 224, 3))`
- Global Average Pooling 2D $\rightarrow$ Dense(128, activation='relu') $\rightarrow$ Dropout(0.3) $\rightarrow$ Dense(1, activation='sigmoid').
- Target: Binary classification (0 = Clean, 1 = Dusty). Note that this performs whole-image condition classification, NOT pixel-level dust segmentation.

### Model Export & Deployment
Save the fine-tuned model to:
```
models/dust/mobilenetv2_dust.keras
```
The backend `dust_service.py` will load this model and predict probabilities dynamically.
