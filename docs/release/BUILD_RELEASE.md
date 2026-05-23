# 人生档案 Diary Desktop 构建发布指南

## Desktop 3.2.0

本文档提供「人生档案 Diary Desktop」的构建和发布流程说明。

---

## 一、开发环境准备

### 1.1 运行环境要求

- Python 3.10+
- Windows 10/11 (64位)
- 至少 4GB 内存
- 至少 1GB 可用磁盘空间

### 1.2 安装依赖

```bash
cd e:\code\life\diary
pip install -r requirements.txt
pip install pyinstaller
```

### 1.3 源码运行方式

```bash
cd e:\code\life\diary
python main.py
```

或使用 Python 模块方式：

```bash
python -m life_dairy.app
```

---

## 二、PyInstaller 打包

### 2.1 打包命令（唯一推荐入口）

```bash
cd e:\code\life\diary\packaging\windows
pyinstaller LifeDiary.spec --clean
```

> **注意**：`电脑直装版/specs/人生档案.spec` 已被标记为 DEPRECATED，其 hiddenimports 和 binaries 配置不完整。请始终使用 `packaging/windows/LifeDiary.spec`。

### 2.2 输出目录

打包成功后，输出目录为：

```
e:\code\life\diary\packaging\windows\dist\LifeDiary\
```

目录结构：

```
dist\LifeDiary\
├── LifeDiary.exe          # 主程序
├── PySide6\               # Qt 插件和动态库
├── Python311.dll
└── ...其他依赖文件
```

### 2.3 验证打包结果

1. **启动测试**：双击 `dist\LifeDiary\LifeDiary.exe` 验证能正常启动

2. **功能测试**：按 docs/test/TEST_CHECKLIST.md 进行功能验证

3. **检查依赖**：
   - PySide6 插件目录存在
   - Qt 平台插件 qwindows.dll 存在
   - 无缺少 DLL 报错

---

## 三、Qt / PySide6 动态库注意事项

### 3.1 必须包含的 Qt 插件

| 文件 | 用途 |
|------|------|
| `platforms/qwindows.dll` | Windows 平台支持（必须） |
| `imageformats/qgif.dll` | GIF 图像支持 |
| `imageformats/qjpeg.dll` | JPEG 图像支持 |
| `imageformats/qpng.dll` | PNG 图像支持 |
| `imageformats/qwebp.dll` | WebP 图像支持 |

### 3.2 PyInstaller hidden imports

以下模块必须添加到 `hiddenimports`：

```
PySide6
PySide6.QtCore
PySide6.QtGui
PySide6.QtWidgets
PySide6.QtXml
shiboken6
shiboken6.Shiboken
docx
docx.oxml
docx.opc
docx.table
docx.text
lxml
lxml.etree
lxml._elementpath
```

### 3.3 常见问题

**问题1：打包后启动报错 "Qt platform plugin not found"**

解决：确保 spec 文件的 `binaries` 中包含 `platforms/qwindows.dll`

**问题2：打包后图片无法显示**

解决：确保 spec 文件包含 imageformats 下的所有 DLL

**问题3：打包后提示 "Python library not found"**

解决：检查 PyInstaller 是否正确找到 Python 动态库

---

## 四、生成免安装版 ZIP

### 4.1 打包后创建 ZIP

```bash
cd e:\code\life\diary\packaging\windows\dist
powershell Compress-Archive -Path LifeDiary -DestinationPath LifeDiary-3.2.0-portable.zip -Force
```

### 4.2 输出文件

```
e:\code\life\diary\packaging\windows\dist\LifeDiary-3.2.0-portable.zip
```

---

## 五、发布前检查清单

在发布前，请确认以下所有项目已完成：

### 功能完整性
- [ ] 所有页面能正常打开和切换
- [ ] 新建、保存、删除功能正常
- [ ] 自动保存不导致光标跳动
- [ ] 日志文件正常生成
- [ ] 旧数据能正常打开

### 打包完整性
- [ ] PyInstaller 打包无错误
- [ ] EXE 能独立启动（不依赖开发环境）
- [ ] Qt 插件正确打包
- [ ] 无缺少 DLL 警告

### 测试完成
- [ ] 已按 docs/test/TEST_CHECKLIST.md 完成所有测试
- [ ] 无已知严重问题
- [ ] 数据兼容性验证通过

---

## 六、SHA256 校验命令

### 6.1 生成校验和

```bash
cd e:\code\life\diary\packaging\windows\dist
powershell Get-FileHash LifeDiary-3.2.0-portable.zip -Algorithm SHA256 | Format-List
```

输出示例：

```
Algorithm : SHA256
Hash      : A1B2C3D4E5F6...（实际哈希值）
Path      : LifeDiary-3.0.1-portable.zip
```

### 6.2 验证校验和

下载后运行：

```bash
powershell Get-FileHash .\LifeDiary-3.2.0-portable.zip -Algorithm SHA256
```

对比哈希值确认文件完整性。

---

## 七、常见打包问题

### 问题1：打包时间过长

**原因**：PyInstaller 需要分析所有依赖
**解决**：耐心等待，首次打包约需 3-5 分钟

### 问题2：打包后文件太大

**原因**：包含完整的 Python 环境
**解决**：可使用 `upx=True` 压缩（已在 spec 中启用）

### 问题3：图标不显示

**原因**：图标路径不正确或图标格式不对
**解决**：
1. 确认图标文件存在且路径正确
2. 图标应为 .ico 格式
3. 或将 icon 参数设为空字符串

### 问题4：权限错误

**原因**：输出目录无写入权限
**解决**：使用管理员权限运行命令提示符

---

## 八、版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| 3.2.0 | 2026-05-14 | 新增信息备忘模块、工程整理 Round 1（统一 spec / 版本号 / allowBackup） |
| 3.0.1 | 2026-05-03 | 工程稳定性修复版：修复自动保存静默失败、完善打包配置、添加日志系统 |
| 3.0.0 | - | 初始版本 |

---

## 九、联系方式

如有问题，请提交 Issue 或联系开发者。
