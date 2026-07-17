---
name: life-diary-mobile-bugfix
description: 修复「人生档案 / Life Diary」Android 手机版 Bug 时加载。包括分享导出失败、UI 显示异常、数据未刷新、删除/编辑异常、文件读写权限等问题。
---

# Android 手机版 Bug 修复规则

## 修复前——定位

1. **入口**：`android/LifeDiaryMobile/` 下的 Activity / Fragment / QML 入口。
2. **页面**：确认 Bug 出现在哪个页面、哪个组件。
3. **共享数据结构**：手机版与桌面版共用哪些数据文件？定位到具体文件路径。
4. **导出/分享逻辑**：定位 `content://` Uri 构建和 `Intent` 分享代码。

## 常见 Bug 排查清单

### 分享导出失败

1. 检查 ZIP 文件是否真实生成了（文件路径、是否存在）。
2. 检查文件 size 是否正常（0 字节 = 生成失败）。
3. 优先使用 `content://` Uri（而非 `file://`）。
4. 必须配置 `FileProvider` + `FLAG_GRANT_READ_URI_PERMISSION`。
5. 检查 `AndroidManifest.xml` 中 FileProvider 声明。
6. 检查 `file_paths.xml` 中路径映射是否正确。

### UI 显示异常

- **原则**：只改显示逻辑，不改数据存储结构。
- 卡片列表不要显示大段正文——只显示标题、日期、摘要或元信息。
- 刷新机制：确认 `notifyDataSetChanged()` 或类似刷新调用已触发。

### 删除/编辑功能异常

1. 操作前必须有确认提示（`AlertDialog` 或 `Snackbar` 带撤销）。
2. 操作后必须刷新当前页面列表。
3. 操作后必须验证数据持久化是否成功（关闭页面重新打开检查）。

## 修改规范

- **每次只修一个 Bug 或一组高度相关的 Bug**。
- 不得顺手修改桌面端代码（`src/life_dairy/`）。
- 不得顺手重构手机版无关代码。

## 修改后输出

必须包含 Android 真机测试步骤，例如：

```
## 真机测试步骤
1. 在 Android 真机上安装 APK（USB 调试或 adb install）
2. 打开 XX 页面，点击 XX 按钮
3. 预期结果：...
4. 检查文件管理器对应目录是否生成正确文件
```
