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
  --ink:#16202E; --text:#1C2B3A; --muted:#64748B; --faint:#94A3B8;
  --bg:#F6F8FB; --surface:#FFFFFF; --line:#E7ECF2; --line-soft:#F1F5F9;
  --amber:#F59E0B; --red:#E53E3E;
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
#MainMenu,footer,header,[data-testid="stToolbar"],[data-testid="stDecoration"]{display:none!important;}
[data-testid="stAppViewBlockContainer"]{padding-top:2.4rem;}
h1,h2,h3,h4{color:var(--ink);letter-spacing:-.01em;}

/* ── Sidebar ──────────────────────────────────────────── */
[data-testid="stSidebar"]{
  background:linear-gradient(180deg,#1F3048 0%,#141E2C 100%)!important;
  border-right:none!important;box-shadow:6px 0 30px rgba(8,15,26,.22);}
[data-testid="stSidebar"] *{color:#CBD5E1!important;}
[data-testid="stSidebar"] strong,[data-testid="stSidebar"] b{color:#EEF2F7!important;}
[data-testid="stSidebar"] hr{border-color:rgba(255,255,255,.09)!important;margin:14px 0!important;}
[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"]{
  background:rgba(255,255,255,.04)!important;
  border:1.5px dashed rgba(255,255,255,.20)!important;border-radius:var(--radius-sm)!important;}
[data-testid="stSidebar"] [data-baseweb="select"]>div,
[data-testid="stSidebar"] [data-testid="stDateInput"] input{
  background:rgba(255,255,255,.07)!important;border:1px solid rgba(255,255,255,.14)!important;
  border-radius:var(--radius-sm)!important;color:#EEF2F7!important;}
[data-testid="stSidebar"] [data-baseweb="tab-list"]{
  background:rgba(255,255,255,.05)!important;border:none!important;}

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
.kpi-sub{font-size:.76rem;color:#AEB8C6;margin-top:3px;}

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
.aiqc-header{background:linear-gradient(120deg,var(--brand) 0%,var(--teal) 100%);
  border-radius:18px;padding:22px 28px;margin-bottom:14px;
  box-shadow:0 8px 26px rgba(26,111,196,.24);position:relative;overflow:hidden;}
.aiqc-header::after{content:"";position:absolute;top:-40%;right:-6%;width:230px;height:230px;
  background:radial-gradient(circle,rgba(255,255,255,.16),transparent 70%);border-radius:50%;}
.aiqc-header h2{color:#FFFFFF!important;margin:0 0 4px;font-size:1.5rem;font-weight:800;}
.aiqc-header .meta{color:rgba(255,255,255,.85);font-size:.875rem;}

/* ── Barra de contexto ────────────────────────────────── */
.quick-bar{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius);
  padding:10px 18px;margin-bottom:18px;box-shadow:var(--shadow-sm);}

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

/* ── Encabezado de sección ────────────────────────────── */
.sec-head{font-size:.95rem;font-weight:700;color:var(--brand);
  border-left:3px solid var(--teal);padding-left:11px;margin:26px 0 14px;}

/* ── Login ────────────────────────────────────────────── */
.login-card{background:var(--surface);border:1px solid var(--line);border-radius:22px;
  padding:52px 48px 40px;max-width:430px;margin:56px auto 0;box-shadow:var(--shadow-lg);}

/* ── Banner Gemini ────────────────────────────────────── */
.gemini-banner{background:linear-gradient(135deg,#EFF6FF 0%,#ECFDF5 100%);
  border:1px solid #C7DEFB;border-radius:var(--radius-sm);padding:11px 16px;
  font-size:12.5px;color:#1E40AF;margin-bottom:14px;}

/* ── Tarjetas Bio-Rad ─────────────────────────────────── */
.biorad-card,.biorad-card-red,.biorad-card-amber{
  background:var(--surface);border:1px solid var(--line);border-left:4px solid var(--brand);
  border-radius:var(--radius);padding:18px 20px;margin-bottom:12px;box-shadow:var(--shadow-sm);}
.biorad-card-red{background:#FFFBFB;border-color:#FBD5D5;border-left-color:var(--red);
  box-shadow:0 2px 14px rgba(229,62,62,.09);}
.biorad-card-amber{background:#FFFDF6;border-color:#FBE7B0;border-left-color:var(--amber);
  box-shadow:0 2px 14px rgba(245,158,11,.09);}

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

/* ── Scrollbar ────────────────────────────────────────── */
::-webkit-scrollbar{width:7px;height:7px;}
::-webkit-scrollbar-track{background:var(--line-soft);}
::-webkit-scrollbar-thumb{background:#CBD5E1;border-radius:4px;}
::-webkit-scrollbar-thumb:hover{background:var(--faint);}
</style>
"""
