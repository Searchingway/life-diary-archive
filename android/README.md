# 人生档案手机版

这是 `android/LifeDiaryMobile` 里的 Qt 6/QML 手机端工程，目标是承接桌面版的本地优先数据结构。Mobile 1.5 当前已经包含：

- 日记：新建、搜索、编辑、保存、软删除
- 足迹：地点档案、地点搜索、日期记录、感悟保存、删除
- 读书：书名、作者、状态、日期、标签、摘要、笔记
- 轻计划：计划标题、日期、状态、优先级、备注、标记完成
- 轻思考：记录暂时想不明白的问题，支持类型、状态、想法追加、初步结论和备注
- 轻资源：记录一件事消耗的时间、金钱、精力、情绪等生命资源，并包含轮回测试
- 自我观察：快速记录当下情绪、强度、触发原因、身体感受和当前需要
- 数据管理：完整导出 `Diary/` ZIP 数据包、Android 系统分享、从数据包导入、查看数据目录与各模块数量
- 日记 / 足迹 / 读书：分别导出 `.zip` 压缩包交换包
- 日记统计：最近 18 周绿色热力图
- APK：已完成 `arm64-v8a` Release 签名包构建，并在 Android 真机正常安装
- 应用信息：应用名为“人生档案”，已配置自定义启动图标

## Mobile 1.5 每日记录闭环版

- 首页改为“人生档案随手记”，主入口为写日记、记足迹、轻计划、轻思考、轻资源、自我观察，并提供数据管理入口。
- 旧的日记、足迹、读书、轻计划页面仍然保留，旧数据目录不迁移、不清空。
- 新增数据保存目录：

```text
Diary/
  thoughts/       轻思考，每条 thought.json
  resources/      轻资源，每条 resource.json
  observations/   自我观察，每条 observation.json
```

- 完整备份文件名为 `LifeDiary_Backup_yyyyMMdd_HHmmss.zip`，包内包含 `manifest.json` 和完整 `Diary/` 目录。
- Android 分享使用 `content://` URI、`FileProvider` 和 `ACTION_SEND`，点击“导出并分享数据包”会生成 ZIP 后直接调起系统分享面板。
- 导入 ZIP 前会自动导出当前数据备份；非法 ZIP 或缺少合法数据目录时不会执行覆盖。

## 2.0 同步内容

安卓版 2.0 已同步桌面版当前能力：

- 从旧的“每日复盘式轻计划”调整为任务式轻计划，字段与桌面版保持一致。
- 保留旧轻计划数据读取兼容，旧字段会合并显示到新版备注里。
- 日记页新增绿色热力图，用于查看最近 18 周写日记频率。
- 日记、足迹、读书三个模块新增“导出包”入口。
- 导出的压缩包包含原始模块目录和 `manifest.json`，用于后续多端交换。
- 页面区域加大，继续使用整页滚动交互，避免表单内容挤在一起。
- 手机端整体视觉同步为浅色绿色系。
- 完成 Android 软件名、启动图标、Release 签名包和真机安装验证。

## 数据位置

手机端默认保存到 Qt 的应用私有目录下，并在里面继续使用同款 `Diary` 目录：

```text
Diary/
  entries/
  footprints/
  books/
  plans/
  thoughts/
  resources/
  observations/
  exports/
```

桌面调试时可以用环境变量指定数据目录：

```powershell
$env:LIFE_DIARY_DATA_ROOT = "E:\code\life\diary\data\Diary"
```

## 压缩包交换包

手机端会把交换包导出到数据目录下的 `exports/`：

```text
Diary/
  exports/
    life_diary_diary_YYYYMMDD_HHMMSS.zip
    life_diary_footprint_YYYYMMDD_HHMMSS.zip
    life_diary_book_YYYYMMDD_HHMMSS.zip
```

压缩包内部会包含：

- `manifest.json`
- `entries/`、`footprints/` 或 `books/` 原始数据目录

当前导出先落在应用数据目录里，后续可以再接 Android 系统分享面板或文件选择器。

## 桌面验证

进入工程目录后，可以先用 Qt 6.10.1 桌面套件验证代码：

```powershell
cd android/LifeDiaryMobile
.\build_desktop.bat
```

## Android 构建与安装包

当前已验证的本机环境：

- Qt 6.10.1
- Android ARM64-v8a 套件
- Android NDK 27.2.12479018
- Android SDK Build Tools 36.0.0

构建入口：

```powershell
cd android/LifeDiaryMobile
.\build_android_arm64.bat
```

已验证的签名 APK：

```text
手机直装版/LifeDiaryMobile-Mobile15-release-signed.apk
```

说明：`build/` 目录是本地构建产物，推送源码到 GitHub 时通常不提交；需要分发安装包时，可以把签名 APK 上传到 GitHub Release。

## 版本迭代史

### 2.0

- 同步桌面版四模块结构：日记、足迹、读书、轻计划。
- 轻计划改为任务式结构，并兼容旧数据读取。
- 新增日记绿色热力图。
- 新增日记、足迹、读书压缩包交换包导出。
- 同步桌面版绿色系视觉风格，并放大主要编辑区域。
- 完成“人生档案”应用名、自定义图标和可安装签名 APK。

### 1.0

- 完成 Qt 6/QML 手机端基础工程。
- 接入桌面版同款本地数据目录结构。
- 实现日记、足迹、读书和旧版轻计划的基础增删改查。
