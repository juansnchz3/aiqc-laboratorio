# Mejoras propuestas para AIQC

Registro de mejoras **incrementales** sobre la app actual (Streamlit). Para la
evolución a producto (API/FastAPI, HL7/ASTM/FHIR, SaaS) ver `ARCHITECTURE.md`;
aquí solo lo que se puede hacer sin cambiar de arquitectura.

Leyenda de esfuerzo: 🟢 bajo · 🟡 medio · 🔴 alto. Cada punto lleva casilla para
ir marcando lo hecho.

---

## 1. Carga de datos desde la interfaz (la petición original)

**Estado actual:** el drag & drop **ya existe** (`st.file_uploader` en el
sidebar, `app.py`), pero está escondido en una pestaña pequeña de la barra
lateral, y el DataFrame cargado vive solo en `st.session_state` → **se pierde
al recargar la página o cerrar sesión**.

- [ ] 🟢 **Hacer protagonista la carga de archivo**: cuando no hay datos reales
  (modo demo), mostrar en el área principal una pantalla de bienvenida con una
  zona grande de drag & drop, ejemplo de formato esperado y un botón
  "Descargar plantilla CSV". El sidebar se queda como acceso secundario.
- [x] 🟡 **Persistir los datos cargados en SQLite** *(hecho:
  `aiqc/measurements.py` con tabla `mediciones`, append con dedup por
  `(fecha, analito, nivel, fuente)`, rehidratación al arrancar, y expander en
  el sidebar para ver/borrar datos por fuente. 12 tests dedicados.
  **Limitación documentada:** disco efímero en Streamlit Cloud → no sobrevive
  a redeploy; para eso hace falta BD externa, ver `ARCHITECTURE.md` Fase 1).*
- [x] 🟢 **Feedback de validación al cargar** *(hecho en versión simple: aviso
  con el nº de filas descartadas en carga manual y sync GitHub; queda pendiente
  la tabla expandible con el motivo por fila)*.
- [ ] 🟢 **Vista previa antes de aceptar**: tras soltar el archivo, mostrar las
  primeras filas ya normalizadas y pedir confirmación (append / reemplazar /
  cancelar), en vez de aplicarlo directamente.
- [ ] 🟡 **Entrada manual de puntos QC**: un `st.data_editor` (o formulario
  "Añadir medición") para teclear el control del día sin necesidad de CSV.
  Es el uso diario real de un técnico: un valor por analito/nivel por corrida.
- [ ] 🟢 **Subida de varios archivos a la vez** (`accept_multiple_files=True`)
  concatenando tras normalizar.

## 2. Sincronización GitHub/OpenLab

- [ ] 🟢 **Cachear la descarga** con `st.cache_data(ttl=...)` y usar el header
  `If-None-Match`/ETag de la API de GitHub para no re-descargar si el CSV no
  cambió (además la API tiene rate limit de 60 req/h sin token).
- [ ] 🟢 El "auto-sincronizar cada 60 min" solo se dispara si hay interacción
  (Streamlit re-ejecuta al interactuar). Documentarlo o usar
  `st.fragment(run_every=...)` para un refresco real periódico.
- [ ] 🟡 Combinar fuentes en vez de prioridad excluyente GitHub > manual >
  demo: con la tabla `mediciones` (punto 1) ambas fuentes hacen append al
  mismo almacén y la "fuente" pasa a ser un atributo de cada fila, no un modo
  global de la app.

## 3. Rendimiento

El problema de fondo: `evaluar_westgard` se llama **decenas de veces por
rerun** (bucle del sidebar "Estado del laboratorio", comparativa de niveles,
tab Bio-Rad, tab Registro, y el asistente IA), y cada llamada recorre el
DataFrame fila a fila en Python puro. Con 2 analitos no se nota; con 20-30
analitos × 3 niveles la app se arrastrará.

- [x] 🟡 **Evaluar una sola vez por rerun**: función
  `evaluar_todo(df_all, f_min, f_max)` cacheada con `st.cache_data` que
  devuelve `{(analito, nivel): df_evaluado}`; todas las secciones consumen ese
  dict en lugar de re-filtrar y re-evaluar. *(Hecho, incluye `evaluar_r4s_todo`;
  el asistente IA aún evalúa por su cuenta.)*
- [ ] 🟡 **Vectorizar `evaluar_westgard`** (rolling de pandas/numpy para 2_2s,
  4_1s, 10_x en vez del bucle `for i in range(len(df))`). Hacerlo *después* de
  tener tests (punto 6) para no romper la semántica.
- [x] 🟢 Cachear también `evaluar_r4s` (hecho); `calcular_sigma` ahora reusa
  los DataFrames ya evaluados del dict cacheado.
- [ ] 🟢 Aislar el chat IA en un `@st.fragment`: hoy cada mensaje al asistente
  re-ejecuta toda la página (sidebar, gráficos, tablas incluidos).

## 4. Interfaz / UX

- [x] 🟡 **Migrar de 8 tabs a páginas** (`st.navigation` / `st.Page`) *(hecho:
  cada sección es una función `_page_X()` en el sidebar; solo se ejecuta la
  página activa. Verificadas las 8 vía AppTest.)*
- [x] 🟢 **Eliminar la barra de "controles rápidos" duplicada** *(hecho: era
  además un bug real — cambiar el analito en el sidebar rompía la app con
  `StreamlitAPIException` al reescribir `sel_analito` tras instanciarse el
  widget. Ahora es una barra de contexto de solo lectura.)*
- [x] 🟢 **Tablas con `st.dataframe` + `column_config`** *(hecho: las 3 tablas
  HTML (Dashboard, EWMA/CUSUM, Sigma) migradas a st.dataframe ordenable, con
  barra de progreso en Score y formato de columnas; sin HTML crudo.)*
- [x] 🟢 **Login dentro de `st.form`** para que Enter envíe el formulario.
- [ ] 🟢 Usar `st.toast` para confirmaciones (guardado de lote, sync OK…) en
  vez de `st.success` que empuja el layout.
- [~] 🟡 **Tema coherente**: *(parcial: creado `.streamlit/config.toml` con
  `[theme]` de marca y `styles.py` reescrito con tokens en `:root`. Pendiente:
  reducir el HTML inline de `app.py` a componentes reutilizables, y un modo
  oscuro real para el área principal.)*
- [ ] 🟢 El PDF generado obliga a dos clics ("Descargar PDF" → generar →
  "Guardar PDF"). Generar directamente en el `st.download_button` (con
  callback o generación perezosa) para dejarlo en un clic.
- [x] 🟡 **Vista global tipo "semáforo"** *(hecho: `aiqc/overview.py`, panel
  HTML embebido al inicio del Dashboard — matriz analito × nivel, analitos en
  Rojo primero, alarmas R-4s; theme-aware, sin toolchain).*
- [ ] 🟢 **Deprecación `use_container_width`**: Streamlit lo retira tras
  2025-12-31 a favor de `width='stretch'`. Está usado decenas de veces en
  `app.py`; migración mecánica pendiente (solo avisos, aún funciona).

## 5. Corrección / lógica de QC

- [x] 🟢 **Claves inestables en el Registro de acciones** *(hecho: clave
  `fecha_analito_nivel_regla` con sufijo solo si hay duplicados exactos.
  Nota: los checks marcados con el formato antiguo quedan huérfanos una vez.)*
- [ ] 🟢 **Sigma Metrics con CV observado**: `calcular_sigma` usa
  `SD_Objetivo` (el σ del inserto) como CV, pero el sesgo sí lo calcula con
  datos observados. Lo metodológicamente correcto es usar la **SD real de los
  valores medidos** en el período. Revisar y documentar la fórmula elegida.
- [ ] 🟡 **Reglas de Westgard configurables por analito**: hoy el juego de
  reglas es fijo. En la práctica el juego de reglas se elige según el sigma
  del método (p. ej. ≥6σ basta 1_3s; 3-4σ requiere multiregla completa).
  Mínimo: poder activar/desactivar 1_2s como rechazo o aviso.
- [ ] 🟢 Persistir en la BD los **valores objetivo y TEa editados** (tab
  Configuración y tab Sigma): ahora viven en `session_state` y se pierden al
  cerrar sesión; además mutan los DataFrames en memoria en vez de guardarse
  como configuración aplicable a datos futuros.

## 6. Calidad de código y robustez

- [x] 🟡 **Suite `pytest` para `aiqc/qc_rules.py`** *(hecho: `tests/` con 36
  tests de Westgard, R-4s, EWMA, CUSUM, Sigma; job `tests` añadido al CI).*
- [x] 🟢 Tests también para `normalizar_df` *(hecho; destaparon y corrigieron
  un bug real: los niveles con acento — "Patológico Alto" — no se mapeaban y
  caían a "N").*
- [ ] 🟢 **Type hints** en `aiqc/` (al menos firmas públicas) + `mypy`/`ruff`
  en CI. `ruff` puede además sustituir a futuro varios checks manuales.
- [ ] 🟡 Migrar `google-generativeai` (deprecado) → **`google-genai`**, y en
  paralelo el salto a Python 3.11+ (ver nota en `CLAUDE.md`).
- [x] 🟢 `registrar_auditoria` traga todas las excepciones con `pass`: al
  menos loggear el fallo *(hecho: `logger.exception`)*.

## 7. Seguridad (sin salir de Streamlit)

- [x] 🟢 **Contraseña admin por defecto** *(hecho: si no hay
  `[auth].admin_password` en secrets, el primer login exige definir una nueva
  contraseña antes de entrar).*
- [x] 🟢 **Rate-limit de login** *(hecho: 5 fallos seguidos → bloqueo de 5
  min; contador y bloqueo en la tabla `usuarios`, se resetea al entrar. El
  mensaje de error ya no revela si el usuario existe.)*
- [ ] 🟢 Expiración de sesión por inactividad (timestamp en `session_state`).
- [ ] 🟡 Confirmar y documentar qué datos se envían a Gemini (hoy: resumen de
  QC completo). Añadir un interruptor en Configuración para desactivar el
  asistente o limitar el contexto que se le inyecta.

## 8. Asistente IA

- [ ] 🟡 La detección `necesita_datos_qc` por palabras clave falla con
  preguntas indirectas ("¿todo bien hoy?" no inyecta datos). Alternativas:
  inyectar siempre un resumen compacto (barato con cache del punto 3), o usar
  *function calling* para que el modelo pida los datos que necesite.
- [ ] 🟢 **Streaming de la respuesta** (`st.write_stream`) en vez de spinner
  bloqueante.
- [ ] 🟢 Botones de acción rápida sobre alarmas activas ("Explícame esta
  alarma", "Plan correctivo") que precargan el prompt.

---

## Orden sugerido de ataque

1. **Tests de `qc_rules` + `normalizar_df`** (§6) — desbloquea todo lo demás.
2. **Evaluación única cacheada** (§3) — mejora inmediata y simplifica `app.py`.
3. **Persistencia en SQLite de mediciones + carga protagonista con validación
   visible** (§1) — la mejora de mayor valor para el usuario real.
4. **Clave estable del Registro + password admin + rate-limit** (§5, §7) —
   correcciones pequeñas pero importantes.
5. **Páginas en vez de tabs + limpieza de la quick-bar + tablas nativas** (§4).
6. El resto según necesidad.
