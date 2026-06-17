#!/usr/bin/env python3
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
    parser = argparse.ArgumentParser(description="Run CAD standardization, validation, parsing, preview, and Blender shell generation.")
    parser.add_argument("input_dxf", help="Input DXF path. Convert DWG to DXF first.")
    parser.add_argument("--skip-blender", action="store_true", help="Stop before Blender.")
    parser.add_argument("--keep-warnings", action="store_true", help="Continue when validation reports warnings.")
    args = parser.parse_args()

    input_path = Path(args.input_dxf)
    if not input_path.exists():
        raise FileNotFoundError(input_path)

    out_dir = ROOT / "output"
    std_dir = out_dir / "standardized"
    diag_dir = out_dir / "diagnostics"
    for folder in (out_dir, std_dir, diag_dir):
        folder.mkdir(parents=True, exist_ok=True)

    stem = input_path.stem
    standardized = std_dir / f"{stem}_standardized.dxf"
    dxf_report = diag_dir / "dxf_report.json"
    project_raw = out_dir / "project_raw.json"
    project_json = out_dir / "project.json"
    project_report = diag_dir / "project_report.json"
    preview_png = diag_dir / "plan_preview.png"
    shell_blend = out_dir / "shell.blend"

    run([sys.executable, str(ROOT / "scripts" / "00_standardize_cad.py"), str(input_path), str(standardized)])
    run([sys.executable, str(ROOT / "scripts" / "00b_validate_dxf.py"), str(standardized), str(dxf_report)])
    run([sys.executable, str(ROOT / "scripts" / "01_parse_cad.py"), str(standardized), str(project_raw)])

    validate_cmd = [sys.executable, str(ROOT / "scripts" / "01b_validate_project_json.py"), str(project_raw), str(project_json), str(project_report)]
    if args.keep_warnings:
        validate_cmd.append("--keep-warnings")
    run(validate_cmd)

    run([sys.executable, str(ROOT / "scripts" / "02b_generate_plan_preview.py"), str(project_json), str(preview_png)])

    if args.skip_blender:
        print(f"Generated: {project_json}")
        print(f"Generated: {preview_png}")
        return

    blender = shutil.which("blender")
    if not blender:
        print("Blender command not found. JSON and diagnostics were generated.")
        print(f"Generated: {project_json}")
        print(f"Generated: {preview_png}")
        return

    run([blender, "--background", "--python", str(ROOT / "scripts" / "02_build_shell_blender.py"), "--", str(project_json), str(shell_blend)])
    print(f"Generated: {shell_blend}")


if __name__ == "__main__":
    main()
