import functools
import pandas as pd
import streamlit as st
from google.cloud import bigquery

PROJECT = "vx-operation"


@st.cache_resource(show_spinner=False)
def get_client() -> bigquery.Client:
    return bigquery.Client(project=PROJECT)


def run_query(sql: str, ttl: int = 300) -> pd.DataFrame:
    """Execute a BigQuery SQL query and return a DataFrame. Results cached by default 5 min."""
    @st.cache_data(ttl=ttl, show_spinner="Consultando BigQuery...")
    def _query(sql: str) -> pd.DataFrame:
        client = get_client()
        return client.query(sql).to_dataframe()

    return _query(sql)
