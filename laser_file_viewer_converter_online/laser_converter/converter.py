from __future__ import annotations

import base64
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Optional

import fitz  # PyMuPDF
from PIL import Image

from .dxf_utils import dxf_to_svg, simple_svg_to_dxf


class ConversionError(RuntimeError):
    pass


def detect_inkscape() -> Optional[str]:
    """Return an Inkscape executable path when available."""
    candidates = [
        shutil.which("inkscape"),
        shutil.which("inkscape.com"),
        shutil.which("inkscape.exe"),
        r"C:\Program Files\Inkscape\bin\inkscape.com",
        r"C:\Program Files\Inkscape\bin\inkscape.exe",
    ]
    for c in candidates:
        if c and Path(c).exists():
            return c
    return None


def dependency_status() -> Dict[str, bool | str | None]:
    return {
        "inkscape_path": detect_inkscape(),
        "pymupdf": True,
        "pillow": True,
        "ezdxf": True,
        "svg_renderer": "PyMuPDF",
    }


def _run_inkscape(input_path: Path, output_path: Path, *, dpi: int | None = None) -> None:
    ink = detect_inkscape()
    if not ink:
        raise ConversionError("Inkscape no está instalado o no fue detectado en PATH.")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [ink, str(input_path), f"--export-filename={output_path}"]
    if dpi and output_path.suffix.lower() == ".png":
        cmd.append(f"--export-dpi={dpi}")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0 or not output_path.exists():
        raise ConversionError(
            "Inkscape no pudo completar la conversión. "
            f"Detalle: {(result.stderr or result.stdout or '').strip()}"
        )


def _open_svg_doc(svg_path: Path) -> fitz.Document:
    """Open SVG with PyMuPDF. This avoids CairoSVG/fontconfig issues on Windows."""
    return fitz.open(stream=svg_path.read_bytes(), filetype="svg")


def svg_to_png(svg_path: Path, png_path: Path, *, dpi: int = 300, transparent: bool = True, prefer_inkscape: bool = False) -> None:
    png_path.parent.mkdir(parents=True, exist_ok=True)
    if prefer_inkscape and detect_inkscape():
        try:
            _run_inkscape(svg_path, png_path, dpi=dpi)
            return
        except Exception:
            # Fall back to PyMuPDF so one Inkscape failure does not block the app.
            pass
    try:
        doc = _open_svg_doc(svg_path)
        if doc.page_count == 0:
            raise ConversionError("El SVG no tiene páginas renderizables.")
        page = doc.load_page(0)
        zoom = dpi / 72
        pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=transparent)
        pix.save(png_path)
        doc.close()
        return
    except Exception as exc:
        # Inkscape tends to be more tolerant with complex SVGs.
        if detect_inkscape():
            _run_inkscape(svg_path, png_path)
            return
        raise ConversionError(
            "No se pudo renderizar SVG → PNG con PyMuPDF y no se detectó Inkscape. "
            f"Detalle: {exc}"
        )


def svg_to_pdf(svg_path: Path, pdf_path: Path, *, prefer_inkscape: bool = False) -> None:
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    if prefer_inkscape and detect_inkscape():
        try:
            _run_inkscape(svg_path, pdf_path)
            return
        except Exception:
            # Fall back to PyMuPDF so one Inkscape failure does not block the app.
            pass
    try:
        doc = _open_svg_doc(svg_path)
        if doc.page_count == 0:
            raise ConversionError("El SVG no tiene páginas renderizables.")
        pdf_path.write_bytes(doc.convert_to_pdf())
        doc.close()
        return
    except Exception as exc:
        if detect_inkscape():
            _run_inkscape(svg_path, pdf_path)
            return
        raise ConversionError(
            "No se pudo convertir SVG → PDF con PyMuPDF y no se detectó Inkscape. "
            f"Detalle: {exc}"
        )


def pdf_to_png(pdf_path: Path, png_path: Path, *, dpi: int = 200, page_number: int = 0) -> None:
    png_path.parent.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(pdf_path)
    if doc.page_count == 0:
        raise ConversionError("El PDF no tiene páginas.")
    page_number = min(max(page_number, 0), doc.page_count - 1)
    page = doc.load_page(page_number)
    zoom = dpi / 72
    matrix = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=matrix, alpha=True)
    pix.save(png_path)
    doc.close()


def pdf_to_svg(pdf_path: Path, svg_path: Path, *, page_number: int = 0) -> None:
    svg_path.parent.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(pdf_path)
    if doc.page_count == 0:
        raise ConversionError("El PDF no tiene páginas.")
    page_number = min(max(page_number, 0), doc.page_count - 1)
    svg_text = doc.load_page(page_number).get_svg_image()
    svg_path.write_text(svg_text, encoding="utf-8")
    doc.close()


def png_to_pdf(png_path: Path, pdf_path: Path) -> None:
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.open(png_path)
    if img.mode in ("RGBA", "LA"):
        bg = Image.new("RGB", img.size, "white")
        bg.paste(img, mask=img.split()[-1])
        img = bg
    else:
        img = img.convert("RGB")
    img.save(pdf_path, "PDF", resolution=300)


def png_to_svg_embed(png_path: Path, svg_path: Path) -> None:
    """Wrap a PNG inside an SVG. This is not vectorization."""
    svg_path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.open(png_path)
    width, height = img.size
    encoded = base64.b64encode(png_path.read_bytes()).decode("ascii")
    svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{width}px" height="{height}px" viewBox="0 0 {width} {height}">
  <image href="data:image/png;base64,{encoded}" width="{width}" height="{height}"/>
</svg>
'''
    svg_path.write_text(svg, encoding="utf-8")


def convert_file(input_path: str | Path, output_path: str | Path, *, dpi: int = 300, transparent_png: bool = True, prefer_inkscape: bool = True) -> dict:
    input_path = Path(input_path)
    output_path = Path(output_path)
    src = input_path.suffix.lower().lstrip(".")
    dst = output_path.suffix.lower().lstrip(".")

    if not input_path.exists():
        raise ConversionError(f"No existe el archivo de entrada: {input_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    info: dict = {"source_format": src, "output_format": dst, "notes": []}

    if src == dst:
        shutil.copy2(input_path, output_path)
        info["notes"].append("Se copió el archivo porque origen y destino tienen el mismo formato.")
        return info

    # SVG input
    if src == "svg":
        if dst == "png":
            svg_to_png(input_path, output_path, dpi=dpi, transparent=transparent_png, prefer_inkscape=prefer_inkscape)
        elif dst == "pdf":
            svg_to_pdf(input_path, output_path, prefer_inkscape=prefer_inkscape)
        elif dst == "dxf":
            try:
                counts = simple_svg_to_dxf(input_path, output_path)
                info["geometry"] = counts
                info["notes"].append("DXF generado desde geometría SVG básica. Transformaciones/efectos complejos pueden ignorarse en V1.")
            except Exception as exc:
                # Try Inkscape as fallback if available.
                if detect_inkscape():
                    _run_inkscape(input_path, output_path)
                    info["notes"].append("DXF generado con Inkscape.")
                else:
                    raise ConversionError(f"No se pudo convertir SVG a DXF: {exc}")
        else:
            raise ConversionError(f"Conversión no soportada en V1: SVG → {dst.upper()}")
        return info

    # DXF input
    if src == "dxf":
        temp_svg = output_path.with_suffix(".preview.svg") if dst != "svg" else output_path
        counts = dxf_to_svg(input_path, temp_svg)
        info["geometry"] = counts
        info["notes"].append("DXF interpretado con entidades comunes: líneas, polilíneas, círculos y arcos.")
        if dst == "svg":
            pass
        elif dst == "png":
            svg_to_png(temp_svg, output_path, dpi=dpi, transparent=transparent_png, prefer_inkscape=prefer_inkscape)
        elif dst == "pdf":
            svg_to_pdf(temp_svg, output_path, prefer_inkscape=prefer_inkscape)
        else:
            raise ConversionError(f"Conversión no soportada en V1: DXF → {dst.upper()}")
        return info

    # PDF input
    if src == "pdf":
        if dst == "png":
            pdf_to_png(input_path, output_path, dpi=dpi)
        elif dst == "svg":
            pdf_to_svg(input_path, output_path)
            info["notes"].append("SVG generado desde la primera página del PDF.")
        elif dst == "dxf":
            if detect_inkscape():
                _run_inkscape(input_path, output_path)
                info["notes"].append("Conversión PDF → DXF realizada con Inkscape. Revisar capas y escala antes de cortar.")
            else:
                raise ConversionError("PDF → DXF requiere Inkscape instalado para esta V1.")
        else:
            raise ConversionError(f"Conversión no soportada en V1: PDF → {dst.upper()}")
        return info

    # PNG input
    if src == "png":
        if dst == "pdf":
            png_to_pdf(input_path, output_path)
        elif dst == "svg":
            png_to_svg_embed(input_path, output_path)
            info["notes"].append("El SVG contiene la imagen PNG embebida. No es vectorización real.")
        elif dst == "dxf":
            raise ConversionError("PNG → DXF requiere vectorización/trazado automático. Lo dejamos para la V2.")
        else:
            raise ConversionError(f"Conversión no soportada en V1: PNG → {dst.upper()}")
        return info

    raise ConversionError(f"Formato de entrada no soportado en V1: {src.upper()}")


def supported_outputs_for(input_ext: str) -> list[str]:
    ext = input_ext.lower().lstrip(".")
    table = {
        "svg": ["png", "pdf", "dxf", "svg"],
        "dxf": ["svg", "png", "pdf", "dxf"],
        "pdf": ["png", "svg", "dxf", "pdf"],
        "png": ["pdf", "svg", "png"],
    }
    return table.get(ext, [])
