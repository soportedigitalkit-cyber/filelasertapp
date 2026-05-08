from __future__ import annotations

import shutil
from pathlib import Path

from PIL import Image

from .converter import pdf_to_png, svg_to_png
from .dxf_utils import dxf_to_png_preview, dxf_to_svg


def make_preview(input_path: str | Path, output_dir: str | Path, *, dpi: int = 160) -> Path:
    input_path = Path(input_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    ext = input_path.suffix.lower().lstrip(".")
    preview_path = output_dir / f"{input_path.stem}_preview.png"

    if ext == "png":
        shutil.copy2(input_path, preview_path)
        return preview_path

    if ext == "svg":
        svg_to_png(input_path, preview_path, dpi=dpi, transparent=False)
        return preview_path

    if ext == "pdf":
        pdf_to_png(input_path, preview_path, dpi=dpi, page_number=0)
        return preview_path

    if ext == "dxf":
        # Preview DXF directly with ezdxf + Pillow so Inkscape is NOT required.
        # If a DXF contains entities outside the simple renderer, fall back to the
        # SVG route, which may still work for common geometry.
        try:
            dxf_to_png_preview(input_path, preview_path)
            return preview_path
        except Exception:
            temp_svg = output_dir / f"{input_path.stem}_preview.svg"
            dxf_to_svg(input_path, temp_svg)
            svg_to_png(temp_svg, preview_path, dpi=dpi, transparent=False)
            return preview_path

    raise ValueError(f"No hay preview para formato: {ext}")


def make_display_thumbnail(
    image_path: str | Path,
    output_dir: str | Path,
    *,
    max_width: int = 420,
    max_height: int = 360,
) -> Path:
    """Create a compact non-cropped PNG thumbnail for Streamlit preview.

    This keeps the UI short: tall laser files no longer push the conversion result
    far below the fold. The full preview is still available in the app expander.
    """
    image_path = Path(image_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    thumb_path = output_dir / f"{image_path.stem}_thumb_{max_width}x{max_height}.png"

    img = Image.open(image_path)
    if img.mode in ("RGBA", "LA"):
        rgba = img.convert("RGBA")
        bg = Image.new("RGBA", rgba.size, "white")
        bg.alpha_composite(rgba)
        img = bg.convert("RGB")
    else:
        img = img.convert("RGB")

    img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
    img.save(thumb_path, "PNG", optimize=True)
    return thumb_path
