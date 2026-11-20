# RoofwiseBD — Comprehensive Dataset Audit Report

**Date of Audit**: November 16, 2026  
**Auditor**: RoofwiseBD Data & Machine Learning Engineering Team  
**Dataset Source Root**: `E:\RoofwiseBD`  
**Application Project Root**: `F:\RoofWiseBD Web`  
**Audit Manifest**: [`data/dataset_manifest.csv`](file:///f:/RoofWiseBD%20Web/data/dataset_manifest.csv)  
**Detailed Audit JSON**: [`data/dataset_audit_report.json`](file:///f:/RoofWiseBD%20Web/data/dataset_audit_report.json)

---

## Executive Summary of Audit Findings

| Dataset Component | Physical Files | Actual Observation Count | Data Size | Data Health & Quality | Integrity Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Bangladesh PV Monitoring** | 295 CSV files | 408,059 rows (30s intervals) | 117.12 MB | Zero duplicate rows. High sensor completeness. Minor nulls in pressure/wind. | **Verified Complete (2020)** |
| **SolNet Clean Images** | 722 JPG images | 722 images (713 unique MD5) | 1,888.60 MB | Zero corrupt files. 9 exact MD5 duplicates. 300 web-compressed `11zon` derivatives. | **Verified (Deduplication Req.)** |
| **SolNet Dusty Images** | 718 JPG images | 718 images (635 unique MD5) | 1,760.25 MB | Zero corrupt files. 83 exact MD5 duplicates. 300 web-compressed `11zon` derivatives. | **Verified (Deduplication Req.)** |
| **NASA POWER Hourly** | 1 CSV file | 61,728 hourly rows | 2.04 MB | 2019-11-01 to 2026-11-15. Year 2020 has 8,784 rows with 0 missing values. | **Verified Complete (Dhaka Coord.)** |
| **Dhaka Rooftop Attributes** | 1 CSV file | 632,745 building polygons | 127.63 MB | Zero duplicates. Complete spatial & yield fields. Unverified price field is 100% NaN. | **Verified Complete** |
| **Dhaka Rooftop Shapefiles** | 4 files (`.shp`, `.shx`, `.dbf`, `.prj`) | Complete GIS vector layer | 479.36 MB | EPSG:32646 (WGS 1984 UTM Zone 46N). High-resolution rooftop footprints. | **Verified & Extracted** |
| **Dhaka Rooftop Metadata** | 1 XLSX workbook | 3 sheets, 22 attribute rows | 10.4 KB | Provenance documented: WorldView-3 imagery (2019). Full data dictionary. | **Verified Complete** |
| **Dhaka Rooftop Research** | 1 PDF document | 24 pages | 1.77 MB | NEO / World Bank technical study (February 2022). | **Verified Complete** |

---

## 1. Bangladesh PV Monitoring Dataset Audit

- **Original Archive**: `E:\RoofwiseBD\A comprehensive dataset for monitoring photovoltai.zip` (51.3 MB, preserved)
- **Extracted Location**: `E:\RoofwiseBD\A comprehensive dataset for monitoring photovoltai\A comprehensive dataset for monitoring photovoltai\Solar Dataset\Solar Dataset\`
- **Project Junction**: `F:\RoofWiseBD Web\data\raw\bangladesh_pv\`
- **Total CSV Files**: **295 files** across 12 monthly directories:
  - `1. JANUARY`: 29 CSVs
  - `2. FEBRUARY`: 23 CSVs
  - `3. MARCH`: 26 CSVs
  - `4. APRIL`: 25 CSVs
  - `5. MAY`: 24 CSVs
  - `6. JUNE`: 24 CSVs
  - `7. JULY`: 25 CSVs
  - `8. AUGUST`: 24 CSVs
  - `9. SEPTEMBER`: 23 CSVs
  - `10. OCTOBER`: 25 CSVs
  - `11. NOVEMBER`: 24 CSVs
  - `12. DECEMBER`: 23 CSVs
- **Total Observation Count**: **408,059 continuous sensor records**
- **Exact Duplicate Rows**: **0 rows** across all 295 CSV files.
- **Unique Calendar Dates**: **293 days** in the year 2020.
- **Sampling Frequency**: **Every 30 seconds** (e.g. `06:26:54 AM`, `06:27:24 AM`, `06:27:54 AM`).

### Master Columns (25 Verified Columns)
```
1.  Date                             (String: YYYY-MM-DD or M/D/YYYY)
2.  Time                             (String: H:MM:SS AM/PM)
3.  Clean Temperature                (Float: Ambient/Module surface °C)
4.  Dusty Temperature                (Float: Soiled Module surface °C)
5.  Clean Current                    (Float: Module short-circuit/operating Amperes)
6.  Dusty Current                    (Float: Soiled Module Amperes)
7.  Wind Speed                       (Float: Local anemometer m/s)
8.  Humidity                         (Float: Relative humidity %)
9.  Air Pressure                     (Float: Barometric pressure hPa/mbar)
10. Tr(Hour)                         (Float: Decimal hour of the day)
11. Ideal_Irradiance                 (Float: Clear-sky solar model W/m²)
12. Clean_Module_Irradiance          (Float: Measured pyranometer irradiance on clean module W/m²)
13. Dusty_Module_Irradiance          (Float: Measured effective irradiance on dusty module W/m²)
14. Clean_Module_Cumulative_Energy   (Float: Integrated Wh energy from clean module)
15. Dusty_Module_Cumulative_Energy   (Float: Integrated Wh energy from dusty module)
16. Clean_Temperature(K)             (Float: Clean module temperature in Kelvin)
17. Dusty_Temperature(K)             (Float: Dusty module temperature in Kelvin)
18. Clean_VOC                        (Float: Clean open-circuit voltage Volts)
19. Dusty_VOC                        (Float: Dusty open-circuit voltage Volts)
20. Clean_pmp                        (Float: Clean maximum peak power output Watts)
21. Dusty_pmp                        (Float: Dusty maximum peak power output Watts)
22. Clean_Panel_Point_Energy         (Float: Incremental instantaneous energy Wh)
23. Dusty_Panel_Point_Energy         (Float: Incremental instantaneous energy Wh)
24. Clean_Panel_Total_Energy         (Float: Cumulative total energy kWh)
25. Dusty_Panel_Total_Energy         (Float: Cumulative total energy kWh)
```

### Missing Value Analysis
- `Air Pressure`: 1,560 null values (0.38% of records, restricted to a few sensor restart intervals).
- `Wind Speed`: 8 null values (0.002%).
- `Humidity`: 6 null values (0.001%).
- `Date`: 1 null value (0.0002%).
- **All Core Electrical & Solar Irradiance Columns**: `Clean Current`, `Dusty Current`, `Clean_VOC`, `Dusty_VOC`, `Clean_pmp`, `Dusty_pmp`, `Clean_Module_Irradiance`, and `Clean Temperature` contain **ZERO missing values (100% complete)**.

### Sensor & Test Bench Scope
- The experimental rig consists of two identical paired 20W polycrystalline solar panels (one regularly cleaned, one naturally accumulating dust) installed in Dhaka, Bangladesh.
- Operating outputs range between 0.0W and ~18.5W peak power (`Clean_pmp`).

---

## 2. SolNet Image Dataset Audit (Clean & Dusty)

- **Original Clean Archive**: `E:\RoofwiseBD\clean-20261116T122047Z-1-001.zip` (1,888.96 MB, preserved)
- **Original Dusty Archive**: `E:\RoofwiseBD\dirty-20261116T123005Z-1-001.zip` (1,760.54 MB, preserved)
- **Extracted Source Directories**:
  - Clean: `E:\RoofwiseBD\clean-20261116T122047Z-1-001\clean\`
  - Dusty: `E:\RoofwiseBD\dirty-20261116T123005Z-1-001\dirty\`
- **Project Junctions**:
  - `F:\RoofWiseBD Web\data\raw\solnet\clean\`
  - `F:\RoofWiseBD Web\data\raw\solnet\dusty\`
- **Total Images**: **1,440 image files**
- **File Formats**: **100% JPEG (`.jpg`)** across both folders.
- **Corrupt File Count**: **0 corrupt files** (All 1,440 images successfully opened and verified with PIL).

### Class Distribution & Balance
- **Clean Images**: 722 images (50.1%) — Total size: 1,888.60 MB
- **Dusty Images**: 718 images (49.9%) — Total size: 1,760.25 MB
- **Balance**: Exceptionally balanced binary dataset ($\approx 1:1$).

### Resolutions and Aspect Ratios
- Primary resolution: **4624 × 3468 pixels** (4:3 aspect ratio, ~16 Megapixel smartphone camera sensor):
  - Clean: 465 images at 4624×3468, 59 images at 3468×4624 (portrait orientation).
  - Dusty: 447 images at 4624×3468, 49 images at 3468×4624 (portrait orientation).
- Secondary resolutions: 3264×2448, 3942×3377, 4072×2910.

### Critical Integrity Findings: Duplicates & Synthetic Derivatives
1. **Exact Byte-for-Byte MD5 Duplicates**:
   - Clean folder: **9 exact duplicate pairs** (e.g. `20210917_151334.jpg` and `20210917_151334(1).jpg`).
   - Dusty folder: **83 exact duplicate pairs** (e.g. `20210916_131020(0).jpg` and `20210916_131020(0)(1).jpg`).
2. **Web-Compressed `11zon` Derivatives**:
   - In both Clean and Dusty folders, exactly **300 images** in each class contain `_11zon` in their filename.
   - These represent downscaled/re-compressed copies produced via an image compression web tool (11zon) from identical base photos.
3. **Data Leakage Risk**:
   - Applying a naive random train/val/test split would place near-duplicate and exact-duplicate versions of the same panel capture into both training and validation sets, producing artificially high validation accuracy.
   - **Remediation**: Grouped splitting based on base filename timestamp (e.g. grouping `20210916_131020*` together) or strict MD5/perceptual hash deduplication is required prior to model training.

---

## 3. NASA POWER Agroclimatology Dataset Audit

- **File Path**: `F:\RoofWiseBD Web\data\raw\nasa_power\POWER_Point_Hourly_20191101_20261115_023d81N_090d41E_UTC.csv`
- **File Size**: 2.04 MB
- **Total Rows**: **61,728 hourly records**
- **Location Coordinates**: Latitude **23.8103° N**, Longitude **90.4125° E** (Dhaka, Bangladesh)
- **Elevation**: 10.06 meters
- **Temporal Range**: **November 1, 2019 00:00 UTC** through **November 15, 2026 23:00 UTC**
- **Timezone**: UTC (Bangladesh Standard Time is UTC + 6 hours)
- **Sampling Frequency**: Hourly (24 readings per day)

### Columns & Parameters Present
```
1. YEAR               (Integer: 2019 - 2026)
2. MO                 (Integer: 1 - 12)
3. DY                 (Integer: 1 - 31)
4. HR                 (Integer: 0 - 23 UTC)
5. ALLSKY_SFC_SW_DWN  (Float: CERES SYN1deg Surface Shortwave Downward Irradiance Wh/m²)
6. T2M                (Float: MERRA-2 Temperature at 2 Meters °C)
7. RH2M               (Float: MERRA-2 Relative Humidity at 2 Meters %)
8. WS10M              (Float: MERRA-2 Wind Speed at 10 Meters m/s)
```

### Missing Value Analysis
- Missing value flag in raw NASA file: `-999.0`
- `ALLSKY_SFC_SW_DWN`: 1,824 missing records (restricted entirely to recent unfinalized months in late 2026).
- `T2M`, `RH2M`, `WS10M`: 24 missing records.
- **Year 2020 Overlap**: For the entirety of 2020 (corresponding to the Bangladesh PV dataset), there are **8,784 hourly rows with ZERO missing values (-999 count = 0)**.

### Geographical Limitation Notice
- This specific CSV file corresponds exclusively to **Dhaka coordinates (23.81N, 90.41E)**.
- While the RoofwiseBD frontend and backend incorporate multi-year monthly PSH baselines for all 8 administrative divisions (Dhaka, Chattogram, Rajshahi, Khulna, Barishal, Sylhet, Rangpur, Mymensingh), hourly granular training data is currently downloaded for Dhaka.

---

## 4. Dhaka Rooftop Solar Potential Dataset Audit

- **Original Shapefile Archive**: `E:\RoofwiseBD\dhaka_rooftop_potential.zip` (45.17 MB, preserved)
- **Extracted Shapefiles**: `F:\RoofWiseBD Web\data\raw\dhaka_rooftop\shp\`
- **Attributes CSV**: `F:\RoofWiseBD Web\data\raw\dhaka_rooftop\csv\dhaka_citycenter_greaterregion_attributes.csv` (127.63 MB)
- **Metadata Workbook**: `F:\RoofWiseBD Web\data\raw\dhaka_rooftop\metadata\dhaka_result_metadata.xlsx` (10.4 KB)
- **Research Technical Report**: `F:\RoofWiseBD Web\data\raw\dhaka_rooftop\research\dhaka_rooftop_potential_neo.pdf` (1.77 MB)

### 4.1. Attributes CSV Audit
- **Total Records**: **632,745 building polygons** across Greater Dhaka.
- **Columns (14)**:
  `OBJECTID, uuid, City, Surface_area, Potential_installable_area, Peak_installable_capacity, Energy_potential_per_year, Assumed_building_type, Estimated_tilt, Estimated_building_height, Estimated_capacity_factor, Unit_installation_price, Date_added, Comment`
- **Duplicate Rows**: **0 duplicates** (632,745 unique building UUIDs).
- **Missing Value Breakdown**:
  - `OBJECTID`, `uuid`, `City`, `Surface_area`, `Potential_installable_area`, `Peak_installable_capacity`, `Energy_potential_per_year`, `Assumed_building_type`, `Estimated_tilt`, `Date_added`: **0 missing values (100% complete)**.
  - `Estimated_building_height`: 5,255 nulls (0.83%).
  - `Estimated_capacity_factor`: 8,936 nulls (1.41%).
  - `Unit_installation_price`: 632,745 nulls (100% null — installation pricing was unverified at dataset publication).
  - `Comment`: 632,745 nulls (100% null).

### 4.2. Building Type Distribution in Greater Dhaka
- `multi-family residential`: **429,462 buildings (67.87%)**
- `single family residential`: **119,767 buildings (18.93%)**
- `commercial`: **31,709 buildings (5.01%)**
- `industrial`: **27,540 buildings (4.35%)**
- `public`: **15,623 buildings (2.47%)**
- `small commercial`: **8,644 buildings (1.37%)**

### 4.3. Spatial & Energy Potential Statistics
- **Surface Area ($m^2$)**: Mean = 158.11 $m^2$ (~1,701 sq ft), Median = 109.38 $m^2$ (~1,177 sq ft), Max = 42,641 $m^2$.
- **Potential Installable Area ($m^2$)**: Mean = 82.22 $m^2$ (Overall usable spatial ratio $\approx 52\%$).
- **Peak Installable Capacity ($kW_p$)**: Mean = 15.96 $kW_p$, Median = 11.04 $kW_p$.
- **Yearly Energy Potential**: Mean = 20,411 kWh/year per building.

### 4.4. Shapefile Layer Technical Details
- Extracted files:
  - `Dhaka_rooftop_potential.shp` (59.22 MB)
  - `Dhaka_rooftop_potential.dbf` (416.90 MB)
  - `Dhaka_rooftop_potential.shx` (3.24 MB)
  - `Dhaka_rooftop_potential.prj` (0.01 MB)
- **Geometry Type**: Polygon (Vector building footprints)
- **Coordinate Reference System (CRS)**: `PROJCS["WGS_1984_UTM_Zone_46N", ...]` (EPSG:32646), Projected Transverse Mercator with meters as distance unit.

### 4.5. Provenance & Research Methodology
- Extracted from `dhaka_rooftop_potential_neo.pdf` (24 pages, published February 2022 by NEO - Network for Earth Observation):
  - **Source Imagery**: Very-high-resolution (VHR) **WorldView-3 satellite stereo imagery** acquired in 2019.
  - **3D Surface Extraction**: Normalized Digital Surface Model (nDSM) and slope/tilt rasterization derived from satellite stereo pairs.
  - **Solar Yield Engine**: Yields calculated via Solargis / pvPlanner models for Bangladesh.
  - **Important Limitation**: While individual building polygons and estimated slopes are provided, raw labeled pixel segmentation masks are not included. Thus, claims of training a U-Net satellite segmentation model on this dataset are unsupported; it serves as a spatial reference lookup and building distribution benchmark.
