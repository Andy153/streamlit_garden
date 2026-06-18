"""Difusión Preaprobados — ruta /difusiones dentro del Garden Dashboard."""

from __future__ import annotations

import hashlib
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed

import altair as alt
import pandas as pd
import streamlit as st

from utils.bq import get_client

# ─── Configuración de marcas ──────────────────────────────────────────────────

BRANDS: dict[str, dict] = {
    "BMW":       {"dataset": "garden_bmw",       "has_objecion": True,  "large_table": False},
    "FIAT":      {"dataset": "garden_fiat",      "has_objecion": True,  "large_table": False},
    "Chevrolet": {"dataset": "garden_chevrolet", "has_objecion": True,  "large_table": False},
    "KIA":       {"dataset": "garden_kia",       "has_objecion": False, "large_table": True},
    "Nissan":    {"dataset": "garden_nissan",    "has_objecion": True,  "large_table": True},
    "Mazda":     {"dataset": "garden_mazda",     "has_objecion": True,  "large_table": False},
    "Jeep/RAM":  {"dataset": "garden_jeep",      "has_objecion": True,  "large_table": False},
    "MINI":      {"dataset": "garden_mini",      "has_objecion": True,  "large_table": False},
}

EXCLUDED_AGENTS = [
    "FERNANDO SANABRIA",
    "Augusto Saldívar",
    "Natalia Gutierrez",
    "Sol Esquivel",
]

BUCKET_ORDER = [
    "< 30 min",
    "30-60 min",
    "1-2 horas",
    "2-4 horas",
    "> 4 horas",
    "Sin respuesta",
]

BUCKET_COLORS = {
    "< 30 min":      "#22c55e",
    "30-60 min":     "#84cc16",
    "1-2 horas":     "#eab308",
    "2-4 horas":     "#f97316",
    "> 4 horas":     "#ef4444",
    "Sin respuesta": "#6b7280",
}

# ─── SQL Builder ──────────────────────────────────────────────────────────────

def build_query(dataset: str, has_objecion: bool, large_table: bool) -> str:
    excluded_list = ", ".join(f"'{a}'" for a in EXCLUDED_AGENTS)
    objecion_col = (
        "a.objecion_preaprobacion"
        if has_objecion
        else "NULL AS objecion_preaprobacion"
    )
    atributos_where = (
        "\n  WHERE internal_customer_id IN (SELECT internal_customer_id FROM aceptados)"
        if large_table
        else ""
    )
    return f"""
WITH aceptados AS (
  SELECT DISTINCT internal_customer_id
  FROM `vx-operation.{dataset}.cio_people_data_with_attributes`
  WHERE LOWER(TRIM(CAST(promo_aceptada AS STRING))) = 'true'
    AND LOWER(TRIM(CAST(promo AS STRING))) = 'difusion_preaprobados'
),

primera_difusion AS (
  SELECT
    internal_customer_id,
    MIN(timestamp)                                              AS ts_difusion_utc,
    DATETIME(MIN(timestamp), 'America/Argentina/Buenos_Aires') AS ts_difusion_ar
  FROM `vx-operation.{dataset}.cio_events`
  WHERE timestamp >= TIMESTAMP('2026-01-01')
    AND name = 'envio_promo_difusion_preaprobados'
  GROUP BY internal_customer_id
),

primera_respuesta AS (
  SELECT
    e.internal_customer_id,
    DATETIME(MIN(e.timestamp), 'America/Argentina/Buenos_Aires') AS ts_respuesta_ar,
    JSON_VALUE(
      ARRAY_AGG(e.data ORDER BY e.timestamp ASC LIMIT 1)[OFFSET(0)],
      '$.agent_name'
    ) AS agente_respuesta
  FROM `vx-operation.{dataset}.cio_events` e
  INNER JOIN primera_difusion d ON e.internal_customer_id = d.internal_customer_id
  WHERE e.timestamp >= TIMESTAMP('2026-01-01')
    AND e.name = 'gochat_outbound_message_sent'
    AND e.timestamp > d.ts_difusion_utc
    AND JSON_VALUE(e.data, '$.agent_name') NOT IN ({excluded_list})
  GROUP BY e.internal_customer_id
),

primera_respuesta_todos AS (
  SELECT
    e.internal_customer_id,
    DATETIME(MIN(e.timestamp), 'America/Argentina/Buenos_Aires') AS ts_respuesta_ar
  FROM `vx-operation.{dataset}.cio_events` e
  INNER JOIN primera_difusion d ON e.internal_customer_id = d.internal_customer_id
  WHERE e.timestamp >= TIMESTAMP('2026-01-01')
    AND e.name = 'gochat_outbound_message_sent'
    AND e.timestamp > d.ts_difusion_utc
  GROUP BY e.internal_customer_id
),

atributos AS (
  SELECT *
  FROM `vx-operation.{dataset}.cio_people_data_with_attributes`{atributos_where}
  QUALIFY ROW_NUMBER() OVER (PARTITION BY internal_customer_id ORDER BY _created_at DESC) = 1
),

dias_habiles AS (
  SELECT
    d.internal_customer_id,
    d.ts_difusion_ar,
    r.ts_respuesta_ar,
    dia
  FROM primera_difusion d
  INNER JOIN primera_respuesta r ON d.internal_customer_id = r.internal_customer_id,
  UNNEST(GENERATE_DATE_ARRAY(DATE(d.ts_difusion_ar), DATE(r.ts_respuesta_ar))) AS dia
  WHERE EXTRACT(DAYOFWEEK FROM dia) BETWEEN 2 AND 6
),

minutos_habiles AS (
  SELECT
    internal_customer_id,
    SUM(GREATEST(0, DATETIME_DIFF(
      CASE WHEN ts_respuesta_ar < DATETIME(dia, TIME(18, 0, 0))
           THEN ts_respuesta_ar
           ELSE DATETIME(dia, TIME(18, 0, 0)) END,
      CASE WHEN ts_difusion_ar > DATETIME(dia, TIME(8, 0, 0))
           THEN ts_difusion_ar
           ELSE DATETIME(dia, TIME(8, 0, 0)) END,
      MINUTE
    ))) AS biz_minutes
  FROM dias_habiles
  GROUP BY internal_customer_id
),

dias_habiles_todos AS (
  SELECT
    d.internal_customer_id,
    d.ts_difusion_ar,
    rt.ts_respuesta_ar,
    dia
  FROM primera_difusion d
  INNER JOIN primera_respuesta_todos rt ON d.internal_customer_id = rt.internal_customer_id,
  UNNEST(GENERATE_DATE_ARRAY(DATE(d.ts_difusion_ar), DATE(rt.ts_respuesta_ar))) AS dia
  WHERE EXTRACT(DAYOFWEEK FROM dia) BETWEEN 2 AND 6
),

minutos_habiles_todos AS (
  SELECT
    internal_customer_id,
    SUM(GREATEST(0, DATETIME_DIFF(
      CASE WHEN ts_respuesta_ar < DATETIME(dia, TIME(18, 0, 0))
           THEN ts_respuesta_ar
           ELSE DATETIME(dia, TIME(18, 0, 0)) END,
      CASE WHEN ts_difusion_ar > DATETIME(dia, TIME(8, 0, 0))
           THEN ts_difusion_ar
           ELSE DATETIME(dia, TIME(8, 0, 0)) END,
      MINUTE
    ))) AS biz_minutes_todos
  FROM dias_habiles_todos
  GROUP BY internal_customer_id
)

SELECT
  d.internal_customer_id,
  a.last_name                                         AS apellido,
  a.id                                                AS telefono,
  a.agente_asignado,
  d.ts_difusion_ar                                    AS fecha_difusion,
  FORMAT_DATETIME('%A', d.ts_difusion_ar)             AS dia_semana_difusion,
  r.ts_respuesta_ar                                   AS fecha_primera_respuesta,
  r.agente_respuesta,
  CASE WHEN r.internal_customer_id IS NOT NULL
       THEN 1 ELSE 0 END                              AS respondio_agente,
  m.biz_minutes                                       AS minutos_habiles_respuesta,
  COALESCE(m.biz_minutes, mt.biz_minutes_todos)       AS minutos_habiles_respuesta_todos,
  CASE
    WHEN m.biz_minutes IS NULL THEN 'Sin respuesta'
    WHEN m.biz_minutes < 30    THEN '< 30 min'
    WHEN m.biz_minutes < 60    THEN '30-60 min'
    WHEN m.biz_minutes < 120   THEN '1-2 horas'
    WHEN m.biz_minutes < 240   THEN '2-4 horas'
    ELSE                            '> 4 horas'
  END                                                 AS bucket_respuesta,
  {objecion_col},
  a.actitud_preaprobacion,
  a.etapa_funnel
FROM primera_difusion d
INNER JOIN aceptados ac
  ON d.internal_customer_id = ac.internal_customer_id
LEFT JOIN primera_respuesta r
  ON d.internal_customer_id = r.internal_customer_id
LEFT JOIN atributos a
  ON d.internal_customer_id = a.internal_customer_id
LEFT JOIN minutos_habiles m
  ON d.internal_customer_id = m.internal_customer_id
LEFT JOIN minutos_habiles_todos mt
  ON d.internal_customer_id = mt.internal_customer_id
"""


# ─── BigQuery ─────────────────────────────────────────────────────────────────

@st.cache_data(ttl=3600, show_spinner=False)
def load_brand_data(brand: str, query_hash: str) -> pd.DataFrame:
    cfg = BRANDS[brand]
    query = build_query(cfg["dataset"], cfg["has_objecion"], cfg["large_table"])
    client = get_client()
    try:
        rows = client.query_and_wait(query)
        df = rows.to_dataframe(create_bqstorage_client=False)
    except Exception:
        job = client.query(query)
        df = job.result().to_arrow().to_pandas()
    df["marca"] = brand
    return df


def _load_brand_task(brand: str) -> tuple[str, pd.DataFrame]:
    cfg = BRANDS[brand]
    query = build_query(cfg["dataset"], cfg["has_objecion"], cfg["large_table"])
    query_hash = hashlib.md5(query.encode()).hexdigest()[:8]
    return brand, load_brand_data(brand, query_hash)


def render() -> None:
    # ─── Sidebar ─────────────────────────────────────────────────────────────

    with st.sidebar:
        all_brand_keys = list(BRANDS.keys())

        if "dif_brand_selection" not in st.session_state:
            st.session_state["dif_brand_selection"] = {b: True for b in all_brand_keys}

        label = (
            "Todas las marcas"
            if all(st.session_state["dif_brand_selection"].values())
            else f"{sum(st.session_state['dif_brand_selection'].values())} marcas seleccionadas"
        )

        with st.popover(f":material/store: {label}", use_container_width=True):

            def _toggle_all_cb():
                val = st.session_state["dif_toggle_all"]
                for _b in all_brand_keys:
                    st.session_state["dif_brand_selection"][_b] = val
                    st.session_state[f"dif_brand_{_b}"] = val

            st.checkbox(
                "Todas",
                value=all(st.session_state["dif_brand_selection"].values()),
                key="dif_toggle_all",
                on_change=_toggle_all_cb,
            )

            for brand in all_brand_keys:
                col_chk, col_btn = st.columns([5, 2], vertical_alignment="center")

                def _brand_cb(_b=brand):
                    st.session_state["dif_brand_selection"][_b] = st.session_state[f"dif_brand_{_b}"]
                    st.session_state["dif_toggle_all"] = all(
                        st.session_state["dif_brand_selection"].values()
                    )

                def _solo_cb(_b=brand):
                    for b2 in all_brand_keys:
                        st.session_state["dif_brand_selection"][b2] = (b2 == _b)
                        st.session_state[f"dif_brand_{b2}"] = (b2 == _b)
                    st.session_state["dif_toggle_all"] = False

                with col_chk:
                    st.checkbox(
                        brand,
                        value=st.session_state["dif_brand_selection"][brand],
                        key=f"dif_brand_{brand}",
                        on_change=_brand_cb,
                    )
                with col_btn:
                    st.button("Solo", key=f"dif_solo_{brand}", type="tertiary", on_click=_solo_cb)

        selected_brands: list[str] = [
            b for b, v in st.session_state["dif_brand_selection"].items() if v
        ]

        st.divider()

        if st.button(":material/refresh: Actualizar datos", use_container_width=True):
            load_brand_data.clear()
            st.session_state.pop("dif_last_refresh", None)
            st.rerun()

        if "dif_last_refresh" in st.session_state:
            st.caption(f"Última actualización: {st.session_state['dif_last_refresh']}")

    # ─── Header ──────────────────────────────────────────────────────────────

    st.markdown("# :material/directions_car: Difusión Preaprobados")
    st.markdown("**Garden Automotores Paraguay** — Análisis multi-marca de preaprobados")
    st.divider()

    if not selected_brands:
        st.info(":material/info: Seleccioná al menos una marca en el panel lateral.")
        st.stop()

    # ─── Carga de datos ──────────────────────────────────────────────────────

    dfs: list[pd.DataFrame] = []
    load_errors: list[str] = []

    progress_bar = st.progress(0, text=f"Consultando BigQuery — 0 / {len(selected_brands)} marcas…")
    completed = 0

    with ThreadPoolExecutor(max_workers=len(selected_brands)) as pool:
        futures = {
            pool.submit(_load_brand_task, brand): brand
            for brand in selected_brands
        }
        for future in as_completed(futures):
            brand = futures[future]
            completed += 1
            progress_bar.progress(
                completed / len(selected_brands),
                text=f"Completado {brand} — {completed} / {len(selected_brands)} marcas…",
            )
            try:
                _, df_brand = future.result()
                dfs.append(df_brand)
            except Exception as exc:
                load_errors.append(
                    f"**{brand}**: `{type(exc).__name__}` — {exc}\n\n"
                    f"```\n{traceback.format_exc()}\n```"
                )

    progress_bar.empty()

    if dfs and "dif_last_refresh" not in st.session_state:
        from datetime import datetime
        st.session_state["dif_last_refresh"] = datetime.now().strftime("%d/%m/%Y %H:%M")
        st.rerun()

    if load_errors:
        with st.expander(f":material/warning: {len(load_errors)} error(es) al cargar"):
            for err in load_errors:
                st.error(err)

    if not dfs:
        st.error("No se pudieron cargar datos de ninguna marca seleccionada.")
        st.stop()

    df = pd.concat(dfs, ignore_index=True)

    # ─── KPI Cards ───────────────────────────────────────────────────────────

    total = len(df)
    respondio_count = int((df["respondio_agente"] == 1).sum())
    pct_resp = respondio_count / total * 100 if total else 0
    no_comercial_count = int((df["respondio_agente"] == 0).sum())
    pct_no_comercial = no_comercial_count / total * 100 if total else 0
    sin_resp_count = int((df["bucket_respuesta"] == "Sin respuesta").sum())
    pct_sin = sin_resp_count / total * 100 if total else 0

    with_time = df[df["minutos_habiles_respuesta_todos"].notna()]
    avg_h = with_time["minutos_habiles_respuesta_todos"].mean() / 60 if not with_time.empty else 0
    med_h = with_time["minutos_habiles_respuesta_todos"].median() / 60 if not with_time.empty else 0

    with st.container(horizontal=True):
        st.metric("Total difundidos", f"{total:,}", border=True)
        st.metric(
            "Respondió agente comercial",
            f"{respondio_count:,}",
            f"{pct_resp:.1f}%",
            border=True,
        )
        st.metric(
            "Sin respuesta de agente comercial",
            f"{no_comercial_count:,}",
            f"{pct_no_comercial:.1f}% del total",
            delta_color="inverse",
            border=True,
        )
        st.metric(
            "Sin respuesta (nadie)",
            f"{sin_resp_count:,}",
            f"{pct_sin:.1f}% del total",
            delta_color="inverse",
            border=True,
        )
        st.metric(
            "Tiempo promedio (hs hábiles)",
            f"{avg_h:.1f} h",
            f"mediana {med_h:.1f} h",
            border=True,
            help="Incluye respuestas de agentes no comerciales",
        )

    st.space("medium")

    # ─── Tabs ────────────────────────────────────────────────────────────────

    tab_marcas, tab_agentes, tab_sin_resp, tab_actitud, tab_detalle = st.tabs([
        ":material/store: Por Marca",
        ":material/person: Por Agente",
        ":material/person_off: Sin Respuesta",
        ":material/psychology: Actitud / Objeción",
        ":material/table: Tabla Detalle",
    ])

    # ── Tab Por Marca ─────────────────────────────────────────────────────────

    with tab_marcas:
        if len(selected_brands) < 2:
            st.info(":material/info: Seleccioná múltiples marcas para ver la comparación.")
        else:
            marca_agg = (
                df.groupby("marca")
                .agg(
                    total=("internal_customer_id", "count"),
                    respondio=("respondio_agente", "sum"),
                )
                .reset_index()
            )
            marca_agg["no_respondio"] = marca_agg["total"] - marca_agg["respondio"]
            marca_agg["pct_resp"] = marca_agg["respondio"] / marca_agg["total"] * 100

            col1, col2 = st.columns(2)

            with col1:
                with st.container(border=True):
                    st.markdown("**Leads por Marca (apilado)**")
                    marca_long = marca_agg.melt(
                        id_vars=["marca"],
                        value_vars=["respondio", "no_respondio"],
                        var_name="estado",
                        value_name="count",
                    )
                    marca_long["estado"] = marca_long["estado"].map(
                        {"respondio": "Con respuesta", "no_respondio": "Sin respuesta"}
                    )
                    chart_marcas = (
                        alt.Chart(marca_long)
                        .mark_bar()
                        .encode(
                            y=alt.Y("marca:N", sort="-x", title=None),
                            x=alt.X("count:Q", title="Leads"),
                            color=alt.Color(
                                "estado:N",
                                scale=alt.Scale(
                                    domain=["Con respuesta", "Sin respuesta"],
                                    range=["#22c55e", "#6b7280"],
                                ),
                                legend=alt.Legend(title=None, orient="bottom"),
                            ),
                            order=alt.Order("estado:N", sort="descending"),
                            tooltip=[
                                alt.Tooltip("marca:N", title="Marca"),
                                alt.Tooltip("estado:N", title="Estado"),
                                alt.Tooltip("count:Q", title="Leads"),
                            ],
                        )
                        .properties(height=300)
                    )
                    st.altair_chart(chart_marcas, use_container_width=True)

            with col2:
                with st.container(border=True):
                    st.markdown("**% Respuesta por Marca**")
                    chart_pct = (
                        alt.Chart(marca_agg)
                        .mark_bar(cornerRadiusTopRight=4, cornerRadiusBottomRight=4)
                        .encode(
                            y=alt.Y("marca:N", sort="-x", title=None),
                            x=alt.X(
                                "pct_resp:Q",
                                title="% con respuesta",
                                scale=alt.Scale(domain=[0, 100]),
                            ),
                            color=alt.Color(
                                "pct_resp:Q",
                                scale=alt.Scale(scheme="greens"),
                                legend=None,
                            ),
                            tooltip=[
                                alt.Tooltip("marca:N", title="Marca"),
                                alt.Tooltip("pct_resp:Q", title="% Respuesta", format=".1f"),
                                alt.Tooltip("respondio:Q", title="Respondidos"),
                                alt.Tooltip("total:Q", title="Total"),
                            ],
                        )
                        .properties(height=300)
                    )
                    st.altair_chart(chart_pct, use_container_width=True)

            with st.container(border=True):
                st.markdown("**Distribución de Bucket por Marca**")
                bm = (
                    df.groupby(["marca", "bucket_respuesta"])
                    .size()
                    .reset_index(name="count")
                )
                bm_total = bm.groupby("marca")["count"].transform("sum")
                bm["pct"] = bm["count"] / bm_total * 100

                chart_heat = (
                    alt.Chart(bm)
                    .mark_rect()
                    .encode(
                        x=alt.X("bucket_respuesta:N", sort=BUCKET_ORDER, title=None),
                        y=alt.Y("marca:N", title=None),
                        color=alt.Color(
                            "pct:Q",
                            scale=alt.Scale(scheme="blues"),
                            title="% del total",
                        ),
                        tooltip=[
                            alt.Tooltip("marca:N", title="Marca"),
                            alt.Tooltip("bucket_respuesta:N", title="Bucket"),
                            alt.Tooltip("count:Q", title="Leads"),
                            alt.Tooltip("pct:Q", title="%", format=".1f"),
                        ],
                    )
                    .properties(height=280)
                )
                st.altair_chart(chart_heat, use_container_width=True)

    # ── Tab Por Agente ────────────────────────────────────────────────────────

    with tab_agentes:
        respondidos = df[
            (df["respondio_agente"] == 1)
            & (~df["agente_respuesta"].isin(EXCLUDED_AGENTS))
        ].copy()

        if respondidos.empty:
            st.info("No hay registros de agentes comerciales que respondieron.")
        else:
            col1, col2 = st.columns(2)

            with col1:
                with st.container(border=True):
                    st.markdown("**Top 15 Agentes Comerciales**")
                    top_agentes = (
                        respondidos["agente_respuesta"]
                        .dropna()
                        .value_counts()
                        .head(15)
                        .reset_index()
                    )
                    top_agentes.columns = ["agente", "count"]

                    chart_ag = (
                        alt.Chart(top_agentes)
                        .mark_bar(cornerRadiusTopRight=4, cornerRadiusBottomRight=4)
                        .encode(
                            y=alt.Y("agente:N", sort="-x", title=None),
                            x=alt.X("count:Q", title="Respuestas"),
                            color=alt.value("#60A5FA"),
                            tooltip=[
                                alt.Tooltip("agente:N", title="Agente"),
                                alt.Tooltip("count:Q", title="Respuestas"),
                            ],
                        )
                        .properties(height=420)
                    )
                    st.altair_chart(chart_ag, use_container_width=True)

            with col2:
                with st.container(border=True):
                    st.markdown("**Tiempo Promedio de Respuesta por Agente (hs hábiles)**")
                    tiempo_ag = (
                        respondidos[respondidos["minutos_habiles_respuesta"].notna()]
                        .groupby("agente_respuesta")
                        .agg(
                            avg_min=("minutos_habiles_respuesta", "mean"),
                            n=("minutos_habiles_respuesta", "count"),
                        )
                        .reset_index()
                        .sort_values("n", ascending=False)
                        .head(15)
                    )
                    tiempo_ag["avg_h"] = tiempo_ag["avg_min"] / 60
                    tiempo_ag = tiempo_ag.rename(columns={"agente_respuesta": "agente"})

                    chart_time = (
                        alt.Chart(tiempo_ag)
                        .mark_bar(cornerRadiusTopRight=4, cornerRadiusBottomRight=4)
                        .encode(
                            y=alt.Y("agente:N", sort="-x", title=None),
                            x=alt.X("avg_h:Q", title="Horas hábiles (promedio)"),
                            color=alt.Color(
                                "avg_h:Q",
                                scale=alt.Scale(scheme="oranges"),
                                legend=None,
                            ),
                            tooltip=[
                                alt.Tooltip("agente:N", title="Agente"),
                                alt.Tooltip("avg_h:Q", title="Promedio (h)", format=".2f"),
                                alt.Tooltip("n:Q", title="Respuestas"),
                            ],
                        )
                        .properties(height=420)
                    )
                    st.altair_chart(chart_time, use_container_width=True)

            with st.container(border=True):
                st.markdown("**Resumen por Agente**")
                resumen_ag = (
                    respondidos.groupby("agente_respuesta")
                    .agg(
                        respuestas=("internal_customer_id", "count"),
                        avg_min=("minutos_habiles_respuesta", "mean"),
                    )
                    .reset_index()
                    .sort_values("respuestas", ascending=False)
                )
                resumen_ag["avg_h"] = (resumen_ag["avg_min"] / 60).round(1)
                resumen_ag = resumen_ag.drop(columns=["avg_min"])
                resumen_ag.columns = ["Agente", "Respuestas", "Tiempo Prom. (h)"]
                st.dataframe(resumen_ag, hide_index=True, height=300)

    # ── Tab Sin Respuesta ─────────────────────────────────────────────────────

    with tab_sin_resp:
        sin_resp_df = df[df["respondio_agente"] == 0].copy()
        total_sin = len(sin_resp_df)

        if sin_resp_df.empty:
            st.success("¡Todos los leads recibieron respuesta de un agente comercial!")
        else:
            with st.container(horizontal=True):
                st.metric("Sin respuesta comercial", f"{total_sin:,}", border=True)
                st.metric(
                    "% del total difundido",
                    f"{total_sin / total * 100:.1f}%",
                    border=True,
                )
                if len(selected_brands) > 1:
                    marca_max = sin_resp_df["marca"].value_counts().idxmax()
                    st.metric("Marca con más pendientes", marca_max, border=True)

            st.space("small")
            col1, col2 = st.columns(2)

            with col1:
                with st.container(border=True):
                    st.markdown("**Sin respuesta por Marca**")
                    sr_marca = sin_resp_df["marca"].value_counts().reset_index()
                    sr_marca.columns = ["marca", "count"]
                    sr_marca["pct_total"] = (
                        sr_marca["count"]
                        / df.groupby("marca").size().reindex(sr_marca["marca"]).values
                        * 100
                    )
                    chart_sr_marca = (
                        alt.Chart(sr_marca)
                        .mark_bar(cornerRadiusTopRight=4, cornerRadiusBottomRight=4)
                        .encode(
                            y=alt.Y("marca:N", sort="-x", title=None),
                            x=alt.X("count:Q", title="Leads sin respuesta"),
                            color=alt.value("#ef4444"),
                            tooltip=[
                                alt.Tooltip("marca:N", title="Marca"),
                                alt.Tooltip("count:Q", title="Sin respuesta"),
                                alt.Tooltip("pct_total:Q", title="% del total marca", format=".1f"),
                            ],
                        )
                        .properties(height=300)
                    )
                    st.altair_chart(chart_sr_marca, use_container_width=True)

            with col2:
                with st.container(border=True):
                    st.markdown("**Sin respuesta por Agente Asignado**")
                    sr_agente = (
                        sin_resp_df["agente_asignado"]
                        .dropna()
                        .value_counts()
                        .head(15)
                        .reset_index()
                    )
                    sr_agente.columns = ["agente", "count"]
                    chart_sr_ag = (
                        alt.Chart(sr_agente)
                        .mark_bar(cornerRadiusTopRight=4, cornerRadiusBottomRight=4)
                        .encode(
                            y=alt.Y("agente:N", sort="-x", title=None),
                            x=alt.X("count:Q", title="Leads sin respuesta"),
                            color=alt.value("#f97316"),
                            tooltip=[
                                alt.Tooltip("agente:N", title="Agente Asignado"),
                                alt.Tooltip("count:Q", title="Sin respuesta"),
                            ],
                        )
                        .properties(height=300)
                    )
                    st.altair_chart(chart_sr_ag, use_container_width=True)

            with st.container(border=True):
                st.markdown("**Sin respuesta por Actitud Preaprobación**")
                sr_actitud = (
                    sin_resp_df["actitud_preaprobacion"].dropna().value_counts().reset_index()
                )
                sr_actitud.columns = ["actitud", "count"]

                if sr_actitud.empty:
                    st.info("Sin datos de actitud para este segmento.")
                else:
                    chart_sr_act = (
                        alt.Chart(sr_actitud)
                        .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
                        .encode(
                            x=alt.X("actitud:N", sort="-y", title=None),
                            y=alt.Y("count:Q", title="Leads"),
                            color=alt.value("#a855f7"),
                            tooltip=[
                                alt.Tooltip("actitud:N", title="Actitud"),
                                alt.Tooltip("count:Q", title="Leads"),
                            ],
                        )
                        .properties(height=250)
                    )
                    st.altair_chart(chart_sr_act, use_container_width=True)

            st.divider()
            st.markdown("**Listado completo — Sin respuesta de agente comercial**")
            sin_resp_df["horas_habiles"] = (sin_resp_df["minutos_habiles_respuesta"] / 60).round(2)

            st.dataframe(
                sin_resp_df[[
                    "marca", "internal_customer_id", "apellido", "telefono",
                    "agente_asignado", "fecha_difusion",
                    "actitud_preaprobacion", "objecion_preaprobacion",
                ]],
                column_config={
                    "marca":                  st.column_config.TextColumn("Marca"),
                    "internal_customer_id":   st.column_config.TextColumn("ID"),
                    "apellido":               st.column_config.TextColumn("Apellido"),
                    "telefono":               st.column_config.TextColumn("Teléfono"),
                    "agente_asignado":        st.column_config.TextColumn("Agente Asignado"),
                    "fecha_difusion":         st.column_config.DatetimeColumn(
                                                  "Fecha Difusión", format="DD/MM/YYYY HH:mm"
                                              ),
                    "actitud_preaprobacion":  st.column_config.TextColumn("Actitud"),
                    "objecion_preaprobacion": st.column_config.TextColumn("Objeción"),
                },
                hide_index=True,
                height=400,
            )

            csv_sr = sin_resp_df[[
                "marca", "internal_customer_id", "apellido", "telefono",
                "agente_asignado", "fecha_difusion",
                "actitud_preaprobacion", "objecion_preaprobacion",
            ]].to_csv(index=False).encode("utf-8")
            st.download_button(
                label=":material/download: Descargar CSV — Sin Respuesta",
                data=csv_sr,
                file_name="sin_respuesta_comercial.csv",
                mime="text/csv",
            )

    # ── Tab Actitud / Objeción ────────────────────────────────────────────────

    with tab_actitud:
        col1, col2 = st.columns(2)

        with col1:
            with st.container(border=True):
                st.markdown("**Actitud Preaprobación**")
                actitud_counts = df["actitud_preaprobacion"].dropna().value_counts().reset_index()
                actitud_counts.columns = ["actitud", "count"]

                if actitud_counts.empty:
                    st.info("Sin datos de actitud disponibles.")
                else:
                    chart_act = (
                        alt.Chart(actitud_counts)
                        .mark_arc(innerRadius=55, outerRadius=110)
                        .encode(
                            theta=alt.Theta("count:Q"),
                            color=alt.Color(
                                "actitud:N",
                                legend=alt.Legend(title=None, orient="bottom"),
                            ),
                            tooltip=[
                                alt.Tooltip("actitud:N", title="Actitud"),
                                alt.Tooltip("count:Q", title="Leads"),
                            ],
                        )
                        .properties(height=300)
                    )
                    st.altair_chart(chart_act, use_container_width=True)

        with col2:
            with st.container(border=True):
                st.markdown("**Objeción Preaprobación**")
                obj_counts = df["objecion_preaprobacion"].dropna().value_counts().reset_index()
                obj_counts.columns = ["objecion", "count"]

                if obj_counts.empty:
                    st.info("Sin datos de objeción (KIA no tiene esta columna).")
                else:
                    chart_obj = (
                        alt.Chart(obj_counts)
                        .mark_arc(innerRadius=55, outerRadius=110)
                        .encode(
                            theta=alt.Theta("count:Q"),
                            color=alt.Color(
                                "objecion:N",
                                legend=alt.Legend(title=None, orient="bottom"),
                            ),
                            tooltip=[
                                alt.Tooltip("objecion:N", title="Objeción"),
                                alt.Tooltip("count:Q", title="Leads"),
                            ],
                        )
                        .properties(height=300)
                    )
                    st.altair_chart(chart_obj, use_container_width=True)

    # ── Tab Tabla Detalle ─────────────────────────────────────────────────────

    with tab_detalle:
        with st.container(horizontal=True, vertical_alignment="bottom"):
            bucket_filter = st.multiselect(
                "Bucket",
                options=BUCKET_ORDER,
                default=BUCKET_ORDER,
            )
            marca_filter = st.multiselect(
                "Marca",
                options=selected_brands,
                default=selected_brands,
            )

        mask = df["bucket_respuesta"].isin(bucket_filter) & df["marca"].isin(marca_filter)
        filtered = df[mask].copy()
        filtered["horas_habiles"] = (filtered["minutos_habiles_respuesta"] / 60).round(2)

        display_cols = [
            "marca", "internal_customer_id", "apellido", "telefono",
            "agente_asignado", "etapa_funnel", "fecha_difusion",
            "fecha_primera_respuesta", "agente_respuesta", "respondio_agente",
            "horas_habiles", "bucket_respuesta", "actitud_preaprobacion",
            "objecion_preaprobacion",
        ]

        st.dataframe(
            filtered[display_cols],
            column_config={
                "marca":                   st.column_config.TextColumn("Marca"),
                "internal_customer_id":    st.column_config.TextColumn("ID"),
                "apellido":               st.column_config.TextColumn("Apellido"),
                "telefono":                st.column_config.TextColumn("Teléfono"),
                "agente_asignado":         st.column_config.TextColumn("Agente Asignado"),
                "etapa_funnel":            st.column_config.TextColumn("Etapa Funnel"),
                "fecha_difusion":          st.column_config.DatetimeColumn(
                                               "Fecha Difusión", format="DD/MM/YYYY HH:mm"
                                           ),
                "fecha_primera_respuesta": st.column_config.DatetimeColumn(
                                               "Fecha Respuesta", format="DD/MM/YYYY HH:mm"
                                           ),
                "agente_respuesta":        st.column_config.TextColumn("Agente Resp."),
                "respondio_agente":        st.column_config.CheckboxColumn("¿Respondió Agente Comercial?"),
                "horas_habiles":           st.column_config.NumberColumn("Hs Hábiles", format="%.1f h"),
                "bucket_respuesta":        st.column_config.TextColumn("Bucket"),
                "actitud_preaprobacion":   st.column_config.TextColumn("Actitud"),
                "objecion_preaprobacion":  st.column_config.TextColumn("Objeción"),
            },
            hide_index=True,
            height=500,
        )

        st.caption(f"Mostrando **{len(filtered):,}** de **{len(df):,}** leads")

        csv_bytes = filtered[display_cols].to_csv(index=False).encode("utf-8")
        st.download_button(
            label=":material/download: Descargar CSV",
            data=csv_bytes,
            file_name="difusion_preaprobados_garden.csv",
            mime="text/csv",
        )
