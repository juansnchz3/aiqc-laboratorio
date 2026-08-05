# ==============================================================
# AIQC – Hoja de estilos (CSS)
# Paleta y tokens centralizados en :root; el resto usa esas variables.
# Comparte paleta con .streamlit/config.toml y el panel de overview.py.
# ==============================================================

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

:root{
  --brand:#1A6FC4; --brand-dark:#1557A0; --teal:#0D9E6E;
  /* Grises secundarios: ajustados para cumplir AA (4.5:1) sobre --surface y
     sobre --bg. Los valores anteriores (#64748B / #94A3B8) daban 4.49:1 y
     2.54:1 en textos pequeños como .kpi-lbl o .qb-lbl. */
  --ink:#16202E; --text:#1C2B3A; --muted:#52607A; --faint:#65728A;
  --bg:#F6F8FB; --surface:#FFFFFF; --line:#E7ECF2; --line-soft:#F1F5F9;
  --amber:#F59E0B; --red:#E53E3E;
  /* Variantes «tinta» de los colores de estado: los vivos (--red, --amber,
     --teal) valen para bordes y fondos, pero como TEXTO sobre fondos claros
     se quedan en 3-4:1. Estas cumplen AA. */
  --red-ink:#A32020; --amber-ink:#8A5A08; --teal-ink:#076647;
  --radius:14px; --radius-sm:9px;
  --shadow-sm:0 1px 3px rgba(16,32,54,.06),0 1px 2px rgba(16,32,54,.04);
  --shadow-md:0 4px 14px rgba(16,32,54,.08);
  --shadow-lg:0 12px 34px rgba(16,32,54,.13);
}

/* ── Base ─────────────────────────────────────────────── */
html,body,[data-testid="stAppViewContainer"]{
  background-color:var(--bg)!important;color:var(--text);
  font-family:'Inter','Segoe UI',system-ui,sans-serif;
  -webkit-font-smoothing:antialiased;}
/* Ojo: NO ocultar [data-testid="stToolbar"] entero — dentro vive
   stExpandSidebarButton, el botón que reabre la barra lateral colapsada
   (Streamlit ≥1.45). Se ocultan solo el menú ⋮, Deploy y demás acciones. */
#MainMenu,footer,[data-testid="stDecoration"],[data-testid="stStatusWidget"],
[data-testid="stMainMenu"],[data-testid="stAppDeployButton"],
[data-testid="stToolbarActions"]{display:none!important;}
[data-testid="stHeader"]{background:transparent!important;box-shadow:none!important;}
[data-testid="stExpandSidebarButton"]{
  background:linear-gradient(135deg,var(--brand),var(--brand-dark))!important;
  border-radius:10px!important;padding:6px!important;box-shadow:var(--shadow-md)!important;
  transition:transform .15s,box-shadow .15s;}
[data-testid="stExpandSidebarButton"]:hover{transform:scale(1.06);box-shadow:var(--shadow-lg)!important;}
[data-testid="stExpandSidebarButton"] *{color:#FFFFFF!important;fill:#FFFFFF!important;}
[data-testid="stAppViewBlockContainer"]{padding-top:2.4rem;}
h1,h2,h3,h4{color:var(--ink);letter-spacing:-.01em;}

/* ── Sidebar ──────────────────────────────────────────── */
[data-testid="stSidebar"]{
  background:linear-gradient(180deg,#1F3048 0%,#141E2C 100%)!important;
  border-right:none!important;box-shadow:6px 0 30px rgba(8,15,26,.22);}
/* Texto del sidebar. Se acota a los contenedores que llevan texto sobre el
   fondo oscuro. NO usar un comodín `*`: pintaba de gris claro también los
   widgets que Streamlit dibuja con fondo blanco propio (botón «Browse
   files», badges de rol, alertas) y los dejaba ilegibles. */
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"],
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] *,
[data-testid="stSidebar"] [data-testid="stCaptionContainer"],
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] *,
[data-testid="stSidebar"] label,[data-testid="stSidebar"] label *,
[data-testid="stSidebar"] [data-baseweb="tab"] *,
[data-testid="stSidebar"] summary,[data-testid="stSidebar"] summary *{
  color:#CBD5E1!important;}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] strong,
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] b{color:#EEF2F7!important;}
[data-testid="stSidebar"] hr{border-color:rgba(255,255,255,.09)!important;margin:14px 0!important;}
[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"]{
  background:rgba(255,255,255,.04)!important;
  border:1.5px dashed rgba(255,255,255,.20)!important;border-radius:var(--radius-sm)!important;}
/* Instrucciones del dropzone y ficha del archivo subido: Streamlit las pinta
   con el color de texto del tema (oscuro), ilegible sobre el sidebar. */
[data-testid="stSidebar"] [data-testid="stFileUploaderDropzoneInstructions"],
[data-testid="stSidebar"] [data-testid="stFileUploaderDropzoneInstructions"] *,
[data-testid="stSidebar"] [data-testid="stFileUploaderFile"],
[data-testid="stSidebar"] [data-testid="stFileUploaderFile"] *{color:#B7C4D4!important;}
/* El botón «Browse files» lo dibuja Streamlit con fondo blanco propio: sin
   esta regla quedaba texto claro sobre blanco. */
[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] button{
  background:rgba(255,255,255,.10)!important;border:1px solid rgba(255,255,255,.24)!important;
  border-radius:var(--radius-sm)!important;color:#EEF2F7!important;}
[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] button *{color:#EEF2F7!important;}
[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] button:hover{
  background:rgba(255,255,255,.18)!important;border-color:rgba(255,255,255,.38)!important;}
[data-testid="stSidebar"] [data-baseweb="select"]>div,
[data-testid="stSidebar"] [data-testid="stDateInput"] [data-baseweb="input"]{
  background:rgba(255,255,255,.07)!important;border:1px solid rgba(255,255,255,.14)!important;
  border-radius:var(--radius-sm)!important;color:#EEF2F7!important;}
/* En BaseWeb el fondo visible del date input vive en el envoltorio
   [data-baseweb="input"], no en el <input>. Pintando solo el <input> la caja
   se quedaba en el #F6F8FB del tema con texto casi blanco encima (1.06:1). */
[data-testid="stSidebar"] [data-testid="stDateInput"] [data-baseweb="base-input"],
[data-testid="stSidebar"] [data-testid="stDateInput"] input{
  background:transparent!important;border:none!important;
  color:#EEF2F7!important;-webkit-text-fill-color:#EEF2F7!important;}
[data-testid="stSidebar"] [data-baseweb="tab-list"]{
  background:rgba(255,255,255,.05)!important;border:none!important;}
/* Las tabs del área principal usan fondos claros (--line-soft al pasar el
   ratón); sobre el sidebar oscuro dejaban texto claro sobre claro (1.36:1).
   El selector encadena tab-list para superar en especificidad al bloque
   .stTabs, que va después en esta hoja. */
[data-testid="stSidebar"] [data-baseweb="tab-list"] [data-baseweb="tab"]:hover{
  background:rgba(255,255,255,.10)!important;}
[data-testid="stSidebar"] [data-baseweb="tab-list"] [data-baseweb="tab"]:hover *{
  color:#FFFFFF!important;}
[data-testid="stSidebar"] [data-baseweb="tab-list"] [data-baseweb="tab"][aria-selected="true"]{
  background:linear-gradient(135deg,var(--brand),var(--teal))!important;}
[data-testid="stSidebar"] [data-baseweb="tab-list"] [data-baseweb="tab"][aria-selected="true"] *{
  color:#FFFFFF!important;}
/* Botón interno para colapsar la barra (la flecha «) — visible sobre el fondo oscuro */
[data-testid="stSidebarCollapseButton"] button{border-radius:8px!important;}
[data-testid="stSidebarCollapseButton"] button:hover{background:rgba(255,255,255,.10)!important;}
[data-testid="stSidebarCollapseButton"] svg,
[data-testid="stSidebarCollapseButton"] span{color:#CBD5E1!important;}
/* Botones del sidebar: pastillas translúcidas sobre el fondo oscuro.
   El selector repite [kind] para ganar en especificidad al bloque global de
   botones: `.stButton>button[kind="secondary"]` empata a (0,2,1) y, al ir
   después en esta hoja, se imponía y devolvía el fondo blanco.
   El texto vive en un <div> interno, de ahí la regla con `*`. */
[data-testid="stSidebar"] .stButton>button,
[data-testid="stSidebar"] .stButton>button[kind="secondary"]{
  background:rgba(255,255,255,.06)!important;border:1px solid rgba(255,255,255,.16)!important;
  color:#D3DCE7!important;box-shadow:none!important;}
[data-testid="stSidebar"] .stButton>button[kind="secondary"] *{color:#D3DCE7!important;}
[data-testid="stSidebar"] .stButton>button:hover,
[data-testid="stSidebar"] .stButton>button[kind="secondary"]:hover{
  background:rgba(255,255,255,.12)!important;border-color:rgba(255,255,255,.32)!important;
  transform:none!important;}
[data-testid="stSidebar"] .stButton>button[kind="secondary"]:hover *{color:#FFFFFF!important;}
[data-testid="stSidebar"] .stButton>button[kind="primary"]{
  background:linear-gradient(135deg,var(--brand),var(--teal))!important;border:none!important;
  color:#FFFFFF!important;box-shadow:0 2px 10px rgba(13,158,110,.30)!important;}
[data-testid="stSidebar"] .stButton>button[kind="primary"] *{color:#FFFFFF!important;}
/* Expander del sidebar (p. ej. «Datos guardados»): versión oscura, no la blanca global */
[data-testid="stSidebar"] [data-testid="stExpander"]{
  background:rgba(255,255,255,.04)!important;border:1px solid rgba(255,255,255,.13)!important;
  box-shadow:none!important;}
/* Títulos de sección y chip de usuario del sidebar */
.sb-sec{font-size:.68rem;font-weight:800;letter-spacing:.13em;text-transform:uppercase;
  color:#7E93AC!important;margin:4px 2px 6px;}
.sb-user{display:flex;align-items:center;justify-content:center;gap:8px;
  background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.10);
  border-radius:999px;padding:6px 14px;margin:0 10px 12px;font-size:.78rem;}
/* Badge de rol del sidebar: variante oscura. Los .role-* de la tabla de
   Usuarios son fondos claros y aquí quedaban ilegibles (1.36:1). */
[data-testid="stSidebar"] .sb-user .sb-role{
  border-radius:6px;padding:2px 9px;font-size:.66rem;font-weight:800;letter-spacing:.05em;}
[data-testid="stSidebar"] .sb-user .sb-role.rol-admin{
  background:rgba(96,165,250,.22)!important;border:1px solid rgba(96,165,250,.45)!important;
  color:#DBEAFE!important;}
[data-testid="stSidebar"] .sb-user .sb-role.rol-supervisor{
  background:rgba(52,211,153,.20)!important;border:1px solid rgba(52,211,153,.42)!important;
  color:#D1FAE5!important;}
[data-testid="stSidebar"] .sb-user .sb-role.rol-tecnico{
  background:rgba(245,158,11,.20)!important;border:1px solid rgba(245,158,11,.42)!important;
  color:#FEF3C7!important;}

/* ── Navegación del sidebar (st.navigation) ───────────── */
[data-testid="stSidebarNav"]{padding:.35rem .25rem .1rem;}
[data-testid="stSidebarNav"] ul{gap:2px!important;}
[data-testid="stSidebarNav"] a{
  border-radius:9px!important;margin:1px 8px!important;padding:8px 12px!important;
  transition:background .15s,box-shadow .15s;}
[data-testid="stSidebarNav"] a:hover{background:rgba(255,255,255,.07)!important;}
[data-testid="stSidebarNav"] a span{color:#D3DCE7!important;font-weight:600!important;}
[data-testid="stSidebarNav"] a[aria-current="page"]{
  background:linear-gradient(135deg,rgba(96,165,250,.26),rgba(52,211,153,.18))!important;
  box-shadow:inset 3px 0 0 #60A5FA;}
[data-testid="stSidebarNav"] a[aria-current="page"] span{color:#FFFFFF!important;font-weight:700!important;}

/* ── Inputs (área principal) ──────────────────────────── */
[data-baseweb="select"]>div,[data-testid="stTextInput"] input,[data-testid="stDateInput"] input,
[data-testid="stNumberInput"] input{
  background-color:var(--surface)!important;border:1.5px solid var(--line)!important;
  border-radius:var(--radius-sm)!important;color:var(--text)!important;
  transition:border-color .15s,box-shadow .15s;}
[data-testid="stTextInput"] input:focus,[data-testid="stNumberInput"] input:focus{
  border-color:var(--brand)!important;box-shadow:0 0 0 3px rgba(26,111,196,.12)!important;}

/* ── Botones ──────────────────────────────────────────── */
.stButton>button{border-radius:var(--radius-sm)!important;font-weight:600!important;
  transition:transform .12s,box-shadow .18s,background .18s!important;}
.stButton>button[kind="primary"]{
  background:linear-gradient(135deg,var(--brand) 0%,var(--brand-dark) 100%)!important;
  border:none!important;color:#FFFFFF!important;box-shadow:0 2px 10px rgba(26,111,196,.28)!important;}
.stButton>button[kind="primary"]:hover{
  box-shadow:0 5px 18px rgba(26,111,196,.36)!important;transform:translateY(-1px)!important;}
.stButton>button[kind="secondary"]{
  background-color:var(--surface)!important;border:1.5px solid var(--line)!important;
  color:var(--brand)!important;}
.stButton>button[kind="secondary"]:hover{border-color:var(--brand)!important;background:#F8FAFF!important;}

/* ── Tabs (residual — la nav principal pasa a páginas) ── */
.stTabs [data-baseweb="tab-list"]{gap:5px;background:var(--surface);border:1px solid var(--line);
  border-radius:var(--radius);padding:5px 6px;box-shadow:var(--shadow-sm);}
.stTabs [data-baseweb="tab"]{background:transparent!important;border:none!important;
  border-radius:var(--radius-sm)!important;color:var(--muted)!important;font-weight:500!important;
  font-size:.875rem!important;padding:8px 18px!important;transition:all .16s!important;}
.stTabs [data-baseweb="tab"]:hover{background:var(--line-soft)!important;color:var(--brand)!important;}
.stTabs [aria-selected="true"]{background:linear-gradient(135deg,var(--brand) 0%,var(--teal) 100%)!important;
  color:#FFFFFF!important;font-weight:700!important;box-shadow:0 2px 8px rgba(26,111,196,.26)!important;}

/* ── KPI cards ────────────────────────────────────────── */
.kpi-card{background:var(--surface);border:1px solid var(--line);border-top:3px solid var(--brand);
  border-radius:var(--radius);padding:22px 20px 18px;text-align:center;
  box-shadow:var(--shadow-sm);transition:box-shadow .22s,transform .22s;}
.kpi-card:hover{box-shadow:var(--shadow-lg);transform:translateY(-3px);}
.kpi-card.estado-verde{border-top-color:var(--teal);}
.kpi-card.estado-ambar{border-top-color:var(--amber);}
.kpi-card.estado-rojo{border-top-color:var(--red);}
.kpi-val{font-size:2.05rem;font-weight:800;letter-spacing:-.02em;line-height:1.1;}
.kpi-lbl{font-size:.68rem;font-weight:700;color:var(--faint);text-transform:uppercase;
  letter-spacing:.1em;margin-top:8px;}
.kpi-sub{font-size:.76rem;color:var(--faint);margin-top:3px;}

/* ── Panel semáforo (overview.py, nativo) ─────────────── */
.ov-wrap{margin-bottom:4px;}
.ov-head{display:flex;align-items:center;gap:14px;flex-wrap:wrap;margin-bottom:14px;}
.ov-title{font-weight:800;font-size:1.08rem;color:var(--ink);}
.ov-chips{display:flex;gap:8px;flex-wrap:wrap;}
.ov-chip{display:inline-flex;align-items:center;gap:5px;padding:3px 11px;border-radius:999px;
  font-size:.78rem;font-weight:700;}
.ov-chip-rojo{background:rgba(229,62,62,.12);color:var(--red-ink);}
.ov-chip-ambar{background:rgba(245,158,11,.15);color:var(--amber-ink);}
.ov-chip-verde{background:rgba(13,158,110,.13);color:var(--teal-ink);}
.ov-grid{display:grid;gap:12px;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));}
.ov-card{background:var(--surface);border:1px solid var(--line);border-top:3px solid var(--brand);
  border-radius:var(--radius);padding:13px 15px;box-shadow:var(--shadow-sm);
  transition:box-shadow .2s,transform .2s;}
.ov-card:hover{box-shadow:var(--shadow-md);transform:translateY(-2px);}
.ov-card-head{display:flex;align-items:center;justify-content:space-between;gap:8px;
  margin-bottom:10px;flex-wrap:wrap;}
.ov-name{font-weight:700;font-size:.95rem;color:var(--ink);}
.ov-r4s{font-size:.68rem;font-weight:700;color:var(--red-ink);background:rgba(229,62,62,.1);
  padding:2px 7px;border-radius:6px;}
.ov-cells{display:flex;gap:8px;flex-wrap:wrap;}
.ov-cell{flex:1 1 76px;min-width:76px;background:var(--bg);border:1px solid var(--line-soft);
  border-left:4px solid var(--teal);border-radius:8px;padding:7px 9px;}
.ov-cell-top{display:flex;align-items:flex-start;gap:5px;min-height:26px;font-size:.72rem;}
.ov-cell-lbl{color:var(--muted);font-weight:600;}
.ov-cell-val{font-size:1.15rem;font-weight:800;color:var(--ink);margin-top:2px;line-height:1.1;}
.ov-cell-meta{font-size:.66rem;color:var(--faint);margin-top:2px;}
.ov-empty{color:var(--muted);padding:22px;text-align:center;background:var(--surface);
  border:1px dashed var(--line);border-radius:var(--radius);}

/* ── Badges de estado ─────────────────────────────────── */
.badge{display:inline-flex;align-items:center;gap:6px;padding:5px 14px;border-radius:999px;
  font-size:.78rem;font-weight:700;box-shadow:var(--shadow-sm);}
.badge-green{background:linear-gradient(135deg,#D1FAE5,#A7F3D0);color:#065F46;border:1px solid #6EE7B7;}
.badge-amber{background:linear-gradient(135deg,#FEF3C7,#FDE68A);color:#92400E;border:1px solid #FCD34D;}
.badge-red{background:linear-gradient(135deg,#FEE2E2,#FECACA);color:#991B1B;border:1px solid #FCA5A5;}

/* ── Pills de nivel ───────────────────────────────────── */
.nivel-pill{display:inline-block;padding:4px 13px;border-radius:999px;font-size:.76rem;font-weight:700;}
.nivel-N{background:#EFF6FF;color:#1D4ED8;border:1px solid #BFDBFE;}
.nivel-PB{background:#FFFBEB;color:#92400E;border:1px solid #FDE68A;}
.nivel-PA{background:#FFF1F2;color:#9F1239;border:1px solid #FECDD3;}

/* ── Cabecera principal ───────────────────────────────── */
.aiqc-header{background:linear-gradient(120deg,var(--brand-dark) 0%,var(--brand) 46%,var(--teal) 100%);
  border-radius:18px;padding:22px 28px;margin-bottom:14px;
  box-shadow:0 8px 26px rgba(26,111,196,.24);position:relative;overflow:hidden;}
.aiqc-header::after{content:"";position:absolute;top:-40%;right:-6%;width:230px;height:230px;
  background:radial-gradient(circle,rgba(255,255,255,.16),transparent 70%);border-radius:50%;}
.aiqc-header::before{content:"";position:absolute;bottom:-55%;left:22%;width:190px;height:190px;
  background:radial-gradient(circle,rgba(255,255,255,.10),transparent 70%);border-radius:50%;}
.aiqc-header h2{color:#FFFFFF!important;margin:0 0 8px;font-size:1.5rem;font-weight:800;}
.aiqc-header .meta{display:flex;gap:8px;flex-wrap:wrap;}
.hd-chip{display:inline-flex;align-items:center;gap:6px;background:rgba(255,255,255,.14);
  border:1px solid rgba(255,255,255,.24);border-radius:999px;padding:3px 12px;
  font-size:.76rem;font-weight:600;color:#FFFFFF;backdrop-filter:blur(3px);}
.hd-chip b{font-weight:800;}

/* ── Barra de contexto ────────────────────────────────── */
.quick-bar{display:flex;align-items:stretch;flex-wrap:wrap;background:var(--surface);
  border:1px solid var(--line);border-radius:var(--radius);padding:0;
  margin-bottom:18px;box-shadow:var(--shadow-sm);overflow:hidden;}
.qb-item{display:flex;flex-direction:column;justify-content:center;gap:2px;
  padding:9px 20px;border-right:1px solid var(--line-soft);}
.qb-item:last-child{border-right:none;}
.qb-lbl{font-size:.62rem;font-weight:800;letter-spacing:.11em;text-transform:uppercase;
  color:var(--faint);}
.qb-val{display:flex;align-items:center;gap:7px;font-size:.9rem;font-weight:700;color:var(--ink);}

/* ── Sidebar branding ─────────────────────────────────── */
.sb-logo{text-align:center;font-size:2.7rem;margin-bottom:2px;
  filter:drop-shadow(0 3px 8px rgba(0,0,0,.28));}
.sb-title{text-align:center;font-size:1.35rem;font-weight:800;letter-spacing:.04em;
  background:linear-gradient(120deg,#60A5FA,#34D399);-webkit-background-clip:text;
  background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:2px;}
.sb-sub{text-align:center;font-size:.72rem;color:#8CA0B8!important;margin-bottom:16px;}
.data-pill{background:rgba(96,165,250,.13);border:1px solid rgba(96,165,250,.30);
  border-radius:var(--radius-sm);padding:10px 14px;font-size:.82rem;color:#BFDBFE!important;margin-top:8px;}
.sync-pill{background:rgba(13,158,110,.13);border:1px solid rgba(13,158,110,.32);
  border-radius:var(--radius-sm);padding:10px 14px;font-size:.82rem;color:#6EE7B7!important;margin-top:8px;}

/* ── Encabezado de página ─────────────────────────────── */
/* Cada página fija su color con --ph-accent (inline); por defecto, brand. */
.page-head{position:relative;display:flex;align-items:center;gap:14px;margin:2px 0 20px;
  padding-bottom:14px;border-bottom:1px solid var(--line);}
.page-head::after{content:"";position:absolute;left:0;bottom:-2px;width:64px;height:3px;
  border-radius:3px;background:var(--ph-accent,var(--brand));}
.page-head .ph-icon{font-size:1.7rem;line-height:1;
  background:linear-gradient(135deg,#EFF6FF,#ECFDF5);border:1px solid var(--line);
  border-radius:12px;width:48px;height:48px;display:flex;align-items:center;justify-content:center;
  box-shadow:var(--shadow-sm);flex-shrink:0;}
.page-head .ph-txt h3{margin:0;font-size:1.32rem;font-weight:800;color:var(--ink);letter-spacing:-.01em;}
.page-head .ph-txt p{margin:2px 0 0;font-size:.86rem;color:var(--muted);}

/* ── Encabezado de sección (letrero tipo «eyebrow») ───── */
.sec-head{display:flex;align-items:center;gap:10px;font-size:.8rem;font-weight:800;
  letter-spacing:.09em;text-transform:uppercase;color:var(--ink);margin:28px 0 14px;}
.sec-head::before{content:"";width:9px;height:9px;border-radius:3px;flex-shrink:0;
  background:linear-gradient(135deg,var(--brand),var(--teal));}
.sec-head::after{content:"";flex:1;height:2px;border-radius:2px;
  background:linear-gradient(90deg,var(--line),transparent);}

/* ── Login ────────────────────────────────────────────── */
.login-card{background:var(--surface);border:1px solid var(--line);border-radius:22px;
  padding:52px 48px 40px;max-width:430px;margin:56px auto 0;box-shadow:var(--shadow-lg);}

/* ── Banners informativos ─────────────────────────────── */
.gemini-banner{background:linear-gradient(135deg,#EFF6FF 0%,#ECFDF5 100%);
  border:1px solid #C7DEFB;border-left:4px solid var(--brand);
  border-radius:var(--radius-sm);padding:11px 16px;
  font-size:12.5px;color:#1E40AF;margin-bottom:14px;}
.demo-banner{display:flex;align-items:center;gap:14px;
  background:linear-gradient(135deg,#EFF6FF,#ECFDF5);
  border:1px solid #BFDBFE;border-left:4px solid var(--brand);
  border-radius:var(--radius);padding:14px 20px;margin-bottom:20px;box-shadow:var(--shadow-sm);}
.demo-banner .db-icon{font-size:1.9rem;line-height:1;}
.demo-banner .db-title{font-weight:800;color:var(--brand);font-size:.93rem;}
.demo-banner .db-text{color:#475569;font-size:.83rem;margin-top:2px;}

/* ── Cobertura KB (chips por grupo analítico) ─────────── */
.kb-group{display:flex;align-items:baseline;gap:8px 10px;flex-wrap:wrap;margin-bottom:10px;}
.kb-group-name{font-size:.72rem;font-weight:800;letter-spacing:.07em;text-transform:uppercase;
  color:var(--muted);margin-right:2px;}
.kb-chip{display:inline-block;background:#EFF6FF;border:1px solid #BFDBFE;color:#1D4ED8;
  border-radius:999px;padding:3px 12px;font-size:.76rem;font-weight:600;}

/* ── Tarjetas Bio-Rad ─────────────────────────────────── */
.biorad-card,.biorad-card-red,.biorad-card-amber{
  background:var(--surface);border:1px solid var(--line);border-left:4px solid var(--brand);
  border-radius:var(--radius);padding:18px 20px;margin-bottom:12px;box-shadow:var(--shadow-sm);}
.biorad-card-red{background:#FFFBFB;border-color:#FBD5D5;border-left-color:var(--red);
  box-shadow:0 2px 14px rgba(229,62,62,.09);}
.biorad-card-amber{background:#FFFDF6;border-color:#FBE7B0;border-left-color:var(--amber);
  box-shadow:0 2px 14px rgba(245,158,11,.09);}
/* Contenido interno de la ficha. La tarjeta se emite como un único bloque
   HTML: repartir el <div> entre varios st.markdown no funciona (cada uno va
   a su propio contenedor y Streamlit cierra las etiquetas sueltas). */
.kb-head{font-size:1.02rem;font-weight:800;color:var(--ink);margin:0 0 3px;line-height:1.4;}
.kb-head code{background:var(--line-soft);border-radius:5px;padding:1px 7px;
  font-size:.85em;color:var(--brand-dark);}
.kb-meta{font-size:.79rem;color:var(--muted);font-style:italic;margin-bottom:13px;}
.kb-cols{display:grid;gap:2px 28px;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));}
.kb-lbl{font-size:.71rem;font-weight:800;letter-spacing:.07em;text-transform:uppercase;
  color:var(--muted);margin:2px 0 6px;}
.kb-cols ul{margin:0 0 12px;padding-left:19px;}
.kb-cols li{font-size:.86rem;color:var(--text);margin-bottom:4px;line-height:1.5;}
.kb-foot{margin-top:6px;padding-top:11px;border-top:1px solid var(--line);
  font-size:.79rem;color:var(--muted);line-height:1.75;}
.kb-foot b{color:var(--text);}

/* ── Filas de auditoría / usuarios ────────────────────── */
.audit-row{background:#FBFCFE;border:1px solid var(--line);border-radius:var(--radius-sm);
  padding:9px 14px;margin-bottom:6px;font-size:.82rem;transition:background .14s;}
.audit-row:hover{background:#F4F8FD;}
.role-admin,.role-supervisor,.role-tecnico{border-radius:6px;padding:2px 8px;
  font-size:.72rem;font-weight:700;}
.role-admin{background:#EFF6FF;color:#1D4ED8;border:1px solid #BFDBFE;}
.role-supervisor{background:#F0FDF4;color:#166534;border:1px solid #BBF7D0;}
.role-tecnico{background:#FFFBEB;color:#92400E;border:1px solid #FDE68A;}

/* ── Tablas HTML (residual — migrando a st.dataframe) ─── */
table{width:100%;border-collapse:collapse;font-size:.86rem;}
thead tr{background:var(--line-soft);}
th{padding:11px 13px;text-align:left;font-weight:700;color:var(--muted);
  border-bottom:2px solid var(--line);text-transform:uppercase;font-size:.72rem;letter-spacing:.06em;}
td{padding:10px 13px;border-bottom:1px solid var(--line-soft);color:var(--text);}
tr:hover td{background:#FBFCFE;}

/* ── Componentes Streamlit ────────────────────────────── */
[data-testid="stForm"]{background:var(--surface);border:1px solid var(--line)!important;
  border-radius:var(--radius)!important;padding:20px 22px!important;box-shadow:var(--shadow-sm);}
[data-testid="stSidebar"] [data-testid="stForm"]{background:rgba(255,255,255,.04);
  border-color:rgba(255,255,255,.13)!important;box-shadow:none;}
[data-testid="stAlert"]{border-radius:var(--radius-sm)!important;}
/* El texto de las alertas nativas se queda en 4.2-4.5:1 con la paleta de
   Streamlit; se fuerza a las variantes «tinta» para cumplir AA. */
[data-testid="stAlertContentSuccess"],[data-testid="stAlertContentSuccess"] *{
  color:var(--teal-ink)!important;}
[data-testid="stAlertContentWarning"],[data-testid="stAlertContentWarning"] *{
  color:var(--amber-ink)!important;}
[data-testid="stAlertContentError"],[data-testid="stAlertContentError"] *{
  color:var(--red-ink)!important;}
[data-testid="stAlertContentInfo"],[data-testid="stAlertContentInfo"] *{
  color:#134E9B!important;}
[data-testid="stChatMessage"]{background:var(--surface)!important;border:1px solid var(--line)!important;
  border-radius:var(--radius)!important;box-shadow:var(--shadow-sm)!important;}
[data-testid="stMetric"]{background:var(--surface);border:1px solid var(--line);
  border-radius:var(--radius);padding:16px 16px;box-shadow:var(--shadow-sm);
  transition:box-shadow .2s;}
[data-testid="stMetric"]:hover{box-shadow:var(--shadow-md);}
[data-testid="stExpander"]{background:var(--surface)!important;border:1px solid var(--line)!important;
  border-radius:var(--radius-sm)!important;box-shadow:var(--shadow-sm);}
[data-testid="stDataFrame"]{border-radius:var(--radius-sm);overflow:hidden;
  border:1px solid var(--line);box-shadow:var(--shadow-sm);}

/* ── Literales de Streamlit en español ────────────────── */
/* Streamlit no tiene i18n: los textos del uploader vienen fijos en inglés.
   Se ocultan con font-size:0 y se reponen desde ::after. Se apoya en los
   data-testid (estables) y en la posición dentro del contenedor, no en las
   clases emotion, que cambian entre versiones.
   OJO: «25 MB» debe cuadrar con maxUploadSize de .streamlit/config.toml. */
[data-testid="stFileUploaderDropzoneInstructions"]>div>span{font-size:0!important;}
[data-testid="stFileUploaderDropzoneInstructions"]>div>span:nth-of-type(1)::after{
  content:"Arrastra aquí el archivo";font-size:.86rem;font-weight:600;}
[data-testid="stFileUploaderDropzoneInstructions"]>div>span:nth-of-type(2)::after{
  content:"Máx. 25 MB · CSV, XLSX o XLS";font-size:.74rem;}
[data-testid="stFileUploaderDropzone"] button,
[data-testid="stFileUploaderDropzone"] button *{font-size:0!important;}
[data-testid="stFileUploaderDropzone"] button::after{
  content:"Examinar";font-size:.85rem;font-weight:600;}

/* ── Scrollbar ────────────────────────────────────────── */
::-webkit-scrollbar{width:7px;height:7px;}
::-webkit-scrollbar-track{background:var(--line-soft);}
::-webkit-scrollbar-thumb{background:#CBD5E1;border-radius:4px;}
::-webkit-scrollbar-thumb:hover{background:var(--faint);}
</style>
"""
