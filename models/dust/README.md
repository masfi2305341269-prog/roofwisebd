# Solar Panel Dust Detection Model (MobileNetV2)

## Model Specification
- **Architecture**: MobileNetV2 Transfer Learning
- **Input Dimensions**: 224 x 224 x 3 RGB images
- **Classes**:
  1. `Clean` (index 0): Unobstructed photovoltaic surface
  2. `Dusty` (index 1): Particle/dust accumulation requiring maintenance
- **Planned Format**: `mobilenetv2_dust.keras` or `model.h5`

## Status
Awaiting SolNet dataset audit and training. In the interim, `dust_service.py` provides image quality validation, file metadata inspection, and transparent heuristic analysis labeled with DEMO mode in the UI.
