from __future__ import annotations

import math
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Iterable, List, Tuple

import ezdxf
from svgpathtools import parse_path

Point = Tuple[float, float]


def _strip_ns(tag: str) -> str:
    return tag.split('}', 1)[-1].lower()


def _float(value, default: float = 0.0) -> float:
    if value is None:
        return default
    text = str(value).strip()
    # Supports values like "10mm", "20px", "5.5"
    match = re.match(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", text)
    if not match:
        return default
    try:
        return float(match.group(0))
    except ValueError:
        return default


def _points_from_attr(value: str | None) -> List[Point]:
    if not value:
        return []
    numbers = [float(x) for x in re.findall(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", value)]
    return list(zip(numbers[0::2], numbers[1::2]))


def _svg_height(root: ET.Element) -> float:
    view_box = root.attrib.get("viewBox") or root.attrib.get("viewbox")
    if view_box:
        nums = [float(x) for x in re.findall(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", view_box)]
        if len(nums) == 4:
            return nums[3]
    return _float(root.attrib.get("height"), 100.0)


def _to_dxf_point(point: Point, svg_height: float) -> Point:
    x, y = point
    return (float(x), float(svg_height - y))


def _approx_ellipse(cx: float, cy: float, rx: float, ry: float, segments: int = 96) -> List[Point]:
    return [
        (cx + rx * math.cos(2 * math.pi * i / segments), cy + ry * math.sin(2 * math.pi * i / segments))
        for i in range(segments + 1)
    ]


def _approx_arc(cx: float, cy: float, r: float, start_deg: float, end_deg: float, segments: int = 48) -> List[Point]:
    # DXF ARC degrees are counter-clockwise. SVG y-axis will be inverted later in dxf_to_svg.
    if end_deg < start_deg:
        end_deg += 360
    span = end_deg - start_deg
    count = max(6, int(segments * span / 360))
    pts: List[Point] = []
    for i in range(count + 1):
        a = math.radians(start_deg + span * i / count)
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def simple_svg_to_dxf(svg_path: str | Path, dxf_path: str | Path, *, curve_steps: int = 80) -> dict:
    """Convert common SVG geometry into DXF polylines/circles.

    This intentionally supports a safe subset for laser workflows: path, line, rect,
    circle, ellipse, polyline and polygon. Complex transforms, masks, effects and
    embedded raster images are ignored in V1.
    """
    svg_path = Path(svg_path)
    dxf_path = Path(dxf_path)

    tree = ET.parse(svg_path)
    root = tree.getroot()
    height = _svg_height(root)

    doc = ezdxf.new("R2010")
    doc.units = ezdxf.units.MM
    msp = doc.modelspace()

    counts = {
        "line": 0,
        "rect": 0,
        "circle": 0,
        "ellipse": 0,
        "polyline": 0,
        "polygon": 0,
        "path": 0,
        "ignored": 0,
    }

    for elem in root.iter():
        tag = _strip_ns(elem.tag)
        a = elem.attrib

        try:
            if tag == "line":
                p1 = _to_dxf_point((_float(a.get("x1")), _float(a.get("y1"))), height)
                p2 = _to_dxf_point((_float(a.get("x2")), _float(a.get("y2"))), height)
                msp.add_line(p1, p2)
                counts["line"] += 1

            elif tag == "rect":
                x, y = _float(a.get("x")), _float(a.get("y"))
                w, h = _float(a.get("width")), _float(a.get("height"))
                pts = [(x, y), (x + w, y), (x + w, y + h), (x, y + h), (x, y)]
                msp.add_lwpolyline([_to_dxf_point(p, height) for p in pts], close=True)
                counts["rect"] += 1

            elif tag == "circle":
                cx, cy, r = _float(a.get("cx")), _float(a.get("cy")), _float(a.get("r"))
                center = _to_dxf_point((cx, cy), height)
                msp.add_circle(center, r)
                counts["circle"] += 1

            elif tag == "ellipse":
                cx, cy = _float(a.get("cx")), _float(a.get("cy"))
                rx, ry = _float(a.get("rx")), _float(a.get("ry"))
                pts = [_to_dxf_point(p, height) for p in _approx_ellipse(cx, cy, rx, ry)]
                msp.add_lwpolyline(pts, close=True)
                counts["ellipse"] += 1

            elif tag in {"polyline", "polygon"}:
                pts = _points_from_attr(a.get("points"))
                if len(pts) >= 2:
                    dxf_pts = [_to_dxf_point(p, height) for p in pts]
                    close = tag == "polygon"
                    msp.add_lwpolyline(dxf_pts, close=close)
                    counts[tag] += 1

            elif tag == "path":
                d = a.get("d")
                if not d:
                    counts["ignored"] += 1
                    continue
                path = parse_path(d)
                if len(path) == 0:
                    counts["ignored"] += 1
                    continue

                # Split at discontinuities approximately by generating separate chunks.
                current: List[Point] = []
                last_end = None
                for segment in path:
                    if last_end is not None and abs(segment.start - last_end) > 1e-6:
                        if len(current) >= 2:
                            msp.add_lwpolyline([_to_dxf_point(p, height) for p in current])
                        current = []

                    if not current:
                        current.append((segment.start.real, segment.start.imag))
                    steps = 1 if segment.__class__.__name__ == "Line" else max(8, curve_steps // max(1, len(path)))
                    for i in range(1, steps + 1):
                        z = segment.point(i / steps)
                        current.append((z.real, z.imag))
                    last_end = segment.end

                if len(current) >= 2:
                    # If the path appears closed, close it.
                    close = math.dist(current[0], current[-1]) < 1e-3
                    msp.add_lwpolyline([_to_dxf_point(p, height) for p in current], close=close)
                counts["path"] += 1

        except Exception:
            counts["ignored"] += 1

    dxf_path.parent.mkdir(parents=True, exist_ok=True)
    doc.saveas(dxf_path)
    return counts


def _collect_dxf_points(entity) -> List[Point]:
    etype = entity.dxftype()
    if etype == "LINE":
        return [(entity.dxf.start.x, entity.dxf.start.y), (entity.dxf.end.x, entity.dxf.end.y)]
    if etype == "LWPOLYLINE":
        return [(p[0], p[1]) for p in entity.get_points()]
    if etype == "POLYLINE":
        return [(v.dxf.location.x, v.dxf.location.y) for v in entity.vertices]
    if etype == "CIRCLE":
        c = entity.dxf.center
        r = float(entity.dxf.radius)
        return [(c.x - r, c.y - r), (c.x + r, c.y + r)]
    if etype == "ARC":
        c = entity.dxf.center
        r = float(entity.dxf.radius)
        return [(c.x - r, c.y - r), (c.x + r, c.y + r)]
    return []


def dxf_to_svg(dxf_path: str | Path, svg_path: str | Path, *, padding: float = 5.0) -> dict:
    """Render common DXF entities to simple SVG for preview/export."""
    dxf_path = Path(dxf_path)
    svg_path = Path(svg_path)
    doc = ezdxf.readfile(dxf_path)
    msp = doc.modelspace()

    supported = []
    all_points: List[Point] = []
    counts = {"line": 0, "polyline": 0, "circle": 0, "arc": 0, "ignored": 0}

    for entity in msp:
        etype = entity.dxftype()
        if etype in {"LINE", "LWPOLYLINE", "POLYLINE", "CIRCLE", "ARC"}:
            supported.append(entity)
            all_points.extend(_collect_dxf_points(entity))
        else:
            counts["ignored"] += 1

    if not all_points:
        min_x, min_y, max_x, max_y = 0.0, 0.0, 100.0, 100.0
    else:
        xs, ys = zip(*all_points)
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)

    width = max(1.0, max_x - min_x + padding * 2)
    height = max(1.0, max_y - min_y + padding * 2)

    def tx(x: float) -> float:
        return x - min_x + padding

    def ty(y: float) -> float:
        # Flip Y for SVG coordinates
        return max_y - y + padding

    elements: List[str] = []
    for entity in supported:
        etype = entity.dxftype()
        if etype == "LINE":
            s, e = entity.dxf.start, entity.dxf.end
            elements.append(
                f'<line x1="{tx(s.x):.3f}" y1="{ty(s.y):.3f}" x2="{tx(e.x):.3f}" y2="{ty(e.y):.3f}" />'
            )
            counts["line"] += 1
        elif etype == "LWPOLYLINE":
            pts = [(tx(p[0]), ty(p[1])) for p in entity.get_points()]
            data = " ".join(f"{x:.3f},{y:.3f}" for x, y in pts)
            tag = "polygon" if entity.closed else "polyline"
            elements.append(f'<{tag} points="{data}" />')
            counts["polyline"] += 1
        elif etype == "POLYLINE":
            pts = [(tx(v.dxf.location.x), ty(v.dxf.location.y)) for v in entity.vertices]
            data = " ".join(f"{x:.3f},{y:.3f}" for x, y in pts)
            tag = "polygon" if entity.is_closed else "polyline"
            elements.append(f'<{tag} points="{data}" />')
            counts["polyline"] += 1
        elif etype == "CIRCLE":
            c = entity.dxf.center
            r = float(entity.dxf.radius)
            elements.append(f'<circle cx="{tx(c.x):.3f}" cy="{ty(c.y):.3f}" r="{r:.3f}" />')
            counts["circle"] += 1
        elif etype == "ARC":
            c = entity.dxf.center
            r = float(entity.dxf.radius)
            pts = _approx_arc(c.x, c.y, r, float(entity.dxf.start_angle), float(entity.dxf.end_angle))
            data = " ".join(f"{tx(x):.3f},{ty(y):.3f}" for x, y in pts)
            elements.append(f'<polyline points="{data}" />')
            counts["arc"] += 1

    svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{width:.3f}mm" height="{height:.3f}mm" viewBox="0 0 {width:.3f} {height:.3f}">
  <rect width="100%" height="100%" fill="white"/>
  <g fill="none" stroke="black" stroke-width="0.2" stroke-linecap="round" stroke-linejoin="round">
    {chr(10).join(elements)}
  </g>
</svg>
'''
    svg_path.parent.mkdir(parents=True, exist_ok=True)
    svg_path.write_text(svg, encoding="utf-8")
    return counts


def _polyline_from_entity_for_preview(entity, arc_segments: int = 72) -> list[list[Point]]:
    """Return drawable 2D polylines for common DXF entities.

    This is intentionally independent from Inkscape so DXF previews work on a clean
    Windows install. It supports the geometry most common in laser files and tries
    virtual entities for inserts/bulged polylines when ezdxf can provide them.
    """
    etype = entity.dxftype()

    # Try virtual entities first for INSERTs and bulged polylines.
    if etype in {"INSERT", "LWPOLYLINE", "POLYLINE"}:
        try:
            virtual_lines: list[list[Point]] = []
            for virtual in entity.virtual_entities():
                virtual_lines.extend(_polyline_from_entity_for_preview(virtual, arc_segments=arc_segments))
            if virtual_lines:
                return virtual_lines
        except Exception:
            pass

    if etype == "LINE":
        s, e = entity.dxf.start, entity.dxf.end
        return [[(float(s.x), float(s.y)), (float(e.x), float(e.y))]]

    if etype == "LWPOLYLINE":
        pts = [(float(p[0]), float(p[1])) for p in entity.get_points()]
        if entity.closed and pts and pts[0] != pts[-1]:
            pts.append(pts[0])
        return [pts] if len(pts) >= 2 else []

    if etype == "POLYLINE":
        pts = [(float(v.dxf.location.x), float(v.dxf.location.y)) for v in entity.vertices]
        if entity.is_closed and pts and pts[0] != pts[-1]:
            pts.append(pts[0])
        return [pts] if len(pts) >= 2 else []

    if etype == "CIRCLE":
        c = entity.dxf.center
        r = float(entity.dxf.radius)
        pts = [
            (float(c.x + r * math.cos(2 * math.pi * i / arc_segments)),
             float(c.y + r * math.sin(2 * math.pi * i / arc_segments)))
            for i in range(arc_segments + 1)
        ]
        return [pts]

    if etype == "ARC":
        c = entity.dxf.center
        r = float(entity.dxf.radius)
        return [_approx_arc(float(c.x), float(c.y), r, float(entity.dxf.start_angle), float(entity.dxf.end_angle), segments=arc_segments)]

    if etype in {"ELLIPSE", "SPLINE"}:
        # Many laser DXFs contain splines/ellipses. ezdxf can flatten several of these.
        try:
            pts = [(float(p.x), float(p.y)) for p in entity.flattening(0.2)]
            return [pts] if len(pts) >= 2 else []
        except Exception:
            return []

    return []


def dxf_to_png_preview(
    dxf_path: str | Path,
    png_path: str | Path,
    *,
    max_size_px: int = 1800,
    padding_px: int = 60,
    line_width: int | None = None,
) -> dict:
    """Create a quick PNG preview of a DXF without Inkscape.

    It is not meant to be a perfect CAD renderer; it is a practical preview for
    common laser files. The actual conversion DXF→SVG/PDF still uses the vector
    path implemented in dxf_to_svg().
    """
    from PIL import Image, ImageDraw

    dxf_path = Path(dxf_path)
    png_path = Path(png_path)
    doc = ezdxf.readfile(dxf_path)
    msp = doc.modelspace()

    polylines: list[list[Point]] = []
    counts = {
        "line": 0,
        "polyline": 0,
        "circle": 0,
        "arc": 0,
        "ellipse_or_spline": 0,
        "insert_or_virtual": 0,
        "ignored": 0,
    }

    for entity in msp:
        etype = entity.dxftype()
        lines = _polyline_from_entity_for_preview(entity)
        if not lines:
            counts["ignored"] += 1
            continue
        polylines.extend(lines)
        if etype == "LINE":
            counts["line"] += 1
        elif etype in {"LWPOLYLINE", "POLYLINE"}:
            counts["polyline"] += 1
        elif etype == "CIRCLE":
            counts["circle"] += 1
        elif etype == "ARC":
            counts["arc"] += 1
        elif etype in {"ELLIPSE", "SPLINE"}:
            counts["ellipse_or_spline"] += 1
        elif etype == "INSERT":
            counts["insert_or_virtual"] += 1

    all_points = [p for line in polylines for p in line]
    if not all_points:
        raise ValueError("El DXF no tiene entidades compatibles para previsualizar en V1.2.")

    xs, ys = zip(*all_points)
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    model_w = max(max_x - min_x, 1e-6)
    model_h = max(max_y - min_y, 1e-6)

    available = max(200, max_size_px - padding_px * 2)
    scale = min(available / model_w, available / model_h)
    canvas_w = int(max(240, min(max_size_px, model_w * scale + padding_px * 2)))
    canvas_h = int(max(240, min(max_size_px, model_h * scale + padding_px * 2)))

    def sx(x: float) -> float:
        return (x - min_x) * scale + padding_px

    def sy(y: float) -> float:
        return (max_y - y) * scale + padding_px

    img = Image.new("RGB", (canvas_w, canvas_h), "white")
    draw = ImageDraw.Draw(img)
    lw = line_width if line_width is not None else max(1, int(max(canvas_w, canvas_h) / 900))

    for line in polylines:
        if len(line) < 2:
            continue
        pts = [(sx(x), sy(y)) for x, y in line]
        try:
            draw.line(pts, fill=(15, 23, 42), width=lw, joint="curve")
        except TypeError:
            draw.line(pts, fill=(15, 23, 42), width=lw)

    png_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(png_path)
    counts["drawable_polylines"] = len(polylines)
    counts["canvas_px"] = f"{canvas_w}x{canvas_h}"
    return counts
