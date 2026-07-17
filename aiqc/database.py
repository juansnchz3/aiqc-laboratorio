# ==============================================================
# AIQC – Base de datos (SQLite)
#   · usuarios, acciones (trazabilidad), auditoría
#   · login con bcrypt, control de permisos por rol
# ==============================================================
import logging
import os
import sqlite3
from datetime import datetime, timedelta

import bcrypt
import streamlit as st

from .config import get_section

logger = logging.getLogger("AIQC")

# Rate-limit de login: tras MAX_INTENTOS fallidos seguidos, la cuenta se
# bloquea BLOQUEO_MINUTOS. El contador se resetea con un login correcto.
MAX_INTENTOS = 5
BLOQUEO_MINUTOS = 5


# ==============================================================
# RUTA DE LA BASE DE DATOS
# ==============================================================
# Raíz del proyecto (carpeta que contiene el paquete aiqc/).
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_db_path():
    # Ruta explícita en secrets ([db].path) si se define; si no, ~/.aiqc/.
    # Las rutas relativas se anclan a la raíz del proyecto (no al cwd), de modo
    # que la BD queda siempre en el mismo sitio sin importar desde dónde se lance.
    custom = (get_section("db").get("path", "") or "").strip()
    if custom:
        custom = os.path.expanduser(custom)
        db_path = custom if os.path.isabs(custom) else os.path.join(_PROJECT_ROOT, custom)
    else:
        db_path = os.path.join(os.path.expanduser("~"), ".aiqc", "aiqc_acciones.db")
    db_path = os.path.abspath(db_path)
    # Garantiza que el directorio contenedor existe (multiplataforma).
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    return db_path


DB_PATH = get_db_path()


# ==============================================================
# INICIALIZACIÓN
# ==============================================================
def init_db():
    con = sqlite3.connect(DB_PATH, check_same_thread=False)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute(
        """CREATE TABLE IF NOT EXISTS acciones (
        clave TEXT PRIMARY KEY, hecha INTEGER DEFAULT 0,
        ts TEXT, usuario TEXT DEFAULT 'sistema')"""
    )
    con.execute(
        """CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL,
        rol TEXT NOT NULL DEFAULT 'tecnico', nombre TEXT DEFAULT '',
        activo INTEGER DEFAULT 1, creado_en TEXT DEFAULT (datetime('now')),
        ultimo_acceso TEXT)"""
    )
    con.execute(
        """CREATE TABLE IF NOT EXISTS auditoria (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts TEXT DEFAULT (datetime('now')),
        usuario TEXT NOT NULL, accion TEXT NOT NULL, detalle TEXT DEFAULT '')"""
    )
    # Mediciones QC persistidas. La clave natural (fecha, analito, nivel, fuente)
    # evita duplicados al recargar el mismo archivo: un INSERT OR REPLACE
    # actualiza la fila en vez de añadir otra igual.
    con.execute(
        """CREATE TABLE IF NOT EXISTS mediciones (
        fecha TEXT NOT NULL, analito TEXT NOT NULL, nivel TEXT NOT NULL DEFAULT 'N',
        valor REAL NOT NULL, media_objetivo REAL NOT NULL, sd_objetivo REAL NOT NULL,
        lote TEXT DEFAULT 'N/A', fuente TEXT NOT NULL DEFAULT 'manual',
        cargado_por TEXT DEFAULT 'sistema', cargado_en TEXT DEFAULT (datetime('now')),
        PRIMARY KEY (fecha, analito, nivel, fuente))"""
    )
    con.commit()
    _migrar_usuarios(con)
    _seed_admin(con)
    return con


def _migrar_usuarios(con):
    # Columnas añadidas después de la v4.13; ALTER falla sin más si ya existen.
    for columna in (
        "debe_cambiar_pwd INTEGER DEFAULT 0",
        "intentos_fallidos INTEGER DEFAULT 0",
        "bloqueado_hasta TEXT",
    ):
        try:
            con.execute(f"ALTER TABLE usuarios ADD COLUMN {columna}")
        except sqlite3.OperationalError:
            pass
    con.commit()


def _seed_admin(con):
    if con.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0] == 0:
        pwd_default = get_section("auth").get("admin_password", "")
        # Sin contraseña definida en secrets se usa la de fábrica, pero se
        # obliga a cambiarla en el primer inicio de sesión.
        forzar_cambio = 0
        if not pwd_default:
            pwd_default = "admin2024"
            forzar_cambio = 1
        pwd_hash = bcrypt.hashpw(pwd_default.encode(), bcrypt.gensalt()).decode()
        con.execute(
            "INSERT INTO usuarios (username,password_hash,rol,nombre,debe_cambiar_pwd) "
            "VALUES (?,?,'admin','Administrador',?)",
            ("admin", pwd_hash, forzar_cambio),
        )
        con.commit()


# ==============================================================
# PASSWORD / LOGIN
# ==============================================================
def verificar_password(password, password_hash):
    try:
        return bcrypt.checkpw(password.encode(), password_hash.encode())
    except Exception:
        return False


def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def login_usuario(con, username, password):
    """Devuelve (usuario | None, motivo). El motivo es genérico de cara al usuario
    cuando la causa es credencial incorrecta (no revela si el usuario existe)."""
    motivo_generico = "Credenciales incorrectas o usuario desactivado."
    row = con.execute(
        "SELECT id,username,password_hash,rol,nombre,activo,debe_cambiar_pwd,"
        "intentos_fallidos,bloqueado_hasta FROM usuarios WHERE username=?",
        (username,),
    ).fetchone()
    if row is None:
        registrar_auditoria(con, username, "LOGIN_FALLIDO", "Usuario no existe")
        return None, motivo_generico
    id_, uname, pwd_hash, rol, nombre, activo, debe_cambiar, intentos, bloqueado_hasta = row
    if bloqueado_hasta:
        try:
            hasta = datetime.fromisoformat(bloqueado_hasta)
        except ValueError:
            hasta = None
        if hasta and datetime.now() < hasta:
            registrar_auditoria(con, username, "LOGIN_BLOQUEADO", f"Hasta {bloqueado_hasta}")
            return None, f"Cuenta bloqueada por intentos fallidos. Prueba a las {hasta:%H:%M}."
    if not activo:
        registrar_auditoria(con, username, "LOGIN_DENEGADO", "Usuario desactivado")
        return None, motivo_generico
    if not verificar_password(password, pwd_hash):
        intentos = (intentos or 0) + 1
        if intentos >= MAX_INTENTOS:
            hasta = (datetime.now() + timedelta(minutes=BLOQUEO_MINUTOS)).isoformat()
            con.execute(
                "UPDATE usuarios SET intentos_fallidos=0, bloqueado_hasta=? WHERE id=?",
                (hasta, id_),
            )
            registrar_auditoria(con, username, "LOGIN_BLOQUEO_ACTIVADO", f"{MAX_INTENTOS} fallos")
        else:
            con.execute("UPDATE usuarios SET intentos_fallidos=? WHERE id=?", (intentos, id_))
            registrar_auditoria(con, username, "LOGIN_FALLIDO", "Contraseña incorrecta")
        con.commit()
        return None, motivo_generico
    con.execute(
        "UPDATE usuarios SET ultimo_acceso=datetime('now'), intentos_fallidos=0, "
        "bloqueado_hasta=NULL WHERE id=?",
        (id_,),
    )
    con.commit()
    registrar_auditoria(con, username, "LOGIN_OK", f"Rol: {rol}")
    return {
        "id": id_,
        "username": uname,
        "rol": rol,
        "nombre": nombre,
        "debe_cambiar_pwd": bool(debe_cambiar),
    }, ""


# ==============================================================
# AUDITORÍA / PERMISOS
# ==============================================================
def registrar_auditoria(con, usuario, accion, detalle=""):
    try:
        con.execute(
            "INSERT INTO auditoria (usuario,accion,detalle) VALUES (?,?,?)",
            (usuario, accion, detalle),
        )
        con.commit()
    except Exception:
        # No interrumpe la app, pero un fallo de auditoría debe quedar registrado.
        logger.exception("Fallo al registrar auditoría: %s %s", usuario, accion)


def tiene_permiso(rol_usuario, rol_requerido):
    jerarquia = {"admin": 3, "supervisor": 2, "tecnico": 1}
    return jerarquia.get(rol_usuario, 0) >= jerarquia.get(rol_requerido, 99)


# ==============================================================
# ACCIONES (trazabilidad de incidencias)
# ==============================================================
def load_acciones(con):
    return {r[0]: bool(r[1]) for r in con.execute("SELECT clave,hecha FROM acciones").fetchall()}


def save_accion(con, clave, hecha, usuario="sistema"):
    con.execute(
        "INSERT OR REPLACE INTO acciones VALUES (?,?,datetime('now'),?)",
        (clave, int(hecha), usuario),
    )
    con.commit()
    registrar_auditoria(con, usuario, f"ACCION_{'COMPLETADA' if hecha else 'PENDIENTE'}", clave)


# ==============================================================
# LOGIN UI
# ==============================================================
def render_login(con):
    st.markdown(
        """<div class="login-card">
    <div style="font-size:3rem;text-align:center">🔬</div>
    <div style="text-align:center;font-size:1.8rem;font-weight:800;color:#1A6FC4;margin-bottom:4px">AIQC</div>
    <div style="text-align:center;font-size:.86rem;color:#64748B;margin-bottom:28px">
    Artificial Intelligence for Quality Control · v4.13</div></div>""",
        unsafe_allow_html=True,
    )
    _, mid, _ = st.columns([1, 1.8, 1])
    with mid:
        pendiente = st.session_state.get("pwd_change_user")
        if pendiente:
            _render_cambio_pwd_obligatorio(con, pendiente)
            return
        st.markdown("<br>", unsafe_allow_html=True)
        # st.form permite enviar con Enter desde cualquier campo.
        with st.form("form_login"):
            username = st.text_input("Usuario", placeholder="admin", key="_u")
            pwd = st.text_input("Contraseña", type="password", placeholder="••••••", key="_p")
            enviado = st.form_submit_button(
                "Acceder al sistema →", use_container_width=True, type="primary"
            )
        if enviado:
            usuario_data, motivo = login_usuario(con, username.strip(), pwd)
            if usuario_data is None:
                st.error(motivo)
            elif usuario_data.get("debe_cambiar_pwd"):
                st.session_state["pwd_change_user"] = usuario_data
                st.rerun()
            else:
                st.session_state["auth"] = True
                st.session_state["usuario"] = usuario_data
                st.rerun()


def _render_cambio_pwd_obligatorio(con, usuario_data):
    st.warning(
        "🔑 Esta cuenta usa la contraseña de fábrica. "
        "Debes definir una nueva antes de continuar."
    )
    with st.form("form_pwd_obligatorio"):
        pwd1 = st.text_input("Nueva contraseña", type="password", placeholder="Mín. 8 caracteres")
        pwd2 = st.text_input("Confirmar contraseña", type="password")
        enviado = st.form_submit_button(
            "Guardar y entrar →", use_container_width=True, type="primary"
        )
    if enviado:
        if len(pwd1) < 8:
            st.error("La contraseña debe tener al menos 8 caracteres.")
        elif pwd1 != pwd2:
            st.error("Las contraseñas no coinciden.")
        else:
            con.execute(
                "UPDATE usuarios SET password_hash=?, debe_cambiar_pwd=0 WHERE id=?",
                (hash_password(pwd1), usuario_data["id"]),
            )
            con.commit()
            registrar_auditoria(
                con, usuario_data["username"], "CAMBIO_PASSWORD", "Primer acceso (obligatorio)"
            )
            usuario_data["debe_cambiar_pwd"] = False
            st.session_state.pop("pwd_change_user", None)
            st.session_state["auth"] = True
            st.session_state["usuario"] = usuario_data
            st.rerun()
