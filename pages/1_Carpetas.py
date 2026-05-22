import streamlit as st
import plotly.express as px
from utils.bq import run_query

st.set_page_config(page_title="Carpetas · Garden", layout="wide")
st.title("Carpetas · Pipeline de Ventas")

BRANDS = ["garden", "garden_bmw", "garden_chery", "garden_chevrolet",
          "garden_fiat", "garden_jeep", "garden_kia", "garden_mazda",
          "garden_mini", "garden_nissan", "garden_volvo"]


def _reset_filters():
    st.session_state.carpetas_filter_modelo = None
    st.session_state.carpetas_filter_vendedor = None


brand = st.selectbox("Dataset / Marca", BRANDS, index=0, on_change=_reset_filters)

st.session_state.setdefault("carpetas_filter_modelo", None)
st.session_state.setdefault("carpetas_filter_vendedor", None)

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
    st.plotly_chart(fig)

with col_right:
    st.subheader("Por Modelo — click para filtrar")
    modelo_counts = df["modelo"].value_counts().head(15).reset_index()
    modelo_counts.columns = ["modelo", "count"]
    fig2 = px.bar(modelo_counts, x="count", y="modelo", orientation="h",
                  color="count", color_continuous_scale="Teal")
    fig2.update_layout(showlegend=False, coloraxis_showscale=False,
                       yaxis_title="", xaxis_title="Carpetas", height=350)
    ev_modelo = st.plotly_chart(fig2, on_select="rerun", key="carpetas_chart_modelo")
    if ev_modelo.selection.points:
        st.session_state.carpetas_filter_modelo = ev_modelo.selection.points[0]["y"]
    else:
        st.session_state.carpetas_filter_modelo = None

col_left2, col_right2 = st.columns(2)

with col_left2:
    st.subheader("Por Fase")
    if "fase" in df.columns:
        fase_counts = df["fase"].value_counts().reset_index()
        fase_counts.columns = ["fase", "count"]
        fig3 = px.pie(fase_counts, values="count", names="fase", hole=0.4)
        fig3.update_layout(height=350)
        st.plotly_chart(fig3)

with col_right2:
    st.subheader("Por Vendedor — click para filtrar")
    vendedor_counts = df["vendedor"].value_counts().head(15).reset_index()
    vendedor_counts.columns = ["vendedor", "count"]
    fig4 = px.bar(vendedor_counts, x="count", y="vendedor", orientation="h",
                  color="count", color_continuous_scale="Oranges")
    fig4.update_layout(showlegend=False, coloraxis_showscale=False,
                       yaxis_title="", xaxis_title="Carpetas", height=350)
    ev_vendedor = st.plotly_chart(fig4, on_select="rerun", key="carpetas_chart_vendedor")
    if ev_vendedor.selection.points:
        st.session_state.carpetas_filter_vendedor = ev_vendedor.selection.points[0]["y"]
    else:
        st.session_state.carpetas_filter_vendedor = None

st.divider()

# ── Filtros activos ────────────────────────────────────────────────────────
active = []
if st.session_state.carpetas_filter_modelo:
    active.append(f"Modelo: **{st.session_state.carpetas_filter_modelo}**")
if st.session_state.carpetas_filter_vendedor:
    active.append(f"Vendedor: **{st.session_state.carpetas_filter_vendedor}**")

if active:
    col_msg, col_btn = st.columns([5, 1])
    col_msg.info("Filtrando por: " + " · ".join(active))
    if col_btn.button("Limpiar filtros"):
        _reset_filters()
        st.rerun()

# ── Tabla filtrada ─────────────────────────────────────────────────────────
filtered = df.copy()
if st.session_state.carpetas_filter_modelo:
    filtered = filtered[filtered["modelo"] == st.session_state.carpetas_filter_modelo]
if st.session_state.carpetas_filter_vendedor:
    filtered = filtered[filtered["vendedor"] == st.session_state.carpetas_filter_vendedor]

st.subheader(f"Tabla de Carpetas ({len(filtered):,} registros)")
st.dataframe(filtered, hide_index=True, height=400)
