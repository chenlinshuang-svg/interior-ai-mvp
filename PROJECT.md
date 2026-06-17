# 项目：室内设计：从 CAD 到 3D 效果图设计

## 当前 MVP 范围

本仓库当前只实现 Phase 0、Phase 1、Phase 2：

1. Phase 0：标准化 CAD/DXF，去除家具、吊顶、灯具、标注、水电等冗余内容，只保留墙体、门、窗、房间名称。
2. Phase 1：解析标准化后的 DXF，生成结构化 `output/project.json`。
3. Phase 2：读取 `project.json`，用 Blender Python 生成毛坯房 `output/shell.blend`。

## 暂不做

- 家具自动布局
- 风格材质生成
- 灯光相机优化
- 渲染效果图
- Web/App 页面

## 核心中间格式

整个项目围绕 `project.json`，后续家具、风格、灯光、网页都接这个格式。