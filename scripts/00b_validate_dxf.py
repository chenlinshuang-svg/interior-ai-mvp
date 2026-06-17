#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import ezdxf

REQUIRED_LAYERS = {"WALL", "DOOR", "WINDOW", "ROOM_TEXT"}
POINT_TYPES = {"LINE", "LWPOLYLINE", "POLYLINE", "ARC", "CIRCLE", "INSERT", "TEXT", "MTEXT"}


def add_point(points: list[tuple[float, float, float]], p) -> None:
    points.append((float(p.x), float(p.y), float(getattr(p, "z", 0) or 0)))


def collect_points(entity, points) -> None:
    t = entity.dxftype()
    try:
        if t == "LINE":
            add_point(points, entity.dxf.start)
            add_point(points, entity.dxf.end)
        elif t == "LWPOLYLINE":
            for p in entity.get_points("xy"):
                points.append((float(p[0]), float(p[1]), 0.0))
        elif t == "POLYLINE":
            for v in entity.vertices:
                add_point(points, v.dxf.location)
        elif hasattr(entity.dxf, "insert"):
            add_point(points, entity.dxf.insert)
        elif hasattr(entity.dxf, "center"):
            add_point(points, entity.dxf.center)
    except Exception:
        pass


def validate(input_dxf: Path, output_json: Path) -> int:
    doc = ezdxf.readfile(input_dxf)
    msp = doc.modelspace()
    layers = {e.dxf.layer for e in msp if hasattr(e.dxf, "layer")}
    by_layer: dict[str, int] = {}
    by_type: dict[str, int] = {}
    points: list[tuple[float, float, float]] = []
    nonzero_z = 0

    for e in msp:
        layer = e.dxf.layer if hasattr(e.dxf, "layer") else ""
        by_layer[layer] = by_layer.get(layer, 0) + 1
        by_type[e.dxftype()] = by_type.get(e.dxftype(), 0) + 1
        if e.dxftype() in POINT_TYPES:
            before = len(points)
            collect_points(e, points)
            if any(abs(p[2]) > 1e-6 for p in points[before:]):
                nonzero_z += 1

    warnings: list[str] = []
    errors: list[str] = []
    missing = sorted(REQUIRED_LAYERS - layers)
    if "WALL" not in layers:
        errors.append("Missing required WALL layer after standardization.")
    for layer in missing:
        if layer != "WALL":
            warnings.append(f"Missing optional semantic layer: {layer}")
    if nonzero_z:
        warnings.append(f"{nonzero_z} entities still have non-zero Z values.")

    bbox = None
    if points:
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        bbox = {"min_x": min(xs), "min_y": min(ys), "max_x": max(xs), "max_y": max(ys)}
        width = bbox["max_x"] - bbox["min_x"]
        height = bbox["max_y"] - bbox["min_y"]
        size = max(width, height)
        if size > 100000:
            warnings.append("Plan extents are very large; coordinates may be far from origin or units may be wrong.")
        if 0 < size < 1000:
            warnings.append("Plan extents are very small; DXF may be in meters or centimeters instead of millimeters.")
    else:
        errors.append("No usable geometry points found.")

    report = {
        "input": str(input_dxf),
        "status": "error" if errors else ("warning" if warnings else "ok"),
        "layers": sorted(layers),
        "by_layer": by_layer,
        "by_type": by_type,
        "bbox": bbox,
        "warnings": warnings,
        "errors": errors,
    }
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"DXF validation: {report['status']} -> {output_json}")
    return 1 if errors else 0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_dxf")
    parser.add_argument("output_json")
    args = parser.parse_args()
    raise SystemExit(validate(Path(args.input_dxf), Path(args.output_json)))


if __name__ == "__main__":
    main()
