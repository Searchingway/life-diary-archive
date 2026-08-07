# 人生档案移动端

这是 `life-diary-archive` 的现代 Android 客户端，技术栈为 Expo SDK 56、React Native、TypeScript 和 SQLite。旧 Qt 客户端保留在仓库中，本目录是新的移动端主实现。

## 功能

- 日记：标题、日期、正文、图片与图片说明，正文延迟自动保存。
- 足迹：按地点保存说明，可在一个地点下记录多次访问、想法和图片。
- 接单备忘：支持在报价、已接单、已完成、已验收、已结款、已放弃。
- 接单排序：已接单未完成优先，其次为已验收未结款；同一状态内按日期倒序。
- 数据管理：导出含图片的 ZIP、恢复前自动安全备份、导入同包名旧 Qt 应用的 `Diary` 目录。
- 删除采用软删除；应用不上传个人记录。

## 本地运行

```powershell
cd mobile
npm install
npm run typecheck
npm test
npx expo start
```

## Android Release

需要 Android SDK、Java 17 或更高版本，以及与已安装版本一致的签名密钥。

```powershell
$env:LIFE_DIARY_STORE_PASSWORD = "..."
$env:LIFE_DIARY_KEY_PASSWORD = "..."
$env:LIFE_DIARY_KEY_ALIAS = "life_diary"
.\scripts\build-release.ps1 -KeystorePath "D:\path\life_diary_release.keystore"
```

产物写入 `mobile/build-output/人生档案-Expo-2.2.0-release-signed.apk`。签名密码和密钥均不进入 Git。

## 数据兼容

Android 包名保持 `com.localfirst.lifediary`，版本号为 `2.2.0 (4)`。使用旧版相同签名安装时可覆盖升级，并可在“数据管理”中导入原应用私有目录下的 `Diary` 文本和图片。

恢复 ZIP 会替换当前日记、足迹和接单记录，因此程序会先在缓存目录生成当前状态安全备份。卸载应用会清除应用私有目录，卸载前必须主动导出 ZIP。
