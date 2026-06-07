from __future__ import annotations

import base64
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
ASSETS_DIR = ROOT / "assets"
LOGO_BY_LANG = {
    "es": ASSETS_DIR / "logo_biblioteca_laser.png",
    "en": ASSETS_DIR / "logo_laser_design_library.png",
    "it": ASSETS_DIR / "logo_biblioteca_laser.png",  # Italian uses the same logo as Spanish
    "fr": ASSETS_DIR / "logo_bibliotheque_laser.png",
}

for folder in [UPLOAD_DIR, OUTPUT_DIR, PREVIEW_DIR]:
    folder.mkdir(parents=True, exist_ok=True)

APP_NAME = "Laser File Viewer & Converter"
APP_VERSION = "Online"

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

TEXTS: dict[str, dict[str, str]] = {'es': {'lang_label': '🌐 Idioma / Language',
        'logo_alt': 'Biblioteca Láser',
        'login_kicker': 'Bonus incluido',
        'app_kicker': 'Herramienta incluida',
        'subtitle': 'Visualizá, convertí y prepará archivos para corte láser en madera.',
        'pill_dxf': 'DXF',
        'pill_svg': 'SVG',
        'pill_pdf': 'PDF',
        'pill_png': 'PNG',
        'pill_viewer': 'Visualizador de archivos',
        'pill_converter': 'Conversor simple',
        'pill_download': 'Descarga inmediata',
        'access_title': 'Acceso a la herramienta',
        'access_input': 'Ingresá tu clave de acceso',
        'access_placeholder': 'Clave de acceso',
        'access_button': 'Entrar',
        'access_error': 'La clave ingresada no es correcta.',
        'what_title': '¿Qué podés hacer?',
        'what_text': 'Subí archivos de diseño, miralos antes de usarlos y descargalos en otro formato compatible para '
                     'tus proyectos de corte o grabado láser.',
        'formats_included': 'Formatos incluidos:',
        'file_ready': '✅ Archivo listo para descargar',
        'generated_format': 'Formato generado',
        'download': '⬇️ Descargar',
        'file_error_title': '❌ No se pudo generar el archivo',
        'file_error_text': 'Probá convertirlo a otro formato o revisá que el archivo original se abra correctamente en '
                           'tu programa de diseño.',
        'file': 'Archivo',
        'convert_file': 'Convertir archivo',
        'current_format': 'Formato actual',
        'size': 'Tamaño',
        'unsupported': 'Este formato todavía no está disponible en esta herramienta.',
        'choose_output': 'Elegí el formato de salida',
        'recommended': 'Recomendado para este archivo',
        'convert_to': 'Convertir a',
        'status_preparing': 'Preparando archivo...',
        'progress_start': 'Iniciando',
        'progress_received': 'Archivo recibido',
        'status_received': 'Archivo recibido correctamente.',
        'progress_converting': 'Generando nuevo formato',
        'status_generating': 'Generando versión',
        'progress_download': 'Preparando descarga',
        'progress_ready': 'Listo',
        'status_success': 'Archivo generado con éxito',
        'progress_failed': 'No se pudo completar',
        'status_failed': 'No se pudo completar la conversión',
        'preview': 'Vista previa',
        'preview_full': 'Ver preview ampliado',
        'preview_error': 'No se pudo generar la vista previa automática para este archivo.',
        'step_1_title': '1. Subí',
        'step_1_text': 'DXF, SVG, PDF o PNG.',
        'step_2_title': '2. Visualizá',
        'step_2_text': 'Revisá el diseño antes de convertir.',
        'step_3_title': '3. Descargá',
        'step_3_text': 'Obtené el archivo en otro formato.',
        'uploader': 'Subí uno o varios archivos',
        'uploader_help': 'Podés subir diseños en DXF, SVG, PDF o PNG.',
        'uploaded_count': 'Archivos cargados',
        'clear': 'Limpiar resultados',
        'available_title': 'Formatos disponibles',
        'available_text': 'La herramienta acepta archivos <strong>DXF, SVG, PDF y PNG</strong>. Una vez cargado el '
                          'archivo, vas a poder elegir el formato de salida disponible y descargarlo.',
        'footer': 'Antes de cortar o grabar, revisá escala, capas y líneas en tu software de láser habitual.'},
 'en': {'lang_label': '🌐 Language / Idioma',
        'logo_alt': 'Laser Design Library',
        'login_kicker': 'Included Bonus',
        'app_kicker': 'Included Tool',
        'subtitle': 'Preview, convert, and prepare files for wood laser cutting projects.',
        'pill_dxf': 'DXF',
        'pill_svg': 'SVG',
        'pill_pdf': 'PDF',
        'pill_png': 'PNG',
        'pill_viewer': 'File Preview',
        'pill_converter': 'Simple Converter',
        'pill_download': 'Instant Download',
        'access_title': 'Tool Access',
        'access_input': 'Enter your access code',
        'access_placeholder': 'Access code',
        'access_button': 'Enter',
        'access_error': 'The access code is not correct.',
        'what_title': 'What can you do?',
        'what_text': 'Upload design files, preview them before using them, and download them in another compatible '
                     'format for your laser cutting or engraving projects.',
        'formats_included': 'Included formats:',
        'file_ready': '✅ File ready to download',
        'generated_format': 'Generated format',
        'download': '⬇️ Download',
        'file_error_title': '❌ The file could not be generated',
        'file_error_text': 'Try converting it to another format, or check that the original file opens correctly in '
                           'your design software.',
        'file': 'File',
        'convert_file': 'Convert file',
        'current_format': 'Current format',
        'size': 'Size',
        'unsupported': 'This format is not available in this tool yet.',
        'choose_output': 'Choose output format',
        'recommended': 'Recommended for this file',
        'convert_to': 'Convert to',
        'status_preparing': 'Preparing file...',
        'progress_start': 'Starting',
        'progress_received': 'File received',
        'status_received': 'File received successfully.',
        'progress_converting': 'Generating new format',
        'status_generating': 'Generating version',
        'progress_download': 'Preparing download',
        'progress_ready': 'Ready',
        'status_success': 'File generated successfully',
        'progress_failed': 'Could not complete',
        'status_failed': 'Conversion could not be completed',
        'preview': 'Preview',
        'preview_full': 'Open larger preview',
        'preview_error': 'Automatic preview could not be generated for this file.',
        'step_1_title': '1. Upload',
        'step_1_text': 'DXF, SVG, PDF, or PNG.',
        'step_2_title': '2. Preview',
        'step_2_text': 'Review your design before converting.',
        'step_3_title': '3. Download',
        'step_3_text': 'Get your file in another format.',
        'uploader': 'Upload one or multiple files',
        'uploader_help': 'You can upload designs in DXF, SVG, PDF, or PNG.',
        'uploaded_count': 'Files uploaded',
        'clear': 'Clear results',
        'available_title': 'Available Formats',
        'available_text': 'This tool supports <strong>DXF, SVG, PDF, and PNG</strong> files. Once your file is '
                          'uploaded, you can choose an available output format and download it.',
        'footer': 'Before cutting or engraving, check scale, layers, and lines in your usual laser software.'},
 'it': {'lang_label': '🌐 Lingua / Language / Idioma',
        'logo_alt': 'Biblioteca Laser',
        'login_kicker': 'Bonus incluso',
        'app_kicker': 'Strumento incluso',
        'subtitle': 'Visualizza, converti e prepara file per il taglio laser su legno.',
        'pill_dxf': 'DXF',
        'pill_svg': 'SVG',
        'pill_pdf': 'PDF',
        'pill_png': 'PNG',
        'pill_viewer': 'Anteprima file',
        'pill_converter': 'Convertitore semplice',
        'pill_download': 'Download immediato',
        'access_title': 'Accesso allo strumento',
        'access_input': 'Inserisci la tua chiave di accesso',
        'access_placeholder': 'Chiave di accesso',
        'access_button': 'Entra',
        'access_error': 'La chiave inserita non è corretta.',
        'what_title': 'Cosa puoi fare?',
        'what_text': 'Carica file di design, visualizzali prima di usarli e scaricali in un altro formato compatibile '
                     'per i tuoi progetti di taglio o incisione laser.',
        'formats_included': 'Formati inclusi:',
        'file_ready': '✅ File pronto per il download',
        'generated_format': 'Formato generato',
        'download': '⬇️ Scarica',
        'file_error_title': '❌ Non è stato possibile generare il file',
        'file_error_text': 'Prova a convertirlo in un altro formato oppure controlla che il file originale si apra '
                           'correttamente nel tuo programma di design.',
        'file': 'File',
        'convert_file': 'Converti file',
        'current_format': 'Formato attuale',
        'size': 'Dimensione',
        'unsupported': 'Questo formato non è ancora disponibile in questo strumento.',
        'choose_output': 'Scegli il formato di uscita',
        'recommended': 'Consigliato per questo file',
        'convert_to': 'Converti in',
        'status_preparing': 'Preparazione del file...',
        'progress_start': 'Avvio',
        'progress_received': 'File ricevuto',
        'status_received': 'File ricevuto correttamente.',
        'progress_converting': 'Generazione del nuovo formato',
        'status_generating': 'Generazione versione',
        'progress_download': 'Preparazione download',
        'progress_ready': 'Pronto',
        'status_success': 'File generato con successo',
        'progress_failed': 'Impossibile completare',
        'status_failed': 'Conversione non completata',
        'preview': 'Anteprima',
        'preview_full': 'Apri anteprima ingrandita',
        'preview_error': 'Non è stato possibile generare l’anteprima automatica per questo file.',
        'step_1_title': '1. Carica',
        'step_1_text': 'DXF, SVG, PDF o PNG.',
        'step_2_title': '2. Visualizza',
        'step_2_text': 'Controlla il design prima di convertirlo.',
        'step_3_title': '3. Scarica',
        'step_3_text': 'Ottieni il file in un altro formato.',
        'uploader': 'Carica uno o più file',
        'uploader_help': 'Puoi caricare design in DXF, SVG, PDF o PNG.',
        'uploaded_count': 'File caricati',
        'clear': 'Cancella risultati',
        'available_title': 'Formati disponibili',
        'available_text': 'Lo strumento accetta file <strong>DXF, SVG, PDF e PNG</strong>. Una volta caricato il file, '
                          'potrai scegliere il formato di uscita disponibile e scaricarlo.',
        'footer': 'Prima di tagliare o incidere, controlla scala, livelli e linee nel tuo software laser abituale.'},
 'fr': {'lang_label': '🌐 Langue / Language / Idioma',
        'logo_alt': 'Bibliothèque Laser',
        'login_kicker': 'Bonus inclus',
        'app_kicker': 'Outil inclus',
        'subtitle': 'Visualisez, convertissez et préparez vos fichiers pour la découpe laser sur bois.',
        'pill_dxf': 'DXF',
        'pill_svg': 'SVG',
        'pill_pdf': 'PDF',
        'pill_png': 'PNG',
        'pill_viewer': 'Aperçu des fichiers',
        'pill_converter': 'Convertisseur simple',
        'pill_download': 'Téléchargement immédiat',
        'access_title': 'Accès à l’outil',
        'access_input': 'Entrez votre clé d’accès',
        'access_placeholder': 'Clé d’accès',
        'access_button': 'Entrer',
        'access_error': 'La clé saisie n’est pas correcte.',
        'what_title': 'Que pouvez-vous faire ?',
        'what_text': 'Téléversez vos fichiers de design, prévisualisez-les avant de les utiliser et téléchargez-les dans un autre format compatible pour vos projets de découpe ou de gravure laser.',
        'formats_included': 'Formats inclus :',
        'file_ready': '✅ Fichier prêt à télécharger',
        'generated_format': 'Format généré',
        'download': '⬇️ Télécharger',
        'file_error_title': '❌ Le fichier n’a pas pu être généré',
        'file_error_text': 'Essayez de le convertir dans un autre format ou vérifiez que le fichier original s’ouvre correctement dans votre logiciel de design.',
        'file': 'Fichier',
        'convert_file': 'Convertir le fichier',
        'current_format': 'Format actuel',
        'size': 'Taille',
        'unsupported': 'Ce format n’est pas encore disponible dans cet outil.',
        'choose_output': 'Choisissez le format de sortie',
        'recommended': 'Recommandé pour ce fichier',
        'convert_to': 'Convertir en',
        'status_preparing': 'Préparation du fichier...',
        'progress_start': 'Démarrage',
        'progress_received': 'Fichier reçu',
        'status_received': 'Fichier reçu correctement.',
        'progress_converting': 'Génération du nouveau format',
        'status_generating': 'Génération de la version',
        'progress_download': 'Préparation du téléchargement',
        'progress_ready': 'Prêt',
        'status_success': 'Fichier généré avec succès',
        'progress_failed': 'Impossible de terminer',
        'status_failed': 'La conversion n’a pas pu être terminée',
        'preview': 'Aperçu',
        'preview_full': 'Ouvrir l’aperçu agrandi',
        'preview_error': 'L’aperçu automatique n’a pas pu être généré pour ce fichier.',
        'step_1_title': '1. Téléversez',
        'step_1_text': 'DXF, SVG, PDF ou PNG.',
        'step_2_title': '2. Visualisez',
        'step_2_text': 'Vérifiez le design avant de le convertir.',
        'step_3_title': '3. Téléchargez',
        'step_3_text': 'Obtenez le fichier dans un autre format.',
        'uploader': 'Téléversez un ou plusieurs fichiers',
        'uploader_help': 'Vous pouvez téléverser des designs en DXF, SVG, PDF ou PNG.',
        'uploaded_count': 'Fichiers téléversés',
        'clear': 'Effacer les résultats',
        'available_title': 'Formats disponibles',
        'available_text': 'L’outil accepte les fichiers <strong>DXF, SVG, PDF et PNG</strong>. Une fois le fichier téléversé, vous pourrez choisir le format de sortie disponible et le télécharger.',
        'footer': 'Avant de découper ou de graver, vérifiez l’échelle, les calques et les lignes dans votre logiciel laser habituel.'}}

RECOMMENDED_BY_INPUT = {'es': {'svg': 'SVG o DXF', 'dxf': 'SVG o PDF', 'pdf': 'PNG o SVG', 'png': 'PDF o SVG', 'default': 'SVG o PDF'},
 'en': {'svg': 'SVG or DXF', 'dxf': 'SVG or PDF', 'pdf': 'PNG or SVG', 'png': 'PDF or SVG', 'default': 'SVG or PDF'},
 'it': {'svg': 'SVG o DXF', 'dxf': 'SVG o PDF', 'pdf': 'PNG o SVG', 'png': 'PDF o SVG', 'default': 'SVG o PDF'},
 'fr': {'svg': 'SVG ou DXF', 'dxf': 'SVG ou PDF', 'pdf': 'PNG ou SVG', 'png': 'PDF ou SVG', 'default': 'SVG ou PDF'}}

LANG_LABELS = {'en': 'English', 'es': 'Español', 'it': 'Italiano', 'fr': 'Français'}


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


def query_lang() -> str:
    try:
        value = st.query_params.get("lang", "en")
    except Exception:
        value = "en"
    if isinstance(value, list):
        value = value[0] if value else "en"
    value = str(value).lower().strip()
    return value if value in TEXTS else "en"


def current_lang() -> str:
    if "lang" not in st.session_state:
        st.session_state.lang = query_lang()
    return st.session_state.lang if st.session_state.lang in TEXTS else "en"


def tx(key: str) -> str:
    return TEXTS[current_lang()].get(key, TEXTS["en"].get(key, key))


def render_language_selector() -> None:
    lang = current_lang()
    left, right = st.columns([1, 0.28])
    with right:
        selected = st.selectbox(
            tx("lang_label"),
            options=["en", "es", "it", "fr"],
            index=["en", "es", "it", "fr"].index(lang),
            format_func=lambda code: LANG_LABELS[code],
            key="language_picker",
            label_visibility="collapsed",
        )
    if selected != lang:
        st.session_state.lang = selected
        try:
            st.query_params["lang"] = selected
        except Exception:
            pass
        st.rerun()


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
    if "lang" not in st.session_state:
        st.session_state.lang = query_lang()


def reset_results() -> None:
    st.session_state.conversion_results = {}


def image_to_base64(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("utf-8")


def render_logo_header() -> None:
    logo_path = LOGO_BY_LANG.get(current_lang(), LOGO_BY_LANG["en"])
    if not logo_path.exists():
        return
    logo_b64 = image_to_base64(logo_path)
    st.markdown(
        f"""
<div class="lfc-logo-header">
  <img src="data:image/png;base64,{logo_b64}" alt="{tx('logo_alt')}" />
</div>
        """,
        unsafe_allow_html=True,
    )


def render_css() -> None:
    st.markdown(
        """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
.block-container {padding-top: 1.05rem; padding-bottom: 3rem; max-width: 1180px;}

.lfc-logo-header {
  display:flex;
  justify-content:center;
  align-items:center;
  margin: 4px 0 16px 0;
}
.lfc-logo-header img {
  width: min(210px, 42vw);
  height:auto;
  border-radius: 999px;
  box-shadow: 0 18px 44px rgba(46,36,28,.24);
  border: 1px solid rgba(217,154,43,.28);
}

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
[data-testid="stFileUploaderDropzone"] small,
[data-testid="stFileUploaderDropzoneInstructions"] small {
  display:none !important;
}
@media(max-width: 740px){
  .lfc-hero {padding: 24px 20px; border-radius: 22px;}
  .lfc-subtitle {font-size: 16px;}
  .lfc-logo-header img {width: min(175px, 52vw);}
}
</style>
        """,
        unsafe_allow_html=True,
    )


def login_screen() -> None:
    render_logo_header()
    render_language_selector()
    st.markdown(
        f"""
<div class="lfc-hero">
  <div class="lfc-kicker">{tx('login_kicker')}</div>
  <div class="lfc-title">{APP_NAME}</div>
  <p class="lfc-subtitle">{tx('subtitle')}</p>
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
        st.markdown(f"### {tx('access_title')}")
        entered = st.text_input(tx("access_input"), type="password", placeholder=tx("access_placeholder"))
        if st.button(tx("access_button"), type="primary", use_container_width=True):
            if entered.strip() == get_access_code():
                st.session_state.unlocked = True
                st.rerun()
            else:
                st.error(tx("access_error"))
    with c2:
        st.markdown(
            f"""
<div class="lfc-card">
  <div class="lfc-step-title">{tx('what_title')}</div>
  <div class="lfc-muted">
    {tx('what_text')}
  </div>
  <br>
  <div class="lfc-soft">
    <strong>{tx('formats_included')}</strong> DXF · SVG · PDF · PNG
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
  <strong>{tx('file_ready')}</strong><br>
  <span class="lfc-muted">{tx('generated_format')}: {output_format.upper()} · {tx('size')}: {human_size(output_path.stat().st_size)}</span>
</div>
            """,
            unsafe_allow_html=True,
        )
        st.download_button(
            label=f"{tx('download')} {output_path.name}",
            data=output_path.read_bytes(),
            file_name=output_path.name,
            mime=MIME_BY_EXT.get(output_format, "application/octet-stream"),
            key=f"download_{file_key}_{output_path.name}",
            type="primary",
            use_container_width=True,
        )
    elif status == "ERROR":
        st.markdown(
            f"""
<div class="lfc-error">
  <strong>{tx('file_error_title')}</strong><br>
  <span class="lfc-muted">{tx('file_error_text')}</span>
</div>
            """,
            unsafe_allow_html=True,
        )


def conversion_block(uploaded, index: int) -> None:
    file_key, input_path, content = save_uploaded_once(uploaded)
    safe_name = safe_filename(uploaded.name)
    input_ext = input_path.suffix.lower().lstrip(".")
    outputs = SUPPORTED_OUTPUTS.get(input_ext, [])

    st.markdown(f"### {tx('file')} {index}: {uploaded.name}")
    col_actions, col_preview = st.columns([0.9, 1.1], gap="large")

    with col_actions:
        st.markdown('<div class="lfc-card">', unsafe_allow_html=True)
        st.markdown(f"#### {tx('convert_file')}")
        st.write(f"**{tx('current_format')}:** {input_ext.upper()}")
        st.write(f"**{tx('size')}:** {human_size(len(content))}")

        if not outputs:
            st.warning(tx("unsupported"))
            st.markdown("</div>", unsafe_allow_html=True)
            return

        output_format = st.selectbox(
            tx("choose_output"),
            options=outputs,
            index=0,
            format_func=lambda x: x.upper(),
            key=f"output_format_{file_key}",
        )

        recommended = RECOMMENDED_BY_INPUT[current_lang()].get(input_ext, RECOMMENDED_BY_INPUT[current_lang()]["default"])
        st.caption(f"{tx('recommended')}: {recommended}.")

        convert_btn = st.button(
            f"{tx('convert_to')} {output_format.upper()}",
            key=f"convert_{file_key}",
            type="primary",
            use_container_width=True,
        )

        if convert_btn:
            out_slug = timestamp_slug()
            out_name = f"{Path(safe_name).stem}_{out_slug}.{output_format}"
            output_path = OUTPUT_DIR / out_name

            status_box = st.status(tx("status_preparing"), expanded=True)
            progress = st.progress(0, text=tx("progress_start"))
            try:
                progress.progress(25, text=tx("progress_received"))
                status_box.write(tx("status_received"))

                progress.progress(55, text=tx("progress_converting"))
                status_box.write(f"{tx('status_generating')} {output_format.upper()}...")

                info = convert_file(
                    input_path,
                    output_path,
                    dpi=300,
                    transparent_png=True,
                    prefer_inkscape=False,
                )

                progress.progress(82, text=tx("progress_download"))
                if not output_path.exists() or output_path.stat().st_size == 0:
                    raise ConversionError("Output file was not generated.")

                progress.progress(100, text=tx("progress_ready"))
                status_box.update(label=tx("status_success"), state="complete", expanded=False)

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
                        "message": "Archivo generado / File generated",
                    },
                )
            except Exception:
                progress.progress(100, text=tx("progress_failed"))
                status_box.update(label=tx("status_failed"), state="error", expanded=False)
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
                        "message": "No se pudo generar / Could not generate",
                    },
                )

        existing_result = st.session_state.conversion_results.get(file_key)
        if existing_result:
            render_result(file_key, existing_result)

        st.markdown("</div>", unsafe_allow_html=True)

    with col_preview:
        st.markdown('<div class="lfc-card">', unsafe_allow_html=True)
        st.markdown(f"#### {tx('preview')}")
        try:
            preview_path = make_preview(input_path, PREVIEW_DIR, dpi=140)
            thumb_path = make_display_thumbnail(preview_path, PREVIEW_DIR, max_width=520, max_height=380)
            st.image(str(thumb_path), width=520)
            with st.expander(tx("preview_full")):
                st.image(str(preview_path), use_container_width=True)
        except Exception:
            st.info(tx("preview_error"))
        st.markdown("</div>", unsafe_allow_html=True)


def app_screen() -> None:
    render_logo_header()
    render_language_selector()
    st.markdown(
        f"""
<div class="lfc-hero">
  <div class="lfc-kicker">{tx('app_kicker')}</div>
  <div class="lfc-title">{APP_NAME}</div>
  <p class="lfc-subtitle">{tx('subtitle')}</p>
  <div class="lfc-pills">
    <span class="lfc-pill">{tx('pill_viewer')}</span>
    <span class="lfc-pill">{tx('pill_converter')}</span>
    <span class="lfc-pill">{tx('pill_download')}</span>
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )

    top_a, top_b, top_c = st.columns(3)
    with top_a:
        st.markdown(f'<div class="lfc-soft"><strong>{tx("step_1_title")}</strong><br><span class="lfc-muted">{tx("step_1_text")}</span></div>', unsafe_allow_html=True)
    with top_b:
        st.markdown(f'<div class="lfc-soft"><strong>{tx("step_2_title")}</strong><br><span class="lfc-muted">{tx("step_2_text")}</span></div>', unsafe_allow_html=True)
    with top_c:
        st.markdown(f'<div class="lfc-soft"><strong>{tx("step_3_title")}</strong><br><span class="lfc-muted">{tx("step_3_text")}</span></div>', unsafe_allow_html=True)

    st.write("")
    uploaded_files = st.file_uploader(
        tx("uploader"),
        type=["svg", "dxf", "pdf", "png"],
        accept_multiple_files=True,
        help=tx("uploader_help"),
    )

    if uploaded_files:
        st.success(f"{tx('uploaded_count')}: {len(uploaded_files)}")
        for index, uploaded in enumerate(uploaded_files, start=1):
            conversion_block(uploaded, index)
            st.divider()

        if st.button(tx("clear"), use_container_width=True):
            reset_results()
            st.rerun()
    else:
        st.markdown(
            f"""
<div class="lfc-card">
  <div class="lfc-step-title">{tx('available_title')}</div>
  <div class="lfc-muted">
    {tx('available_text')}
  </div>
</div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        f"""
<div class="lfc-footer">
  {tx('footer')}
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
