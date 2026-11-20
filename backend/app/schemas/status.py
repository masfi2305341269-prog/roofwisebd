from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class ModelRegistryItem(BaseModel):
    id: str
    name: str
    target_task: str
    algorithm: str
    framework: str
    status: str # "not_connected", "active_trained", "demo_baseline"
    model_file_expected: str
    model_file_found: bool
    weights_path: Optional[str]
    input_features_planned: List[str]
    academic_scope: str
    limitations: str

class DatasetRegistryItem(BaseModel):
    id: str
    name: str
    folder_path: str
    exists: bool
    file_count: int
    total_size_mb: float
    status: str # "ready_for_audit", "empty_placeholder", "audited"
    description: str

class SystemStatusResponse(BaseModel):
    app_name: str
    version: str
    python_runtime: str
    berc_tariff_schedule: str
    sreda_guideline_active: str
    models: List[ModelRegistryItem]
    datasets: List[DatasetRegistryItem]
    overall_readiness: str
