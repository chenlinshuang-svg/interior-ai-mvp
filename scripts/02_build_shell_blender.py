#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import bpy


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def make_mat(name, color):
    material = bpy.data.materials.new(name)
    material.diffuse_color = color
    return material


def cube(name, loc, scale, material):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(material)
    return obj


def to_m(value, scale):
    return float(value) * scale


def wall_obj(wall, material, scale):
    s, e = wall.get("start"), wall.get("end")
    if not s or not e:
        return None
    x1, y1 = to_m(s[0], scale), to_m(s[1], scale)
    x2, y2 = to_m(e[0], scale), to_m(e[1], scale)
    dx, dy = x2 - x1, y2 - y1
    length = math.hypot(dx, dy)
    if length < 0.01:
        return None
    height = to_m(wall.get("height", 2800), scale)
    thick = to_m(wall.get("thickness", 200), scale)
    obj = cube(wall.get("id", "wall"), ((x1 + x2) / 2, (y1 + y2) / 2, height / 2), (length, thick, height), material)
    obj.rotation_euler[2] = math.atan2(dy, dx)
    obj["semantic_type"] = "wall"
    obj["source_id"] = wall.get("id", "")
    return obj


def marker_obj(item, material, scale, kind):
    c = item.get("center")
    if not c and item.get("start") and item.get("end"):
        c = [(item["start"][0] + item["end"][0]) / 2, (item["start"][1] + item["end"][1]) / 2]
    if not c:
        return None
    z = 1.05 if kind == "door" else to_m(item.get("sill_height", 900), scale) + to_m(item.get("height", 1200), scale) / 2
    h = 2.1 if kind == "door" else to_m(item.get("height", 1200), scale)
    w = to_m(item.get("width", 900 if kind == "door" else 1200), scale)
    obj = cube(item.get("id", kind), (to_m(c[0], scale), to_m(c[1], scale), z), (w, 0.06, h), material)
    obj.name = f"{kind}_{item.get('id', '')}"
    obj["semantic_type"] = kind
    obj["matched_wall_id"] = item.get("matched_wall_id", "")
    return obj


def bounds(project, scale):
    xs, ys = [], []
    for wall in project.get("walls", []):
        for p in [wall.get("start"), wall.get("end")]:
            if p:
                xs.append(to_m(p[0], scale))
                ys.append(to_m(p[1], scale))
    if not xs:
        return -2, -2, 2, 2
    return min(xs), min(ys), max(xs), max(ys)


def add_camera_and_light(minx, miny, maxx, maxy):
    cx, cy = (minx + maxx) / 2, (miny + maxy) / 2
    size = max(maxx - minx, maxy - miny, 4)
    bpy.ops.object.light_add(type="AREA", location=(cx, cy, 4))
    light = bpy.context.object
    light.name = "Area_Light"
    light.data.energy = 450
    light.data.size = size
    bpy.ops.object.camera_add(location=(cx, cy - size * 1.2, size * 0.9), rotation=(math.radians(60), 0, 0))
    bpy.context.scene.camera = bpy.context.object


def build(project):
    clear_scene()
    scale = float(project.get("meta", {}).get("blender_unit_scale", 0.001))
    wall_m = make_mat("wall_white", (0.86, 0.84, 0.78, 1))
    floor_m = make_mat("floor_concrete", (0.55, 0.55, 0.52, 1))
    door_m = make_mat("door_marker_blue", (0.1, 0.35, 1.0, 0.75))
    window_m = make_mat("window_marker_green", (0.1, 0.7, 0.3, 0.75))
    minx, miny, maxx, maxy = bounds(project, scale)
    cx, cy = (minx + maxx) / 2, (miny + maxy) / 2
    floor = cube("Floor_from_project_json", (cx, cy, -0.01), (max(maxx - minx, 0.1) + 0.4, max(maxy - miny, 0.1) + 0.4, 0.02), floor_m)
    floor["semantic_type"] = "floor"
    for wall in project.get("walls", []):
        wall_obj(wall, wall_m, scale)
    for item in project.get("doors", []):
        marker_obj(item, door_m, scale, "door")
    for item in project.get("windows", []):
        marker_obj(item, window_m, scale, "window")
    add_camera_and_light(minx, miny, maxx, maxy)


def main():
    args = sys.argv[sys.argv.index("--") + 1:]
    project = json.loads(Path(args[0]).read_text(encoding="utf-8"))
    build(project)
    bpy.ops.wm.save_as_mainfile(filepath=str(Path(args[1])))


if __name__ == "__main__":
    main()
