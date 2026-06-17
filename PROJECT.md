# 项目：室内设计：从 CAD 到 3D 效果图设计

## 当前 MVP 范围

本仓库当前只实现 Phase 0、Phase 1、Phase 2：

1. Phase 0：标准化 CAD/DXF，去除家具、吊顶、灯具、标注、水电等冗余内容，只保留墙体、门、窗、房间名称。
2. Phase 0b：校验标准化 DXF，检查图层、实体类型、坐标范围、Z 值异常。
3. Phase 1：解析标准化后的 DXF，生成结构化 `output/project_raw.json`。
4. Phase 1b：校验并补全 `output/project.json`，包括坐标归一化、门窗最近墙匹配、房间类型标记。
5. Phase 2b：生成 `output/diagnostics/plan_preview.png`，在进入 Blender 前确认二维语义是否正确。
6. Phase 2：读取 `project.json`，用 Blender Python 生成毛坯房 `output/shell.blend`。

## 核心原则

Blender 不直接导入 CAD。Blender 只读取 `project.json`，根据已经确定的空间语义生成模型。

## 重点规避的问题

- Blender 无法理解 CAD 线条含义。
- CAD 图层命名不统一。
- 门窗是 INSERT/BLOCK，不是简单线段。
- CAD 单位、坐标、Z 值异常导致错层、看不到模型或比例错误。
- 标注、吊顶、家具、水电线误识别为墙体。
- 门窗离墙过远导致开洞失败。

## 暂不做

- 家具自动布局
- 风格材质生成
- 灯光相机优化
- 商业级渲染效果图
- Web/App 页面

## 核心中间格式

整个项目围绕 `project.json`。后续家具、风格、灯光、网页都接这个格式，不直接接 CAD。
