# ¿El hogar ecuatoriano promedio gana $1.135 al mes?

Análisis reproducible de los microdatos abiertos de la **ENIGHUR 2024-2025**
(Encuesta Nacional de Ingresos y Gastos de los Hogares Urbanos y Rurales,
INEC Ecuador).

> **TL;DR** — El INEC publica que el hogar promedio gana **$1.135/mes**, pero ese
> promedio no representa la realidad: **65,8%** de los hogares gana *menos*. Quita
> solo al 10% más rico y la media cae a **$874**. El hogar típico (mediana) gana
> **$838**. Además, ese ingreso casi nunca lo aporta una sola persona (el hogar
> tiene **1,83 perceptores**) y apenas **6% de quienes trabajan** gana $1.200 por
> sí solo.

🔗 **Sitio con gráficos:** publica la carpeta `docs/` en GitHub Pages.

---

## Hallazgos

### 1. El "promedio" no representa la realidad

| Métrica (ingreso corriente total del hogar) | USD/mes |
|---|---|
| Media (lo que se publica) | **$1.135** |
| **Hogares que ganan MENOS que la media** | **65,8%** |
| **Mediana (hogar típico)** | **$838** |
| Media si se excluye al 10% más rico | **$874** |
| Percentil 25 | $520 |
| Percentil 90 | $2.212 |

Dos tercios de los hogares ganan menos que el "promedio". La media la empujan
hacia arriba los hogares de altos ingresos: basta quitar al **10% más rico** para
que caiga de $1.135 a **$874**. El número honesto para el hogar común es la
**mediana: $838**. El $1.135 no es falso ni está mal calculado — es una media
correcta mal interpretada: en una distribución con cola rica, la media *siempre*
queda por encima de lo típico.

### 2. Una brecha enorme: quién ahorra y quién se endeuda

Ordenando a las **personas** por ingreso per cápita en 5 grupos iguales (cada
quintil = 20% de la población), aparece la desigualdad detrás del promedio:

| Quintil de personas | Ingreso pc | Gasto pc | Tasa de ahorro | % ingreso nacional |
|---|---|---|---|---|
| Q1 (+ pobre) | $101 | $102 | **−0,3%** | 5,9% |
| Q2 | $169 | $160 | 5,5% | 9,9% |
| Q3 | $245 | $217 | 11,2% | 14,3% |
| Q4 | $366 | $305 | 16,6% | 21,3% |
| Q5 (+ rico) | $833 | $620 | **25,6%** | **48,6%** |

- El **20% más rico concentra el 48,6%** del ingreso nacional — casi tanto como el
  otro 80% junto — y gana **8,2x** lo que el más pobre.
- El **20% más pobre vive con $101/persona/mes** (~$3,4/día) y gasta *todo* lo que
  tiene (desahorra). El ahorro es un lujo de los de arriba.

> **¿Por qué por persona y no por hogar?** 20% de hogares no es 20% de personas:
> los hogares pobres son más pequeños, así que el quintil más pobre de *hogares*
> contiene solo el 14,3% de la población. Ordenar por persona reparte a la
> población en cinco grupos exactamente iguales de gente real. *No hay sesgo de
> muestreo*: cada quintil descansa sobre miles de hogares encuestados y todo se
> pondera con el factor de expansión `Fexp`.

### 3. El ingreso del hogar lo aportan ~2 personas, no una

- Promedio de **1.83 perceptores por hogar**.
- 42% de los hogares tiene **1 solo** perceptor, 40% tiene **2**.
- Un perceptor gana en promedio ~$513 de trabajo; se necesitan **~2** sumados
  (más transferencias y rentas) para llegar al ingreso del hogar.

### 4. Ganar $1.200 uno solo es raro: solo el 6%

Ingreso laboral por persona (perceptores con ingreso > 0; 7,08 millones):

| Métrica | USD/mes |
|---|---|
| Media | $513 |
| Mediana | **$426** |
| Ganan ≥ $470 (salario básico) | 42% |
| Ganan ≥ $800 | 14,5% |
| Ganan ≥ $1.000 | 9,1% |
| **Ganan ≥ $1.200** | **6,0% — 425.291 personas** |
| Ganan ≥ $2.000 | 1,9% |

Solo **425.291 personas** ganan $1.200 o más por su trabajo (~2,3% de la
población total de 18,1 millones).

### 5. "Ayuda con dinero a otros hogares" — la redistribución informal

El dato que originó este proyecto (código ENIGHUR `2009006`):

- **$140,6 millones/mes** que los hogares dan a otros hogares e instituciones.
- **19,8%** de los hogares da ayuda; en promedio **$130/mes** (mediana $70).
- Es el componente más grande del *gasto de no consumo*.

> La encuesta junta "otros hogares" e "instituciones" en una sola pregunta, así
> que no se pueden separar. Pero como las donaciones *recibidas* de instituciones
> son mínimas ($1,3M/mes), casi todo es transferencia **entre hogares** (ayuda a
> familiares).

---

## Reproducir el análisis

Requisitos: `bash`, `curl`, `unzip`, `python3` (3.8+). El análisis usa solo la
librería estándar de Python.

```bash
# 1. Descargar y extraer los microdatos del INEC (~170 MB, CC BY 4.0)
bash scripts/01_download.sh

# 2. Correr el análisis -> genera results/resumen.json y docs/data/resumen.json
python3 scripts/02_analysis.py
```

El paso 1 baja `DATOS_ABIERTOS_ENIGHUR.zip` de la web oficial del INEC, verifica
que sea un ZIP válido y extrae solo los 3 CSV necesarios. El paso 2 calcula todas
las cifras (ponderadas por el factor de expansión `Fexp`) y las guarda en JSON.

### Ver el sitio localmente

```bash
python3 -m http.server -d docs 8000
# abre http://localhost:8000
```

---

## Estructura

```
.
├── scripts/
│   ├── 01_download.sh      # descarga + verifica + extrae los CSV del INEC
│   └── 02_analysis.py      # calcula todas las cifras -> resumen.json
├── results/
│   └── resumen.json        # resultados agregados (versionado, ligero)
├── docs/                   # sitio estático para GitHub Pages
│   ├── index.html
│   ├── app.js              # carga resumen.json y dibuja los gráficos
│   ├── styles.css
│   └── data/resumen.json   # copia para el sitio
├── data/                   # microdatos crudos (NO versionados, ver .gitignore)
├── requirements.txt
└── LICENSE                 # MIT (código). Datos: CC BY 4.0 del INEC.
```

---

## Metodología y notas

- **Ponderación:** toda media/porcentaje usa el factor de expansión `Fexp`.
- **Ingreso del hogar:** `ing_cor_tot` (corriente total) y `ing_mon_cor`
  (monetario) del archivo `ENIGHUR25_HOGARES_AGREGADOS.csv`.
- **Ingreso individual:** `i1703099` (ingreso neto del trabajo dependiente) +
  `i1706099` (ingreso neto del trabajo independiente) de
  `ENIGHUR2025_PERSONAS_INGRESOS.csv`. Validado: agregado por hogar reproduce
  el 96-100% del ingreso laboral del hogar (`ing_trab_mon`).
- **Ayuda a otros hogares:** `i2009006` de `ENIGHUR2025_INGRESOS_H.csv`.
- **Salario básico unificado 2024-2025:** $470.

## Fuente y licencia

- **Datos:** [ENIGHUR 2024-2025, INEC Ecuador](https://www.ecuadorencifras.gob.ec/encuesta-nacional-de-ingresos-y-gastos-de-los-hogares-urbanos-y-rurales/) — CC BY 4.0.
- **Código:** MIT (ver `LICENSE`).
