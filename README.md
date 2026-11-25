# EJEMPLO DASHBOARD DEL PIB PARA ADMIN AGRO

Dashboard interactivo del **Producto Interno Bruto Trimestral de México**
(INEGI, base 2018) con estética de terminal Matrix y foco en las actividades
primarias: agricultura, ganadería, forestal y pesca.

Construido con **Python + Streamlit + Plotly + Matplotlib + Pandas**.

## Qué incluye

- **Panorama:** PIB total vs actividades primarias (índice 2018 = 100),
  crecimiento anual por sector e historia larga 1980–2025.
- **Agro:** evolución de los componentes agropecuarios, crecimiento anual y
  participación dentro de las actividades primarias.
- **Estructura:** composición del valor agregado bruto (primarias,
  secundarias, terciarias), su evolución y un gráfico de círculos con área
  proporcional al peso de cada sector.
- **Ciclo:** mapas de calor de variación anual por año y trimestre para el PIB
  total y las actividades primarias.
- **Precios:** PIB nominal vs real y deflactor implícito (2018 = 100).
- **Datos y stats:** estadística descriptiva (media, mediana, desviación
  estándar, CV, percentiles, mínimos/máximos y variación anual), tabla
  descargable en CSV y diccionario de datos.
- Filtros de ventana temporal, selección de componentes agropecuarios y lluvia
  digital opcional.

## Datos

Fuente: **INEGI, Sistema de Cuentas Nacionales de México, Producto Interno
Bruto Trimestral, base 2018.** Series originales (sin desestacionalizar).

| Archivo | Contenido | Unidad | Cobertura |
|---|---|---|---|
| `PIBT_2.xlsx` | PIB real y variación anual, detalle por actividad | Millones de pesos anualizados a precios de 2018 | 1993 T1–2026 T3 |
| `PIBT_3.xlsx` | PIB nominal y variación anual | Millones de pesos anualizados a precios corrientes | 1993 T1–2026 T3 |
| `PIBT_4.xlsx` | Deflactor implícito | Índice 2018 = 100 | 1993 T1–2026 T3 |
| `PIBT_r_2.xlsx` | Serie larga real de agregados | Millones de pesos a precios de 2018 | 1980 T1–2026 T3 |
| `PIBT_r_3.xlsx` | Serie larga de variación anual | Porcentaje | 1980 T1–2026 T3 |

Notas:

- Cifras **2024–2025 revisadas**; **2026 T1–T2 revisadas** y **T3
  preliminar**.
- El PIB está anualizado: cada trimestre se expresa en millones de pesos a
  tasa anual para facilitar comparaciones.
- Los sectores primarias, secundarias y terciarias suman el **valor agregado
  bruto (VAB)**. El PIB incluye además los impuestos netos sobre los productos.
- Al ser series originales, la comparación recomendada es **anual** (mismo
  trimestre del año anterior), no trimestre contra trimestre.

## Ejecutar

Requiere **Python 3.12 o 3.13** (para 3.15 aún faltan wheels de parte del
stack).

```bash
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

La app abre en `http://localhost:8501`.

## Estructura

```text
app.py                 # interfaz Streamlit, KPIs, tabs y gráficos
pib_data.py            # parser de los cinco Excel y caché de datos
matrix_theme.py        # tema Matrix: paleta, Plotly, Matplotlib y CSS
requirements.txt
.streamlit/config.toml # tema oscuro de Streamlit
tabulados_PIBT/        # datos fuente del INEGI
```

## Metodología

- `pib_data.py` lee la hoja `Tabulado` de cada archivo, normaliza los encabezados
  de año/periodo (incluidos los sufijos R/P) y extrae únicamente los conceptos
  usados por el dashboard.
- Los índices se calculan con el nivel anual de 2018 como base.
- Las participaciones sectoriales se calculan sobre el VAB; la participación
  primaria del KPI se calcula sobre el PIB total.
- Los mapas de calor usan una escala divergente verde–magenta centrada en cero,
  acotada al percentil 95 para evitar que los outliers de 2020 aplanen el resto.
- La estadística descriptiva se calcula sobre los trimestres de la ventana
  seleccionada: media, mediana, desviación estándar, coeficiente de variación,
  percentiles 25/75 y mínimos/máximos en billones de pesos de 2018; la
  variación anual resume el bloque de variación porcentual del INEGI.
- El gráfico de círculos usa el área de cada círculo para representar la
  participación de cada sector en el VAB del año elegido.
- Todo el procesamiento ocurre en memoria; los Excel no se modifican.

## Limitaciones

- Es un ejemplo académico/administrativo, no una publicación oficial.
- Las cifras preliminares pueden cambiar en la siguiente actualización del
  INEGI.
- La estética Matrix es decorativa; los colores de las series fueron validados
  para daltonismo y contraste sobre fondo negro.
- El dashboard no hace pronósticos ni ajuste estacional.

## Créditos

- Datos: **INEGI**, Producto Interno Bruto Trimestral, base 2018.
- Tema visual: skill `matrix-dashboards` (paleta validada, Plotly, Matplotlib y
  CSS de terminal).
