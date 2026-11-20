# Atlas IA Latam

**¿Quién usa la IA generativa en América Latina, para qué y en qué condiciones?**

Sitio: https://camilocontrerasphd.github.io/atlas-ia-latam/ (en inglés: `?lang=en`)

## Para qué y de dónde nace

El sitio muestra el uso de la IA generativa con enfoque en América Latina, medido con el uso de Claude: cuánto se usa en cada país, para qué se usa y qué condiciones acompañan ese uso. Compara 16 países latinoamericanos con 121 países del mundo.

La fuente central es el [Anthropic Economic Index](https://huggingface.co/datasets/Anthropic/EconomicIndex) (licencia CC-BY), que publica el uso de Claude.ai por país, por propósito (trabajo, cursos, asuntos personales), por categoría de solicitud y por ocupación. La vista Ciencia aplica las técnicas del estudio de OpenAI «Science at the Frontier» (Liao, Shan y Chatterji, 2026), que describe cómo usan la IA los científicos pero no tiene variables geográficas.

El índice mide a todos los usuarios de Claude.ai, estudiantes incluidos, y un solo producto. No identifica a investigadores ni mide el uso de otras herramientas de IA.

## Vistas del sitio

| Vista | Qué muestra |
|---|---|
| Adopción | Índice de uso por país frente al ingreso y al uso de IA en general, concentración del uso, departamentos y estados de Colombia, Brasil y México, y cambios entre agosto de 2025 y mayo de 2026 |
| Condiciones | Costo de Claude Pro y de internet frente al ingreso, graduados en STEM y TIC, y un explorador de dos variables por país |
| Usos | Trabajo, cursos y asuntos personales; especialización por grupo ocupacional; uso frente a la estructura del empleo; desarrolladores de GitHub |
| Ciencia | Flujos y tareas de trabajo científico por país, involucramiento del usuario y producción académica sobre modelos de lenguaje |
| Método y datos | Fuentes, filtros, reglas de clasificación y límites |

Cada gráfico tiene un botón «Cómo se calcula» con la fórmula y la definición de cada término.

## Estructura del repositorio

```
docs/                 sitio publicado en GitHub Pages
  index.html          página
  cx.css, site.css    estilos
  js/dash-shim.js     carga los datos de docs/data y redibuja los gráficos al cambiar filtros o idioma
  js/cx-*.js          motor de gráficos (cx-base), textos en inglés (cx-i18n), navegación (cx-nav) y gráficos por vista (cx-s1 a cx-s5)
  js/d3.min.js        D3 v7.9.2
  data/*.json         29 conjuntos de datos que lee el sitio, cada uno {rows, meta}
scripts/              scripts de análisis en Python, numerados en orden de ejecución
```

Los datos crudos (carpeta `data/` del proyecto) no se incluyen; se descargan de las fuentes listadas abajo. Los scripts se ejecutan desde la raíz del proyecto con esa carpeta en su lugar (`python3 scripts/<archivo>`) y escriben en `output/`. Los JSON de `docs/data/` son la copia de `output/sitio/*.json` y de nueve archivos de `output/charts/`.

Para ver el sitio en local: `cd docs && python3 -m http.server` y abrir http://localhost:8000.

## Fuentes

| Fuente | Qué se toma | Periodo |
|---|---|---|
| Anthropic Economic Index (Hugging Face) | Índice de uso, propósito, categorías de solicitud, ocupaciones SOC, patrones de colaboración, pericia y duración | Agosto y noviembre de 2025; febrero, abril y mayo de 2026 |
| Banco Mundial (API) | PIB per cápita PPA, ingreso nacional bruto per cápita (Atlas), I+D, investigadores, matrícula terciaria, internet, regiones y grupos de ingreso | Último dato 2015-2025 |
| Microsoft AI Diffusion Report (vía Our World in Data) | % de la población de 15 a 64 años que usa IA generativa | Marzo de 2026 |
| UIT, ICT Price Baskets | Precio de banda ancha móvil y fija de 5 GB en % del ingreso | 2025 |
| Instituto de Estadística de la UNESCO (vía Banco Mundial) | % de graduados terciarios en STEM y TIC | Último dato desde 2015 |
| OIT, ILOSTAT | Empleo por subgrupo de la CIUO-08 | Último año desde 2018 |
| BLS y paquete iscoCrosswalks (CRAN) | Correspondencias SOC 2018 → SOC 2010 → CIUO-08 | — |
| GitHub Innovation Graph | Cuentas de desarrolladores por país | Primer trimestre de 2026 |
| OpenAlex | Artículos por país, total y sobre modelos de lenguaje | 2025 |
| Gemini y DeepSeek V4.1 Flash | Poblaciones subnacionales (DANE, IBGE, INEGI), EF EPI y calendarios académicos; solo se usan los valores en que ambos coinciden | — |

Las URL exactas de descarga y los filtros de cada fuente están en la vista Método y datos.

## Reproducción

Requisitos: Python 3 con pandas, numpy, scipy, statsmodels, scikit-learn, pycountry, openpyxl y pyreadr.

| Script | Qué hace |
|---|---|
| regiones.py | Regiones del Banco Mundial y lista de los 16 países de América Latina |
| 01–03 | Reconstrucción de la jerarquía de categorías de solicitud (solo se usa el núcleo estable) |
| 04–06 | Perfil académico por flujo y tareas O*NET de ocupaciones científicas |
| 07–09 | Índice de uso por entrega, trayectoria con 113 países fijos, intensidad y propósito en mayo de 2026 |
| 10, 19, 24 | Datos de gráficos de rondas anteriores (`output/charts/`) |
| 11 | Lectura y comparación de las tablas pedidas a Gemini y DeepSeek |
| 12 | Vacaciones académicas y uso: efectos fijos de país y periodo |
| 13 | Intensidad y propósito por departamento o estado |
| 14 | Correlaciones de Spearman con intervalos por remuestreo |
| 15–16 | Ventaja comparativa revelada por grupo ocupacional, cercanía, densidad y AUC |
| 17 | Análisis de correspondencias de las categorías de solicitud |
| 18 | Artículos sobre modelos de lenguaje frente al uso |
| 20 | Curvas de Lorenz y Gini, entre países y dentro de Colombia, Brasil y México |
| 21 | Clasificación de categorías en flujos y tareas científicas por acuerdo entre dos modelos |
| 22 `[cobertura] [mes]` | Peso de cada flujo por país, ANOVA de Welch entre regiones con ajuste de Holm, difusión de tareas con intervalo de Wilson. Variables de entorno `FUENTE=acuerdo/ds/gm` y `PESO=todo/trabajo` |
| 23 | Involucramiento por flujo y su regresión sobre pericia y duración |
| 25 | Datos del sitio (`output/sitio/*.json`) |
| 26 | Análisis con fuentes externas (`output/sitio/ext_*.json`); se corre después del 25 |

Instrumentos editables: `scripts/scholarly_request_map.csv` (categorías de solicitud → flujo del estudio de OpenAI) y `scripts/onet_science_task_map.csv` (tareas O*NET → flujo).

## Límites

- El índice mide a todos los usuarios de Claude.ai. Las tareas «explicar conceptos científicos» y «apoyar docencia y mentoría» recogen sobre todo uso de estudiantes.
- El índice no publica las celdas con pocas conversaciones; una categoría ausente es «no publicada», no cero. Por eso muchos países no entran en los gráficos de uso científico.
- Las entregas de 2026 cubren un mes completo y tienen reglas de publicación nuevas; un salto entre febrero y abril de 2026 puede venir de ese cambio.
- El índice asigna cada conversación a una tarea por su contenido, no por la ocupación de quien escribe.

---

## English

**Who uses generative AI in Latin America, for what, and under which conditions?** The site compares 16 Latin American countries with 121 countries worldwide using the Anthropic Economic Index (Claude.ai usage by country, purpose, request category and occupation), together with World Bank, Microsoft, ITU, UNESCO, ILO, GitHub and OpenAlex data. The Science view applies the techniques of OpenAI's "Science at the Frontier" (Liao, Shan and Chatterji, 2026).

- Site: https://camilocontrerasphd.github.io/atlas-ia-latam/?lang=en (the flag selector switches language).
- `docs/` holds the static site; `scripts/` holds the Python analysis, numbered in execution order (see the table above). Raw data are not included; the sources and filters are listed in the site's Methods and data view.
- The index covers all Claude.ai users, students included, and a single product.

Autor: Camilo Andrés Rojas-Contreras, Facultad de Administración, Universidad de los Andes.
