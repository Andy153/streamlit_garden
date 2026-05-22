import json
import pandas as pd
import streamlit as st
from google.cloud import bigquery
from google.oauth2 import service_account

PROJECT = "vx-operation"


@st.cache_resource(show_spinner=False)
def get_client() -> bigquery.Client:
    try:
        secret = st.secrets["gcp_service_account_json"]
        info = json.loads(secret)
        creds = service_account.Credentials.from_service_account_info(
            info,
            scopes=["https://www.googleapis.com/auth/cloud-platform"],
        )
        return bigquery.Client(project=PROJECT, credentials=creds)
    except Exception:
        # Local: usa Application Default Credentials (gcloud auth)
        return bigquery.Client(project=PROJECT)


@st.cache_data(ttl=300, show_spinner="Consultando BigQuery...")
def run_query(sql: str) -> pd.DataFrame:
    return get_client().query(sql).to_dataframe()
