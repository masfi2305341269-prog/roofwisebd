"""
RoofwiseBD Solar Panel Dust Detection Service
---------------------------------------------
Classifies solar panel surface condition (Clean vs Dusty).
Prepares MobileNetV2 Keras model integration and transparent fallback.
"""

from pathlib import Path
from typing import Tuple, Optional
from PIL import Image, ImageStat
from app.core.config import settings
from app.schemas.dust import DustPredictionResponse

def get_trained_dust_model():
    """Checks if trained MobileNetV2 weights exist in models/dust/"""
    model_dir = settings.MODELS_DIR / "dust"
    keras_path = model_dir / "mobilenetv2_dust.keras"
    h5_path = model_dir / "model.h5"
    
    if keras_path.exists():
        try:
            import tensorflow as tf
            model = tf.keras.models.load_model(str(keras_path))
            return model, "mobilenetv2_dust.keras"
        except Exception:
            return None, None
    elif h5_path.exists():
        try:
            import tensorflow as tf
            model = tf.keras.models.load_model(str(h5_path))
            return model, "model.h5"
        except Exception:
            return None, None
    return None, None

def analyze_panel_image(image_path: Path) -> DustPredictionResponse:
    # 1. Inspect image using PIL
    try:
        with Image.open(image_path) as im:
            width, height = im.size
            im_rgb = im.convert("RGB")
            stat = ImageStat.Stat(im_rgb)
            mean_brightness = sum(stat.mean) / 3.0
            variance = sum(stat.var) / 3.0
    except Exception as e:
        raise ValueError(f"Unable to read image file: {str(e)}")

    # 2. Check for trained MobileNetV2 model
    model, model_filename = get_trained_dust_model()

    if model:
        # Run actual Keras inference
        import numpy as np
        resized = im_rgb.resize((224, 224))
        arr = np.expand_dims(np.array(resized) / 255.0, axis=0)
        preds = model.predict(arr)
        score = float(preds[0][0])
        is_dusty = score > 0.5
        classification = "Dusty" if is_dusty else "Clean"
        model_score = round(score if is_dusty else 1.0 - score, 3)
        model_status = f"Trained MobileNetV2 Active ({model_filename})"
        is_demo = False
        explanation = "Classified via fine-tuned MobileNetV2 model trained on SolNet dataset."
    else:
        # Transparent Heuristic DEMO preview when weights are absent
        # Lower variance or high particulate haze indicates potential dust in demo mode
        classification = "Dusty" if (variance < 1400 or mean_brightness < 90) else "Clean"
        model_score = 0.82 if classification == "Dusty" else 0.88
        model_status = "Model Not Connected (SolNet weights pending)"
        is_demo = True
        explanation = (
            "Demonstration Heuristic: The trained MobileNetV2 model weights ('mobilenetv2_dust.keras') "
            "have not yet been placed in models/dust/. This output demonstrates the UI/API workflow only."
        )

    if classification == "Dusty":
        recommendation = (
            "Dust and particulate accumulation detected. Cleaning recommended within 3–5 days. "
            "Uncleaned dust in dry Bangladesh winter months can cause an 8% to 18% loss in solar energy harvest."
        )
        tip = (
            "Best Practice: Clean panels in the early morning (before 8:00 AM) or after sunset using a soft sponge, "
            "squeegee, and clean water. Avoid cleaning hot panels under direct sunlight to prevent thermal shock micro-cracks."
        )
    else:
        recommendation = (
            "The panel surface appears clean and unobstructed. Photovoltaic cells are operating at normal optical transmission."
        )
        tip = (
            "Routine Maintenance: Perform visual inspection once a month. Re-check after sandstorms, heavy construction nearby, "
            "or extended rainless periods."
        )

    return DustPredictionResponse(
        filename=image_path.name,
        image_width=width,
        image_height=height,
        classification=classification,
        model_score=model_score,
        model_status=model_status,
        cleaning_recommendation=recommendation,
        maintenance_tip=tip,
        is_demo=is_demo,
        explanation=explanation
    )
