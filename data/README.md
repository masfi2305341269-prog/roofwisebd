# RoofwiseBD Datasets Directory

This directory stores raw and processed datasets for training and validating the RoofwiseBD AI models and rooftop analytics.

## Folder Organization

```
data/
  raw/
    bangladesh_pv/       # Bangladesh PV Monitoring Dataset (hourly solar generation time-series)
    solnet/              # SolNet Clean & Dusty Solar Panel Image Dataset
      clean/             # Images of clean solar panels
      dusty/             # Images of dust-accumulated solar panels
    nasa_power/          # NASA POWER Weather Dataset for Bangladesh coordinates (GHI, DNI, Temp, Wind)
    dhaka_rooftop/       # Dhaka Rooftop Solar Potential Dataset
      csv/               # Rooftop polygons, area, slope, and building height CSVs
      shp/               # Rooftop GIS shapefile zip archives
      metadata/          # Dataset metadata, dictionaries, and research notes
      research/          # Accompanying research papers and technical methodology
  processed/             # Cleaned, normalized, and feature-engineered datasets ready for model training
```

## Dataset Audit
Before training any ML model, run the audit script:
```powershell
python scripts/audit_datasets.py
```
This inspects file counts, column schemas, missing data, image dimensions, and flags any corrupted files without modifying original source files.
