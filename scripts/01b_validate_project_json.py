#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULTS = json.loads((ROOT / "config" / "defaults.json").read_text(encoding="utf-8")) if (ROOT / "config" / "defaults.json").exists() else {}
MATCH_TOL = float(DEFAULTS.get("door_window_wall_match_tolerance", 150))


def distance_point_to_segment(p, a, b) -> float:
    px, py = p
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    x, y = ax + t * dx, ay + t * dy
    return math.hypot(px - x, py - y)


def center(item):
    if "center" in item:
        return item["center"]
    if "start" in item and "end" in item:
        return [(item["start"][0] + item["end"][0]) / 2, (item["start"][1] + item["end"][1]) / 2]
    return None


def nearest_wall(item, walls):
    c = center(item)
    if c is None:
        return None, None
    best = None
    best_dist = None
    for wall in walls:
        if "start" not in wall or "end" not in wall:
            continue
        d = distance_point_to_segment(c, wall["start"], wall["end"])
        if best_dist is None or d < best_dist:
            best = wall
            best_dist = d
    return best, best_dist


def validate(input_json: Path, output_json: Path, report_json: Path, keep_warnings: bool) -> int:
    project = json.loads(input_json.read_text(encoding="utf-8"))
    errors: list[str] = []
    warnings: list[str] = []

    walls = project.get("walls", [])
    doors = project.get("doors", [])
    windows = project.get("windows", [])
    rooms = project.get("rooms", [])
    bbox = project.get("meta", {}).get("bbox") or {}

    if not walls:
        errors.append("No walls found. Check CAD layer mapping and standardization.")
    if not rooms:
        warnings.append("No room names found. Add ROOM_TEXT layer or房间名称 text.")
    for room in rooms:
        if room.get("type") == "unknown":
            warnings.append(f"Room {room.get('id')} name '{room.get('name')}' could not be mapped to a known room type.")

    size = max(float(bbox.get("width", 0) or 0), float(bbox.get("height", 0) or 0))
    if size > float(DEFAULTS.get("max_reasonable_plan_size_mm", 100000)):
        warnings.append("Plan bbox is very large after normalization; units or stray entities may be wrong.")
    if 0 < size < float(DEFAULTS.get("min_reasonable_plan_size_mm", 1000)):
        warnings.append("Plan bbox is very small; CAD may be in meters or centimeters.")

    for group_name, items in [("door", doors), ("window", windows)]:
        for item in items:
            wall, d = nearest_wall(item, walls)
            if wall is None or d is None:
                warnings.append(f"{item.get('id')} cannot be matched because no usable wall exists.")
                item["matched_wall_id"] = None
                item["needs_manual_review"] = True
                continue
            item["matched_wall_id"] = wall.get("id")
            item["distance_to_wall"] = round(d, 3)
            if d > MATCH_TOL:
                warnings.append(f"{item.get('id')} is {round(d,1)}mm away from nearest wall; opening may fail in Blender.")
                item["needs_manual_review"] = True
            else:
                item["needs_manual_review"] = False

    status = "error" if errors else ("warning" if warnings else "ok")
    project["validation"] = {"status": status, "warnings": warnings, "errors": errors}
    output_json.parent.mkdir(parents=True, exist_ok=True)
    report_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(project, ensure_ascii=False, indent=2), encoding="utf-8")
    report = {"status": status, "summary": {"rooms": len(rooms), "walls": len(walls), "doors": len(doors), "windows": len(windows)}, "bbox": bbox, "warnings": warnings, "errors": errors}
    report_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Project validation: {status} -> {report_json}")
    if errors:
        return 1
    if warnings and not keep_warnings:
        return 0
    return 0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_json")
    parser.add_argument("output_json")
    parser.add_argument("report_json")
    parser.add_argument("--keep-warnings", action="store_true")
    args = parser.parse_args()
    raise SystemExit(validate(Path(args.input_json), Path(args.output_json), Path(args.report_json), args.keep_warnings))


if __name__ == "__main__":
    main()
