# 室内设计：从 CAD 到 3D 效果图设计

本仓库用于跑通 MVP：**原始 CAD/DXF → 标准化 DXF → project.json → Blender 毛坯房**。

## 为什么这样设计

Blender 不直接理解 CAD 线条的语义。CAD 里的 LINE、POLYLINE、INSERT、TEXT 只是图元，不等于墙、门、窗、房间。因此本项目把 Blender 前置为“执行器”，先用 Python 把 CAD 转成结构化 `project.json`，再让 Blender 按语义建模。

## 当前阶段

```text
Phase 0  标准化 CAD/DXF
Phase 0b 校验 standardized.dxf
Phase 1  解析 DXF → project.json
Phase 1b 校验 project.json
Phase 2b 生成 2D 诊断预览图
Phase 2  Blender 生成毛坯房 shell.blend
```

## 推荐运行

```bash
pip install -r requirements.txt
python run_phase1_2.py input/house.dxf --skip-blender
```

有 Blender 时：

```bash
python run_phase1_2.py input/house.dxf
```

## 输出文件

```text
output/standardized/house_standardized.dxf
output/project_raw.json
output/project.json
output/diagnostics/dxf_report.json
output/diagnostics/project_report.json
output/diagnostics/plan_preview.png
output/shell.blend
```

## 核心规避点

- CAD 先标准化，只保留墙、门、窗、房间名。
- 坐标统一归零，避免 Blender 离原点太远。
- 统一用 mm 存储，进入 Blender 时换算为 m。
- 所有 2D 图元强制压平到 Z=0，避免错层。
- Blender 不直接导入 CAD，只读取 `project.json`。
- 每一步都输出诊断报告，避免错误传到最后才发现。
