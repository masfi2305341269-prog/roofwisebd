# RoofwiseBD Dataset Audit Plan

## 1. Objective
Ensure academic integrity and statistical quality of downloaded datasets prior to model training. All audits are non-destructive and preserve original source archives.

## 2. Audit Tool
The automated audit tool is located at:
```powershell
python scripts/audit_datasets.py
```
This generates `data/dataset_audit_report.json` with detailed summaries.

## 3. Audit Checkpoints

### 3.1. Bangladesh PV Monitoring Dataset (`data/raw/bangladesh_pv/`)
- **Row and Column Inspection**: Audit CSV column names, total records, sampling frequency (1-minute, 5-minute, or 15-minute).
- **Missing Value Rate**: Count null values across sensor fields.
- **Timestamp Coverage**: Check for missing hours or days in the continuous time-series.
- **Physical Feasibility**: Verify that solar power output is zero during night hours (19:00 to 05:00) to ensure sensor offset calibration.

### 3.2. SolNet Clean and Dusty Dataset (`data/raw/solnet/`)
- **Class Balance**: Measure count of clean vs dusty images.
- **Resolution & Aspect Ratios**: Inspect dimensions across image files.
- **Corrupt File Detection**: Attempt PIL image verification on each file to flag truncated or unreadable files.
- **Duplicate Detection**: Check MD5 hashes to identify redundant images.

### 3.3. NASA POWER Agroclimatology (`data/raw/nasa_power/`)
- **Spatial Coverage**: Confirm coordinates match Bangladesh divisional capitals.
- **Variables Present**: Verify `ALLSKY_SFC_SW_DWN` (GHI), `T2M` (Temperature), `RH2M` (Relative Humidity), and `WS2M` (Wind Speed).

### 3.4. Dhaka Rooftop Solar Potential Dataset (`data/raw/dhaka_rooftop/`)
- **Format Inspection**: Verify CSV attributes (building ID, polygon area, height, slope) and shapefile archive integrity.
