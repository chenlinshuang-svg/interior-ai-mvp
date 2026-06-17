#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import ezdxf

ROOT = Path(__file__).resolve().parents[1]
LAYER_CONFIG = ROOT / "config" / "layers.json"
SEMANTIC_LAYERS = {"WALL", "DOOR", "WINDOW", "ROOM_TEXT"}
KEEP_TYPES = {"LINE", "LWPOLYLINE", "POLYLINE", "ARC", "CIRCLE", "INSERT", "TEXT", "MTEXT"}


def load_layers() -> dict:
    if LAYER_CONFIG.exists():
        return json.loads(LAYER_CONFIG.read_text(encoding="utf-8"))
    return {
        "wall_layers": ["WALL", "A-WALL", "墙体", "墙"],
        "door_layers": ["DOOR", "A-DOOR", "门"],
        "window_layers": ["WINDOW", "A-WINDOW", "窗"],
        "room_text_layers": ["ROOM", "ROOM_TEXT", "房间名称"],
        "remove_layers": []
    }


def norm(s: str) -> str:
    return (s or "").strip().upper()


def layer_map(config: dict) -> dict[str, str]:
    mapping = {}
    for key, target in [
        ("wall_layers", "WALL"),
        ("door_layers", "DOOR"),
        ("window_layers", "WINDOW"),
        ("room_text_layers", "ROOM_TEXT"),
    ]:
        for name in config.get(key, []):
            mapping[norm(name)] = target
    return mapping


def flatten_entity(entity) -> None:
    try:
        if hasattr(entity.dxf, "start"):
            entity.dxf.start = (entity.dxf.start.x, entity.dxf.start.y, 0)
        if hasattr(entity.dxf, "end"):
            entity.dxf.end = (entity.dxf.end.x, entity.dxf.end.y, 0)
        if hasattr(entity.dxf, "insert"):
            entity.dxf.insert = (entity.dxf.insert.x, entity.dxf.insert.y, 0)
        if hasattr(entity.dxf, "center"):
            entity.dxf.center = (entity.dxf.center.x, entity.dxf.center.y, 0)
        if entity.dxftype() == "LWPOLYLINE":
            points = [(p[0], p[1], 0, 0, p[4] if len(p) > 4 else 0) for p in entity.get_points()]
            entity.set_points(points, format="xyseb")
    except Exception:
        pass


def standardize(input_path: Path, output_path: Path) -> None:
    config = load_layers()
    mapping = layer_map(config)
    remove = {norm(x) for x in config.get("remove_layers", [])}

    doc = ezdxf.readfile(input_path)
    out = ezdxf.new("R2010")
    out.units = doc.units
    out_msp = out.modelspace()

    for layer in sorted(SEMANTIC_LAYERS):
        if layer not in out.layers:
            out.layers.add(layer)

    stats = {"kept": 0, "skipped": 0, "by_type": {}, "by_layer": {}, "removed_layers": sorted(remove)}
    for entity in doc.modelspace():
        source_layer = entity.dxf.layer if hasattr(entity.dxf, "layer") else ""
        source_key = norm(source_layer)
        target = mapping.get(source_key)
        if source_key in remove or target is None or entity.dxftype() not in KEEP_TYPES:
            stats["skipped"] += 1
            continue
        copied = entity.copy()
        copied.dxf.layer = target
        flatten_entity(copied)
        out_msp.add_entity(copied)
        stats["kept"] += 1
        stats["by_type"][copied.dxftype()] = stats["by_type"].get(copied.dxftype(), 0) + 1
        stats["by_layer"][target] = stats["by_layer"].get(target, 0) + 1

    output_path.parent.mkdir(parents=True, exist_ok=True)
    out.saveas(output_path)
    stats_path = output_path.with_suffix(".standardize.json")
    stats_path.write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"standardized: {output_path}")
    print(f"stats: {stats_path}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_dxf")
    parser.add_argument("output_dxf")
    args = parser.parse_args()
    standardize(Path(args.input_dxf), Path(args.output_dxf))


if __name__ == "__main__":
    main()
