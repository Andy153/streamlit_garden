"""Garden Dashboard — multi-brand entry point. v2

URL paths: /kia  /bmw  /chery  /chevrolet  /fiat  /jeep  /mazda  /mini  /nissan  /volvo
           /difusiones
Each brand requires its own password (set in .streamlit/secrets.toml).
"""
import streamlit as st

from auth import is_authenticated, show_login
from brand_dashboard import render
from brands import BRANDS

st.set_page_config(
    page_title="Garden Dashboard",
    page_icon=":material/directions_car:",
    layout="wide",
    initial_sidebar_state="expanded",
)


def _make_page(brand_key: str):
    def _page():
        config = BRANDS[brand_key]
        if not is_authenticated(brand_key):
            show_login(brand_key, config)
            st.stop()
        render(brand_key, config)
    return _page


pages = [
    st.Page(_make_page(key), title=cfg["title"], url_path=key)
    for key, cfg in BRANDS.items()
]

from difusiones_app import render as _render_difusiones
pages.append(
    st.Page(_render_difusiones, title="Difusiones Preaprobados", url_path="difusiones")
)

nav = st.navigation(pages, position="hidden")
nav.run()
