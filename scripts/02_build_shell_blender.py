#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import bpy

MM = 0.001


def to_m(v):
    return float(v) * MM


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def mat(name, color):
    m = bpy.data.materials.new(name)
    m.diffuse_color = color
    return m


def cube(name, loc, scale, material):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(material)
    return obj


def wall_obj(wall, material):
    s = wall.get("start")
    e = wall.get("end")
    if not s or not e:
        return
    x1, y1 = to_m(s[0]), to_m(s[1])
    x2, y2 = to_m(e[0]), to_m(e[1])
    dx, dy = x2 - x1, y2 - y1
    length = math.hypot(dx, dy)
    if length < 0.01:
        return
    height = to_m(wall.get("height", 2800))
    thick = to_m(wall.get("thickness", 200))
    obj = cube(wall.get("id", "wall"), ((x1 + x2) / 2, (y1 + y2) / 2, height / 2), (length, thick, height), material)
    obj.rotation_euler[2] = math.atan2(dy, dx)


def bounds(project):
    xs, ys = [], []
    for w in project.get("walls", []):
        for p in [w.get("start"), w.get("end")]:
            if p:
                xs.append(to_m(p[0]))
                ys.append(to_m(p[1]))
    if not xs:
        return -2, -2, 2, 2
    return min(xs), min(ys), max(xs), max(ys)


def build(project):
    clear_scene()
    wall_m = mat("wall_white", (0.85, 0.85, 0.82, 1))
    floor_m = mat("floor_grey", (0.55, 0.55, 0.55, 1))
    marker_m = mat("opening_marker", (0.2, 0.5, 1, 1))
    minx, miny, maxx, maxy = bounds(project)
    cx, cy = (minx + maxx) / 2, (miny + maxy) / 2
    cube("Floor", (cx, cy, -0.01), (maxx - minx + 0.4, maxy - miny + 0.4, 0.02), floor_m)
    for wall in project.get("walls", []):
        wall_obj(wall, wall_m)
    for group in ["doors", "windows"]:
        for item in project.get(group, []):
            s = item.get("start")
            e = item.get("end")
            if s and e:
                cube(item.get("id", group), (to_m((s[0] + e[0]) / 2), to_m((s[1] + e[1]) / 2), 1.2), (0.8, 0.08, 1.8), marker_m)


def main():
    args = sys.argv[sys.argv.index("--") + 1:]
    project = json.loads(Path(args[0]).read_text(encoding="utf-8"))
    build(project)
    bpy.ops.wm.save_as_mainfile(filepath=str(Path(args[1])))


if __name__ == "__main__":
    main()
