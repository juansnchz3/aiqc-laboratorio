# CLAUDE.md

Guía para Claude Code (y otros agentes) al trabajar en este repositorio.

## Qué es

**AIQC v4.13** — app **Streamlit** de control de calidad para laboratorio
clínico. Pila: `streamlit`, `pandas`, `numpy`, `plotly`, `fpdf2`, `bcrypt`,
`google-generativeai`, `requests`. SQLite local para usuarios/auditoría.
El idioma de la interfaz y de los textos de dominio es **español** (con
acentos); manténlo así.

## Entorno (.venv) — IMPORTANTE

Todo el trabajo se hace dentro de un **entorno virtual `.venv`** en la raíz del
repo. **No instalar paquetes globalmente** (el sistema solo debe tener el Python
base). Crear/usar el entorno:

```bash
python3 -m venv .venv                    # crear (una sola vez)
source .venv/bin/activate                # activar (macOS/Linux)
# Windows: .venv\Scripts\activate
```

Una vez activado, `python`, `pip`, `streamlit` y `black` apuntan al venv. Si no
quieres activarlo, prefija los comandos con `.venv/bin/` (p. ej.
`.venv/bin/streamlit run app.py`). `.venv/` está ignorado por git.

**Nota de versión:** este macOS solo trae **Python 3.9.6** del sistema (sin
Homebrew). El proyecto declara objetivo 3.11+ (CI y Black), pero corre en 3.9
con las dependencias actuales. Las libs de Google (`google-generativeai`,
`google-auth`) emiten `FutureWarning` en 3.9 — no bloquean, pero conviene
migrar a 3.11+ y a `google.genai` (ver `ARCHITECTURE.md`). No instales otra
versión de Python fuera del venv sin acordarlo.

## Comandos

Asumen el venv **activado** (o prefija con `.venv/bin/`):

```bash
pip install -r requirements.txt         # dependencias de ejecución
pip install -r requirements-dev.txt     # + black (desarrollo)
streamlit run app.py                    # ejecutar la app (http://localhost:8501)
python -m py_compile app.py aiqc/*.py   # comprobación rápida de sintaxis
python -c "import aiqc"                 # comprobar que el paquete importa
black app.py aiqc/                      # formatear (antes de commit)
black --check --diff app.py aiqc/       # lo que valida el CI
```

No hay aún suite de tests. La verificación mínima antes de dar algo por bueno es
`py_compile` de todos los módulos **y** un `import aiqc` correcto. Idealmente,
arrancar `streamlit run app.py` y comprobar que no rompe al cargar.

El **formato lo impone Black** (config en `pyproject.toml`, `line-length = 100`).
El CI (`.github/workflows/ci.yml`) falla si `black --check` no pasa, así que
ejecuta `black app.py aiqc/` antes de hacer commit.

## Arquitectura

> Para la visión a futuro (paso a API/FastAPI, integración real de datos vía
> HL7/ASTM/FHIR, requisitos de producto clínico y plan por fases) ver
> **`ARCHITECTURE.md`**. El principio rector es mantener la lógica de dominio
> (`aiqc/`) independiente de UI, almacenamiento y fuente de datos.

Punto de entrada `app.py` (raíz). Toda la lógica vive en el paquete `aiqc/`:

| Módulo                 | Responsabilidad |
|------------------------|-----------------|
| `aiqc/config.py`       | Acceso seguro a `st.secrets`: `get_section`, `get_value`. Único sitio que toca `st.secrets`. |
| `aiqc/styles.py`       | CSS (constante `CSS`). |
| `aiqc/knowledge_base.py` | `BIORAD_KB`, `GRUPOS_ANALITICOS`, `NIVELES`, `COBAS_8000_KB`, `TEA_CLIA`, `buscar_kb`, `nivel_badge`. **Sin** dependencias de terceros. |
| `aiqc/database.py`     | SQLite: usuarios, acciones, auditoría; login bcrypt; `tiene_permiso`; `render_login`. |
| `aiqc/data_io.py`      | `build_demo` (cacheado), lectura/normalización CSV-Excel, sync GitHub/OpenLab. |
| `aiqc/measurements.py` | Persistencia de mediciones QC en SQLite: `guardar_mediciones` (append con dedup), `cargar_mediciones`, `borrar_fuente`, `resumen_fuentes`. Sin dependencias de UI. |
| `aiqc/qc_rules.py`     | Núcleo estadístico: `evaluar_westgard`, `evaluar_r4s`, `calcular_ewma`, `calcular_cusum`, `calcular_sigma`. |
| `aiqc/charts.py`       | Figuras Plotly (LJ, EWMA, CUSUM) y paneles UI (`render_kb_panel`, `render_r4s_alert`, `estado_badge`). |
| `aiqc/reports.py`      | Exportación `generar_csv` y `generar_pdf`. |
| `aiqc/ai_assistant.py` | Asistente Gemini: `ia_responde_gemini`, `necesita_datos_qc`. |

Fuera del paquete, `scripts/sync_openlab.py` es el **agente de subida** que corre
**en el laboratorio**: lee los TXT que exporta OpenLab, los normaliza al contrato
de datos y los sube a GitHub (el espejo de escritura de `leer_csv_github`). No es
lógica de la app ni se importa desde `aiqc/`; corre como proceso autónomo. El
token sale de `GITHUB_TOKEN` o de `[github].token` — **nunca** hardcodeado. Sus
dependencias están en `scripts/requirements-sync.txt` (aparte de la app).

### Reglas de dependencia entre módulos

El grafo de imports es **acíclico**; respétalo al añadir código:

```
knowledge_base ← qc_rules ← charts ← reports
       ↑             ↑                   ↑
       └──────── ai_assistant ───────────┘
app.py importa de todos.
```

- `knowledge_base` y `qc_rules` no deben importar de `charts`, `reports`,
  `ai_assistant` ni `app` (evita ciclos).
- Dentro del paquete usa **imports relativos**: `from .knowledge_base import ...`.
- `app.py` usa imports absolutos: `from aiqc.qc_rules import ...`.

## Convenciones

- El contrato de datos en todo el código es un `DataFrame` con columnas:
  `Fecha, Analito, Nivel, Valor, Media_Objetivo, SD_Objetivo, Lote`.
  `evaluar_westgard` añade `Z_Score, Regla_Violada, Score_Riesgo, Estado`.
- Estados: `"Verde"`, `"Ámbar"`, `"Rojo"` (con acento, exactamente así).
- Niveles: códigos `"N"`, `"PB"`, `"PA"` → etiquetas vía `NIVELES`.
- Z-Score = `(Valor - Media_Objetivo) / SD_Objetivo`.
- **R-4s** es error aleatorio entre niveles → la acción correcta es repetir
  ambos niveles, **no** recalibrar como primer paso. No cambies esta semántica.
- El PDF (`fpdf2`) solo admite latin-1: todo texto pasa por `pdf_txt()`
  (`reports.py`), que sustituye emojis/símbolos. Si añades caracteres nuevos al
  PDF, amplía `PDF_REP`.
- El CSV se exporta con `;` y UTF-8 BOM para Excel español. No lo cambies sin motivo.

## Estado / sesión

- La conexión SQLite vive en `st.session_state["db_con"]`.
- Prioridad de fuente de datos: `df_github` → `df_manual` → `build_demo()`.
- **Persistencia de mediciones:** al cargar un CSV/Excel o sincronizar GitHub,
  los datos se guardan en la tabla `mediciones` (`aiqc/measurements.py`) además
  de en `session_state`. Al arrancar, la app rehidrata `df_manual`/`df_github`
  desde la BD si `session_state` está vacío (una vez por sesión de servidor,
  flag `_persistencia_rehidratada`). Clave de dedup: `(fecha, analito, nivel,
  fuente)` — recargar el mismo archivo actualiza, no duplica.
- **⚠ Disco efímero en Streamlit Community Cloud:** la BD SQLite sobrevive a
  recargas de página y reruns, pero **NO a un redeploy o reinicio del
  contenedor**. Para persistencia duradera hay que apuntar `[db].path` a un
  volumen persistente o migrar a una BD externa (Postgres, Turso/libSQL). Ver
  `ARCHITECTURE.md` (Fase 1).
- Toda acción relevante (login, export, sync, cambios de usuario) debe llamar a
  `registrar_auditoria(...)`.

## Base de datos (ubicación)

- `get_db_path()` (`aiqc/database.py`) resuelve la ruta: usa `[db].path` de
  secrets si se define; si está vacío, usa `~/.aiqc/aiqc_acciones.db`.
- Las rutas **relativas** en `[db].path` se anclan a la **raíz del proyecto**
  (no al cwd), y el directorio se crea automáticamente. Multiplataforma.
- **En desarrollo** `secrets.toml` apunta a `.aiqc/aiqc_acciones.db` (dentro del
  proyecto, ignorado por git) para no dejar ficheros en el home. En despliegue
  real, déjalo vacío o usa una ruta absoluta gestionada.

## Secretos y seguridad

- Configuración en `.streamlit/secrets.toml` (plantilla en
  `.streamlit/secrets.toml.example`). **Nunca** subir `secrets.toml` ni `*.db`
  (ya están en `.gitignore`).
- No imprimas ni registres claves de API ni hashes de contraseña.
- **Nunca** uses `st.secrets` directamente: lanza excepción si no hay
  `secrets.toml`. Usa siempre `aiqc/config.py` (`get_section`/`get_value`), que
  permite que la app arranque en modo demo sin ninguna configuración.

## Al modificar

- Cambios de UI → normalmente `app.py` y/o `aiqc/styles.py`.
- Lógica de QC nueva → `aiqc/qc_rules.py`, y su visualización en `aiqc/charts.py`.
- Mantén el español y el estilo del código existente (snake_case, comentarios
  de sección con `# ===`). Tras cualquier cambio, recompila y reimporta.
