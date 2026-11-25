"""Matrix terminal theme for Streamlit dashboards (Plotly + Matplotlib).

Copy this file next to your app and import it::

    from matrix_theme import init_streamlit, terminal_header, SERIES, PLOTLY_CONFIG

The palette is fixed and pre-validated against a pure-black surface:
  * 8 categorical slots pass adjacent-pair CVD and normal-vision checks;
  * the 3-colour scatter trio passes all-pairs checks;
  * every text/status colour clears WCAG 3:1 on #000000.
Do not invent new series colours without re-running a palette validator.
"""

from __future__ import annotations

import html as _html
import copy
from contextlib import contextmanager

import matplotlib as mpl
from matplotlib import font_manager
from matplotlib.colors import LinearSegmentedColormap

# ---------------------------------------------------------------------------
# Design tokens - single source of truth
# ---------------------------------------------------------------------------

PALETTE = {
    # surfaces
    "surface": "#000000",
    "panel": "#050B08",
    "panel_elevated": "#07120C",
    "sidebar": "#030805",
    # ink
    "text_primary": "#D7FFE0",
    "text_secondary": "#8FA89A",
    "text_muted": "#5C7A66",
    # chrome
    "phosphor": "#00FF41",
    "phosphor_dim": "#00B85C",
    "grid": "#0E2A17",
    "axis": "#1D5C31",
    "border": "#1D5C31",
    # status (reserved meaning - never use for series identity)
    "good": "#00E05A",
    "warning": "#FFC400",
    "serious": "#FF8A00",
    "critical": "#FF3B3B",
}

# Fixed order. Assign slots in sequence, never cycle.
SERIES = [
    "#00B85C",  # 1 matrix green
    "#0FA6C4",  # 2 cyber cyan
    "#C98F00",  # 3 amber
    "#E24D8B",  # 4 magenta
    "#9887EF",  # 5 violet
    "#E76624",  # 6 orange
    "#338CED",  # 7 blue
    "#EB6263",  # 8 red
]

# All-pairs forms (scatter / bubble / map / small multiples) can put any two
# marks side by side. This trio passes all-pairs CVD + normal-vision checks.
SERIES_SCATTER = ["#0FA6C4", "#E24D8B", "#C98F00"]

STATUS = {
    "good": PALETTE["good"],
    "warning": PALETTE["warning"],
    "serious": PALETTE["serious"],
    "critical": PALETTE["critical"],
}

STATUS_ICON = {
    "good": "✓",
    "warning": "!",
    "serious": "▲",
    "critical": "✕",
}

# One-hue green ramp: dark (near zero) -> bright (high). Used for sequential
# magnitude on a black surface.
SEQUENTIAL_GREEN = [
    (0.00, "#02140A"),
    (0.25, "#0A3D1B"),
    (0.50, "#0E7A2E"),
    (0.75, "#00B85C"),
    (1.00, "#00FF41"),
]

# Diverging: phosphor green <-> magenta with a neutral dark midpoint.
DIVERGING_GREEN_MAGENTA = [
    (0.00, "#E24D8B"),
    (0.25, "#7A2347"),
    (0.50, "#2A2A2A"),
    (0.75, "#0E7A2E"),
    (1.00, "#00FF41"),
]

FONT_STACK = (
    "'Share Tech Mono', 'JetBrains Mono', 'IBM Plex Mono', 'Fira Code', "
    "'SF Mono', Menlo, monospace"
)
FONT_STACK_PLOTLY = (
    "Share Tech Mono, JetBrains Mono, IBM Plex Mono, Fira Code, "
    "SFMono-Regular, Menlo, monospace"
)

PLOTLY_CONFIG = {
    "displayModeBar": False,
    "responsive": True,
}

# ---------------------------------------------------------------------------
# Fonts
# ---------------------------------------------------------------------------

_PREFERRED_MONO = [
    "Share Tech Mono",
    "JetBrains Mono",
    "IBM Plex Mono",
    "Fira Code",
    "SF Mono",
    "Menlo",
    "DejaVu Sans Mono",
]


def available_mono_fonts() -> list[str]:
    """Return the preferred monospace fonts actually installed, with fallback."""
    installed = {f.name for f in font_manager.fontManager.ttflist}
    found = [name for name in _PREFERRED_MONO if name in installed]
    return found or ["DejaVu Sans Mono"]


# ---------------------------------------------------------------------------
# Plotly
# ---------------------------------------------------------------------------

_AXIS = {
    "gridcolor": PALETTE["grid"],
    "gridwidth": 1,
    "linecolor": PALETTE["axis"],
    "linewidth": 1,
    "zerolinecolor": PALETTE["axis"],
    "zerolinewidth": 1,
    "tickfont": {"color": PALETTE["text_secondary"], "size": 12,
                 "family": FONT_STACK_PLOTLY},
    "title": {"font": {"color": PALETTE["text_secondary"], "size": 12,
                       "family": FONT_STACK_PLOTLY}},
    "automargin": True,
}


def plotly_template():
    """Build the Matrix Plotly template. Cached by plotly's template registry."""
    import plotly.graph_objects as go

    return go.layout.Template(
        layout=go.Layout(
            paper_bgcolor=PALETTE["surface"],
            plot_bgcolor=PALETTE["surface"],
            font={
                "family": FONT_STACK_PLOTLY,
                "size": 13,
                "color": PALETTE["text_primary"],
            },
            title={
                "font": {
                    "family": FONT_STACK_PLOTLY,
                    "size": 17,
                    "color": PALETTE["phosphor"],
                },
                "x": 0.0,
                "xanchor": "left",
            },
            colorway=SERIES,
            xaxis=copy.deepcopy(_AXIS),
            yaxis=copy.deepcopy(_AXIS),
            legend={
                "orientation": "h",
                "yanchor": "bottom",
                "y": 1.02,
                "xanchor": "left",
                "x": 0.0,
                "bgcolor": "rgba(0,0,0,0)",
                "bordercolor": PALETTE["border"],
                "borderwidth": 0,
                "font": {"color": PALETTE["text_secondary"], "size": 11,
                         "family": FONT_STACK_PLOTLY},
                "itemsizing": "constant",
                "tracegroupgap": 12,
            },
            hovermode="closest",
            hoverlabel={
                "bgcolor": PALETTE["panel_elevated"],
                "bordercolor": PALETTE["phosphor_dim"],
                "font": {"family": FONT_STACK_PLOTLY, "size": 12,
                         "color": PALETTE["text_primary"]},
                "align": "left",
            },
            margin={"l": 64, "r": 24, "t": 64, "b": 48},
            coloraxis={
                "colorscale": SEQUENTIAL_GREEN,
                "colorbar": {
                    "bgcolor": PALETTE["surface"],
                    "bordercolor": PALETTE["border"],
                    "tickfont": {"color": PALETTE["text_secondary"],
                                 "family": FONT_STACK_PLOTLY},
                    "outlinewidth": 0,
                },
            },
            bargap=0.32,
            bargroupgap=0.08,
        )
    )


def register_plotly_theme(name: str = "matrix") -> None:
    """Register and activate the Matrix template in Plotly."""
    import plotly.io as pio

    pio.templates[name] = plotly_template()
    pio.templates.default = name


def style_fig(fig, *, title: str | None = None, height: int | None = None,
              x_title: str | None = None, y_title: str | None = None):
    """Apply the finishing touches to one Plotly figure and return it."""
    if title is not None:
        fig.update_layout(title=title)
    if height is not None:
        fig.update_layout(height=height)
    if x_title is not None:
        fig.update_xaxes(title=x_title)
    if y_title is not None:
        fig.update_yaxes(title=y_title)
    return fig


def matrix_cmap(name: str = "matrix_green") -> LinearSegmentedColormap:
    """Matplotlib colormap for sequential magnitude."""
    return LinearSegmentedColormap.from_list(name, SEQUENTIAL_GREEN)


def diverging_cmap(name: str = "matrix_diverging") -> LinearSegmentedColormap:
    """Matplotlib colormap for polarity (negative <-> positive)."""
    return LinearSegmentedColormap.from_list(name, DIVERGING_GREEN_MAGENTA)


# ---------------------------------------------------------------------------
# Matplotlib
# ---------------------------------------------------------------------------

_MATPLOTLIB_RC = {
    "figure.facecolor": PALETTE["surface"],
    "figure.edgecolor": PALETTE["surface"],
    "savefig.facecolor": PALETTE["surface"],
    "axes.facecolor": PALETTE["surface"],
    "axes.edgecolor": PALETTE["axis"],
    "axes.linewidth": 1.0,
    "axes.labelcolor": PALETTE["text_secondary"],
    "axes.labelsize": 10,
    "axes.labelpad": 8,
    "axes.titlesize": 13,
    "axes.titleweight": "bold",
    "axes.titlecolor": PALETTE["phosphor"],
    "axes.grid": True,
    "axes.axisbelow": True,
    "grid.color": PALETTE["grid"],
    "grid.linewidth": 0.7,
    "grid.alpha": 1.0,
    "text.color": PALETTE["text_primary"],
    "font.family": "monospace",
    "font.monospace": available_mono_fonts(),
    "font.size": 10,
    "xtick.color": PALETTE["text_secondary"],
    "ytick.color": PALETTE["text_secondary"],
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "xtick.major.size": 3,
    "ytick.major.size": 3,
    "legend.fontsize": 9,
    "legend.frameon": False,
    "legend.facecolor": PALETTE["surface"],
    "legend.edgecolor": PALETTE["border"],
    "lines.linewidth": 2.0,
    "lines.markersize": 7,
    "axes.prop_cycle": mpl.cycler(color=SERIES),
}


def use_matrix_style() -> None:
    """Apply the Matrix rcParams globally (safe to call once at app start)."""
    mpl.rcParams.update(_MATPLOTLIB_RC)


@contextmanager
def matrix_style():
    """Apply the Matrix style for one block and restore the previous rcParams."""
    previous = mpl.rcParams.copy()
    try:
        use_matrix_style()
        yield
    finally:
        mpl.rcParams.update(previous)


def style_axes(ax, *, title: str | None = None, xlabel: str | None = None,
               ylabel: str | None = None, grid_axis: str = "y"):
    """Style one Matplotlib axes: recessive chrome, green title, thin spines."""
    if title:
        ax.set_title(title, loc="left", pad=12)
    if xlabel:
        ax.set_xlabel(xlabel)
    if ylabel:
        ax.set_ylabel(ylabel)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(PALETTE["axis"])
        ax.spines[side].set_linewidth(1.0)
    ax.grid(True, axis=grid_axis, color=PALETTE["grid"], linewidth=0.7)
    ax.grid(False, axis="x" if grid_axis == "y" else "y")
    ax.tick_params(colors=PALETTE["text_secondary"], labelsize=9)
    return ax


# ---------------------------------------------------------------------------
# Streamlit CSS + HTML helpers
# ---------------------------------------------------------------------------

MATRIX_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=JetBrains+Mono:wght@400;600&display=swap');

:root {
  --mx-bg: #000000;
  --mx-panel: #050B08;
  --mx-panel-2: #07120C;
  --mx-text: #D7FFE0;
  --mx-text-2: #8FA89A;
  --mx-muted: #5C7A66;
  --mx-phosphor: #00FF41;
  --mx-green: #00B85C;
  --mx-border: #1D5C31;
  --mx-grid: #0E2A17;
}

html, body, .stApp, [class*="st-"], [data-testid="stAppViewContainer"] {
  font-family: 'Share Tech Mono', 'JetBrains Mono', 'IBM Plex Mono',
               'Fira Code', 'SF Mono', Menlo, monospace !important;
}

/* Keep Streamlit's icon ligatures on their own font. */
[data-testid="stIconMaterial"],
.material-symbols-rounded,
.material-icons,
span[class*="material-symbols"] {
  font-family: 'Material Symbols Rounded', 'Material Icons' !important;
  font-weight: normal !important;
  font-style: normal !important;
  letter-spacing: normal !important;
  text-transform: none !important;
  line-height: 1 !important;
}

.stApp {
  background:
    radial-gradient(ellipse 80% 55% at 50% -10%,
                    rgba(0, 184, 92, 0.10), transparent 70%),
    var(--mx-bg);
  color: var(--mx-text);
}

/* Kiosk-like console: hide Deploy/menu, keep the sidebar toggle. */
[data-testid="stAppDeployButton"],
[data-testid="stMainMenu"],
[data-testid="stDecoration"],
footer {
  display: none !important;
}
[data-testid="stHeader"] { background: transparent !important; }

/* CRT scanlines + subtle vignette. Pointer-events off: never blocks UI. */
.stApp::before {
  content: "";
  position: fixed;
  inset: 0;
  z-index: 9999;
  pointer-events: none;
  background: repeating-linear-gradient(
    0deg,
    rgba(0, 0, 0, 0) 0px,
    rgba(0, 0, 0, 0) 2px,
    rgba(0, 255, 65, 0.025) 3px,
    rgba(0, 0, 0, 0.10) 4px
  );
}
.stApp::after {
  content: "";
  position: fixed;
  inset: 0;
  z-index: 9998;
  pointer-events: none;
  background: radial-gradient(ellipse at center,
              transparent 62%, rgba(0, 0, 0, 0.35) 100%);
}

h1, h2, h3, h4, h5 {
  color: var(--mx-phosphor) !important;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  text-shadow: 0 0 12px rgba(0, 255, 65, 0.35);
}
h1 { font-size: clamp(1.6rem, 2.4vw, 2.4rem) !important; }
h2 { font-size: clamp(1.2rem, 1.7vw, 1.6rem) !important; }
h3 { font-size: 1.05rem !important; }
h5 { font-size: 0.8rem !important; color: var(--mx-text-2) !important; }

a { color: var(--mx-phosphor) !important; }
hr { border-color: var(--mx-border) !important; }

/* Sidebar */
[data-testid="stSidebar"] {
  background: #030805;
  border-right: 1px solid var(--mx-border);
}
[data-testid="stSidebar"]::before {
  content: "// CONTROL PANEL";
  display: block;
  padding: 10px 0 14px;
  color: var(--mx-muted);
  font-size: 0.68rem;
  letter-spacing: 0.22em;
}
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] .stMarkdown p {
  color: var(--mx-text-2);
}

/* Metric / KPI tiles */
[data-testid="stMetric"] {
  background: linear-gradient(180deg,
              rgba(0, 184, 92, 0.07), rgba(5, 11, 8, 0.92));
  border: 1px solid var(--mx-border);
  border-radius: 4px;
  padding: 14px 16px;
  box-shadow: inset 0 0 0 1px rgba(0, 255, 65, 0.03),
              0 0 20px rgba(0, 255, 65, 0.05);
}
[data-testid="stMetricLabel"] p {
  color: var(--mx-text-2) !important;
  text-transform: uppercase;
  letter-spacing: 0.13em;
  font-size: 0.68rem !important;
}
[data-testid="stMetricValue"] {
  color: var(--mx-phosphor) !important;
  text-shadow: 0 0 14px rgba(0, 255, 65, 0.35);
  font-variant-numeric: tabular-nums;
}
[data-testid="stMetricDelta"] { font-size: 0.78rem !important; }

/* Buttons */
.stButton > button, .stDownloadButton > button {
  background: transparent;
  color: var(--mx-phosphor);
  border: 1px solid var(--mx-green);
  border-radius: 3px;
  text-transform: uppercase;
  letter-spacing: 0.09em;
  font-family: inherit;
  transition: box-shadow 120ms ease, background 120ms ease;
}
.stButton > button:hover, .stDownloadButton > button:hover {
  border-color: var(--mx-phosphor);
  background: rgba(0, 255, 65, 0.06);
  box-shadow: 0 0 16px rgba(0, 255, 65, 0.30);
  color: var(--mx-phosphor);
}

/* Tabs */
[data-baseweb="tab-list"] {
  gap: 4px;
  border-bottom: 1px solid var(--mx-border);
}
[data-baseweb="tab"] {
  background: transparent;
  color: var(--mx-text-2);
  text-transform: uppercase;
  letter-spacing: 0.10em;
  font-size: 0.78rem;
}
[aria-selected="true"][data-baseweb="tab"] { color: var(--mx-phosphor); }
[data-baseweb="tab-highlight"] {
  background-color: var(--mx-phosphor);
  box-shadow: 0 0 10px rgba(0, 255, 65, 0.55);
}
[data-baseweb="tab-border"] { background: var(--mx-border); }

/* Inputs / selects */
[data-baseweb="select"] > div,
[data-baseweb="input"] > div,
.stTextInput input,
.stNumberInput input,
.stDateInput input {
  background-color: #030805 !important;
  border-color: var(--mx-border) !important;
  color: var(--mx-text) !important;
}
[data-baseweb="popover"] {
  background-color: var(--mx-panel) !important;
  border: 1px solid var(--mx-border) !important;
}
[data-baseweb="menu"] { background-color: var(--mx-panel) !important; }
[data-baseweb="tag"],
[data-tag] {
  background: rgba(0, 184, 92, 0.12) !important;
  border: 1px solid var(--mx-border) !important;
  border-radius: 2px !important;
}
[data-baseweb="tag"] span,
[data-baseweb="tag"] svg,
[data-tag] span,
[data-tag] button,
[data-tag] svg {
  color: var(--mx-phosphor) !important;
  fill: var(--mx-phosphor) !important;
}

/* Dataframe + alerts + code */
[data-testid="stDataFrame"] {
  border: 1px solid var(--mx-border);
  border-radius: 3px;
}
[data-testid="stAlert"] {
  background: var(--mx-panel);
  border: 1px solid var(--mx-border);
  border-radius: 3px;
}
code, pre, kbd {
  font-family: 'Share Tech Mono', 'JetBrains Mono', Menlo, monospace !important;
}

/* Custom Matrix classes */
.mx-head {
  border-left: 2px solid var(--mx-phosphor);
  padding: 2px 0 10px 16px;
  margin: 2px 0 18px;
}
.mx-prompt {
  color: var(--mx-phosphor);
  font-size: 1.02rem;
  letter-spacing: 0.04em;
  text-shadow: 0 0 10px rgba(0, 255, 65, 0.35);
}
.mx-cmd { color: var(--mx-text); }
.mx-sub {
  color: var(--mx-text-2);
  font-size: 0.78rem;
  letter-spacing: 0.08em;
  margin-top: 5px;
}
.mx-cursor {
  display: inline-block;
  width: 0.58em;
  height: 1.05em;
  margin-left: 6px;
  vertical-align: -0.18em;
  background: var(--mx-phosphor);
  box-shadow: 0 0 8px rgba(0, 255, 65, 0.65);
  animation: mx-blink 1.1s steps(2, start) infinite;
}
@keyframes mx-blink { to { visibility: hidden; } }
@media (prefers-reduced-motion: reduce) {
  .mx-cursor { animation: none; }
}
.mx-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border: 1px solid currentColor;
  border-radius: 2px;
  padding: 2px 8px;
  font-size: 0.7rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}
.mx-badge--good { color: #00E05A; }
.mx-badge--warning { color: #FFC400; }
.mx-badge--serious { color: #FF8A00; }
.mx-badge--critical { color: #FF3B3B; }
.mx-note {
  color: var(--mx-text-2);
  font-size: 0.76rem;
  border-left: 1px solid var(--mx-border);
  padding-left: 10px;
  line-height: 1.5;
}

/* Scrollbar + focus */
::-webkit-scrollbar { width: 10px; height: 10px; }
::-webkit-scrollbar-track { background: #000000; }
::-webkit-scrollbar-thumb {
  background: #123B20;
  border: 2px solid #000000;
  border-radius: 4px;
}
::-webkit-scrollbar-thumb:hover { background: var(--mx-border); }
*:focus-visible {
  outline: 1px solid var(--mx-phosphor) !important;
  outline-offset: 2px;
}

@media (max-width: 640px) {
  .block-container { padding-left: 1rem !important; padding-right: 1rem !important; }
  [data-testid="stMetricValue"] { font-size: 1.4rem !important; }
}
"""


def inject_css() -> None:
    """Inject the Matrix CSS once per Streamlit run."""
    import streamlit as st

    st.markdown(f"<style>{MATRIX_CSS}</style>", unsafe_allow_html=True)


def init_streamlit(title: str = "MATRIX // ANALYTICS", icon: str = "🟩",
                   layout: str = "wide") -> None:
    """First Streamlit call: page config + CSS + Plotly/Matplotlib themes."""
    import streamlit as st

    st.set_page_config(page_title=title, page_icon=icon, layout=layout,
                       initial_sidebar_state="auto")
    inject_css()
    register_plotly_theme()
    use_matrix_style()


def terminal_header(title: str, subtitle: str = "", prompt: str = "root@matrix:~$") -> str:
    """Return HTML for a terminal-style page header (pass to st.markdown)."""
    safe_title = _html.escape(title)
    safe_sub = _html.escape(subtitle)
    safe_prompt = _html.escape(prompt)
    sub = f'<div class="mx-sub">{safe_sub}</div>' if subtitle else ""
    return (
        '<div class="mx-head">'
        f'<div class="mx-prompt">{safe_prompt} '
        f'<span class="mx-cmd">{safe_title}</span>'
        '<span class="mx-cursor" aria-hidden="true"></span></div>'
        f"{sub}</div>"
    )


def badge(text: str, status: str = "good") -> str:
    """Return HTML for a status badge (icon + label, never colour alone)."""
    if status not in STATUS:
        raise ValueError(f"status must be one of {sorted(STATUS)}")
    icon = STATUS_ICON[status]
    return (
        f'<span class="mx-badge mx-badge--{status}">'
        f'<span aria-hidden="true">{icon}</span>{_html.escape(text)}</span>'
    )


def hero(title: str, subtitle: str = "", height: int = 190) -> None:
    """Render an optional digital-rain hero banner above the dashboard.

    Motion is disabled when the viewer prefers reduced motion. Keep it at the
    top of the page; do not use it as a full-page background.
    """
    import streamlit as st

    safe_title = _html.escape(title)
    safe_sub = _html.escape(subtitle)
    document = f"""<!doctype html>
<html><head><meta charset="utf-8">
<style>
  @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&display=swap');
  html, body {{ margin: 0; height: 100%; background: #000; overflow: hidden; }}
  .wrap {{ position: relative; width: 100%; height: {height}px; }}
  canvas {{ position: absolute; inset: 0; width: 100%; height: 100%; }}
  .overlay {{
    position: absolute; inset: 0; display: grid; place-content: center;
    text-align: center; padding: 0 24px;
    background: radial-gradient(ellipse at center,
                rgba(0,0,0,0.35) 0%, rgba(0,0,0,0.72) 100%);
    font-family: 'Share Tech Mono', 'JetBrains Mono', Menlo, monospace;
  }}
  .kicker {{ color: #00B85C; font-size: 11px; letter-spacing: .42em;
            text-transform: uppercase; margin-bottom: 10px; }}
  .title {{ color: #00FF41; font-size: clamp(22px, 4.2vw, 42px);
           letter-spacing: .14em; text-transform: uppercase;
           text-shadow: 0 0 18px rgba(0,255,65,.55), 0 0 42px rgba(0,255,65,.22); }}
  .sub {{ color: #8FA89A; font-size: 12px; letter-spacing: .18em;
         text-transform: uppercase; margin-top: 10px; }}
  .rule {{ width: 220px; height: 1px; margin: 14px auto 0;
          background: linear-gradient(90deg, transparent, #1D5C31, transparent); }}
</style></head>
<body>
  <div class="wrap">
    <canvas id="mx-rain"></canvas>
    <div class="overlay">
      <div class="kicker">wake up, neo // connection established</div>
      <div class="title">{safe_title}</div>
      <div class="sub">{safe_sub}</div>
      <div class="rule"></div>
    </div>
  </div>
<script>
  (function () {{
    const canvas = document.getElementById('mx-rain');
    const ctx = canvas.getContext('2d');
    const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const glyphs = 'アイウエオカキクケコサシスセソタチツテト0123456789ABCDEFXYZ<>/\\\\|{{}}[]';
    const size = 15;
    let w = 0, h = 0, cols = 0, drops = [];
    const dpr = Math.min(window.devicePixelRatio || 1, 2);

    function resize() {{
      w = canvas.clientWidth; h = canvas.clientHeight;
      canvas.width = Math.max(1, w * dpr); canvas.height = Math.max(1, h * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      cols = Math.max(1, Math.floor(w / size));
      drops = Array.from({{ length: cols }}, () => Math.random() * h / size);
      ctx.fillStyle = '#000'; ctx.fillRect(0, 0, w, h);
    }}

    function frame() {{
      ctx.fillStyle = 'rgba(0, 0, 0, 0.10)';
      ctx.fillRect(0, 0, w, h);
      ctx.font = size + 'px "Share Tech Mono", monospace';
      for (let i = 0; i < cols; i++) {{
        const ch = glyphs[Math.floor(Math.random() * glyphs.length)];
        const y = drops[i] * size;
        ctx.fillStyle = Math.random() > 0.97 ? '#D7FFE0' : '#00FF41';
        ctx.globalAlpha = Math.random() > 0.88 ? 0.75 : 0.30;
        ctx.fillText(ch, i * size, y);
        if (y > h && Math.random() > 0.975) drops[i] = 0;
        else drops[i] += 1;
      }}
      ctx.globalAlpha = 1;
      if (!reduce) requestAnimationFrame(frame);
    }}

    resize();
    frame();
    if (!reduce) window.addEventListener('resize', resize);
  }})();
</script>
</body></html>"""
    if hasattr(st, "iframe"):
        st.iframe(document, width="stretch", height=height)
    else:  # Streamlit < 1.6x
        import streamlit.components.v1 as components

        components.html(document, height=height, scrolling=False)
