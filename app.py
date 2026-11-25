"""PIB MÉXICO // ADMIN AGRO

Dashboard del Producto Interno Bruto Trimestral del INEGI (base 2018),
con foco en las actividades primarias y su lugar dentro de la economía.

Datos: tabulados_PIBT/*.xlsx (series originales, millones de pesos
anualizados). La app no modifica los archivos fuente.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import pib_data
from matrix_theme import (
    DIVERGING_GREEN_MAGENTA,
    PALETTE,
    PLOTLY_CONFIG,
    SERIES,
    badge,
    hero,
    init_streamlit,
    matrix_style,
    style_axes,
    style_fig,
    terminal_header,
)

APP_TITLE = "PIB MÉXICO // ADMIN AGRO"
DATA_DIR = Path(__file__).resolve().parent / "tabulados_PIBT"
Q = ["T1", "T2", "T3", "T4"]

SHORT = {
    "pib": "PIB total",
    "primarias": "Primarias",
    "secundarias": "Secundarias",
    "terciarias": "Terciarias",
    "agro": "Agropecuario",
    "agricultura": "Agricultura",
    "ganaderia": "Ganadería",
    "forestal": "Forestal",
    "pesca": "Pesca",
    "serv_agro": "Servicios agro",
    "alimentos": "Alimentos",
    "bebidas": "Bebidas y tabaco",
    "vab": "Valor agregado",
}

# Color follows the entity across the dashboard.
COLORS = {
    "pib": SERIES[0],
    "primarias": SERIES[1],
    "secundarias": SERIES[2],
    "terciarias": SERIES[3],
    "agricultura": SERIES[4],
    "ganaderia": SERIES[5],
    "forestal": SERIES[6],
    "pesca": SERIES[7],
}

AGRO_CHART_KEYS = ["agricultura", "ganaderia", "forestal", "pesca"]
AGRO_TABLE_KEYS = AGRO_CHART_KEYS + ["serv_agro"]
SECTOR_KEYS = ["primarias", "secundarias", "terciarias"]


# ---------------------------------------------------------------------------
# Formatting (Spanish separators)
# ---------------------------------------------------------------------------

def _es(text: str) -> str:
    return text.replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_num(value: float, decimals: int = 1) -> str:
    if value is None or not np.isfinite(value):
        return "—"
    return _es(f"{value:,.{decimals}f}")


def fmt_pct(value: float, decimals: int = 1, sign: bool = True) -> str:
    if value is None or not np.isfinite(value):
        return "—"
    pattern = f"{value:+.{decimals}f}" if sign else f"{value:.{decimals}f}"
    return _es(pattern) + "%"


def fmt_billones(value: float, decimals: int = 1) -> str:
    if value is None or not np.isfinite(value):
        return "—"
    return f"{fmt_num(value / 1e6, decimals)} billones"


def fmt_pp(value: float, decimals: int = 1) -> str:
    if value is None or not np.isfinite(value):
        return "—"
    return _es(f"{value:+.{decimals}f}") + " pp"


def quarter_label(fecha: pd.Timestamp) -> str:
    quarter = (fecha.month - 1) // 3 + 1
    return f"{fecha.year} T{quarter}"


# ---------------------------------------------------------------------------
# Data access
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def load_data(mtimes: tuple[float, ...]) -> pd.DataFrame:
    """Cache keyed by source-file mtimes; reloads if an Excel changes."""
    return pib_data.load_pib(DATA_DIR)


def pick(df: pd.DataFrame, serie: str, bloque: str, key: str,
         fecha: pd.Timestamp) -> float:
    values = df[
        (df.serie == serie)
        & (df.bloque == bloque)
        & (df.key == key)
        & (df.fecha == fecha)
    ]["valor"]
    return float(values.iloc[0]) if not values.empty else np.nan


def latest_quarter(df: pd.DataFrame) -> pd.Timestamp:
    d = df[
        (df.serie == "real")
        & (df.bloque == "nivel")
        & (df.key == "pib")
        & (df.periodo.isin(Q))
    ]
    return d["fecha"].max()


def add_index(d: pd.DataFrame, df: pd.DataFrame,
              keys: list[str]) -> pd.DataFrame:
    base = df[
        (df.serie == "real")
        & (df.bloque == "nivel")
        & (df.periodo == "Anual")
        & (df.anio == 2018)
        & (df.key.isin(keys))
    ].set_index("key")["valor"]
    out = d.copy()
    out["base"] = out["key"].map(base)
    out["indice"] = out["valor"] / out["base"] * 100
    out["etiqueta"] = out["key"].map(SHORT)
    return out.dropna(subset=["indice"])


def annual_shares(df: pd.DataFrame, start: int, end: int) -> pd.DataFrame:
    d = df[
        (df.serie == "real")
        & (df.bloque == "nivel")
        & (df.periodo == "Anual")
        & (df.key.isin(SECTOR_KEYS))
        & (df.anio.between(start, min(end, 2025)))
    ]
    if d.empty:
        return pd.DataFrame()
    pivot = d.pivot_table(index="anio", columns="key", values="valor",
                          aggfunc="first")
    pivot = pivot.reindex(columns=SECTOR_KEYS).dropna()
    if pivot.empty:
        return pd.DataFrame()
    vab = pivot.sum(axis=1)
    shares = pivot.div(vab, axis=0) * 100
    shares.index.name = "anio"
    return shares


# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------

def line_index(d: pd.DataFrame, keys: list[str], title: str,
               height: int = 430, direct_labels: bool = False) -> go.Figure:
    color_map = {SHORT[k]: COLORS[k] for k in keys}
    fig = px.line(
        d.sort_values("fecha"),
        x="fecha",
        y="indice",
        color="etiqueta",
        color_discrete_map=color_map,
        labels={
            "fecha": "",
            "indice": "Índice 2018 = 100",
            "etiqueta": "",
        },
    )
    fig.update_traces(line={"width": 2})
    fig.add_hline(
        y=100,
        line_dash="dot",
        line_color=PALETTE["axis"],
        line_width=1,
        annotation_text="2018 = 100",
        annotation_position="bottom left",
        annotation_font={"color": PALETTE["text_secondary"], "size": 10},
    )
    if direct_labels:
        for key in keys:
            sub = d[d.key == key].dropna(subset=["indice"]).sort_values("fecha")
            if sub.empty:
                continue
            last = sub.iloc[-1]
            fig.add_annotation(
                x=last.fecha,
                y=last.indice,
                text=fmt_num(last.indice, 0),
                showarrow=False,
                xanchor="right",
                xshift=-8,
                yshift=10,
                font={"color": COLORS[key], "size": 10},
            )
    fig.update_xaxes(showgrid=False)
    fig.update_layout(
        hovermode="x unified",
        legend_title_text="",
        separators=",.",
    )
    return style_fig(
        fig,
        title=title,
        height=height,
        y_title="Índice 2018 = 100",
    )


def growth_bar(labels: list[str], values: list[float], title: str,
               height: int = 390) -> go.Figure:
    fig = go.Figure(
        go.Bar(
            x=values,
            y=labels,
            orientation="h",
            marker_color=SERIES[0],
            marker_line_color=PALETTE["surface"],
            marker_line_width=2,
            text=[fmt_pct(v) for v in values],
            textposition="outside",
            cliponaxis=False,
            hovertemplate="%{y}: %{x:+.1f}%<extra></extra>",
        )
    )
    fig.add_vline(x=0, line_color=PALETTE["axis"], line_width=1)
    finite = [v for v in values if np.isfinite(v)]
    lo = min(0, min(finite) * 1.35) if finite else -1
    hi = max(0, max(finite) * 1.35) if finite else 1
    fig.update_xaxes(title="Variación % anual", ticksuffix="%",
                     range=[lo, hi])
    fig.update_yaxes(title="")
    fig.update_layout(showlegend=False, separators=",.")
    return style_fig(fig, title=title, height=height)


def share_line(shares: pd.DataFrame, title: str,
               height: int = 430) -> go.Figure:
    long = (
        shares.reset_index()
        .melt(id_vars="anio", var_name="key", value_name="share")
    )
    long["etiqueta"] = long["key"].map(SHORT)
    color_map = {SHORT[k]: COLORS[k] for k in SECTOR_KEYS}
    fig = px.line(
        long.sort_values("anio"),
        x="anio",
        y="share",
        color="etiqueta",
        color_discrete_map=color_map,
        labels={"anio": "", "share": "% del VAB", "etiqueta": ""},
    )
    fig.update_traces(line={"width": 2})
    fig.update_xaxes(showgrid=False, dtick=2)
    fig.update_yaxes(range=[0, 100], ticksuffix="%")
    fig.update_layout(hovermode="x unified", legend_title_text="",
                      separators=",.")
    return style_fig(fig, title=title, height=height,
                     y_title="% del valor agregado bruto")


def stacked_share(shares: pd.DataFrame, year: int,
                  height: int = 250) -> go.Figure:
    row = shares.loc[year]
    fig = go.Figure()
    for key in SECTOR_KEYS:
        value = float(row[key])
        fig.add_trace(
            go.Bar(
                x=[value],
                y=[str(year)],
                orientation="h",
                name=SHORT[key],
                marker_color=COLORS[key],
                marker_line_color=PALETTE["surface"],
                marker_line_width=2,
                text=[f"{fmt_num(value)}%" if value >= 8 else ""],
                textposition="inside",
                insidetextanchor="middle",
                hovertemplate=(
                    f"{SHORT[key]}: %{{x:.1f}}% del VAB<extra></extra>"
                ),
            )
        )
    fig.update_layout(
        barmode="stack",
        showlegend=True,
        xaxis={"range": [0, 100], "ticksuffix": "%", "title": ""},
        yaxis={"title": ""},
        separators=",.",
    )
    return style_fig(fig, title=f"COMPOSICIÓN DEL VAB // {year}",
                     height=height)


def heatmap_growth(df: pd.DataFrame, key: str, title: str,
                   vmax: float, start: int, end: int,
                   height: int = 560) -> go.Figure:
    d = df[
        (df.serie == "real")
        & (df.bloque == "var_anual")
        & (df.key == key)
        & (df.periodo.isin(Q))
        & (df.anio.between(start, end))
    ]
    pivot = d.pivot_table(
        index="anio", columns="trimestre", values="valor", aggfunc="first"
    ).reindex(columns=[1, 2, 3, 4])
    fig = go.Figure(
        go.Heatmap(
            z=pivot.values,
            x=["T1", "T2", "T3", "T4"],
            y=[str(year) for year in pivot.index],
            colorscale=DIVERGING_GREEN_MAGENTA,
            zmin=-vmax,
            zmax=vmax,
            zmid=0,
            xgap=2,
            ygap=2,
            hoverongaps=False,
            hovertemplate="%{y} %{x}: %{z:+.1f}% anual<extra></extra>",
            colorbar={
                "title": {"text": "Var. %", "side": "right"},
                "thickness": 10,
                "outlinewidth": 0,
                "ticksuffix": "%",
                "tickfont": {"size": 9},
            },
        )
    )
    fig.update_xaxes(title="", tickfont={"size": 10})
    fig.update_yaxes(title="", autorange="reversed",
                     tickfont={"size": 9})
    fig.update_layout(separators=",.")
    return style_fig(fig, title=title, height=height)


def long_run_chart(df: pd.DataFrame) -> None:
    """Matplotlib: índice largo 1980-2025 + crecimiento anual."""
    levels = df[
        (df.serie == "real_largo")
        & (df.bloque == "nivel")
        & (df.periodo == "Anual")
        & (df.key.isin(["pib", "primarias"]))
        & (df.anio <= 2025)
    ]
    pivot = levels.pivot_table(index="anio", columns="key",
                               values="valor", aggfunc="first")
    if pivot.empty or 2018 not in pivot.index:
        st.info("No hay serie larga suficiente para el gráfico histórico.")
        return
    indexed = pivot.div(pivot.loc[2018], axis=1) * 100

    growth = df[
        (df.serie == "var_largo")
        & (df.bloque == "var_anual")
        & (df.periodo == "Anual")
        & (df.key == "pib")
        & (df.anio.between(1980, 2025))
    ].set_index("anio")["valor"].reindex(indexed.index)

    with matrix_style():
        fig, (ax1, ax2) = plt.subplots(
            2,
            1,
            figsize=(11.2, 6.4),
            dpi=130,
            sharex=True,
            gridspec_kw={"height_ratios": [2.4, 1]},
        )
        ax1.plot(indexed.index, indexed["pib"], color=COLORS["pib"],
                 lw=2, label="PIB total")
        ax1.plot(indexed.index, indexed["primarias"],
                 color=COLORS["primarias"], lw=2,
                 label="Actividades primarias")
        ax1.axhline(100, color=PALETTE["axis"], lw=1, ls=":")
        for key, label in (("pib", "PIB"), ("primarias", "Primarias")):
            last_y = indexed[key].iloc[-1]
            ax1.annotate(
                f"{last_y:.0f}",
                xy=(indexed.index[-1], last_y),
                xytext=(-6, 9),
                textcoords="offset points",
                color=COLORS[key],
                fontsize=9,
                ha="right",
            )
        style_axes(
            ax1,
            title="PIB REAL // ÍNDICE 2018 = 100 · 1980–2025",
            ylabel="Índice",
            grid_axis="y",
        )
        ax1.legend(loc="upper left")

        colors = [
            COLORS["pib"] if value >= 0 else SERIES[3]
            for value in growth.fillna(0).values
        ]
        ax2.bar(growth.index, growth.values, color=colors, width=0.8)
        ax2.axhline(0, color=PALETTE["axis"], lw=1)
        style_axes(
            ax2,
            title="CRECIMIENTO ANUAL DEL PIB REAL",
            ylabel="Var. % anual",
            grid_axis="y",
        )
        ax2.yaxis.set_major_formatter(
            mticker.FuncFormatter(lambda x, _pos: f"{x:.0f}%")
        )
        ax2.set_xlim(1980, 2025)
        fig.tight_layout()
        st.pyplot(fig, width="stretch")
        plt.close(fig)


# ---------------------------------------------------------------------------
# Page
# ---------------------------------------------------------------------------

def main() -> None:
    init_streamlit(APP_TITLE, "🟩")

    try:
        mtimes = pib_data.file_mtimes(DATA_DIR)
        df = load_data(mtimes)
    except Exception as exc:  # noqa: BLE001 - show a useful message
        st.error(f"No se pudieron leer los tabulados del PIB: {exc}")
        st.stop()

    latest = latest_quarter(df)
    if pd.isna(latest):
        st.error("No se encontró la serie del PIB en los tabulados.")
        st.stop()
    latest_status = df[
        (df.serie == "real")
        & (df.bloque == "nivel")
        & (df.key == "pib")
        & (df.fecha == latest)
    ]["estatus"].iloc[0]
    status_label = {"P": "preliminar", "R": "revisado"}.get(
        latest_status, "final"
    )
    status_kind = "warning" if latest_status == "P" else "good"

    pib_now = pick(df, "real", "nivel", "pib", latest)
    prim_now = pick(df, "real", "nivel", "primarias", latest)
    pib_yoy = pick(df, "real", "var_anual", "pib", latest)
    prim_yoy = pick(df, "real", "var_anual", "primarias", latest)
    agri_yoy = pick(df, "real", "var_anual", "agricultura", latest)

    prev = latest - pd.DateOffset(years=1)
    pib_prev = pick(df, "real", "nivel", "pib", prev)
    prim_prev = pick(df, "real", "nivel", "primarias", prev)
    share_now = prim_now / pib_now * 100 if pib_now else np.nan
    share_prev = prim_prev / pib_prev * 100 if pib_prev else np.nan
    share_delta = share_now - share_prev

    # Sidebar -------------------------------------------------------------
    with st.sidebar:
        st.markdown("### Parámetros")
        start_year, end_year = st.slider(
            "Ventana de análisis",
            min_value=1993,
            max_value=2026,
            value=(2000, 2026),
            step=1,
            help="Aplica a los gráficos trimestrales. Los KPIs usan el "
                 "último dato disponible.",
        )
        agro_keys = st.multiselect(
            "Componentes agropecuarios",
            options=AGRO_CHART_KEYS,
            default=AGRO_CHART_KEYS,
            format_func=lambda key: SHORT[key],
            help="Máximo 4 series para mantener la paleta validada.",
        )
        st.divider()
        show_rain = st.toggle("Lluvia digital", value=True)
        st.markdown(
            '<div class="mx-note">Fuente: INEGI · PIB Trimestral · '
            "base 2018. Series originales (sin desestacionalizar). "
            "Cifras 2024–2025 revisadas; 2026 T1–T2 revisadas y T3 "
            "preliminar.</div>",
            unsafe_allow_html=True,
        )

    if show_rain:
        hero(APP_TITLE, "INEGI · PRODUCTO INTERNO BRUTO TRIMESTRAL · BASE 2018",
             height=180)

    st.markdown(
        terminal_header(
            "pib --admin-agro --base=2018",
            f"ÚLTIMO DATO: {quarter_label(latest)} · SERIES ORIGINALES",
        ),
        unsafe_allow_html=True,
    )
    st.markdown(
        badge(f"{quarter_label(latest)} · {status_label}", status_kind),
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="mx-note">Millones de pesos anualizados a precios de '
        "2018 · series originales.</div>",
        unsafe_allow_html=True,
    )

    # KPI row -------------------------------------------------------------
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.metric(
            "PIB real · último trimestre",
            fmt_billones(pib_now),
            delta=fmt_pct(pib_yoy),
            help="Producto interno bruto a precios de 2018, anualizado.",
        )
    with k2:
        st.metric(
            "Actividades primarias",
            fmt_billones(prim_now),
            delta=fmt_pct(prim_yoy),
            help="Agricultura, ganadería, forestal, pesca y servicios agro.",
        )
    with k3:
        st.metric(
            "Participación primaria en el PIB",
            f"{fmt_num(share_now, 2)}%",
            delta=(
                fmt_pp(share_delta, 2)
                if np.isfinite(share_delta) else None
            ),
            delta_color="off",
            help="PIB primario / PIB total. La variación es en puntos "
                 "porcentuales contra el mismo trimestre del año previo.",
        )
    with k4:
        st.metric(
            "Agricultura · var. anual",
            fmt_pct(agri_yoy),
            delta=(
                f"vs PIB: {fmt_pp(agri_yoy - pib_yoy, 1)}"
                if np.isfinite(agri_yoy) and np.isfinite(pib_yoy) else None
            ),
            delta_color="off",
            help="Rama 111 (agricultura). La brecha compara con el PIB total.",
        )

    st.markdown(
        '<div class="mx-note">Los KPIs muestran el último trimestre '
        "publicado, independientemente de la ventana seleccionada. "
        "La serie es original: usa variaciones anuales, no trimestrales, "
        "para evitar el efecto estacional.</div>",
        unsafe_allow_html=True,
    )

    # Filtered frames -----------------------------------------------------
    real_q = df[
        (df.serie == "real")
        & (df.bloque == "nivel")
        & (df.periodo.isin(Q))
        & (df.anio.between(start_year, end_year))
    ]

    tabs = st.tabs(
        ["Panorama", "Agro", "Estructura", "Ciclo", "Precios", "Datos"]
    )

    # Panorama ------------------------------------------------------------
    with tabs[0]:
        panorama_keys = ["pib", "primarias"]
        pan = real_q[real_q.key.isin(panorama_keys)]
        pan_idx = add_index(pan, df, panorama_keys)
        left, right = st.columns([2.1, 1])
        with left:
            if pan_idx.empty:
                st.info("No hay datos para la ventana seleccionada.")
            else:
                st.plotly_chart(
                    line_index(
                        pan_idx,
                        panorama_keys,
                        "PIB REAL // PIB TOTAL vs ACTIVIDADES PRIMARIAS",
                        direct_labels=True,
                    ),
                    width="stretch",
                    theme=None,
                    config=PLOTLY_CONFIG,
                )
        with right:
            sector_growth = {
                key: pick(df, "real", "var_anual", key, latest)
                for key in ["pib", "primarias", "secundarias", "terciarias"]
            }
            st.plotly_chart(
                growth_bar(
                    [SHORT[k] for k in sector_growth],
                    list(sector_growth.values()),
                    "VAR. ANUAL // ÚLTIMO TRIMESTRE",
                ),
                width="stretch",
                theme=None,
                config=PLOTLY_CONFIG,
            )
            st.markdown(
                '<div class="mx-note">Comparación anual del último '
                "trimestre. Una sola escala: todas las barras son "
                "variaciones porcentuales.</div>",
                unsafe_allow_html=True,
            )

        st.markdown("##### Historia larga")
        long_run_chart(df)
        st.markdown(
            '<div class="mx-note">Serie larga 1980–2025 (PIBT_r_2 y '
            "PIBT_r_3). El índice usa el nivel anual de 2018 como base; "
            "las barras muestran la variación anual del PIB real.</div>",
            unsafe_allow_html=True,
        )

    # Agro ----------------------------------------------------------------
    with tabs[1]:
        if not agro_keys:
            st.warning("Selecciona al menos un componente agropecuario.")
        else:
            agro = real_q[real_q.key.isin(agro_keys)]
            agro_idx = add_index(agro, df, agro_keys)
            left, right = st.columns([2.1, 1])
            with left:
                if agro_idx.empty:
                    st.info("No hay datos para la ventana seleccionada.")
                else:
                    st.plotly_chart(
                        line_index(
                            agro_idx,
                            agro_keys,
                            "COMPONENTES AGROPECUARIOS // ÍNDICE 2018 = 100",
                        ),
                        width="stretch",
                        theme=None,
                        config=PLOTLY_CONFIG,
                    )
            with right:
                agro_growth = {
                    key: pick(df, "real", "var_anual", key, latest)
                    for key in agro_keys
                }
                st.plotly_chart(
                    growth_bar(
                        [SHORT[k] for k in agro_growth],
                        list(agro_growth.values()),
                        "VAR. ANUAL // AGRO",
                        height=390,
                    ),
                    width="stretch",
                    theme=None,
                    config=PLOTLY_CONFIG,
                )

            latest_rows = df[
                (df.serie == "real")
                & (df.bloque == "nivel")
                & (df.fecha == latest)
                & (df.key.isin(AGRO_TABLE_KEYS))
            ].copy()
            if not latest_rows.empty:
                latest_rows = (
                    latest_rows.set_index("key")
                    .reindex(AGRO_TABLE_KEYS)
                    .dropna(subset=["valor"])
                    .reset_index()
                )
                total = latest_rows["valor"].sum()
                latest_rows["participación del agro (%)"] = (
                    latest_rows["valor"] / total * 100
                )
                table = pd.DataFrame(
                    {
                        "Componente": latest_rows["key"].map(SHORT),
                        "Millones de pesos (2018)": latest_rows["valor"].map(
                            lambda v: fmt_num(v, 1)
                        ),
                        "Participación (%)": latest_rows[
                            "participación del agro (%)"
                        ].map(lambda v: fmt_num(v, 1)),
                    }
                )
                st.markdown("##### Último trimestre por componente")
                st.dataframe(table, hide_index=True,
                             width="stretch")
                st.markdown(
                    '<div class="mx-note">Participación calculada sobre '
                    "las actividades primarias. Los servicios agropecuarios "
                    "son una rama pequeña; se muestran en la tabla.</div>",
                    unsafe_allow_html=True,
                )

    # Estructura ----------------------------------------------------------
    with tabs[2]:
        shares = annual_shares(df, start_year, end_year)
        if shares.empty:
            st.info("No hay datos anuales completos para la ventana.")
        else:
            latest_year = int(shares.index.max())
            left, right = st.columns([1.5, 1])
            with left:
                st.plotly_chart(
                    share_line(
                        shares,
                        "COMPOSICIÓN DEL VALOR AGREGADO // % DEL VAB",
                    ),
                    width="stretch",
                    theme=None,
                    config=PLOTLY_CONFIG,
                )
            with right:
                st.plotly_chart(
                    stacked_share(shares, latest_year),
                    width="stretch",
                    theme=None,
                    config=PLOTLY_CONFIG,
                )
                row = shares.loc[latest_year]
                table = pd.DataFrame(
                    {
                        "Sector": [SHORT[k] for k in SECTOR_KEYS],
                        "Participación": [
                            f"{fmt_num(row[k], 1)}%" for k in SECTOR_KEYS
                        ],
                    }
                )
                st.dataframe(table, hide_index=True,
                             width="stretch")
            st.markdown(
                '<div class="mx-note">Los tres sectores suman el valor '
                "agregado bruto (VAB). El PIB incluye además los impuestos "
                "netos sobre los productos, por eso la participación "
                "primaria en el PIB es algo menor. El año más reciente "
                "con dato anual completo es "
                f"{latest_year}.</div>",
                unsafe_allow_html=True,
            )

    # Ciclo ---------------------------------------------------------------
    with tabs[3]:
        cycle = df[
            (df.serie == "real")
            & (df.bloque == "var_anual")
            & (df.key.isin(["pib", "primarias"]))
            & (df.periodo.isin(Q))
            & (df.anio.between(max(1994, start_year), end_year))
        ]
        if cycle.empty:
            st.info("No hay variaciones anuales para la ventana.")
        else:
            vmax = float(np.nanpercentile(np.abs(cycle["valor"]), 95))
            vmax = max(4.0, float(np.ceil(vmax / 2) * 2))
            left, right = st.columns(2)
            with left:
                st.plotly_chart(
                    heatmap_growth(
                        df, "pib",
                        "PIB TOTAL // VAR. ANUAL POR TRIMESTRE",
                        vmax, max(1994, start_year), end_year,
                    ),
                    width="stretch",
                    theme=None,
                    config=PLOTLY_CONFIG,
                )
            with right:
                st.plotly_chart(
                    heatmap_growth(
                        df, "primarias",
                        "ACTIVIDADES PRIMARIAS // VAR. ANUAL",
                        vmax, max(1994, start_year), end_year,
                    ),
                    width="stretch",
                    theme=None,
                    config=PLOTLY_CONFIG,
                )
            st.markdown(
                f'<div class="mx-note">Verde = crecimiento; magenta = '
                "contracción; gris = cero o sin dato. La escala se acota "
                f"a ±{fmt_num(vmax, 0)}% (percentil 95) para que los "
                "outliers de 2020 no aplanen el resto.</div>",
                unsafe_allow_html=True,
            )

    # Precios -------------------------------------------------------------
    with tabs[4]:
        price = df[
            (df.serie.isin(["real", "nominal"]))
            & (df.bloque == "nivel")
            & (df.key == "pib")
            & (df.periodo.isin(Q))
            & (df.anio.between(start_year, end_year))
        ].copy()
        price["billones"] = price["valor"] / 1e6
        price["medida"] = price["serie"].map(
            {"real": "PIB real (2018)", "nominal": "PIB nominal"}
        )
        defl = df[
            (df.serie == "deflactor")
            & (df.bloque == "nivel")
            & (df.key == "pib")
            & (df.periodo.isin(Q))
            & (df.anio.between(start_year, end_year))
        ]

        nom_now = pick(df, "nominal", "nivel", "pib", latest)
        defl_now = pick(df, "deflactor", "nivel", "pib", latest)
        nom_yoy = pick(df, "nominal", "var_anual", "pib", latest)
        defl_yoy = pick(df, "deflactor", "var_anual", "pib", latest)

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("PIB nominal", fmt_billones(nom_now),
                      delta=fmt_pct(nom_yoy))
        with c2:
            st.metric("Deflactor del PIB", fmt_num(defl_now, 1),
                      delta=fmt_pct(defl_yoy), delta_color="inverse",
                      help="Índice de precios implícitos, 2018 = 100.")
        with c3:
            st.metric("PIB real", fmt_billones(pib_now),
                      delta=fmt_pct(pib_yoy),
                      help="PIB a precios de 2018, anualizado.")
        with c4:
            st.metric("Brecha nominal-real",
                      fmt_pp(nom_yoy - pib_yoy, 1)
                      if np.isfinite(nom_yoy) and np.isfinite(pib_yoy)
                      else "—",
                      help="Diferencia entre el crecimiento nominal y real.")

        left, right = st.columns(2)
        with left:
            fig = px.line(
                price.sort_values("fecha"),
                x="fecha",
                y="billones",
                color="medida",
                color_discrete_map={
                    "PIB real (2018)": COLORS["pib"],
                    "PIB nominal": COLORS["primarias"],
                },
                labels={"fecha": "", "billones": "Billones de pesos",
                        "medida": ""},
            )
            fig.update_traces(line={"width": 2})
            fig.update_xaxes(showgrid=False)
            fig.update_layout(hovermode="x unified",
                              legend_title_text="", separators=",.")
            st.plotly_chart(
                style_fig(fig, title="PIB NOMINAL vs REAL",
                          height=430, y_title="Billones de pesos"),
                width="stretch",
                theme=None,
                config=PLOTLY_CONFIG,
            )
        with right:
            fig = px.line(
                defl.sort_values("fecha"),
                x="fecha",
                y="valor",
                color_discrete_sequence=[COLORS["pib"]],
                labels={"fecha": "", "valor": "Índice 2018 = 100"},
            )
            fig.update_traces(line={"width": 2})
            fig.add_hline(y=100, line_dash="dot",
                          line_color=PALETTE["axis"], line_width=1)
            fig.update_xaxes(showgrid=False)
            fig.update_layout(showlegend=False, separators=",.")
            st.plotly_chart(
                style_fig(fig, title="DEFLACTOR IMPLÍCITO DEL PIB",
                          height=430, y_title="Índice 2018 = 100"),
                width="stretch",
                theme=None,
                config=PLOTLY_CONFIG,
            )
        st.markdown(
            '<div class="mx-note">El PIB nominal está a precios '
            "corrientes; el real, a precios de 2018. El deflactor es el "
            "cociente implícito entre ambos (2018 = 100).</div>",
            unsafe_allow_html=True,
        )

    # Datos ---------------------------------------------------------------
    with tabs[5]:
        data = real_q[real_q.key.isin(
            ["pib", "primarias", "agricultura", "ganaderia",
             "forestal", "pesca", "serv_agro"]
        )].copy()
        if data.empty:
            st.info("No hay datos para la ventana seleccionada.")
        else:
            data["etiqueta"] = data["key"].map(SHORT)
            wide = data.pivot_table(
                index=["fecha", "anio", "periodo", "estatus"],
                columns="etiqueta",
                values="valor",
                aggfunc="first",
            ).reset_index()
            wide = wide.sort_values("fecha", ascending=False)
            for key in ["PIB total", "Primarias", "Agricultura",
                        "Ganadería", "Forestal", "Pesca", "Servicios agro"]:
                if key in wide.columns:
                    wide[key] = (wide[key] / 1e6).round(2)
            wide = wide.rename(columns={
                "fecha": "Fecha",
                "anio": "Año",
                "periodo": "Trimestre",
                "estatus": "Estatus",
            })
            wide["Fecha"] = wide["Fecha"].dt.strftime("%Y-%m")
            order = ["Fecha", "Año", "Trimestre", "Estatus",
                     "PIB total", "Primarias", "Agricultura", "Ganadería",
                     "Forestal", "Pesca", "Servicios agro"]
            wide = wide[[c for c in order if c in wide.columns]]
            st.markdown("##### Billones de pesos de 2018 (anualizados)")
            st.dataframe(wide.head(500), hide_index=True,
                         width="stretch")
            st.caption(
                f"{len(wide):,} filas · mostrando las 500 más recientes"
            )

            tidy = data[
                ["fecha", "anio", "periodo", "estatus", "nombre",
                 "valor"]
            ].sort_values("fecha", ascending=False)
            st.download_button(
                "Descargar CSV",
                data=tidy.to_csv(index=False).encode("utf-8-sig"),
                file_name="pib_real_trimestral.csv",
                mime="text/csv",
            )

            with st.expander("Diccionario de datos y notas"):
                st.markdown(
                    "- **PIB real:** millones de pesos anualizados a "
                    "precios de 2018 (PIBT_2).\n"
                    "- **PIB nominal:** millones de pesos anualizados a "
                    "precios corrientes (PIBT_3).\n"
                    "- **Deflactor:** índice de precios implícitos, "
                    "2018 = 100 (PIBT_4).\n"
                    "- **Variación anual:** porcentaje respecto al mismo "
                    "trimestre del año anterior (PIBT_2/PIBT_r_3).\n"
                    "- **Serie larga:** 1980–2026 para los agregados "
                    "(PIBT_r_2 y PIBT_r_3).\n"
                    "- **Estatus:** R = cifra revisada; P = preliminar; "
                    "vacío = final.\n"
                    "- Las series son originales (no desestacionalizadas); "
                    "las comparaciones trimestrales pueden estar afectadas "
                    "por estacionalidad.\n"
                    "- Cifras 2024–2025 revisadas; 2026 T1–T2 revisadas y "
                    "T3 preliminar. Cobertura hasta 2026 T3."
                )

    st.markdown(
        '<div class="mx-note" style="margin-top:28px">'
        "Fuente: INEGI. Sistema de Cuentas Nacionales de México. "
        "Producto Interno Bruto Trimestral, base 2018. "
        "Series originales. Elaborado con datos abiertos; "
        "las cifras oficiales son las publicadas por el INEGI.</div>",
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
