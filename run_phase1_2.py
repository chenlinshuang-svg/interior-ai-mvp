#!/usr/bin/env python3
"""Run Phase 0-2: CAD standardization, DXF parsing, Blender shell generation."""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def run(cmd: list[str]) -> None:
    print("$", " ".join(cmd))
    subprocess.run(cmd, check=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_dxf", help="Input DWG/DXF path. DWG must be converted to DXF first.")
    parser.add_argument("--skip-blender", action="store_true", help="Only generate standardized DXF and project.json.")
    args = parser.parse_args()

    input_path = Path(args.input_dxf)
    if not input_path.exists():
        raise FileNotFoundError(input_path)

    out_dir = ROOT / "output"
    std_dir = out_dir / "standardized"
    out_dir.mkdir(exist_ok=True)
    std_dir.mkdir(parents=True, exist_ok=True)

    stem = input_path.stem
    standardized = std_dir / f"{stem}_standardized.dxf"
    project_json = out_dir / "project.json"
    shell_blend = out_dir / "shell.blend"

    run([sys.executable, str(ROOT / "scripts" / "00_standardize_cad.py"), str(input_path), str(standardized)])
    run([sys.executable, str(ROOT / "scripts" / "01_parse_cad.py"), str(standardized), str(project_json)])

    if args.skip_blender:
        print(f"Generated {project_json}")
        return

    blender = shutil.which("blender")
    if not blender:
        print("Blender command not found. Phase 0 and Phase 1 finished.")
        print(f"Generated: {standardized}")
        print(f"Generated: {project_json}")
        return

    run([blender, "--background", "--python", str(ROOT / "scripts" / "02_build_shell_blender.py"), "--", str(project_json), str(shell_blend)])
    print(f"Generated: {shell_blend}")


if __name__ == "__main__":
    main()
