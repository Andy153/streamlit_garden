import streamlit as st

st.set_page_config(
    page_title="Garden Dashboard",
    page_icon="🌿",
    layout="wide",
)

st.title("Garden Dashboard")
st.markdown("Seleccioná una sección en el menú lateral.")

col1, col2, col3 = st.columns(3)
col1.page_link("pages/1_Carpetas.py", label="Carpetas / Pipeline", icon="📋")
col2.page_link("pages/2_CIO_Deliveries.py", label="CIO Deliveries", icon="📧")
col3.page_link("pages/3_Ventas_SAP.py", label="Ventas SAP", icon="💰")
