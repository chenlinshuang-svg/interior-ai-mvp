#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt


def draw_segment(ax, item, color, linewidth, label=None):
    if "start" in item and "end" in item:
        xs = [item["start"][0], item["end"][0]]
        ys = [item["start"][1], item["end"][1]]
        ax.plot(xs, ys, color=color, linewidth=linewidth, label=label)
    elif "center" in item:
        ax.scatter([item["center"][0]], [item["center"][1]], color=color, s=35, label=label)


def generate(project_json: Path, output_png: Path) -> None:
    project = json.loads(project_json.read_text(encoding="utf-8"))
    fig, ax = plt.subplots(figsize=(10, 8))

    used = set()
    for wall in project.get("walls", []):
        draw_segment(ax, wall, "#d62728", 2.5, None if "wall" in used else "wall")
        used.add("wall")
    for door in project.get("doors", []):
        draw_segment(ax, door, "#1f77b4", 3.0, None if "door" in used else "door")
        used.add("door")
    for window in project.get("windows", []):
        draw_segment(ax, window, "#2ca02c", 3.0, None if "window" in used else "window")
        used.add("window")
    for room in project.get("rooms", []):
        p = room.get("label_position")
        if p:
            ax.text(p[0], p[1], f"{room.get('name','')}\n{room.get('type','unknown')}", fontsize=9, color="#9467bd")
            ax.scatter([p[0]], [p[1]], color="#9467bd", s=20)

    bbox = project.get("meta", {}).get("bbox") or {}
    title = f"plan preview | validation={project.get('validation', {}).get('status', 'unchecked')}"
    if bbox:
        title += f" | {bbox.get('width')} x {bbox.get('height')} mm"
    ax.set_title(title)
    ax.set_aspect("equal", adjustable="box")
    ax.grid(True, linewidth=0.4)
    if used:
        ax.legend(loc="best")
    output_png.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(output_png, dpi=180)
    plt.close(fig)
    print(f"preview: {output_png}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("project_json")
    parser.add_argument("output_png")
    args = parser.parse_args()
    generate(Path(args.project_json), Path(args.output_png))


if __name__ == "__main__":
    main()
