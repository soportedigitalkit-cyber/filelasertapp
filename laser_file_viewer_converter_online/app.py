from __future__ import annotations

import hashlib
import os
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st

from laser_converter.converter import ConversionError, convert_file
from laser_converter.file_utils import append_history, human_size, safe_filename, timestamp_slug
from laser_converter.preview import make_display_thumbnail, make_preview

ROOT = Path(__file__).parent
DATA_DIR = ROOT / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
OUTPUT_DIR = DATA_DIR / "outputs"
PREVIEW_DIR = DATA_DIR / "previews"
HISTORY_CSV = DATA_DIR / "history.csv"

for folder in [UPLOAD_DIR, OUTPUT_DIR, PREVIEW_DIR]:
    folder.mkdir(parents=True, exist_ok=True)

APP_NAME = "Laser File Viewer & Converter"
APP_SUBTITLE = "Visualizá, convertí y prepará archivos para corte láser en madera."
APP_VERSION = "Online"

# Salidas pensadas para la versión online, evitando opciones que dependen de programas externos.
SUPPORTED_OUTPUTS: dict[str, list[str]] = {
    "svg": ["png", "pdf", "dxf", "svg"],
    "dxf": ["svg", "png", "pdf", "dxf"],
    "pdf": ["png", "svg", "pdf"],
    "png": ["pdf", "svg", "png"],
}

MIME_BY_EXT = {
    "svg": "image/svg+xml",
    "png": "image/png",
    "pdf": "application/pdf",
    "dxf": "application/dxf",
}

RECOMMENDED_BY_INPUT = {
    "svg": "SVG o DXF",
    "dxf": "SVG o PDF",
    "pdf": "PNG o SVG",
    "png": "PDF o SVG",
}


def get_access_code() -> str:
    """Read access code from Streamlit secrets or environment, with a simple fallback."""
    try:
        secret_value = st.secrets.get("APP_ACCESS_CODE", None)
        if secret_value:
            return str(secret_value).strip()
    except Exception:
        pass
    env_value = os.getenv("APP_ACCESS_CODE")
    if env_value:
        return env_value.strip()
    return "LASER2026"


def file_key_from_bytes(filename: str, content: bytes) -> str:
    digest = hashlib.md5(content).hexdigest()[:12]
    return f"{safe_filename(filename)}_{len(content)}_{digest}"


def save_uploaded_once(uploaded) -> tuple[str, Path, bytes]:
    content = uploaded.getvalue()
    file_key = file_key_from_bytes(uploaded.name, content)
    safe_name = safe_filename(uploaded.name)
    input_path = UPLOAD_DIR / f"{file_key}_{safe_name}"
    if not input_path.exists():
        input_path.write_bytes(content)
    return file_key, input_path, content


def init_state() -> None:
    st.session_state.setdefault("unlocked", False)
    st.session_state.setdefault("conversion_results", {})


def reset_results() -> None:
    st.session_state.conversion_results = {}


def render_css() -> None:
    st.markdown(
        """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
.block-container {padding-top: 1.2rem; padding-bottom: 3rem; max-width: 1180px;}

.lfc-hero {
  border: 1px solid rgba(146, 102, 37, .18);
  background:
    radial-gradient(circle at 12% 12%, rgba(217,154,43,.22), transparent 32%),
    linear-gradient(135deg, #1F2937 0%, #2B1F16 55%, #7A4E1D 100%);
  border-radius: 28px;
  padding: 30px 32px;
  margin: 6px 0 22px 0;
  box-shadow: 0 18px 48px rgba(31, 41, 55, .18);
}
.lfc-kicker {
  color: #FDE68A;
  font-size: 13px;
  font-weight: 900;
  letter-spacing: .12em;
  text-transform: uppercase;
  margin-bottom: 10px;
}
.lfc-title {
  color: #FFFFFF;
  font-size: clamp(32px, 5vw, 58px);
  line-height: 1.02;
  font-weight: 950;
  letter-spacing: -.045em;
  margin: 0 0 10px 0;
}
.lfc-subtitle {
  color: #F3F4F6;
  font-size: 18px;
  line-height: 1.52;
  max-width: 880px;
  margin: 0;
}
.lfc-pills {display:flex; flex-wrap:wrap; gap:10px; margin-top:18px;}
.lfc-pill {
  background: rgba(255,255,255,.10);
  border: 1px solid rgba(255,255,255,.18);
  color: #FFFFFF;
  padding: 8px 12px;
  border-radius: 999px;
  font-size: 13px;
  font-weight: 800;
}
.lfc-card {
  border: 1px solid rgba(120, 87, 45, .16);
  border-radius: 24px;
  background: rgba(255,255,255,.78);
  box-shadow: 0 12px 32px rgba(31,41,55,.07);
  padding: 18px;
  margin-bottom: 16px;
}
.lfc-soft {
  border-radius: 20px;
  background: #FFF8EC;
  border: 1px solid rgba(217,154,43,.24);
  padding: 14px 16px;
}
.lfc-step-title {font-weight: 900; font-size: 17px; color:#1F2937; margin-bottom:6px;}
.lfc-muted {font-size: 14px; color: #6B7280; line-height:1.45;}
.lfc-result {
  border: 1px solid rgba(22, 163, 74, .22);
  background: #F0FDF4;
  border-radius: 18px;
  padding: 14px 16px;
  margin-top: 14px;
}
.lfc-error {
  border: 1px solid rgba(220, 38, 38, .20);
  background: #FEF2F2;
  border-radius: 18px;
  padding: 14px 16px;
  margin-top: 14px;
}
.lfc-footer {
  color:#6B7280;
  font-size: 13px;
  line-height:1.45;
  text-align:center;
  margin-top:28px;
}
[data-testid="stFileUploader"] section {
  border-radius: 22px;
  border: 1.5px dashed rgba(217,154,43,.45);
  background: rgba(255,248,236,.58);
}
</style>
        """,
        unsafe_allow_html=True,
    )


def login_screen() -> None:
    st.markdown(
        f"""
<div class="lfc-hero">
  <div class="lfc-kicker">Bonus incluido</div>
  <div class="lfc-title">{APP_NAME}</div>
  <p class="lfc-subtitle">{APP_SUBTITLE}</p>
  <div class="lfc-pills">
    <span class="lfc-pill">DXF</span>
    <span class="lfc-pill">SVG</span>
    <span class="lfc-pill">PDF</span>
    <span class="lfc-pill">PNG</span>
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns([0.95, 1.05], gap="large")
    with c1:
        st.markdown("### Acceso a la herramienta")
        entered = st.text_input("Ingresá tu clave de acceso", type="password", placeholder="Clave de acceso")
        if st.button("Entrar", type="primary", use_container_width=True):
            if entered.strip() == get_access_code():
                st.session_state.unlocked = True
                st.rerun()
            else:
                st.error("La clave ingresada no es correcta.")
    with c2:
        st.markdown(
            """
<div class="lfc-card">
  <div class="lfc-step-title">¿Qué podés hacer?</div>
  <div class="lfc-muted">
    Subí archivos de diseño, miralos antes de usarlos y descargalos en otro formato compatible para tus proyectos de corte o grabado láser.
  </div>
  <br>
  <div class="lfc-soft">
    <strong>Formatos incluidos:</strong> DXF · SVG · PDF · PNG
  </div>
</div>
            """,
            unsafe_allow_html=True,
        )


def render_result(file_key: str, result: dict[str, Any]) -> None:
    status = result.get("status")
    output_path = Path(result.get("output_path", ""))
    if status == "OK" and output_path.exists():
        output_format = result.get("output_format", output_path.suffix.lstrip(".")).lower()
        st.markdown(
            f"""
<div class="lfc-result">
  <strong>✅ Archivo listo para descargar</strong><br>
  <span class="lfc-muted">Formato generado: {output_format.upper()} · Tamaño: {human_size(output_path.stat().st_size)}</span>
</div>
            """,
            unsafe_allow_html=True,
        )
        st.download_button(
            label=f"⬇️ Descargar {output_path.name}",
            data=output_path.read_bytes(),
            file_name=output_path.name,
            mime=MIME_BY_EXT.get(output_format, "application/octet-stream"),
            key=f"download_{file_key}_{output_path.name}",
            type="primary",
            use_container_width=True,
        )
    elif status == "ERROR":
        st.markdown(
            """
<div class="lfc-error">
  <strong>❌ No se pudo generar el archivo</strong><br>
  <span class="lfc-muted">Probá convertirlo a otro formato o revisá que el archivo original se abra correctamente en tu programa de diseño.</span>
</div>
            """,
            unsafe_allow_html=True,
        )


def conversion_block(uploaded, index: int) -> None:
    file_key, input_path, content = save_uploaded_once(uploaded)
    safe_name = safe_filename(uploaded.name)
    input_ext = input_path.suffix.lower().lstrip(".")
    outputs = SUPPORTED_OUTPUTS.get(input_ext, [])

    st.markdown(f"### Archivo {index}: {uploaded.name}")
    col_actions, col_preview = st.columns([0.9, 1.1], gap="large")

    with col_actions:
        st.markdown('<div class="lfc-card">', unsafe_allow_html=True)
        st.markdown("#### Convertir archivo")
        st.write(f"**Formato actual:** {input_ext.upper()}")
        st.write(f"**Tamaño:** {human_size(len(content))}")

        if not outputs:
            st.warning("Este formato todavía no está disponible en esta herramienta.")
            st.markdown("</div>", unsafe_allow_html=True)
            return

        output_format = st.selectbox(
            "Elegí el formato de salida",
            options=outputs,
            index=0,
            format_func=lambda x: x.upper(),
            key=f"output_format_{file_key}",
        )

        st.caption(f"Recomendado para este archivo: {RECOMMENDED_BY_INPUT.get(input_ext, 'SVG o PDF')}.")

        convert_btn = st.button(
            f"Convertir a {output_format.upper()}",
            key=f"convert_{file_key}",
            type="primary",
            use_container_width=True,
        )

        if convert_btn:
            out_slug = timestamp_slug()
            out_name = f"{Path(safe_name).stem}_{out_slug}.{output_format}"
            output_path = OUTPUT_DIR / out_name

            status_box = st.status("Preparando archivo...", expanded=True)
            progress = st.progress(0, text="Iniciando")
            try:
                progress.progress(25, text="Archivo recibido")
                status_box.write("Archivo recibido correctamente.")

                progress.progress(55, text="Generando nuevo formato")
                status_box.write(f"Generando versión {output_format.upper()}...")

                info = convert_file(
                    input_path,
                    output_path,
                    dpi=300,
                    transparent_png=True,
                    prefer_inkscape=False,
                )

                progress.progress(82, text="Preparando descarga")
                if not output_path.exists() or output_path.stat().st_size == 0:
                    raise ConversionError("No se pudo generar un archivo descargable.")

                progress.progress(100, text="Listo")
                status_box.update(label="Archivo generado con éxito", state="complete", expanded=False)

                result = {
                    "status": "OK",
                    "output_path": str(output_path),
                    "output_format": output_format,
                    "finished_at": datetime.now().isoformat(timespec="seconds"),
                    "info": info,
                }
                st.session_state.conversion_results[file_key] = result
                append_history(
                    HISTORY_CSV,
                    {
                        "timestamp": datetime.now().isoformat(timespec="seconds"),
                        "input_file": uploaded.name,
                        "input_format": input_ext.upper(),
                        "output_file": output_path.name,
                        "output_format": output_format.upper(),
                        "status": "OK",
                        "message": "Archivo generado",
                    },
                )
            except Exception:
                progress.progress(100, text="No se pudo completar")
                status_box.update(label="No se pudo completar la conversión", state="error", expanded=False)
                st.session_state.conversion_results[file_key] = {
                    "status": "ERROR",
                    "output_path": str(output_path),
                    "output_format": output_format,
                    "finished_at": datetime.now().isoformat(timespec="seconds"),
                }
                append_history(
                    HISTORY_CSV,
                    {
                        "timestamp": datetime.now().isoformat(timespec="seconds"),
                        "input_file": uploaded.name,
                        "input_format": input_ext.upper(),
                        "output_file": output_path.name,
                        "output_format": output_format.upper(),
                        "status": "ERROR",
                        "message": "No se pudo generar",
                    },
                )

        existing_result = st.session_state.conversion_results.get(file_key)
        if existing_result:
            render_result(file_key, existing_result)

        st.markdown("</div>", unsafe_allow_html=True)

    with col_preview:
        st.markdown('<div class="lfc-card">', unsafe_allow_html=True)
        st.markdown("#### Vista previa")
        try:
            preview_path = make_preview(input_path, PREVIEW_DIR, dpi=140)
            thumb_path = make_display_thumbnail(preview_path, PREVIEW_DIR, max_width=520, max_height=380)
            st.image(str(thumb_path), width=520)
            with st.expander("Ver preview ampliado"):
                st.image(str(preview_path), use_container_width=True)
        except Exception:
            st.info("No se pudo generar la vista previa automática para este archivo.")
        st.markdown("</div>", unsafe_allow_html=True)


def app_screen() -> None:
    st.markdown(
        f"""
<div class="lfc-hero">
  <div class="lfc-kicker">Herramienta incluida</div>
  <div class="lfc-title">{APP_NAME}</div>
  <p class="lfc-subtitle">{APP_SUBTITLE}</p>
  <div class="lfc-pills">
    <span class="lfc-pill">Visualizador de archivos</span>
    <span class="lfc-pill">Conversor simple</span>
    <span class="lfc-pill">Descarga inmediata</span>
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )

    top_a, top_b, top_c = st.columns(3)
    with top_a:
        st.markdown('<div class="lfc-soft"><strong>1. Subí</strong><br><span class="lfc-muted">DXF, SVG, PDF o PNG.</span></div>', unsafe_allow_html=True)
    with top_b:
        st.markdown('<div class="lfc-soft"><strong>2. Visualizá</strong><br><span class="lfc-muted">Revisá el diseño antes de convertir.</span></div>', unsafe_allow_html=True)
    with top_c:
        st.markdown('<div class="lfc-soft"><strong>3. Descargá</strong><br><span class="lfc-muted">Obtené el archivo en otro formato.</span></div>', unsafe_allow_html=True)

    st.write("")
    uploaded_files = st.file_uploader(
        "Subí uno o varios archivos",
        type=["svg", "dxf", "pdf", "png"],
        accept_multiple_files=True,
        help="Podés subir diseños en DXF, SVG, PDF o PNG.",
    )

    if uploaded_files:
        st.success(f"Archivos cargados: {len(uploaded_files)}")
        for index, uploaded in enumerate(uploaded_files, start=1):
            conversion_block(uploaded, index)
            st.divider()

        if st.button("Limpiar resultados", use_container_width=True):
            reset_results()
            st.rerun()
    else:
        st.markdown(
            """
<div class="lfc-card">
  <div class="lfc-step-title">Formatos disponibles</div>
  <div class="lfc-muted">
    La herramienta acepta archivos <strong>DXF, SVG, PDF y PNG</strong>. Una vez cargado el archivo, vas a poder elegir el formato de salida disponible y descargarlo.
  </div>
</div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        """
<div class="lfc-footer">
  Antes de cortar o grabar, revisá escala, capas y líneas en tu software de láser habitual.
</div>
        """,
        unsafe_allow_html=True,
    )


st.set_page_config(
    page_title=APP_NAME,
    page_icon="🪵",
    layout="wide",
    initial_sidebar_state="collapsed",
)

init_state()
render_css()

if not st.session_state.unlocked:
    login_screen()
else:
    app_screen()
