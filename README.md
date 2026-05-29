# Life Diary

当前主版本是 `diary_v2.0`。

这次仓库已经按“新版可直接用，旧版单独归档”的思路整理过：

- 新版运行入口保留在 `diary_v2.0/`
- 旧安装包、旧直装包、旧打包工作目录已移动到 `旧版/`
- 没有改动新版 2.0 的目录结构和启动脚本

## 当前推荐使用

新版 2.0 目录：

- `diary_v2.0/launcher.py`
- `diary_v2.0/launcher.pyw`
- `diary_v2.0/run_life_diary_2.0.vbs`
- `diary_v2.0/data/`
- `diary_v2.0/Untitled/`

如果是在 Windows 桌面环境中直接使用，优先走 `diary_v2.0/run_life_diary_2.0.vbs` 对应的启动方式，避免命令行黑框。

## 仓库结构

### 1. 新版

- `diary_v2.0/`
  - 当前实际在用的 2.0 版本
  - 包含启动器、前端页面、2.0 独立数据目录

### 2. 旧版源码

- `src/`
- `main.py`
- `data/`

这部分是更早的桌面版本代码，当前没有移动，主要是为了保留历史实现和兼容参考，避免误伤仍可能要对照的旧逻辑。

### 3. 旧版归档

- `旧版/电脑直装版/`
- `旧版/手机直装版/`
- `旧版/pc_installer_work/`

这里放的是旧的安装包、APK 和旧打包过程目录，已经从根目录挪开，避免继续和新版混在一起。

## 2.0 已有能力

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

补充说明：

- 日记支持图片、全部导出 `Word / PDF / TXT`
- 足迹支持图片，当前已改为导出 `Word`
- 其他内容板块提供各自导出入口
- 数据管理页提供“全部导出”

## 数据位置

新版 2.0 默认使用独立数据目录：

```text
diary_v2.0/data/Diary/
```

这和旧版根目录下的 `data/Diary/` 是分开的。

## 开发说明

前端页面位于：

```text
diary_v2.0/Untitled/
```

后端启动与本地接口位于：

```text
diary_v2.0/launcher.py
```

旧版桌面源码位于：

```text
src/life_dairy/
```

## 测试

旧版桌面主线的常用测试命令仍然是：

```powershell
python -B -m unittest discover -s tests -v
```

## 这次整理做了什么

- 更新了根目录 `README.md`
- 新建 `旧版/`
- 将 `电脑直装版`、`手机直装版`、`pc_installer_work` 移入 `旧版/`
- 保持 `diary_v2.0/` 不动

## Git 名字建议

这次提交如果想起一个清楚、以后自己也好找的名字，推荐：

```text
chore: archive legacy builds and refresh README for diary v2
```

如果你想用中文，也推荐这个版本：

```text
整理旧版归档并更新 README，保留 diary_v2.0 为主版本
```
