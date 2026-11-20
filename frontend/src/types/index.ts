export interface LocationInfo {
  division: string;
  district: string;
  area?: string;
  latitude?: number;
  longitude?: number;
}

export interface ConsumptionInfo {
  monthly_units_kwh: number;
  billing_period_days: number;
  bill_amount_bdt?: number;
  sanctioned_load_kw: number;
  consumer_category: string;
}

export interface RooftopInfo {
  total_area_sqft: number;
  usable_area_sqft?: number;
  roof_type: 'concrete_flat' | 'tin_shed' | 'tiled';
  shading_condition: 'none' | 'low' | 'medium' | 'heavy';
  orientation?: string;
  tilt_degrees?: number;
  roof_image_url?: string;
}

export interface SystemTier {
  tier_name: string;
  dc_capacity_kwp: number;
  inverter_ac_kw: number;
  panel_count: number;
  panel_wattage_wp: number;
  required_usable_area_sqft: number;
  daily_generation_kwh: number;
  monthly_generation_kwh: number;
  annual_generation_kwh: number;
  consumption_offset_pct: number;
  est_turnkey_cost_bdt_min: number;
  est_turnkey_cost_bdt_max: number;
  est_monthly_savings_bdt: number;
  est_annual_savings_bdt: number;
  est_payback_years_min: number;
  est_payback_years_max: number;
  sreda_ac_compliant: boolean;
  sreda_note: string;
}

export interface SredaComplianceStatus {
  is_compliant: boolean;
  sanctioned_load_kw: number;
  recommended_inverter_ac_kw: number;
  ac_to_sanctioned_ratio: number;
  requires_three_phase: boolean;
  utility_approval_required: boolean;
  rule_summary: string;
  advisory_text: string;
}

export interface SolarRecommendationResponse {
  recommended_system: SystemTier;
  alternative_options: SystemTier[];
  sreda_compliance: SredaComplianceStatus;
  tariff_breakdown: {
    schedule_version: string;
    units_kwh: number;
    energy_charge_bdt: number;
    demand_charge_bdt: number;
    meter_rent_bdt: number;
    vat_bdt: number;
    total_bill_bdt: number;
    slab_breakdown: Array<{
      slab: string;
      units: number;
      rate: number;
      cost_bdt: number;
    }>;
  };
  division: string;
  monthly_psh_avg: number;
  disclaimer: string;
}

export interface MonthlyGeneration {
  month_name: string;
  month_index: number;
  psh: number;
  generation_kwh: number;
}

export interface GenerationPredictionResponse {
  system_capacity_kwp: number;
  division: string;
  annual_generation_kwh: number;
  average_daily_generation_kwh: number;
  monthly_breakdown: MonthlyGeneration[];
  hourly_sample_profile: Array<{
    hour: number;
    time_label: string;
    generation_kw: number;
    energy_kwh: number;
  }>;
  model_status: string;
  model_name: string;
  is_demo: boolean;
  data_source: string;
  prediction_explanation: string;
  limitations_notice: string;
}

export interface DustPredictionResponse {
  filename: string;
  image_width: number;
  image_height: number;
  classification: 'Clean' | 'Dusty' | 'Indeterminate';
  model_score: number | null;
  model_status: string;
  cleaning_recommendation: string;
  maintenance_tip: string;
  is_demo: boolean;
  explanation: string;
}

export interface ApplianceItem {
  name: string;
  wattage: number;
  quantity: number;
  daily_usage_hours: number;
  is_critical: boolean;
}

export interface BatteryDispatchHour {
  hour: number;
  grid_available: boolean;
  solar_available: boolean;
  load_watts: number;
  battery_soc_pct: number;
  mode: string;
}

export interface BatteryOptimizationResponse {
  total_critical_load_watts: number;
  total_appliance_count: number;
  required_backup_energy_wh: number;
  usable_capacity_required_kwh: number;
  recommended_nominal_capacity_kwh: number;
  battery_chemistry: string;
  dod_used: number;
  inverter_eff_used: number;
  est_battery_cost_bdt_min: number;
  est_battery_cost_bdt_max: number;
  schedule_profile: BatteryDispatchHour[];
  optimization_explanation: string;
  preliminary_notice: string;
}

export interface ModelRegistryItem {
  id: string;
  name: string;
  target_task: string;
  algorithm: string;
  framework: string;
  status: string;
  model_file_expected: string;
  model_file_found: boolean;
  weights_path: string | null;
  input_features_planned: string[];
  academic_scope: string;
  limitations: string;
}

export interface DatasetRegistryItem {
  id: string;
  name: string;
  folder_path: string;
  exists: boolean;
  file_count: number;
  total_size_mb: number;
  status: string;
  description: string;
}

export interface SystemStatusResponse {
  app_name: string;
  version: string;
  python_runtime: string;
  berc_tariff_schedule: string;
  sreda_guideline_active: string;
  models: ModelRegistryItem[];
  datasets: DatasetRegistryItem[];
  overall_readiness: string;
}

export interface User {
  id: number;
  email: string;
  full_name: string;
  phone?: string;
  address?: string;
  role: 'user' | 'admin';
  is_active: boolean;
  email_verified: boolean;
  created_at: string;
  auth_user_id?: string;
}

export interface AdminUserItem extends User {
  assessment_count: number;
}

export interface AdminStats {
  total_users: number;
  active_users: number;
  total_assessments: number;
  guest_assessments: number;
  user_assessments: number;
  total_capacity_kwp: number;
  total_monthly_savings_bdt: number;
}

export interface SavedAssessmentRecord {
  id: number;
  created_at: string;
  user_id?: number;
  division: string;
  district: string;
  area?: string;
  monthly_units_kwh: number;
  billing_period_days: number;
  bill_amount_bdt?: number;
  sanctioned_load_kw: number;
  consumer_category: string;
  total_area_sqft: number;
  usable_area_sqft: number;
  roof_type: string;
  shading_condition: string;
  orientation?: string;
  tilt_degrees?: number;
  recommended_capacity_kwp: number;
  recommended_inverter_ac_kw: number;
  panel_count: number;
  daily_generation_kwh: number;
  monthly_generation_kwh: number;
  annual_generation_kwh: number;
  monthly_savings_bdt: number;
  estimated_payback_years: number;
  sreda_compliant: boolean;
  notes?: string;
}

