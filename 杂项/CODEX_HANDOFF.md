# CODEX_HANDOFF

## Expo Android 离线启动与图标验收（2026-07-28）

### 修改文件

- `mobile/app.json` — 移除 Expo 默认蓝色箭头自适应图标，让 Android 启动器使用 `assets/images/icon.png` 中已复用的旧 Qt 笔记本图标。
- `mobile/package-lock.json` — 修正 `@emnapi/wasi-threads` 的锁定版本和 `npm-package-arg` 的镜像 URL，使腾讯 npm 源可完成确定性依赖安装。

### 真机验收

- Android 16 / HONOR ELP-AN00（`arm64-v8a`）已实际卸载旧 Qt 签名包、安装 Expo 重构版并完成两轮冷启动。
- 根因是 `assembleDebug` 不内置 `index.android.bundle`，离开 Metro 会报 `Unable to load script`；使用 `:app:assembleRelease` 后 JS bundle 已打入 APK，未再出现该错误或 Android/React Native 崩溃。
- Android 启动器生成资源已直接检查为旧 Qt 笔记本图标。

### 交付风险

- 本机验收 APK 使用 Expo 生成的 debug signing config，仅适合本机测试；面向正式用户的包仍须在 `mobile/scripts/build-release.ps1` 中提供正式 keystore、别名及密码环境变量后签名。
- 当前网络对 Google Maven/国内 Maven 的 TLS 握手不稳定。构建可在缓存完整时完成；`react-native-worklets:generateReleaseLintModel` 只在本机因下载 `androidx.documentfile` 失败，验收构建中已精确跳过该非运行时 lint 模型任务。

## 日记自动保存并发修复（2026-07-19）

### 原因与方案

- 前端旧保存请求会无条件清除 dirty，且自动、手动、切换和图片写入没有统一队列。
- `Diary.tsx` 现在用编辑版本号判断响应是否仍对应当前编辑，并通过 `SaveCoordinator` 串行化保存与图片请求；切换和新建会等待保存成功，失败时保留当前页面和 dirty。
- 后端为每个日记 ID 设置 `RLock`，正文先写入唯一 `content.<revision>.md`，再原子更新 `entry.json` 的 `body_file`。旧 `content.md` 继续可读。
- `atomic_write_text()` 使用同目录唯一临时文件，避免并发请求共用固定 `.tmp` 名，并对 Windows 短暂占用的 `os.replace()` 做有限重试。

### 新增测试与验证

- 前端：保存串行、失败恢复、旧响应失效、最新快照和空草稿规则。
- 后端：并发原子写、同记录并发保存、旧正文兼容和 metadata 失败保护。
- 实际执行：`npm run test -- --run`、`npm run build`、`python -B -m unittest discover -s tests -v`。

### 风险与回退

- 记录锁表按已访问 ID 缓存，长期运行时会缓慢增长；本轮用该有限风险换取更低的并发复杂度。
- 回退代码时需同时回退 `data_api.py`、`Diary.tsx` 和保存协调器，避免新 metadata 指向的版本化正文失去读取路径。

这份文档给下一位接手本仓库的 Codex/开发者看。当前用户最在意的是：新版 2.0 不要被旧版代码误伤，UI 风格保持现在这套 Figma 迁移后的简洁样式，功能改动要能直接落地运行。

## 当前主线

当前主版本是：

```text
diary_v2.0/
```

旧版 PySide6/Python 桌面源码仍在根目录的 `src/`、`main.py`、`data/`，主要作为历史参考。旧安装包和旧打包目录已经整理到：

```text
旧版/
```

除非用户明确要求修旧版，否则不要把改动落回旧版 UI。

## 启动方式

推荐启动入口：

```text
diary_v2.0/run_life_diary_2.0.vbs
```

这个入口用于避免启动时弹出黑色命令行窗口。`diary_v2.0/run_life_diary_2.0.bat` 仍可能显示黑框，不适合作为普通桌面启动入口。

后端入口：

```text
diary_v2.0/launcher.py
diary_v2.0/launcher.pyw
```

前端静态产物由后端本地服务加载：

```text
diary_v2.0/Untitled/dist/
```

## 2.0 目录结构

关键位置：

```text
diary_v2.0/launcher.py              # 本地 HTTP 后端、数据读写、导出、图片接口
diary_v2.0/launcher.pyw             # 无控制台启动包装
diary_v2.0/data/Diary/              # 2.0 独立数据目录
diary_v2.0/Untitled/src/            # React 前端源码
diary_v2.0/Untitled/dist/           # Vite 构建产物
diary_v2.0/Untitled/package.json    # 前端依赖和构建脚本
```

根目录 `README.md` 已经说明了新版、旧版和归档目录的关系。修改前建议先读 `README.md`。

## 数据原则

2.0 使用独立数据目录：

```text
diary_v2.0/data/Diary/
```

旧版数据目录是：

```text
data/Diary/
```

不要直接覆盖用户数据。涉及迁移、导入、批量改结构时，优先做备份或只做增量兼容。

常见数据模型：

- 日记：`entries/{id}/entry.json + content.md + images/`
- 足迹：`footprints/{id}/footprint.json + visits/{visit_id}/visit.json + thought.md + images/`
- 其他记录类模块：通常是模块目录下每条记录一个文件夹，里面一个 json 加正文或字段

## 当前功能概况

前端主路由在：

```text
diary_v2.0/Untitled/src/app/App.tsx
```

侧边栏在：

```text
diary_v2.0/Untitled/src/app/components/layouts/Sidebar.tsx
```

当前已有板块包括：

- 工作台
- 日记
- 足迹
- 轻计划
- 行动计划
- 轻思考
- 轻资源
- 信息备忘
- 自我观察
- 教训与反思
- 自我分析
- 作品感悟
- 数据管理
- AI 设置

后端模块配置在 `diary_v2.0/launcher.py` 顶部的 `MODULES`。目前代码里存在 `notes` 模块配置，但前端还没有真正把它作为新的 Markdown 信息备忘独立暴露出来。

## 最近重点改动背景

用户已经多轮要求围绕 2.0 做这些方向：

- Figma 生成 UI 已被迁移成 React/Vite 页面，用户认为当前界面整体已经好看，不要随意改审美比例。
- 日记图片支持插入、拖入、重命名、删除、排序，图片区域需要保持克制，不要把正文区域挤没。
- 日记导出支持全部导出 Word/PDF/TXT。
- 足迹支持图片，并且用户明确要求足迹应导出 Word，不是 TXT。
- 数据管理页需要保留全部导出能力。
- 启动软件和导出时尽量避免黑色命令行窗口。
- 下拉框曾出现不断变长的问题，涉及 Select/弹层时要特别留意高度、定位和滚动容器。
- 自动保存不能重置光标，也不能有明显抖动。

## 当前已知未完成/易混点

### 信息备忘与接单备忘

用户最新意图是：

- 现在这个“信息备忘”其实更像接单备忘，应改名为“接单备忘”。
- 另外新增一个真正的“信息备忘”，最好做成 Markdown 编辑器。
- 新“信息备忘”可以复用后端已有的 `notes` 模块。

当前代码状态仍需要核对后继续：

- `diary_v2.0/Untitled/src/app/pages/InfoMemo.tsx` 仍使用后端模块 `info_memos`。
- 侧边栏仍只有一个 `信息备忘` 入口，路径是 `/info-memo`。
- 后端 `MODULES` 中 `info_memos` 标签仍是 `信息备忘`，`notes` 标签是 `笔记`。
- 后端全部导出逻辑里目前会跳过 `notes`。

如果继续做这项，推荐最稳妥的落地方式：

1. 把当前 `InfoMemo.tsx` 重命名/拆成 `OrderMemo.tsx`，文案改为“接单备忘”，但继续使用 `info_memos` 数据。
2. 新建一个 `InfoMemo.tsx`，使用 `notes` 模块，做 Markdown 编辑 + 预览 + `.md` 导出。
3. 在 `App.tsx` 增加 `/order-memo` 路由，并保留 `/info-memo` 给新的 Markdown 信息备忘。
4. 在 `Sidebar.tsx` 同时显示“接单备忘”和“信息备忘”。
5. 在 `launcher.py` 中把 `info_memos` 的标签改为“接单备忘”，把 `notes` 的标签改为“信息备忘”，并让全部导出包含 `notes`。

### 前端构建产物

当前 dist 里存在：

```text
diary_v2.0/Untitled/dist/assets/index-BaQ-gy3M.js
diary_v2.0/Untitled/dist/assets/index-Vk5a6I8I.css
```

如果重新运行 Vite build，hash 文件名可能变化。构建后一定检查：

```text
diary_v2.0/Untitled/dist/index.html
```

确保它引用的 JS/CSS 文件真实存在。不要留下失配的 hash，否则软件会白屏。

## 常用开发命令

检查后端语法：

```powershell
python -B -c "import ast, pathlib; ast.parse(pathlib.Path('diary_v2.0/launcher.py').read_text(encoding='utf-8'))"
```

构建前端：

```powershell
cd diary_v2.0/Untitled
npm install
npm run build
```

构建后建议删除 `node_modules/`，避免把依赖目录留在工作区：

```powershell
Remove-Item -Recurse -Force diary_v2.0/Untitled/node_modules
```

旧版桌面测试命令仍可用于旧主线参考：

```powershell
python -B -m unittest discover -s tests -v
```

注意：这个测试主要覆盖旧版 `src/life_dairy/`，不等价于 2.0 React 页面验证。

## 改动注意事项

- 优先改 `diary_v2.0/`，不要顺手重构旧版。
- 不要移动或删除 `diary_v2.0/data/Diary/`。
- UI 改动要贴近现有 2.0 风格：浅色、克制、8px 左右圆角、工具型布局，不要做成大面积营销页。
- 图片显示不要压缩原图文件；展示可以控制尺寸，但不要损坏存储的原始图片。
- 导出功能要优先使用用户设置的导出目录。
- 批量导出要导出全部记录，而不是当前选中一条。
- Word/PDF 导出涉及图片时，注意图片标题和图片不要跨页分离。
- Windows 上避免黑框时优先使用 `.pyw` 或 `.vbs` 启动。

## 交接前自检

每次较大改动后至少做：

```powershell
git status --short
python -B -c "import ast, pathlib; ast.parse(pathlib.Path('diary_v2.0/launcher.py').read_text(encoding='utf-8'))"
```

如果改了前端：

```powershell
cd diary_v2.0/Untitled
npm install
npm run build
```

然后打开软件验证：

- 不白屏
- 侧边栏可切换
- 当前修改板块可保存
- 图片相关操作不复制出多余图片
- 导出路径、文件名、导出内容符合预期

## 推荐提交名

如果只是新增这份交接文档，推荐：

```text
docs: add Codex handoff notes for diary v2
```

如果连同信息备忘/接单备忘拆分一起提交，推荐：

```text
feat: split order memo and markdown info memo
```
