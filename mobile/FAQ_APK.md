# Life Diary Mobile 2.2 APK 常见问题

本文记录 Expo/React Native 手机版的构建、签名和桌面交付处理方式。命令均在 `mobile/` 目录执行。

## 启动页显示 Expo 白色 “A”

启动页必须使用 `assets/images/icon.png`，它是 Life Diary 的应用图标；不要继续使用 Expo 示例的 `splash-icon.png`。修改 `app.json` 后必须重新执行 `expo prebuild` 和 Gradle 构建，旧 APK 不会自动更新资源。

## 先区分：Expo export 不是 APK

`npx expo export --platform android` 只生成 Metro/Hermes bundle，输出到 `mobile/dist/`，不能直接安装到 Android。

要生成 APK，必须执行 Gradle release 构建：

```powershell
.\android\gradlew.bat -p android :app:assembleRelease --no-daemon
```

成功文件通常位于：

```text
mobile/android/app/build/outputs/apk/release/app-release.apk
```

## Gradle 报 TLS、握手或 `CRYPT_E_REVOCATION_OFFLINE`

这表示 Windows 证书吊销检查无法访问，不代表 Google Maven 地址不存在。先做不改系统配置的诊断：

```powershell
curl.exe --ssl-no-revoke -I --max-time 20 `
  https://dl.google.com/android/maven2/com/android/tools/analytics-library/shared/30.3.1/shared-30.3.1.jar
```

如果返回 `HTTP/1.1 200 OK`，说明网络可达。`--ssl-no-revoke` 仅用于确认问题，不要把它写入全局 Git、系统代理或长期构建配置。

接下来按顺序处理：

1. 使用项目现有的 release 脚本，它会把 Expo 生成的 wrapper 从 Gradle 9.3.1 调整到项目验证过的 Gradle 8.14.3。
2. 如果只需要本机调试 APK，可先确保所需依赖已经缓存，再使用 `--offline`；出现 `No cached version available` 时不要继续重试，说明缓存不完整。
3. 恢复系统证书吊销访问或配置经过批准的企业代理后，再重新执行 Gradle。不要关闭 Windows 安全校验作为永久修复。

## 发布脚本提示缺少 keystore 或密码

正式签名构建需要以下环境变量，值只在本机安全环境设置，不要写入文档、日志或提交：

```text
LIFE_DIARY_STORE_PASSWORD
LIFE_DIARY_KEY_PASSWORD
LIFE_DIARY_KEY_ALIAS
```

密钥文件也必须存在于本机。缺少任一项时只能生成项目当前配置的本地 debug-signed release，不能把它称为正式发布包。

无正式 keystore、只需验证当前代码时，使用项目的 Maven 镜像 init 脚本：

```powershell
$projectRoot = (Resolve-Path .).Path
.\android\gradlew.bat -p android `
  -I (Join-Path $projectRoot 'scripts\gradle-init.gradle') `
  :app:assembleRelease --no-daemon
```

如果 wrapper 仍为 9.3.1，先使用项目生成目录中已验证的 8.14.3 分发包；不要在仓库中提交生成的 `mobile/android/` 或 APK。

## 如何判断 APK 是否是当前代码

检查 APK 时间、包名和版本信息：

```powershell
$apk = Resolve-Path .\android\app\build\outputs\apk\release\app-release.apk
$buildTools = Get-ChildItem "$env:LOCALAPPDATA\Android\Sdk\build-tools" -Directory |
  Sort-Object Name -Descending | Select-Object -First 1
& "$($buildTools.FullName)\aapt.exe" dump badging $apk
Get-FileHash $apk -Algorithm SHA256
```

不要把早于本轮源码修改时间的旧 APK 改名后当作新版本交付。

## 如何复制到桌面并校验

先确认目标文件名，再复制；不要覆盖已有 APK：

```powershell
$source = (Resolve-Path .\android\app\build\outputs\apk\release\app-release.apk).Path
$target = Join-Path $env:USERPROFILE 'Desktop\LifeDiary-Mobile-current.apk'
if (Test-Path -LiteralPath $target) { throw "目标已存在，请先选择新文件名：$target" }
Copy-Item -LiteralPath $source -Destination $target
Get-FileHash $source -Algorithm SHA256
Get-FileHash $target -Algorithm SHA256
```

只有源文件和桌面文件 SHA-256 完全一致，才报告复制成功。

## APK 生成了但无法安装

- `versionCode` 相同：卸载旧包或使用 `adb install -r` 前确认签名一致。
- 签名不同：debug keystore 与正式 keystore 不能互相覆盖安装。
- 架构不匹配：确认构建配置包含目标设备的 `arm64-v8a`。
- 只完成了 `expo export`：这不是可安装 APK，回到本文第一节执行 Gradle。

## 交付红线

- 默认不提交 `*.apk`、`*.aab`、`dist/`、`build/` 或 keystore；只有在明确要求把安装包放进 GitHub 时，才将经过哈希校验的 APK 单独放入 `mobile/build-output/`，并仍然排除 `android/` 生成目录与 keystore。本次 2.2.0 APK 属于此明确授权例外。
- 不打印完整密码、API Key 或签名凭据。
- 不修改真实用户数据，不因为 UI 隐藏 `orders` 就从备份中删除它。
- 报告时明确区分：类型/单元测试、Expo 导出、APK 构建、签名验证和真机安装。
