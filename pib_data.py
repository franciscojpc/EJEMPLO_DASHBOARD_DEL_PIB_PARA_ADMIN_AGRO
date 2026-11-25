"""Cargador y normalizador del PIB Trimestral del INEGI (base 2018).

Los cinco tabulados comparten una hoja ``Tabulado`` con:

* fila 4: año de cada bloque (celdas combinadas; se rellena hacia adelante)
* fila 5: periodo (T1..T4, 6 Meses, 9 Meses, Anual; sufijos R/P)
* fila 6: unidad (solo en los archivos detallados)
* filas 7+: conceptos (código - nombre), y luego un segundo bloque de
  variación porcentual anual.

El resultado es un DataFrame largo y tipado que la app consume sin volver a
tocar los Excel.
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent / "tabulados_PIBT"

FILES = {
    "PIBT_2.xlsx": {
        "serie": "real",
        "unidad": "millones_pesos_2018",
        "start": 7,
        "bloque": None,
        "allowed": ("nivel", "var_anual"),
    },
    "PIBT_3.xlsx": {
        "serie": "nominal",
        "unidad": "millones_pesos_corrientes",
        "start": 7,
        "bloque": None,
        "allowed": ("nivel", "var_anual"),
    },
    "PIBT_4.xlsx": {
        "serie": "deflactor",
        "unidad": "indice_2018_100",
        "start": 7,
        "bloque": None,
        "allowed": ("nivel", "var_anual"),
    },
    "PIBT_r_2.xlsx": {
        "serie": "real_largo",
        "unidad": "millones_pesos_2018",
        "start": 6,
        "bloque": "nivel",
        "allowed": ("nivel",),
    },
    "PIBT_r_3.xlsx": {
        "serie": "var_largo",
        "unidad": "porcentaje",
        "start": 6,
        "bloque": "var_anual",
        "allowed": ("var_anual",),
    },
}

_SECTION_HEADERS = {
    "Variación porcentual anual": "var_anual",
    "Estructura porcentual": "estructura",
    "Contribución a la variación nacional": "contribucion",
}

# (key, etiqueta, códigos exactos, nombres exactos)
CONCEPTOS = [
    ("pib", "PIB", (), ("Producto interno bruto",)),
    ("vab", "Valor agregado bruto", (), ("Valor agregado bruto",)),
    ("primarias", "Actividades primarias", (), ("Actividades primarias",)),
    ("secundarias", "Actividades secundarias", (), ("Actividades secundarias",)),
    ("terciarias", "Actividades terciarias", (), ("Actividades terciarias",)),
    ("agro", "Agropecuario (11)", ("11",), ()),
    ("agricultura", "Agricultura (111)", ("111",), ()),
    ("ganaderia", "Ganadería (112)", ("112",), ()),
    ("forestal", "Forestal (113)", ("113",), ()),
    ("pesca", "Pesca (114)", ("114",), ()),
    ("serv_agro", "Servicios agro (115)", ("115",), ()),
    ("alimentos", "Industria alimentaria (311)", ("311",), ()),
    ("bebidas", "Bebidas y tabaco (312)", ("312",), ()),
]

PERIODOS = {"T1", "T2", "T3", "T4", "6 Meses", "9 Meses", "Anual"}
_HEADER_YEAR = 4
_HEADER_PERIOD = 5


def _clean_concept(raw: str) -> tuple[str | None, str]:
    clean = re.sub(r"^[_\s]+", "", str(raw)).strip()
    if " - " in clean:
        code, name = clean.split(" - ", 1)
        return code.strip(), name.strip()
    return None, clean


def _match_key(code: str | None, name: str) -> str | None:
    if code and code.endswith("B.1bP"):
        return "pib"
    if code and code.endswith("B.1bV"):
        return "vab"
    for key, _label, codes, names in CONCEPTOS:
        if code and code in codes:
            return key
        if name in names:
            return key
    return None


def _period_columns(df: pd.DataFrame) -> list[tuple[int, int, str, int | None, pd.Timestamp, str]]:
    years = df.iloc[_HEADER_YEAR].ffill()
    periods = df.iloc[_HEADER_PERIOD]
    columns: list[tuple[int, int, str, int | None, pd.Timestamp, str]] = []
    for j in range(1, df.shape[1]):
        year_raw = years.iloc[j]
        period_raw = periods.iloc[j]
        if pd.isna(year_raw) or pd.isna(period_raw):
            continue
        year_match = re.search(r"(\d{4})", str(year_raw))
        if not year_match:
            continue
        year = int(year_match.group(1))
        raw_period = str(period_raw).strip()
        status = raw_period[-1] if raw_period and raw_period[-1] in "RP" else ""
        period = raw_period[:-1] if status else raw_period
        if period not in PERIODOS:
            continue
        if period.startswith("T"):
            quarter = int(period[1])
            fecha = pd.Timestamp(year, 3 * (quarter - 1) + 1, 1)
        elif period == "6 Meses":
            quarter, fecha = None, pd.Timestamp(year, 6, 30)
        elif period == "9 Meses":
            quarter, fecha = None, pd.Timestamp(year, 9, 30)
        else:  # Anual
            quarter, fecha = None, pd.Timestamp(year, 12, 31)
        columns.append((j, year, period, quarter, fecha, status))
    return columns


def _parse_number(value) -> float | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().replace(",", "")
    if text.upper() in {"", "NA", "N/A", "NAN", "-"}:
        return None
    match = re.search(r"-?\d+(?:\.\d+)?", text)
    return float(match.group(0)) if match else None


def parse_workbook(path: Path, config: dict) -> pd.DataFrame:
    """Convierte un tabulado ancho en filas (concepto, periodo, valor)."""
    width = pd.read_excel(path, sheet_name="Tabulado", header=None)
    columns = _period_columns(width)
    block = config["bloque"]
    records: list[dict] = []

    for i in range(config["start"], len(width)):
        raw = width.iloc[i, 0]
        if not isinstance(raw, str) or not raw.strip():
            continue
        stripped = raw.strip()
        section = next(
            (block for header, block in _SECTION_HEADERS.items() if header in stripped),
            None,
        )
        if section is not None:
            block = section
            continue
        if block is None:
            block = "nivel"
        if block not in config["allowed"]:
            continue

        code, name = _clean_concept(raw)
        key = _match_key(code, name)
        if key is None:
            continue
        label = next(label for k, label, _c, _n in CONCEPTOS if k == key)
        for j, year, period, quarter, fecha, status in columns:
            value = _parse_number(width.iloc[i, j])
            if value is None:
                continue
            records.append(
                {
                    "serie": config["serie"],
                    "unidad": config["unidad"],
                    "bloque": block,
                    "key": key,
                    "nombre": label,
                    "codigo": code,
                    "anio": year,
                    "periodo": period,
                    "trimestre": quarter,
                    "fecha": fecha,
                    "estatus": status,
                    "valor": value,
                }
            )

    frame = pd.DataFrame.from_records(records)
    if frame.empty:
        raise ValueError(f"{path.name}: no se extrajeron observaciones")
    frame["archivo"] = path.name
    return frame


def load_pib(data_dir: Path | str = DATA_DIR) -> pd.DataFrame:
    """Carga los cinco tabulados y devuelve un DataFrame largo."""
    directory = Path(data_dir)
    frames = []
    for filename, config in FILES.items():
        path = directory / filename
        if not path.exists():
            raise FileNotFoundError(f"Falta {path}")
        frames.append(parse_workbook(path, config))
    df = pd.concat(frames, ignore_index=True)
    df = df.sort_values(["serie", "bloque", "key", "fecha"]).reset_index(drop=True)
    return df


def file_mtimes(data_dir: Path | str = DATA_DIR) -> tuple[float, ...]:
    """Firma de caché: cambia si cambia cualquier Excel."""
    directory = Path(data_dir)
    return tuple((directory / name).stat().st_mtime for name in FILES)
