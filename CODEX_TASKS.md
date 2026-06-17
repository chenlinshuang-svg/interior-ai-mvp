# Codex 任务

当前只做 Phase 0、Phase 1、Phase 2，不做家具、风格、灯光、网页。

## 核心原则

Blender 不直接导入 CAD。CAD 先经过标准化、语义解析和校验，最终只让 Blender 读取 `output/project.json`。

## 当前流程

```bash
pip install -r requirements.txt
python run_phase1_2.py input/house.dxf --skip-blender
```

有 Blender 时：

```bash
python run_phase1_2.py input/house.dxf
```

## Codex 优先检查

1. `output/standardized/*_standardized.dxf` 是否只剩 WALL、DOOR、WINDOW、ROOM_TEXT。
2. `output/diagnostics/dxf_report.json` 是否有 error。
3. `output/project_raw.json` 是否提取到 walls、doors、windows、rooms。
4. `output/project.json` 是否完成坐标归一化和门窗匹配。
5. `output/diagnostics/plan_preview.png` 是否能在二维图中看出墙、门、窗、房间名。
6. 只有前面都合理，才运行 Blender 生成 `output/shell.blend`。

## 本阶段必须提前规避的问题

- 图层名称不统一。
- 门窗是 INSERT/BLOCK 而不是 LINE。
- CAD 单位错误。
- 坐标离原点太远。
- Z 值不为 0 导致错层。
- 标注线、吊顶线、家具线误识别为墙。
- 墙线断开或房间不闭合。
- 门窗离墙太远，Blender 无法开洞。
- 房间文字无法识别。

## 当前不要做

- 不要开发真实家具库。
- 不要开发风格系统。
- 不要开发商业级渲染。
- 不要开发网页/App。
