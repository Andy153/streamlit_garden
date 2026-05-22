"""KIA · Panorama de Leads — standalone Streamlit app."""

from __future__ import annotations

import sys
import os
from datetime import date, timedelta

import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils.bq import run_query

# ── Page setup ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="KIA · Panorama en detalle de Leads",
    page_icon=":material/directions_car:",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Oculta la navegación automática de páginas (carpeta pages/)
st.markdown(
    """<style>
    [data-testid='stSidebarNav']{display:none!important}
    [data-testid='stToolbar']{display:none!important}
    [data-testid='stSidebarCollapseButton']{display:none!important}
    [data-testid='stSidebar']{min-width:21rem!important;max-width:21rem!important;transform:translateX(0)!important}
    [data-testid='stSidebarCollapsedControl']{display:none!important}
    </style>""",
    unsafe_allow_html=True,
)

# ── Branding header ───────────────────────────────────────────────────────────
st.html("""
<div style="
    background: linear-gradient(135deg, #7F0000 0%, #B71C1C 40%, #E53935 100%);
    padding: 18px 28px;
    border-radius: 10px;
    margin-bottom: 8px;
    display: flex;
    align-items: center;
    gap: 18px;
    box-shadow: 0 4px 24px rgba(229,57,53,0.25);
">
    <span style="color:white; font-size:26px; font-weight:900; letter-spacing:5px; font-family:Inter,sans-serif;">KIA</span>
    <span style="color:rgba(255,255,255,0.35); font-size:22px; font-weight:200;">|</span>
    <div>
        <div style="color:white; font-size:17px; font-weight:600; font-family:Inter,sans-serif; letter-spacing:0.3px;">Panorama en detalle de Leads</div>
        <div style="color:rgba(255,255,255,0.6); font-size:12px; font-weight:400; font-family:Inter,sans-serif; margin-top:2px;">Garden · Dashboard Gerencial</div>
    </div>
</div>
""")

# ── Constants ─────────────────────────────────────────────────────────────────
COLOR: dict[str, str] = {
    "Caliente":      "#BF360C",
    "Tibio":         "#F9A825",
    "Frio":          "#1565C0",
    "Sin Respuesta": "#00695C",
    "Call center":   "#0097A7",
    "Sin clasificar":"#424242",
    "Descartado":    "#37474F",
}

CLASIF_ORDER = [
    "Caliente", "Tibio", "Frio",
    "Sin Respuesta", "Call center", "Sin clasificar", "Descartado",
]

SHOW_VENDOR = {"Frio", "Tibio", "Caliente"}

# ── Sidebar filters ───────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### :material/filter_list: Período")

    today = date.today()

    # ── Date range helpers ─────────────────────────────────────────────────────
    _fst_month        = today.replace(day=1)
    _last_month_end   = _fst_month - timedelta(1)
    _last_month_start = _last_month_end.replace(day=1)

    _monday_this = today - timedelta(today.weekday())
    _monday_last = _monday_this - timedelta(7)
    _sunday_last = _monday_this - timedelta(1)

    _q             = (today.month - 1) // 3
    _fst_this_q    = today.replace(month=_q * 3 + 1, day=1)
    _last_q_end    = _fst_this_q - timedelta(1)
    _last_q_s_mon  = ((_last_q_end.month - 1) // 3) * 3 + 1
    _last_q_start  = _last_q_end.replace(month=_last_q_s_mon, day=1)

    _fst_year   = today.replace(month=1, day=1)
    _prev_year_s = date(today.year - 1, 1, 1)
    _prev_year_e = date(today.year - 1, 12, 31)

    SHORTCUTS: dict[str, tuple | None] = {
        "Hoy":             (today, today),
        "Ayer":            (today - timedelta(1), today - timedelta(1)),
        "Esta semana":     (_monday_this, today),
        "Semana pasada":   (_monday_last, _sunday_last),
        "Últimos 7 días":  (today - timedelta(6), today),
        "Este mes":        (_fst_month, today),
        "Mes pasado":      (_last_month_start, _last_month_end),
        "Últimos 30 días": (today - timedelta(29), today),
        "Últimos 60 días": (today - timedelta(59), today),
        "Últimos 90 días": (today - timedelta(89), today),
        "Este trimestre":  (_fst_this_q, today),
        "Trim. pasado":    (_last_q_start, _last_q_end),
        "Este año (YTD)":  (_fst_year, today),
        "Año pasado":      (_prev_year_s, _prev_year_e),
        "Personalizado":   None,
    }

    # Inicializar preset en el primer load (evita que el selectbox arranque en "Hoy")
    if "period_preset" not in st.session_state:
        st.session_state["period_preset"] = "Este mes"

    # Aplicar preset cuando cambia
    _chosen = st.session_state["period_preset"]
    if _chosen != st.session_state.get("_applied_preset"):
        if _chosen != "Personalizado":
            _sd, _ed = SHORTCUTS[_chosen]
            st.session_state["start_date"] = _sd
            st.session_state["end_date"]   = _ed
        st.session_state["_applied_preset"] = _chosen

    st.selectbox(
        "Período",
        list(SHORTCUTS.keys()),
        key="period_preset",
        label_visibility="collapsed",
    )

    st.divider()

    def _on_date_manual_change() -> None:
        st.session_state["period_preset"]   = "Personalizado"
        st.session_state["_applied_preset"] = "Personalizado"

    start_date = st.date_input(
        "Desde", value=_fst_month, max_value=today,
        key="start_date", on_change=_on_date_manual_change,
    )
    end_date = st.date_input(
        "Hasta", value=today, max_value=today,
        key="end_date", on_change=_on_date_manual_change,
    )

    if start_date > end_date:
        st.error("La fecha inicio debe ser menor o igual a la fecha fin.")
        st.stop()

    st.caption(f"{start_date:%d/%m/%Y} → {end_date:%d/%m/%Y}")

# ── SQL ───────────────────────────────────────────────────────────────────────
SQL = f"""
SELECT
  CASE
      WHEN UPPER(TRIM(model_requested)) IN ('', 'NULL', 'KIA') OR model_requested IS NULL THEN 'Otros'
      WHEN UPPER(TRIM(model_requested)) = 'PICANTO'            THEN 'PICANTO'
      WHEN UPPER(TRIM(model_requested)) = 'SOLUTO'             THEN 'SOLUTO'
      WHEN UPPER(TRIM(model_requested)) IN ('K3-SEDAN','K3 SEDAN')    THEN 'K3 SEDAN'
      WHEN UPPER(TRIM(model_requested)) IN ('K3-CROSS','K3 CROSS')    THEN 'K3 CROSS'
      WHEN UPPER(TRIM(model_requested)) = 'CARNIVAL HEV'       THEN 'CARNIVAL HEV'
      WHEN UPPER(TRIM(model_requested)) IN ('SONET PE','SONET')        THEN 'SONET PE'
      WHEN UPPER(TRIM(model_requested)) IN ('SELTOS PE','SELTOS')      THEN 'SELTOS PE'
      WHEN UPPER(TRIM(model_requested)) = 'CARENS'             THEN 'CARENS'
      WHEN UPPER(TRIM(model_requested)) IN ('SPORTAGE PE','SPORTAGE')  THEN 'SPORTAGE PE'
      WHEN UPPER(TRIM(model_requested)) = 'SPORTAGE PE HEV'    THEN 'SPORTAGE PE HEV'
      WHEN UPPER(TRIM(model_requested)) IN ('SORENTO','SORRENTO')      THEN 'SORENTO'
      WHEN UPPER(TRIM(model_requested)) = 'SORENTO HEV'        THEN 'SORENTO HEV'
      WHEN UPPER(TRIM(model_requested)) = 'EV5'                THEN 'EV5'
      WHEN UPPER(TRIM(model_requested)) = 'K2700'              THEN 'K2700'
      WHEN UPPER(TRIM(model_requested)) = 'TASMAN'             THEN 'TASMAN'
      WHEN UPPER(TRIM(model_requested)) = 'NIRO'               THEN 'NIRO'
      WHEN UPPER(TRIM(model_requested)) = 'EV9'                THEN 'EV9'
      ELSE 'Otros'
  END AS modelo,
  CASE
      WHEN lower(etapa_funnel) = 'descartado'         THEN 'Descartado'
      WHEN lower(etapa_funnel) = 'externo comercial'  THEN 'Call center'
      WHEN lower(clasificacion_de_lead) IN ('warm','tibio')     THEN 'Tibio'
      WHEN lower(clasificacion_de_lead) IN ('cold','frio')      THEN 'Frio'
      WHEN lower(clasificacion_de_lead) IN ('hot','caliente')   THEN 'Caliente'
      WHEN lower(clasificacion_de_lead) = 'sin respuesta'       THEN 'Sin Respuesta'
      WHEN clasificacion_de_lead IS NULL                        THEN 'Sin clasificar'
      ELSE 'Sin clasificar'
  END AS clasificacion,
  COALESCE(
    NULLIF(TRIM(COALESCE(nombre, '') || ' ' || COALESCE(apellido, '')), ''),
    first_name_wpp,
    'Sin nombre'
  ) AS cliente,
  COALESCE(agente_asignado, 'Sin asignar') AS vendedor,
  id           AS telefono,
  origen_lead
FROM `vx-operation.garden_kia.cio_people_data_with_attributes`
WHERE gochat_users_ns IS NOT NULL
  AND _created_at >= TIMESTAMP('{start_date.isoformat()}', 'America/Asuncion')
  AND _created_at <  TIMESTAMP(DATE_ADD(DATE '{end_date.isoformat()}', INTERVAL 1 DAY), 'America/Asuncion')
"""

df = run_query(SQL)

if df.empty:
    st.warning("No hay datos para el período seleccionado.")
    st.stop()

# ── Derived counts ────────────────────────────────────────────────────────────
total     = len(df)
cnt       = {c: int((df["clasificacion"] == c).sum()) for c in CLASIF_ORDER}
total_com = total - cnt.get("Call center", 0)

def pct(n: int) -> str:
    return f"{n / total * 100:.1f}%" if total else "0.0%"

# ── KPI cards ─────────────────────────────────────────────────────────────────
st.html(f"""
<style>
.kpi-wrap{{width:100%;box-sizing:border-box;font-family:Inter,sans-serif;overflow:visible}}
.kpi-title{{font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:1px;
            color:#78909C;margin:0 0 14px;border-left:4px solid #C62828;padding-left:10px;line-height:1.5}}
.kpi-row{{display:flex;gap:12px;width:100%;box-sizing:border-box;margin-bottom:28px}}
.kpi-card{{flex:1;min-width:0;background:#fff;border-radius:10px;padding:16px 18px 14px;
           box-shadow:0 2px 14px rgba(0,0,0,0.09),0 0 0 1px rgba(0,0,0,0.04);
           border-top:5px solid var(--a);position:relative;cursor:default}}
.kpi-icon{{position:absolute;top:9px;right:10px;font-size:12px;color:#CFD8DC;
           line-height:1;transition:color 0.15s;user-select:none}}
.kpi-card:hover .kpi-icon{{color:#90A4AE}}
.kpi-lbl{{font-size:10.5px;font-weight:600;text-transform:uppercase;letter-spacing:0.8px;
          color:#90A4AE;margin-bottom:8px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.kpi-val{{font-size:32px;font-weight:800;color:#1A1A2E;line-height:1;margin-bottom:8px}}
.kpi-pct{{display:inline-block;background:#EEF2F7;color:#546E7A;font-size:11px;
           font-weight:600;padding:2px 8px;border-radius:20px}}
.kpi-card::after{{
    content:attr(data-tip);
    position:absolute;
    bottom:calc(100% + 8px);
    left:50%;
    transform:translateX(-50%);
    background:#1A1A2E;
    color:#fff;
    font-size:11px;
    font-weight:400;
    line-height:1.5;
    padding:7px 12px;
    border-radius:7px;
    white-space:normal;
    width:200px;
    text-align:center;
    opacity:0;
    pointer-events:none;
    transition:opacity 0.18s;
    z-index:9999;
    box-shadow:0 4px 12px rgba(0,0,0,0.18);
}}
.kpi-card:hover::after{{opacity:1}}
</style>
<div class="kpi-wrap">
<p class="kpi-title">Clasificación de Leads</p>
<div class="kpi-row">
  <div class="kpi-card" style="--a:#C62828"
       data-tip="Leads ingresados en el período seleccionado.">
    <span class="kpi-icon">ⓘ</span>
    <div class="kpi-lbl">Total</div>
    <div class="kpi-val">{total:,}</div>
  </div>
  <div class="kpi-card" style="--a:#2E7D32"
       data-tip="Total excluyendo Call Center. Refleja el pipeline comercial real">
    <span class="kpi-icon">ⓘ</span>
    <div class="kpi-lbl">Total Comercial</div>
    <div class="kpi-val">{total_com:,}</div>
    <span class="kpi-pct">{pct(total_com)}</span>
  </div>
  <div class="kpi-card" style="--a:#424242"
       data-tip="Leads nuevos pendientes de calificación por el agente.">
    <span class="kpi-icon">ⓘ</span>
    <div class="kpi-lbl">Sin Clasificar</div>
    <div class="kpi-val">{cnt.get('Sin clasificar',0):,}</div>
    <span class="kpi-pct">{pct(cnt.get('Sin clasificar',0))}</span>
  </div>
  <div class="kpi-card" style="--a:#0097A7"
       data-tip="Consultas de repuestos, service o RRHH derivadas al canal correspondiente.">
    <span class="kpi-icon">ⓘ</span>
    <div class="kpi-lbl">Call Center</div>
    <div class="kpi-val">{cnt.get('Call center',0):,}</div>
    <span class="kpi-pct">{pct(cnt.get('Call center',0))}</span>
  </div>
  <div class="kpi-card" style="--a:#00695C"
       data-tip="Leads contactados que aún no respondieron al primer mensaje.">
    <span class="kpi-icon">ⓘ</span>
    <div class="kpi-lbl">Sin Respuesta</div>
    <div class="kpi-val">{cnt.get('Sin Respuesta',0):,}</div>
    <span class="kpi-pct">{pct(cnt.get('Sin Respuesta',0))}</span>
  </div>
</div>
<div class="kpi-row">
  <div class="kpi-card" style="--a:#37474F"
       data-tip="Leads no válidos: spam, duplicados o fuera de target.">
    <span class="kpi-icon">ⓘ</span>
    <div class="kpi-lbl">Descartados</div>
    <div class="kpi-val">{cnt.get('Descartado',0):,}</div>
    <span class="kpi-pct">{pct(cnt.get('Descartado',0))}</span>
  </div>
  <div class="kpi-card" style="--a:#1565C0"
       data-tip="Solo consulta, sin intención de compra declarada.">
    <span class="kpi-icon">ⓘ</span>
    <div class="kpi-lbl">Frío</div>
    <div class="kpi-val">{cnt.get('Frio',0):,}</div>
    <span class="kpi-pct">{pct(cnt.get('Frio',0))}</span>
  </div>
  <div class="kpi-card" style="--a:#F9A825"
       data-tip="Interés de compra declarado a más de 60 días o derivado por bot a agente.">
    <span class="kpi-icon">ⓘ</span>
    <div class="kpi-lbl">Tibio</div>
    <div class="kpi-val">{cnt.get('Tibio',0):,}</div>
    <span class="kpi-pct">{pct(cnt.get('Tibio',0))}</span>
  </div>
  <div class="kpi-card" style="--a:#BF360C"
       data-tip="Intención de compra confirmada dentro de los próximos 60 días.">
    <span class="kpi-icon">ⓘ</span>
    <div class="kpi-lbl">Caliente</div>
    <div class="kpi-val">{cnt.get('Caliente',0):,}</div>
    <span class="kpi-pct">{pct(cnt.get('Caliente',0))}</span>
  </div>
</div>
</div>
""")

# ── Waterfall chart (clickable selector) ─────────────────────────────────────
st.markdown("### :material/waterfall_chart: Desglose por clasificación")
st.caption(":material/touch_app: Hacé click en una barra para ver el desglose")

sel_c     = st.session_state.get("clasif_sel")
values    = [cnt.get(c, 0) for c in CLASIF_ORDER]
total_val = sum(values)
bases     = [sum(values[:i]) for i in range(len(values))]

_all_labels  = CLASIF_ORDER + ["Total"]
_base_colors = [COLOR.get(c, "#9E9E9E") for c in CLASIF_ORDER] + ["#757575"]
bar_colors   = (
    [c if lbl == sel_c else "#D5D8DC" for lbl, c in zip(_all_labels, _base_colors)]
    if sel_c else _base_colors
)

y_tops  = [b + v for b, v in zip(bases + [0], values + [total_val])]
y_range = max(y_tops) * 1.18 if y_tops else 100

fig_wf = go.Figure(go.Bar(
    x=_all_labels,
    y=values + [total_val],
    base=bases + [0],
    marker_color=bar_colors,
    marker_line_width=0,
    text=[f"{v:,}" for v in values] + [f"{total_val:,}"],
    textposition="outside",
    cliponaxis=False,
    showlegend=False,
    hovertemplate="<b>%{x}</b><br>Leads: %{y:,}<extra></extra>",
    selected=dict(marker=dict(opacity=1)),
    unselected=dict(marker=dict(opacity=1)),
))
fig_wf.update_layout(
    showlegend    = False,
    height        = 440,
    margin        = dict(t=50, b=10, l=60, r=80),
    plot_bgcolor  = "rgba(0,0,0,0)",
    paper_bgcolor = "rgba(0,0,0,0)",
    xaxis         = dict(showgrid=False, tickfont=dict(size=13)),
    yaxis         = dict(showgrid=True, gridcolor="#E8EAF0", title="Leads",
                         range=[0, y_range]),
    dragmode      = False,
)
wf_event = st.plotly_chart(
    fig_wf, key="waterfall", on_select="rerun",
    config={"displayModeBar": False, "scrollZoom": False},
)

if wf_event and wf_event.selection and wf_event.selection.points:
    clicked = wf_event.selection.points[0].get("x")
    if clicked and clicked in CLASIF_ORDER and clicked != sel_c:
        st.session_state["clasif_sel"] = clicked
        st.session_state.pop("model_sel",  None)
        st.session_state.pop("vendor_sel", None)
        st.rerun()

sel_c = st.session_state.get("clasif_sel")

if sel_c:
    _hdr, _close = st.columns([11, 1])
    with _hdr:
        st.markdown(f"##### :material/subdirectory_arrow_right: Desglose · **{sel_c}**")
    with _close:
        if st.button("✕", key="close_clasif", help="Cerrar desglose"):
            st.session_state.pop("clasif_sel",  None)
            st.session_state.pop("model_sel",   None)
            st.session_state.pop("vendor_sel",  None)
            st.rerun()

# ── Drill-down (fragment = solo rerenderiza este bloque, sin volver a correr SQL)
@st.fragment
def drilldown(df, sel_c):
    if not sel_c:
        return

    show_vendor = sel_c in SHOW_VENDOR
    accent      = COLOR.get(sel_c, "#757575")
    df_c        = df[df["clasificacion"] == sel_c]
    sel_m       = st.session_state.get("model_sel")
    sel_v       = st.session_state.get("vendor_sel") if show_vendor else None

    # Accent animado al abrir el desglose
    # Keyframe names únicos por clasificación para forzar retrigger en cada apertura
    _aid = sel_c.replace(" ", "_")
    st.markdown(f"""
<style>
@keyframes accentSlide_{_aid} {{
    from {{ transform: scaleX(0); opacity: 0; }}
    to   {{ transform: scaleX(1); opacity: 1; }}
}}
@keyframes fadeUp_{_aid} {{
    from {{ opacity: 0; transform: translateY(10px); }}
    to   {{ opacity: 1; transform: translateY(0); }}
}}
.drill-accent {{ transform-origin: left; animation: accentSlide_{_aid} 0.4s cubic-bezier(.22,.68,0,1.1) both; }}
.drill-title  {{ animation: fadeUp_{_aid} 0.4s ease both; }}
</style>
<div class="drill-accent" style="
    height: 3px;
    background: linear-gradient(90deg, {accent} 0%, {accent}30 100%);
    border-radius: 2px;
    margin-bottom: 10px;
"></div>
<div class="drill-title" style="
    display: flex;
    align-items: baseline;
    gap: 10px;
    margin-bottom: 4px;
    font-family: Inter, sans-serif;
">
    <span style="font-size:26px;font-weight:800;color:{accent};letter-spacing:-0.3px">{sel_c}</span>
    <span style="color:#CFD8DC;font-size:22px;font-weight:300">·</span>
    <span style="font-size:22px;font-weight:700;color:#1A1A2E">{len(df_c):,} leads</span>
</div>
""", unsafe_allow_html=True)

    # Migas + botón limpiar (solo cuando hay modelo o vendedor activo)
    if sel_m or sel_v:
        crumbs = [sel_c]
        if sel_m: crumbs.append(sel_m)
        if sel_v: crumbs.append(sel_v)
        col_t, col_clr = st.columns([9, 1])
        with col_t:
            st.markdown("  ›  ".join(f"**{c}**" for c in crumbs))
        with col_clr:
            if st.button("✕", key="clear_inner", help="Limpiar modelo/vendedor"):
                st.session_state.pop("model_sel",  None)
                st.session_state.pop("vendor_sel", None)
                st.rerun()

    cols = st.columns(2 if show_vendor else 1)
    col1 = cols[0]

    # ── Por Modelo ────────────────────────────────────────────────────────────
    with col1:
        src_m = df_c if not sel_v else df_c[df_c["vendedor"] == sel_v]
        mc    = src_m.groupby("modelo").size().reset_index(name="n").sort_values("n")
        mc_colors = [
            accent if (sel_m and m == sel_m) else ("#BDBDBD" if sel_m else accent)
            for m in mc["modelo"]
        ]
        fig_m = go.Figure(go.Bar(
            x=mc["n"], y=mc["modelo"], orientation="h",
            marker_color=mc_colors, marker_line_width=0,
            text=mc["n"], textposition="outside",
            cliponaxis=False,
            hovertemplate="<b>%{y}</b><br>%{x:,} leads<extra></extra>",
        ))
        fig_m.update_layout(
            title="Por Modelo", height=max(300, len(mc) * 34),
            margin=dict(t=40, b=20, l=20, r=90),
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(255,255,255,0)",
            xaxis=dict(showgrid=True, gridcolor="#E8EAF0",
                       range=[0, mc["n"].max() * 1.25] if not mc.empty else None),
            yaxis=dict(showgrid=False),
            dragmode=False,
        )
        m_event = st.plotly_chart(
            fig_m, key="model_chart", on_select="rerun",
            config={"displayModeBar": False, "scrollZoom": False},
        )
        if m_event and m_event.selection and m_event.selection.points:
            clicked_m = m_event.selection.points[0].get("y")
            if clicked_m:
                st.session_state["model_sel"]  = None if clicked_m == sel_m else clicked_m
                st.session_state["vendor_sel"] = None
                st.rerun()

    # ── Por Vendedor (solo Frío / Tibio / Caliente) ───────────────────────────
    if show_vendor:
        with cols[1]:
            src_v = df_c if not sel_m else df_c[df_c["modelo"] == sel_m]
            vc    = src_v.groupby("vendedor").size().reset_index(name="n").sort_values("n")
            vc_colors = [
                accent if (sel_v and v == sel_v) else ("#BDBDBD" if sel_v else accent)
                for v in vc["vendedor"]
            ]
            fig_v = go.Figure(go.Bar(
                x=vc["n"], y=vc["vendedor"], orientation="h",
                marker_color=vc_colors, marker_line_width=0,
                text=vc["n"], textposition="outside",
                cliponaxis=False,
                hovertemplate="<b>%{y}</b><br>%{x:,} leads<extra></extra>",
            ))
            fig_v.update_layout(
                title="Por Vendedor", height=max(300, len(vc) * 34),
                margin=dict(t=40, b=20, l=20, r=90),
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(255,255,255,0)",
                xaxis=dict(showgrid=True, gridcolor="#E8EAF0",
                           range=[0, vc["n"].max() * 1.25] if not vc.empty else None),
                yaxis=dict(showgrid=False),
                dragmode=False,
            )
            v_event = st.plotly_chart(
                fig_v, key="vendor_chart", on_select="rerun",
                config={"displayModeBar": False, "scrollZoom": False},
            )
            if v_event and v_event.selection and v_event.selection.points:
                clicked_v = v_event.selection.points[0].get("y")
                if clicked_v:
                    st.session_state["vendor_sel"] = None if clicked_v == sel_v else clicked_v
                    st.rerun()

    # ── Tabla clientes ─────────────────────────────────────────────────────────
    df_tbl = df_c.copy()
    if sel_m: df_tbl = df_tbl[df_tbl["modelo"]   == sel_m]
    if sel_v: df_tbl = df_tbl[df_tbl["vendedor"] == sel_v]
    df_tbl = df_tbl[["cliente", "vendedor", "modelo", "telefono", "origen_lead"]].reset_index(drop=True)

    st.markdown(f"#### :material/group: Clientes &nbsp;·&nbsp; {len(df_tbl):,}")
    st.dataframe(
        df_tbl,
        hide_index=True,
        height=min(520, 35 * len(df_tbl) + 40),
        column_config={
            "cliente":     st.column_config.TextColumn("Cliente"),
            "vendedor":    st.column_config.TextColumn("Vendedor"),
            "modelo":      st.column_config.TextColumn("Modelo"),
            "telefono":    st.column_config.TextColumn("Teléfono"),
            "origen_lead": st.column_config.TextColumn("Origen"),
        },
    )

drilldown(df, sel_c)
