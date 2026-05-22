"""Per-brand configuration: dataset, colors, model SQL mapping."""
from __future__ import annotations

_KIA_MODEL_SQL = """
CASE
    WHEN UPPER(TRIM(model_requested)) IN ('', 'NULL', 'KIA') OR model_requested IS NULL THEN 'Otros'
    WHEN UPPER(TRIM(model_requested)) = 'PICANTO'            THEN 'PICANTO'
    WHEN UPPER(TRIM(model_requested)) = 'SOLUTO'             THEN 'SOLUTO'
    WHEN UPPER(TRIM(model_requested)) IN ('K3-SEDAN','K3 SEDAN')   THEN 'K3 SEDAN'
    WHEN UPPER(TRIM(model_requested)) IN ('K3-CROSS','K3 CROSS')   THEN 'K3 CROSS'
    WHEN UPPER(TRIM(model_requested)) = 'CARNIVAL HEV'       THEN 'CARNIVAL HEV'
    WHEN UPPER(TRIM(model_requested)) IN ('SONET PE','SONET')       THEN 'SONET PE'
    WHEN UPPER(TRIM(model_requested)) IN ('SELTOS PE','SELTOS')     THEN 'SELTOS PE'
    WHEN UPPER(TRIM(model_requested)) = 'CARENS'             THEN 'CARENS'
    WHEN UPPER(TRIM(model_requested)) IN ('SPORTAGE PE','SPORTAGE') THEN 'SPORTAGE PE'
    WHEN UPPER(TRIM(model_requested)) = 'SPORTAGE PE HEV'    THEN 'SPORTAGE PE HEV'
    WHEN UPPER(TRIM(model_requested)) IN ('SORENTO','SORRENTO')     THEN 'SORENTO'
    WHEN UPPER(TRIM(model_requested)) = 'SORENTO HEV'        THEN 'SORENTO HEV'
    WHEN UPPER(TRIM(model_requested)) = 'EV5'                THEN 'EV5'
    WHEN UPPER(TRIM(model_requested)) = 'K2700'              THEN 'K2700'
    WHEN UPPER(TRIM(model_requested)) = 'TASMAN'             THEN 'TASMAN'
    WHEN UPPER(TRIM(model_requested)) = 'NIRO'               THEN 'NIRO'
    WHEN UPPER(TRIM(model_requested)) = 'EV9'                THEN 'EV9'
    ELSE 'Otros'
END
"""

# Generic fallback — uses raw model_requested, just trims whitespace
_DEFAULT_MODEL_SQL = "COALESCE(NULLIF(TRIM(model_requested), ''), 'Otros')"

# Keys are used as URL paths: /kia, /bmw, etc.
BRANDS: dict[str, dict] = {
    "kia": {
        "dataset":   "garden_kia",
        "title":     "KIA",
        "subtitle":  "Panorama en detalle de Leads",
        "gradient":  "linear-gradient(135deg, #7F0000 0%, #B71C1C 40%, #E53935 100%)",
        "accent":    "#C62828",
        "model_sql": _KIA_MODEL_SQL,
    },
    "bmw": {
        "dataset":   "garden_bmw",
        "title":     "BMW",
        "subtitle":  "Panorama en detalle de Leads",
        "gradient":  "linear-gradient(135deg, #0D1B2A 0%, #1B4F72 50%, #2980B9 100%)",
        "accent":    "#1565C0",
        "model_sql": _DEFAULT_MODEL_SQL,
    },
    "chery": {
        "dataset":   "garden_chery",
        "title":     "Chery",
        "subtitle":  "Panorama en detalle de Leads",
        "gradient":  "linear-gradient(135deg, #880000 0%, #C0392B 50%, #E74C3C 100%)",
        "accent":    "#C0392B",
        "model_sql": _DEFAULT_MODEL_SQL,
    },
    "chevrolet": {
        "dataset":   "garden_chevrolet",
        "title":     "Chevrolet",
        "subtitle":  "Panorama en detalle de Leads",
        "gradient":  "linear-gradient(135deg, #7A5800 0%, #B7860C 50%, #D4A017 100%)",
        "accent":    "#B7860C",
        "model_sql": _DEFAULT_MODEL_SQL,
    },
    "fiat": {
        "dataset":   "garden_fiat",
        "title":     "Fiat",
        "subtitle":  "Panorama en detalle de Leads",
        "gradient":  "linear-gradient(135deg, #7B0000 0%, #A50000 50%, #C0392B 100%)",
        "accent":    "#A50000",
        "model_sql": _DEFAULT_MODEL_SQL,
    },
    "jeep": {
        "dataset":   "garden_jeep",
        "title":     "Jeep",
        "subtitle":  "Panorama en detalle de Leads",
        "gradient":  "linear-gradient(135deg, #1B3A1B 0%, #2E7D32 50%, #388E3C 100%)",
        "accent":    "#2E7D32",
        "model_sql": _DEFAULT_MODEL_SQL,
    },
    "mazda": {
        "dataset":   "garden_mazda",
        "title":     "Mazda",
        "subtitle":  "Panorama en detalle de Leads",
        "gradient":  "linear-gradient(135deg, #7B0000 0%, #C0392B 50%, #E53935 100%)",
        "accent":    "#C0392B",
        "model_sql": _DEFAULT_MODEL_SQL,
    },
    "mini": {
        "dataset":   "garden_mini",
        "title":     "MINI",
        "subtitle":  "Panorama en detalle de Leads",
        "gradient":  "linear-gradient(135deg, #1A1A1A 0%, #2D2D2D 50%, #424242 100%)",
        "accent":    "#212121",
        "model_sql": _DEFAULT_MODEL_SQL,
    },
    "nissan": {
        "dataset":   "garden_nissan",
        "title":     "Nissan",
        "subtitle":  "Panorama en detalle de Leads",
        "gradient":  "linear-gradient(135deg, #7B0000 0%, #B71C1C 50%, #D32F2F 100%)",
        "accent":    "#B71C1C",
        "model_sql": _DEFAULT_MODEL_SQL,
    },
    "volvo": {
        "dataset":   "garden_volvo",
        "title":     "Volvo",
        "subtitle":  "Panorama en detalle de Leads",
        "gradient":  "linear-gradient(135deg, #002244 0%, #003777 50%, #1B5499 100%)",
        "accent":    "#003777",
        "model_sql": _DEFAULT_MODEL_SQL,
    },
}
