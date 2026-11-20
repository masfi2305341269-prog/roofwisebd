"""
RoofwiseBD System & Model Status Service
----------------------------------------
Scans the filesystem to dynamically report ML model readiness, weights detection,
and raw dataset directory file statistics.
"""

from pathlib import Path
import sys
from app.core.config import settings
from app.core.tariffs import ACTIVE_SCHEDULE_KEY, BERC_TARIFF_SCHEDULES
from app.schemas.status import (
    SystemStatusResponse,
    ModelRegistryItem,
    DatasetRegistryItem
)

def inspect_system_status() -> SystemStatusResponse:
    models_dir = settings.MODELS_DIR
    data_dir = settings.DATA_DIR / "raw"
    
    # 1. Inspect ML 1: Solar Generation (XGBoost)
    gen_dir = models_dir / "generation"
    gen_file_json = gen_dir / "model.json"
    gen_file_ubj = gen_dir / "model.ubj"
    gen_found = gen_file_json.exists() or gen_file_ubj.exists()
    gen_weights_path = str(gen_file_json if gen_file_json.exists() else gen_file_ubj) if gen_found else None
    
    model_gen = ModelRegistryItem(
        id="ml-1-generation",
        name="Solar Electricity Generation Predictor",
        target_task="Predict hourly/daily solar generation in kWh",
        algorithm="XGBoost Regressor / NASA POWER Physics Baseline",
        framework="XGBoost 2.0+ / Scikit-learn",
        status="active_trained" if gen_found else "physics_baseline_active",
        model_file_expected="models/generation/model.json or model.ubj",
        model_file_found=gen_found,
        weights_path=gen_weights_path,
        input_features_planned=[
            "GHI_irradiance_wm2",
            "ambient_temp_c",
            "relative_humidity_pct",
            "wind_speed_ms",
            "hour_sin", "hour_cos",
            "month_sin", "month_cos",
            "capacity_kwp"
        ],
        academic_scope="Experimental PV monitoring benchmark with NASA POWER multi-year validation",
        limitations="Trained on experimental PV rig; not verified across all Bangladesh microclimates"
    )

    # 2. Inspect ML 2: Solar Dust Classifier (MobileNetV2)
    dust_dir = models_dir / "dust"
    dust_file_keras = dust_dir / "mobilenetv2_dust.keras"
    dust_file_h5 = dust_dir / "model.h5"
    dust_found = dust_file_keras.exists() or dust_file_h5.exists()
    dust_weights_path = str(dust_file_keras if dust_file_keras.exists() else dust_file_h5) if dust_found else None

    model_dust = ModelRegistryItem(
        id="ml-2-dust",
        name="Solar Panel Dust & Soiling Classifier",
        target_task="Classify panel cleanliness as Clean or Dusty from camera images",
        algorithm="MobileNetV2 (Transfer Learning)",
        framework="TensorFlow / Keras 2.15+",
        status="active_trained" if dust_found else "not_connected",
        model_file_expected="models/dust/mobilenetv2_dust.keras or model.h5",
        model_file_found=dust_found,
        weights_path=dust_weights_path,
        input_features_planned=["224x224x3 RGB image tensor"],
        academic_scope="SolNet Clean & Dusty Solar Panel Image Dataset (Classification only)",
        limitations="Performs whole-image condition classification; does not perform pixel-level dust segmentation"
    )

    # 3. Inspect Datasets in data/raw/
    def get_dir_stats(subfolder: Path):
        if not subfolder.exists():
            return False, 0, 0.0
        files = [f for f in subfolder.rglob("*") if f.is_file() and f.name != ".gitkeep"]
        total_size = sum(f.stat().st_size for f in files) / (1024 * 1024)
        return True, len(files), round(total_size, 2)

    datasets = []
    
    # Bangladesh PV
    pv_exists, pv_count, pv_size = get_dir_stats(data_dir / "bangladesh_pv")
    datasets.append(DatasetRegistryItem(
        id="dataset-pv",
        name="Bangladesh PV Monitoring Dataset",
        folder_path="data/raw/bangladesh_pv/",
        exists=pv_exists,
        file_count=pv_count,
        total_size_mb=pv_size,
        status="audited" if pv_count > 0 else "awaiting_files",
        description="Hourly solar generation time-series logs from Bangladesh test setup."
    ))

    # SolNet
    solnet_exists, solnet_count, solnet_size = get_dir_stats(data_dir / "solnet")
    datasets.append(DatasetRegistryItem(
        id="dataset-solnet",
        name="SolNet Clean & Dusty Image Dataset",
        folder_path="data/raw/solnet/",
        exists=solnet_exists,
        file_count=solnet_count,
        total_size_mb=solnet_size,
        status="audited" if solnet_count > 0 else "awaiting_files",
        description="Curated photographic image dataset of clean and dust-coated solar modules."
    ))

    # NASA POWER
    nasa_exists, nasa_count, nasa_size = get_dir_stats(data_dir / "nasa_power")
    datasets.append(DatasetRegistryItem(
        id="dataset-nasa",
        name="NASA POWER Solar & Weather Dataset",
        folder_path="data/raw/nasa_power/",
        exists=nasa_exists,
        file_count=nasa_count,
        total_size_mb=nasa_size,
        status="audited" if nasa_count > 0 else "awaiting_files",
        description="Daily & hourly agroclimatology GHI, DNI, temperature, and wind records for Bangladesh."
    ))

    # Dhaka Rooftop
    rooftop_exists, rooftop_count, rooftop_size = get_dir_stats(data_dir / "dhaka_rooftop")
    datasets.append(DatasetRegistryItem(
        id="dataset-dhaka-rooftop",
        name="Dhaka Rooftop Solar Potential Dataset",
        folder_path="data/raw/dhaka_rooftop/",
        exists=rooftop_exists,
        file_count=rooftop_count,
        total_size_mb=rooftop_size,
        status="audited" if rooftop_count > 0 else "awaiting_files",
        description="GIS polygon building attributes, roof slopes, and areas for urban Dhaka."
    ))

    overall = "Architecture Operational — Ready for Model Weights & Dataset Audit"

    return SystemStatusResponse(
        app_name=settings.PROJECT_NAME,
        version=settings.VERSION,
        python_runtime=f"Python {sys.version.split()[0]}",
        berc_tariff_schedule=BERC_TARIFF_SCHEDULES[ACTIVE_SCHEDULE_KEY]["version"],
        sreda_guideline_active="SREDA Net Metering Guideline 2025",
        models=[model_gen, model_dust],
        datasets=datasets,
        overall_readiness=overall
    )
