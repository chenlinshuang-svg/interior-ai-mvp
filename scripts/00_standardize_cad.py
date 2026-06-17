#!/usr/bin/env python3
"""Standardize a DXF for the interior design MVP.

This script keeps only the basic semantic layers needed by Phase 1:
walls, doors, windows, and room names. It does not require DraftSight.
DraftSight can still be used manually before this script to convert DWG to DXF.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import ezdxf

WALL_LAYERS = {"WALL", "A-WALL", "墙体"}
DOOR_LAYERS = {"DOOR", "A-DOOR", "门"}
WINDOW_LAYERS = {"WINDOW", "A-WINDOW", "窗"}
ROOM_TEXT_LAYERS = {"ROOM", "ROOM_TEXT", "房间名称", "房间名"}
KEEP_LAYERS = WALL_LAYERS | DOOR_LAYERS | WINDOW_LAYERS | ROOM_TEXT_LAYERS


def normalize_layer(layer: str) -> str | None:
    name = (layer or "").strip()
    upper = name.upper()
    if name in WALL_LAYERS or upper in WALL_LAYERS:
        return "WALL"
    if name in DOOR_LAYERS or upper in DOOR_LAYERS:
        return "DOOR"
    if name in WINDOW_LAYERS or upper in WINDOW_LAYERS:
        return "WINDOW"
    if name in ROOM_TEXT_LAYERS or upper in ROOM_TEXT_LAYERS:
        return "ROOM_TEXT"
    return None


def copy_entity_to_modelspace(out_msp, entity, target_layer: str) -> None:
    copied = entity.copy()
    copied.dxf.layer = target_layer
    out_msp.add_entity(copied)


def standardize(input_path: Path, output_path: Path) -> None:
    doc = ezdxf.readfile(input_path)
    out = ezdxf.new("R2010")
    msp = doc.modelspace()
    out_msp = out.modelspace()

    for layer in ["WALL", "DOOR", "WINDOW", "ROOM_TEXT"]:
        if layer not in out.layers:
            out.layers.add(layer)

    kept = 0
    skipped = 0
    for entity in msp:
        target_layer = normalize_layer(entity.dxf.layer)
        if target_layer is None:
            skipped += 1
            continue
        copy_entity_to_modelspace(out_msp, entity, target_layer)
        kept += 1

    output_path.parent.mkdir(parents=True, exist_ok=True)
    out.saveas(output_path)
    print(f"standardized: {output_path}")
    print(f"kept={kept}, skipped={skipped}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_dxf")
    parser.add_argument("output_dxf")
    args = parser.parse_args()
    standardize(Path(args.input_dxf), Path(args.output_dxf))


if __name__ == "__main__":
    main()
