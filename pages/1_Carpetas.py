import streamlit as st
import plotly.express as px
from utils.bq import run_query

st.set_page_config(page_title="Carpetas · Garden", layout="wide")
st.title("Carpetas · Pipeline de Ventas")

BRANDS = ["garden", "garden_bmw", "garden_chery", "garden_chevrolet",
          "garden_fiat", "garden_jeep", "garden_kia", "garden_mazda",
          "garden_mini", "garden_nissan", "garden_volvo"]

brand = st.selectbox("Dataset / Marca", BRANDS, index=0)

df = run_query(f"""
    SELECT
        fecha,
        estado,
        marca,
        modelo,
        vendedor,
        score_desc,
        fase,
        rubro,
        contactociudad,
        fecha_ins
    FROM `vx-operation.{brand}.carpetas_dynamics_deduped`
    WHERE fecha >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
    ORDER BY fecha DESC
    LIMIT 5000
""")

if df.empty:
    st.warning("No hay datos para el período seleccionado.")
    st.stop()

# ── KPIs ───────────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Carpetas", f"{len(df):,}")
c2.metric("Marcas únicas", df["marca"].nunique() if "marca" in df.columns else "—")
c3.metric("Vendedores únicos", df["vendedor"].nunique())
c4.metric("Modelos únicos", df["modelo"].nunique())

st.divider()

col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Por Estado")
    estado_counts = df["estado"].value_counts().reset_index()
    estado_counts.columns = ["estado", "count"]
    fig = px.bar(estado_counts, x="count", y="estado", orientation="h",
                 color="count", color_continuous_scale="Blues")
    fig.update_layout(showlegend=False, coloraxis_showscale=False,
                      yaxis_title="", xaxis_title="Carpetas", height=350)
    st.plotly_chart(fig, use_container_width=True)

with col_right:
    st.subheader("Por Modelo")
    modelo_counts = df["modelo"].value_counts().head(15).reset_index()
    modelo_counts.columns = ["modelo", "count"]
    fig2 = px.bar(modelo_counts, x="count", y="modelo", orientation="h",
                  color="count", color_continuous_scale="Teal")
    fig2.update_layout(showlegend=False, coloraxis_showscale=False,
                       yaxis_title="", xaxis_title="Carpetas", height=350)
    st.plotly_chart(fig2, use_container_width=True)

st.subheader("Por Fase")
if "fase" in df.columns:
    fase_counts = df["fase"].value_counts().reset_index()
    fase_counts.columns = ["fase", "count"]
    fig3 = px.pie(fase_counts, values="count", names="fase", hole=0.4)
    fig3.update_layout(height=300)
    st.plotly_chart(fig3, use_container_width=True)

st.divider()
st.subheader("Tabla de Carpetas")
st.dataframe(df, use_container_width=True, height=400)
