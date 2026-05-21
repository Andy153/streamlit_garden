import streamlit as st
import plotly.express as px
from utils.bq import run_query

st.set_page_config(page_title="Ventas SAP · Garden", layout="wide")
st.title("Ventas SAP")

BRANDS_SAP = ["garden_bmw", "garden_chery", "garden_chevrolet",
              "garden_fiat", "garden_jeep", "garden_kia", "garden_mazda",
              "garden_mini", "garden_nissan", "garden_volvo"]

col_brand, col_days = st.columns([2, 1])
brand = col_brand.selectbox("Marca", BRANDS_SAP, index=0)
days = col_days.selectbox("Período", [30, 60, 90, 180, 365], index=1, format_func=lambda x: f"Últimos {x} días")

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

col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Ventas por Modelo")
    modelo_counts = df["modelo"].value_counts().head(15).reset_index()
    modelo_counts.columns = ["modelo", "ventas"]
    fig = px.bar(modelo_counts, x="ventas", y="modelo", orientation="h",
                 color="ventas", color_continuous_scale="Viridis")
    fig.update_layout(showlegend=False, coloraxis_showscale=False,
                      yaxis_title="", height=380)
    st.plotly_chart(fig, use_container_width=True)

with col_right:
    st.subheader("Origen de Lead")
    origen_counts = df["origen_lead"].value_counts().reset_index()
    origen_counts.columns = ["origen", "ventas"]
    fig2 = px.pie(origen_counts, values="ventas", names="origen", hole=0.4)
    fig2.update_layout(height=380)
    st.plotly_chart(fig2, use_container_width=True)

col_left2, col_right2 = st.columns(2)

with col_left2:
    st.subheader("Ventas por Sucursal")
    suc_counts = df["sucursal"].value_counts().reset_index()
    suc_counts.columns = ["sucursal", "ventas"]
    fig3 = px.bar(suc_counts, x="ventas", y="sucursal", orientation="h",
                  color_discrete_sequence=["#00b4d8"])
    fig3.update_layout(yaxis_title="", height=320)
    st.plotly_chart(fig3, use_container_width=True)

with col_right2:
    st.subheader("Distribución Días hasta Venta")
    fig4 = px.histogram(df, x="dias_hasta_venta", nbins=30,
                        color_discrete_sequence=["#90e0ef"])
    fig4.update_layout(xaxis_title="Días", yaxis_title="Ventas", height=320)
    st.plotly_chart(fig4, use_container_width=True)

st.divider()
with st.expander("Datos crudos"):
    st.dataframe(df, use_container_width=True, height=300)
