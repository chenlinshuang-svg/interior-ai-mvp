#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import ezdxf

ROOT = Path(__file__).resolve().parents[1]
DEFAULTS_PATH = ROOT / "config" / "defaults.json"
ROOM_TYPES = {
    "客厅": "living_room", "起居室": "living_room",
    "餐厅": "dining_room", "卧室": "bedroom", "主卧": "bedroom", "次卧": "bedroom",
    "厨房": "kitchen", "卫生间": "bathroom", "洗手间": "bathroom", "阳台": "balcony",
    "书房": "study", "玄关": "entry", "走廊": "corridor"
}


def defaults() -> dict:
    if DEFAULTS_PATH.exists():
        return json.loads(DEFAULTS_PATH.read_text(encoding="utf-8"))
    return {"unit": "mm", "floor_height": 2800, "wall_height": 2800, "wall_thickness": 200, "door_width": 900, "door_height": 2100, "window_width": 1200, "window_height": 1200, "window_sill_height": 900, "blender_unit_scale": 0.001}


def p2(v) -> list[float]:
    return [round(float(v[0]), 3), round(float(v[1]), 3)]


def dist(a: list[float], b: list[float]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def line_len(start: list[float], end: list[float]) -> float:
    return dist(start, end)


def center_of(points: list[list[float]]) -> list[float]:
    return [round(sum(p[0] for p in points) / len(points), 3), round(sum(p[1] for p in points) / len(points), 3)]


def poly_points(entity) -> list[list[float]]:
    if entity.dxftype() == "LWPOLYLINE":
        return [p2((p[0], p[1])) for p in entity.get_points()]
    if entity.dxftype() == "POLYLINE":
        return [p2(v.dxf.location) for v in entity.vertices]
    return []


def segment_records(entity, kind: str, idx: int, d: dict) -> list[dict[str, Any]]:
    layer = entity.dxf.layer
    records: list[dict[str, Any]] = []
    if entity.dxftype() == "LINE":
        start, end = p2(entity.dxf.start), p2(entity.dxf.end)
        if line_len(start, end) > 1:
            records.append({"id": f"{kind}_{idx:04d}", "kind": kind, "source_layer": layer, "start": start, "end": end})
    elif entity.dxftype() in {"LWPOLYLINE", "POLYLINE"}:
        pts = poly_points(entity)
        for i in range(len(pts) - 1):
            if line_len(pts[i], pts[i + 1]) > 1:
                records.append({"id": f"{kind}_{idx:04d}_{i:02d}", "kind": kind, "source_layer": layer, "start": pts[i], "end": pts[i + 1]})
    elif entity.dxftype() == "INSERT":
        c = p2(entity.dxf.insert)
        width = d.get("door_width" if kind == "door" else "window_width", 900)
        records.append({"id": f"{kind}_{idx:04d}", "kind": kind, "source_layer": layer, "block_name": entity.dxf.name, "center": c, "width": width, "rotation": float(getattr(entity.dxf, "rotation", 0) or 0)})
    return records


def text_record(entity, idx: int) -> dict[str, Any] | None:
    if entity.dxftype() == "TEXT":
        text = str(entity.dxf.text).strip()
        loc = p2(entity.dxf.insert)
    elif entity.dxftype() == "MTEXT":
        text = str(entity.text).strip()
        loc = p2(entity.dxf.insert)
    else:
        return None
    if not text:
        return None
    rtype = "unknown"
    for key, value in ROOM_TYPES.items():
        if key in text:
            rtype = value
            break
    return {"id": f"room_{idx:04d}", "name": text, "type": rtype, "label_position": loc, "polygon": [], "confidence": 0.8 if rtype != "unknown" else 0.3, "needs_manual_review": rtype == "unknown"}


def normalize(project: dict) -> None:
    points: list[list[float]] = []
    for w in project["walls"]:
        points.extend([w["start"], w["end"]])
    for group in ("doors", "windows"):
        for item in project[group]:
            if "start" in item:
                points.extend([item["start"], item["end"]])
            elif "center" in item:
                points.append(item["center"])
    for r in project["rooms"]:
        points.append(r["label_position"])
    if not points:
        project["meta"]["origin_offset"] = [0, 0]
        project["meta"]["bbox"] = None
        return
    min_x, min_y = min(p[0] for p in points), min(p[1] for p in points)
    max_x, max_y = max(p[0] for p in points), max(p[1] for p in points)
    for p in points:
        p[0] = round(p[0] - min_x, 3)
        p[1] = round(p[1] - min_y, 3)
    project["meta"]["origin_offset"] = [round(min_x, 3), round(min_y, 3)]
    project["meta"]["bbox"] = {"width": round(max_x - min_x, 3), "height": round(max_y - min_y, 3)}


def parse_dxf(input_path: Path, output_path: Path) -> None:
    d = defaults()
    doc = ezdxf.readfile(input_path)
    walls: list[dict[str, Any]] = []
    doors: list[dict[str, Any]] = []
    windows: list[dict[str, Any]] = []
    rooms: list[dict[str, Any]] = []
    raw_entities: list[dict[str, Any]] = []
    counters = {"wall": 1, "door": 1, "window": 1, "room": 1}

    for entity in doc.modelspace():
        layer = (entity.dxf.layer if hasattr(entity.dxf, "layer") else "").upper()
        raw_entities.append({"type": entity.dxftype(), "layer": layer})
        if layer == "WALL":
            for rec in segment_records(entity, "wall", counters["wall"], d):
                rec.update({"thickness": d["wall_thickness"], "height": d.get("wall_height", d["floor_height"]), "confidence": 0.9})
                walls.append(rec)
                counters["wall"] += 1
        elif layer == "DOOR":
            for rec in segment_records(entity, "door", counters["door"], d):
                rec.update({"height": d["door_height"], "confidence": 0.75})
                doors.append(rec)
                counters["door"] += 1
        elif layer == "WINDOW":
            for rec in segment_records(entity, "window", counters["window"], d):
                rec.update({"height": d["window_height"], "sill_height": d["window_sill_height"], "confidence": 0.75})
                windows.append(rec)
                counters["window"] += 1
        elif layer == "ROOM_TEXT":
            rec = text_record(entity, counters["room"])
            if rec:
                rooms.append(rec)
                counters["room"] += 1

    project = {
        "meta": {"project_name": "室内设计：从 CAD 到 3D 效果图设计", "unit": "mm", "blender_unit_scale": d["blender_unit_scale"], "source_file": str(input_path), "floor_height": d["floor_height"]},
        "validation": {"status": "unchecked", "warnings": [], "errors": []},
        "rooms": rooms,
        "walls": walls,
        "doors": doors,
        "windows": windows,
        "furniture": [],
        "style": {},
        "raw_entities_summary": raw_entities,
    }
    normalize(project)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(project, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"project raw json: {output_path}")
    print(f"rooms={len(rooms)}, walls={len(walls)}, doors={len(doors)}, windows={len(windows)}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_dxf")
    parser.add_argument("output_json")
    args = parser.parse_args()
    parse_dxf(Path(args.input_dxf), Path(args.output_json))


if __name__ == "__main__":
    main()
