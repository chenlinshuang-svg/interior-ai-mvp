#!/usr/bin/env python3
"""Parse standardized DXF into project.json."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import ezdxf

DEFAULTS = {
    "unit": "mm",
    "floor_height": 2800,
    "default_wall_thickness": 200,
    "default_wall_height": 2800,
    "default_window_sill_height": 900,
    "default_window_height": 1200,
}


def point2(p) -> list[float]:
    return [round(float(p[0]), 3), round(float(p[1]), 3)]


def line_record(entity, layer: str, index: int, kind: str) -> dict[str, Any] | None:
    if entity.dxftype() == "LINE":
        start = point2(entity.dxf.start)
        end = point2(entity.dxf.end)
    elif entity.dxftype() in {"LWPOLYLINE", "POLYLINE"}:
        pts = []
        if entity.dxftype() == "LWPOLYLINE":
            pts = [point2((p[0], p[1])) for p in entity.get_points()]
        else:
            pts = [point2(v.dxf.location) for v in entity.vertices]
        if len(pts) < 2:
            return None
        return {
            "id": f"{kind}_{index:04d}",
            "kind": kind,
            "layer": layer,
            "polyline": pts,
        }
    else:
        return None

    return {
        "id": f"{kind}_{index:04d}",
        "kind": kind,
        "layer": layer,
        "start": start,
        "end": end,
    }


def text_record(entity, index: int) -> dict[str, Any] | None:
    if entity.dxftype() == "TEXT":
        text = entity.dxf.text
        location = point2(entity.dxf.insert)
    elif entity.dxftype() == "MTEXT":
        text = entity.text
        location = point2(entity.dxf.insert)
    else:
        return None
    return {"id": f"room_{index:04d}", "name": str(text).strip(), "type": "unknown", "label_position": location, "polygon": []}


def parse_dxf(input_path: Path, output_path: Path) -> None:
    doc = ezdxf.readfile(input_path)
    msp = doc.modelspace()

    walls: list[dict[str, Any]] = []
    doors: list[dict[str, Any]] = []
    windows: list[dict[str, Any]] = []
    rooms: list[dict[str, Any]] = []

    counts = {"wall": 1, "door": 1, "window": 1, "room": 1}

    for entity in msp:
        layer = entity.dxf.layer.upper()
        if layer == "WALL":
            rec = line_record(entity, layer, counts["wall"], "wall")
            if rec:
                rec.setdefault("thickness", DEFAULTS["default_wall_thickness"])
                rec.setdefault("height", DEFAULTS["default_wall_height"])
                walls.append(rec)
                counts["wall"] += 1
        elif layer == "DOOR":
            rec = line_record(entity, layer, counts["door"], "door")
            if rec:
                doors.append(rec)
                counts["door"] += 1
        elif layer == "WINDOW":
            rec = line_record(entity, layer, counts["window"], "window")
            if rec:
                rec.setdefault("sill_height", DEFAULTS["default_window_sill_height"])
                rec.setdefault("height", DEFAULTS["default_window_height"])
                windows.append(rec)
                counts["window"] += 1
        elif layer == "ROOM_TEXT":
            rec = text_record(entity, counts["room"])
            if rec:
                rooms.append(rec)
                counts["room"] += 1

    project = {
        "meta": {
            "unit": DEFAULTS["unit"],
            "source_file": str(input_path),
            "floor_height": DEFAULTS["floor_height"],
        },
        "rooms": rooms,
        "walls": walls,
        "doors": doors,
        "windows": windows,
        "furniture": [],
        "style": {},
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(project, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"project json: {output_path}")
    print(f"rooms={len(rooms)}, walls={len(walls)}, doors={len(doors)}, windows={len(windows)}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_dxf")
    parser.add_argument("output_json")
    args = parser.parse_args()
    parse_dxf(Path(args.input_dxf), Path(args.output_json))


if __name__ == "__main__":
    main()
