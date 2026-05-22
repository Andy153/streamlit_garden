import streamlit as st
import plotly.express as px
from utils.bq import run_query

st.set_page_config(page_title="Ventas SAP · Garden", layout="wide")
st.title("Ventas SAP")

BRANDS_SAP = ["garden_bmw", "garden_chery", "garden_chevrolet",
              "garden_fiat", "garden_jeep", "garden_kia", "garden_mazda",
              "garden_mini", "garden_nissan", "garden_volvo"]


def _reset_filters():
    st.session_state.sap_filter_modelo = None
    st.session_state.sap_filter_vendedor = None


col_brand, col_days = st.columns([2, 1])
brand = col_brand.selectbox("Marca", BRANDS_SAP, index=0, on_change=_reset_filters)
days = col_days.selectbox("Período", [30, 60, 90, 180, 365], index=1, format_func=lambda x: f"Últimos {x} días")

st.session_state.setdefault("sap_filter_modelo", None)
st.session_state.setdefault("sap_filter_vendedor", None)

df = run_query(f"""
    SELECT
        fecha,
        modelo,
        sucursal,
        vendedor,
        origen_lead,
        grupo_suborigen,
        suborigen,
        etapa_funnel,
        etapa_funnel_sale,
        dias_hasta_venta,
        match_type,
        cio_matching
    FROM `vx-operation.{brand}.ventas_sap`
    WHERE fecha >= DATE_SUB(CURRENT_DATE(), INTERVAL {days} DAY)
    ORDER BY fecha DESC
""")

if df.empty:
    st.warning("No hay datos para el período seleccionado.")
    st.stop()

# ── KPIs ───────────────────────────────────────────────────────────────────
avg_days = df["dias_hasta_venta"].dropna().mean()
c1, c2, c3, c4 = st.columns(4)
c1.metric("Ventas totales", f"{len(df):,}")
c2.metric("Modelos únicos", f"{df['modelo'].nunique():,}")
c3.metric("Sucursales", f"{df['sucursal'].nunique():,}")
c4.metric("Días prom. hasta venta", f"{avg_days:.0f}" if avg_days == avg_days else "—")

st.divider()

# ── Gráficos con filtro por click ──────────────────────────────────────────
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Ventas por Modelo — click para filtrar")
    modelo_counts = df["modelo"].value_counts().head(15).reset_index()
    modelo_counts.columns = ["modelo", "ventas"]
    fig = px.bar(modelo_counts, x="ventas", y="modelo", orientation="h",
                 color="ventas", color_continuous_scale="Viridis")
    fig.update_layout(showlegend=False, coloraxis_showscale=False,
                      yaxis_title="", height=380)
    ev_modelo = st.plotly_chart(fig, on_select="rerun", key="sap_chart_modelo")
    if ev_modelo.selection.points:
        st.session_state.sap_filter_modelo = ev_modelo.selection.points[0]["y"]
    else:
        st.session_state.sap_filter_modelo = None

with col_right:
    st.subheader("Ventas por Vendedor — click para filtrar")
    vendedor_counts = df["vendedor"].value_counts().head(15).reset_index()
    vendedor_counts.columns = ["vendedor", "ventas"]
    fig_v = px.bar(vendedor_counts, x="ventas", y="vendedor", orientation="h",
                   color="ventas", color_continuous_scale="Oranges")
    fig_v.update_layout(showlegend=False, coloraxis_showscale=False,
                        yaxis_title="", height=380)
    ev_vendedor = st.plotly_chart(fig_v, on_select="rerun", key="sap_chart_vendedor")
    if ev_vendedor.selection.points:
        st.session_state.sap_filter_vendedor = ev_vendedor.selection.points[0]["y"]
    else:
        st.session_state.sap_filter_vendedor = None

# ── Gráficos auxiliares ────────────────────────────────────────────────────
col_left2, col_right2 = st.columns(2)

with col_left2:
    st.subheader("Origen de Lead")
    origen_counts = df["origen_lead"].value_counts().reset_index()
    origen_counts.columns = ["origen", "ventas"]
    fig2 = px.pie(origen_counts, values="ventas", names="origen", hole=0.4)
    fig2.update_layout(height=320)
    st.plotly_chart(fig2)

with col_right2:
    st.subheader("Ventas por Sucursal")
    suc_counts = df["sucursal"].value_counts().reset_index()
    suc_counts.columns = ["sucursal", "ventas"]
    fig3 = px.bar(suc_counts, x="ventas", y="sucursal", orientation="h",
                  color_discrete_sequence=["#00b4d8"])
    fig3.update_layout(yaxis_title="", height=320)
    st.plotly_chart(fig3)

st.subheader("Distribución Días hasta Venta")
fig4 = px.histogram(df, x="dias_hasta_venta", nbins=30,
                    color_discrete_sequence=["#90e0ef"])
fig4.update_layout(xaxis_title="Días", yaxis_title="Ventas", height=300)
st.plotly_chart(fig4)

st.divider()

# ── Filtros activos ────────────────────────────────────────────────────────
active = []
if st.session_state.sap_filter_modelo:
    active.append(f"Modelo: **{st.session_state.sap_filter_modelo}**")
if st.session_state.sap_filter_vendedor:
    active.append(f"Vendedor: **{st.session_state.sap_filter_vendedor}**")

if active:
    col_msg, col_btn = st.columns([5, 1])
    col_msg.info("Filtrando por: " + " · ".join(active))
    if col_btn.button("Limpiar filtros"):
        _reset_filters()
        st.rerun()

# ── Tabla filtrada ─────────────────────────────────────────────────────────
filtered = df.copy()
if st.session_state.sap_filter_modelo:
    filtered = filtered[filtered["modelo"] == st.session_state.sap_filter_modelo]
if st.session_state.sap_filter_vendedor:
    filtered = filtered[filtered["vendedor"] == st.session_state.sap_filter_vendedor]

st.subheader(f"Datos ({len(filtered):,} registros)")
st.dataframe(filtered, hide_index=True, height=400)
