"""Per-brand configuration: dataset, colors, model SQL mapping."""
from __future__ import annotations

# ── KIA ───────────────────────────────────────────────────────────────────────
_KIA_MODEL_SQL = """
CASE
    WHEN UPPER(TRIM(model_requested)) IN ('', 'NULL', 'KIA') OR model_requested IS NULL THEN 'Otros'
    WHEN UPPER(TRIM(model_requested)) = 'SOLUTO'                                        THEN 'SOLUTO'
    WHEN UPPER(TRIM(model_requested)) IN ('K3-SEDAN', 'K3 SEDAN', 'K3SEDAN')           THEN 'K3 SEDAN'
    WHEN UPPER(TRIM(model_requested)) IN ('K3-CROSS', 'K3 CROSS', 'K3CROSS')           THEN 'K3 CROSS'
    WHEN UPPER(TRIM(model_requested)) = 'CARNIVAL HEV'                                 THEN 'CARNIVAL HEV'
    WHEN UPPER(TRIM(model_requested)) IN ('SONET PE', 'SONET')                         THEN 'SONET PE'
    WHEN UPPER(TRIM(model_requested)) IN ('SELTOS PE', 'SELTOS')                       THEN 'SELTOS PE'
    WHEN UPPER(TRIM(model_requested)) IN ('NEW CARENS', 'CARENS')                      THEN 'NEW CARENS'
    WHEN UPPER(TRIM(model_requested)) IN ('SPORTAGE PE HEV', 'SPORTAGE HEV', 'SPORTAGE PE', 'SPORTAGE') THEN 'SPORTAGE PE HEV'
    WHEN UPPER(TRIM(model_requested)) IN ('SORENTO HEV', 'SORRENTO HEV', 'SORENTO', 'SORRENTO')         THEN 'SORENTO HEV'
    WHEN UPPER(TRIM(model_requested)) = 'EV5'                                          THEN 'EV5'
    WHEN UPPER(TRIM(model_requested)) = 'K2700'                                        THEN 'K2700'
    WHEN UPPER(TRIM(model_requested)) = 'TASMAN'                                       THEN 'TASMAN'
    ELSE 'Otros'
END
"""

# ── Nissan ────────────────────────────────────────────────────────────────────
_NISSAN_MODEL_SQL = """
CASE
    WHEN UPPER(TRIM(model_requested)) = 'SENTRA'                                        THEN 'SENTRA'
    WHEN UPPER(TRIM(model_requested)) = 'PATHFINDER'                                    THEN 'PATHFINDER'
    WHEN UPPER(TRIM(model_requested)) = 'KICKS'                                         THEN 'KICKS'
    WHEN UPPER(TRIM(model_requested)) = 'QASHQAI'                                       THEN 'QASHQAI'
    WHEN UPPER(TRIM(model_requested)) IN ('X-TRAIL ICE', 'X TRAIL ICE', 'XTRAIL ICE')  THEN 'X-TRAIL ICE'
    WHEN UPPER(TRIM(model_requested)) IN ('X-TRAIL E', 'X TRAIL E', 'XTRAIL E', 'X-TRAIL EV') THEN 'X-TRAIL e'
    WHEN UPPER(TRIM(model_requested)) = 'FRONTIER'                                      THEN 'FRONTIER'
    WHEN UPPER(TRIM(model_requested)) = 'KAIT'                                          THEN 'KAIT'
    ELSE 'Otros'
END
"""

# ── Fiat ──────────────────────────────────────────────────────────────────────
_FIAT_MODEL_SQL = """
CASE
    WHEN UPPER(TRIM(model_requested)) = 'MOBI'     THEN 'MOBI'
    WHEN UPPER(TRIM(model_requested)) = 'ARGO'     THEN 'ARGO'
    WHEN UPPER(TRIM(model_requested)) = 'PULSE'    THEN 'PULSE'
    WHEN UPPER(TRIM(model_requested)) = 'FASTBACK' THEN 'FASTBACK'
    WHEN UPPER(TRIM(model_requested)) = 'TORO'     THEN 'TORO'
    WHEN UPPER(TRIM(model_requested)) = 'STRADA'   THEN 'STRADA'
    WHEN UPPER(TRIM(model_requested)) = 'FIORINO'  THEN 'FIORINO'
    ELSE 'Otros'
END
"""

# ── Jeep + RAM (mismo dataset) ────────────────────────────────────────────────
_JEEP_MODEL_SQL = """
CASE
    WHEN UPPER(TRIM(model_requested)) IN ('1500 RHO', 'RAM 1500 RHO', 'RAM1500 RHO')       THEN '1500 RHO'
    WHEN UPPER(TRIM(model_requested)) IN ('1500 REBEL', 'RAM 1500 REBEL', 'RAM1500 REBEL') THEN '1500 REBEL'
    WHEN UPPER(TRIM(model_requested)) = 'RAMPAGE'   THEN 'RAMPAGE'
    WHEN UPPER(TRIM(model_requested)) = 'WRANGLER'  THEN 'WRANGLER'
    WHEN UPPER(TRIM(model_requested)) = 'COMPASS'   THEN 'COMPASS'
    WHEN UPPER(TRIM(model_requested)) = 'COMMANDER' THEN 'COMMANDER'
    ELSE 'Otros'
END
"""

# ── Chery ─────────────────────────────────────────────────────────────────────
_CHERY_MODEL_SQL = """
CASE
    WHEN UPPER(TRIM(model_requested)) = 'T2'    THEN 'T2'
    WHEN UPPER(TRIM(model_requested)) = 'T4'    THEN 'T4'
    WHEN UPPER(TRIM(model_requested)) = 'T7'    THEN 'T7'
    WHEN UPPER(TRIM(model_requested)) = 'M7'    THEN 'M7'
    WHEN UPPER(TRIM(model_requested)) = 'T8'    THEN 'T8'
    WHEN UPPER(TRIM(model_requested)) = 'HIMLA' THEN 'HIMLA'
    WHEN UPPER(TRIM(model_requested)) = 'V23'   THEN 'V23'
    WHEN UPPER(TRIM(model_requested)) = '03T'   THEN '03T'
    WHEN UPPER(TRIM(model_requested)) = 'V27'   THEN 'V27'
    ELSE 'Otros'
END
"""

# ── MINI ─────────────────────────────────────────────────────────────────────
# Ordered most-specific → least-specific to avoid partial overlaps
_MINI_MODEL_SQL = """
CASE
    WHEN UPPER(TRIM(model_requested)) LIKE '%COUNTRYMAN C%'      THEN 'MINI COUNTRYMAN C'
    WHEN UPPER(TRIM(model_requested)) LIKE '%JCW HATCH%'         THEN 'MINI COOPER JCW HATCH'
    WHEN UPPER(TRIM(model_requested)) LIKE '%COOPER C FAVOURED%' THEN 'MINI COOPER C FAVOURED'
    WHEN UPPER(TRIM(model_requested)) LIKE '%COOPER S FAVOURED%' THEN 'MINI COOPER S FAVOURED'
    WHEN UPPER(TRIM(model_requested)) LIKE '%ACEMAN JCW%'        THEN 'MINI ACEMAN JCW'
    WHEN UPPER(TRIM(model_requested)) LIKE '%ACEMAN SE%'         THEN 'MINI ACEMAN SE'
    WHEN UPPER(TRIM(model_requested)) LIKE '%ACEMAN E%'          THEN 'MINI ACEMAN E'
    WHEN UPPER(TRIM(model_requested)) LIKE '%COOPER JCW%'        THEN 'MINI COOPER JCW'
    WHEN UPPER(TRIM(model_requested)) LIKE '%COOPER CABRIO%'     THEN 'MINI COOPER CABRIO'
    WHEN UPPER(TRIM(model_requested)) LIKE '%COUNTRYMAN%'        THEN 'MINI COUNTRYMAN'
    ELSE 'Otros'
END
"""

# ── BMW Motorrad ──────────────────────────────────────────────────────────────
# Ordered most-specific → least-specific (ADV before GS, GS before base)
_BMW_MODEL_SQL = """
CASE
    WHEN UPPER(TRIM(model_requested)) LIKE '%R 1300 GS ADV%' OR UPPER(TRIM(model_requested)) LIKE '%R1300 GS ADV%' THEN 'R 1300 GS ADV'
    WHEN UPPER(TRIM(model_requested)) LIKE '%R 1300 GS%'     OR UPPER(TRIM(model_requested)) LIKE '%R1300 GS%'     THEN 'R 1300 GS'
    WHEN UPPER(TRIM(model_requested)) LIKE '%F 900 GS%'      OR UPPER(TRIM(model_requested)) LIKE '%F900 GS%'      THEN 'F 900 GS'
    WHEN UPPER(TRIM(model_requested)) LIKE '%G 310%'         OR UPPER(TRIM(model_requested)) LIKE '%G310%'         THEN 'G 310'
    WHEN UPPER(TRIM(model_requested)) LIKE '%R 12%'          OR UPPER(TRIM(model_requested)) LIKE '%R12%'          THEN 'R 12'
    WHEN UPPER(TRIM(model_requested)) LIKE '%F 800%'         OR UPPER(TRIM(model_requested)) LIKE '%F800%'         THEN 'F 800'
    WHEN UPPER(TRIM(model_requested)) LIKE '%F 900%'         OR UPPER(TRIM(model_requested)) LIKE '%F900%'         THEN 'F 900'
    WHEN UPPER(TRIM(model_requested)) LIKE '%R 1300%'        OR UPPER(TRIM(model_requested)) LIKE '%R1300%'        THEN 'R 1300'
    WHEN UPPER(TRIM(model_requested)) LIKE '%K 1600%'        OR UPPER(TRIM(model_requested)) LIKE '%K1600%'        THEN 'K 1600'
    WHEN UPPER(TRIM(model_requested)) LIKE '%S 1000%'        OR UPPER(TRIM(model_requested)) LIKE '%S1000%'        THEN 'S 1000'
    WHEN UPPER(TRIM(model_requested)) LIKE '%M 1000%'        OR UPPER(TRIM(model_requested)) LIKE '%M1000%'        THEN 'M 1000'
    ELSE 'Otros'
END
"""

# ── Chevrolet ─────────────────────────────────────────────────────────────────
_CHEVROLET_MODEL_SQL = """
CASE
    WHEN UPPER(TRIM(model_requested)) = 'SPARK'                                  THEN 'SPARK'
    WHEN UPPER(TRIM(model_requested)) IN ('ONIX PLUS', 'ONIX+', 'ONIX SEDAN')   THEN 'ONIX PLUS'
    WHEN UPPER(TRIM(model_requested)) = 'ONIX'                                   THEN 'ONIX'
    WHEN UPPER(TRIM(model_requested)) = 'TRACKER'                                THEN 'TRACKER'
    WHEN UPPER(TRIM(model_requested)) = 'MONTANA'                                THEN 'MONTANA'
    WHEN UPPER(TRIM(model_requested)) = 'S10'                                    THEN 'S10'
    WHEN UPPER(TRIM(model_requested)) = 'TRAILBLAZER'                            THEN 'TRAILBLAZER'
    WHEN UPPER(TRIM(model_requested)) = 'SILVERADO'                              THEN 'SILVERADO'
    WHEN UPPER(TRIM(model_requested)) = 'CAPTIVA'                                THEN 'CAPTIVA'
    ELSE 'Otros'
END
"""

# ── Volvo ─────────────────────────────────────────────────────────────────────
_VOLVO_MODEL_SQL = """
CASE
    WHEN UPPER(TRIM(model_requested)) = 'EX30'                               THEN 'EX30'
    WHEN UPPER(TRIM(model_requested)) = 'EX40'                               THEN 'EX40'
    WHEN UPPER(TRIM(model_requested)) = 'EC40'                               THEN 'EC40'
    WHEN UPPER(TRIM(model_requested)) IN ('NEW XC60', 'XC60', 'XC 60')      THEN 'NEW XC60'
    WHEN UPPER(TRIM(model_requested)) IN ('NEW XC90', 'XC90', 'XC 90')      THEN 'NEW XC90'
    WHEN UPPER(TRIM(model_requested)) = 'EX90'                               THEN 'EX90'
    ELSE 'Otros'
END
"""

# ── Mazda ─────────────────────────────────────────────────────────────────────
_MAZDA_MODEL_SQL = """
CASE
    WHEN UPPER(TRIM(model_requested)) IN ('CX-30', 'CX30', 'CX 30') THEN 'CX-30'
    WHEN UPPER(TRIM(model_requested)) IN ('CX-5',  'CX5',  'CX 5')  THEN 'CX-5'
    WHEN UPPER(TRIM(model_requested)) IN ('CX-60', 'CX60', 'CX 60') THEN 'CX-60'
    WHEN UPPER(TRIM(model_requested)) IN ('CX-90', 'CX90', 'CX 90') THEN 'CX-90'
    WHEN UPPER(TRIM(model_requested)) IN ('BT-50', 'BT50', 'BT 50') THEN 'BT-50'
    ELSE 'Otros'
END
"""

# Generic fallback — uses raw model_requested, just trims whitespace
_DEFAULT_MODEL_SQL = "COALESCE(NULLIF(TRIM(model_requested), ''), 'Otros')"

# ── Brand registry ────────────────────────────────────────────────────────────
# Keys are used as URL paths: /kia, /bmw, /nissan, etc.
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
        "title":     "BMW Motorrad",
        "subtitle":  "Panorama en detalle de Leads",
        "gradient":  "linear-gradient(135deg, #0D1B2A 0%, #1B4F72 50%, #2980B9 100%)",
        "accent":    "#1565C0",
        "model_sql": _BMW_MODEL_SQL,
    },
    "chery": {
        "dataset":   "garden_chery",
        "title":     "Chery",
        "subtitle":  "Panorama en detalle de Leads",
        "gradient":  "linear-gradient(135deg, #880000 0%, #C0392B 50%, #E74C3C 100%)",
        "accent":    "#C0392B",
        "model_sql": _CHERY_MODEL_SQL,
    },
    "chevrolet": {
        "dataset":   "garden_chevrolet",
        "title":     "Chevrolet",
        "subtitle":  "Panorama en detalle de Leads",
        "gradient":  "linear-gradient(135deg, #7A5800 0%, #B7860C 50%, #D4A017 100%)",
        "accent":    "#B7860C",
        "model_sql": _CHEVROLET_MODEL_SQL,
    },
    "fiat": {
        "dataset":   "garden_fiat",
        "title":     "Fiat",
        "subtitle":  "Panorama en detalle de Leads",
        "gradient":  "linear-gradient(135deg, #7B0000 0%, #A50000 50%, #C0392B 100%)",
        "accent":    "#A50000",
        "model_sql": _FIAT_MODEL_SQL,
    },
    "jeep": {
        "dataset":   "garden_jeep",
        "title":     "Jeep · RAM",
        "subtitle":  "Panorama en detalle de Leads",
        "gradient":  "linear-gradient(135deg, #1B3A1B 0%, #2E7D32 50%, #388E3C 100%)",
        "accent":    "#2E7D32",
        "model_sql": _JEEP_MODEL_SQL,
    },
    "mazda": {
        "dataset":   "garden_mazda",
        "title":     "Mazda",
        "subtitle":  "Panorama en detalle de Leads",
        "gradient":  "linear-gradient(135deg, #7B0000 0%, #C0392B 50%, #E53935 100%)",
        "accent":    "#C0392B",
        "model_sql": _MAZDA_MODEL_SQL,
    },
    "mini": {
        "dataset":   "garden_mini",
        "title":     "MINI",
        "subtitle":  "Panorama en detalle de Leads",
        "gradient":  "linear-gradient(135deg, #1A1A1A 0%, #2D2D2D 50%, #424242 100%)",
        "accent":    "#212121",
        "model_sql": _MINI_MODEL_SQL,
    },
    "nissan": {
        "dataset":   "garden_nissan",
        "title":     "Nissan",
        "subtitle":  "Panorama en detalle de Leads",
        "gradient":  "linear-gradient(135deg, #7B0000 0%, #B71C1C 50%, #D32F2F 100%)",
        "accent":    "#B71C1C",
        "model_sql": _NISSAN_MODEL_SQL,
    },
    "volvo": {
        "dataset":   "garden_volvo",
        "title":     "Volvo",
        "subtitle":  "Panorama en detalle de Leads",
        "gradient":  "linear-gradient(135deg, #002244 0%, #003777 50%, #1B5499 100%)",
        "accent":    "#003777",
        "model_sql": _VOLVO_MODEL_SQL,
    },
}
