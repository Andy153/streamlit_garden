import streamlit as st
import plotly.express as px
from utils.bq import run_query

st.set_page_config(page_title="CIO Deliveries · Garden", layout="wide")
st.title("CIO Deliveries · Email Marketing")

BRANDS = ["garden", "garden_bmw", "garden_chery", "garden_chevrolet",
          "garden_fiat", "garden_jeep", "garden_kia", "garden_mazda",
          "garden_mini", "garden_nissan", "garden_volvo"]

col_brand, col_days = st.columns([2, 1])
brand = col_brand.selectbox("Dataset / Marca", BRANDS, index=0)
days = col_days.selectbox("Período", [7, 14, 30, 60, 90], index=2, format_func=lambda x: f"Últimos {x} días")

df = run_query(f"""
    SELECT
        DATE(created_at) AS date,
        campaign_name,
        action_name,
        metric,
        last_metric,
        recipient,
        delivery_type,
        subject
    FROM `vx-operation.{brand}.cio_deliveries_metrics`
    WHERE created_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {days} DAY)
    ORDER BY created_at DESC
    LIMIT 10000
""")

if df.empty:
    st.warning("No hay datos para el período seleccionado.")
    st.stop()

# ── KPIs ───────────────────────────────────────────────────────────────────
total = len(df)
campaigns = df["campaign_name"].nunique()
recipients = df["recipient"].nunique()
metrics_dist = df["metric"].value_counts()
sent = int(metrics_dist.get("delivered", 0))
opened = int(metrics_dist.get("opened", 0))
clicked = int(metrics_dist.get("clicked", 0))

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total Eventos", f"{total:,}")
c2.metric("Campañas", f"{campaigns:,}")
c3.metric("Recipients únicos", f"{recipients:,}")
c4.metric("Delivered", f"{sent:,}")
c5.metric("Open Rate", f"{opened/sent*100:.1f}%" if sent else "—")

st.divider()

col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Distribución de Métricas")
    metric_counts = df["metric"].value_counts().reset_index()
    metric_counts.columns = ["metric", "count"]
    fig = px.bar(metric_counts, x="metric", y="count",
                 color="metric", color_discrete_sequence=px.colors.qualitative.Set2)
    fig.update_layout(showlegend=False, xaxis_title="", yaxis_title="Eventos", height=320)
    st.plotly_chart(fig, use_container_width=True)

with col_right:
    st.subheader("Eventos por Día")
    daily = df.groupby("date").size().reset_index(name="count")
    fig2 = px.line(daily, x="date", y="count", markers=True)
    fig2.update_layout(xaxis_title="", yaxis_title="Eventos", height=320)
    st.plotly_chart(fig2, use_container_width=True)

st.subheader("Top Campañas por Eventos")
top_campaigns = (
    df.groupby("campaign_name")
    .agg(
        eventos=("metric", "count"),
        delivered=("metric", lambda x: (x == "delivered").sum()),
        opened=("metric", lambda x: (x == "opened").sum()),
        clicked=("metric", lambda x: (x == "clicked").sum()),
    )
    .sort_values("eventos", ascending=False)
    .head(20)
    .reset_index()
)
st.dataframe(top_campaigns, use_container_width=True, height=350)

st.divider()
with st.expander("Datos crudos"):
    st.dataframe(df, use_container_width=True, height=300)
