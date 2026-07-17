---
name: life-diary-release-check
description: 提交代码、打包安装包、交付发版前执行检查时加载。包括 git commit 前审查、Windows 打包、Android 打包、发布 release 等操作。
---

# 发布前检查清单

## 1. Git 状态检查

执行 `git status --short`，确认：

- 没有意外修改：确认所有变更都是有意为之。
- 没有遗漏文件：新增文件是否应该被跟踪？

## 2. 禁止提交清单

以下内容必须被 `.gitignore` 排除，且 commit 中不得出现：

| 禁止提交项 | 说明 |
|---|---|
| `data/` | 用户真实数据 |
| `.venv/`、`venv/` | 虚拟环境 |
| `__pycache__/`、`*.pyc` | Python 缓存 |
| `.pytest_cache/` | 测试缓存 |
| `.gradle-api27-home/` | Gradle 缓存 |
| `dist/`、`build/`、`release/` | 构建产物 |
| `*.apk`、`*.aab`、`*.exe`、`*.msi` | 安装包/应用文件 |
| `android_release.keystore`、`*.keystore`、`*.jks` | 签名密钥 |
| `pc_installer_work/` | 安装器工作目录 |

## 3. 文档一致性检查

对比代码实际变更，检查以下文档是否需同步更新：

- `README.md` — 功能列表、使用说明、截图
- `HANDOFF.md` — 项目状态、已知问题
- `TODO` — 待办完成情况
- `docs/test/05_测试清单.md` — 测试覆盖

如果实际改动与文档描述不一致，必须修复文档。

## 4. 打包路径检查

### Windows 打包

- 入口：`main.py` → 确认可正常启动。
- 打包配置：`packaging/windows/` 下的打包脚本/spec 文件。
- 输出产物确认路径。

### Android 打包

- 入口：`android/LifeDiaryMobile/`。
- Gradle 构建：`android/LifeDiaryMobile/gradlew` 或相关构建脚本。
- APK 签名：确认使用 `android_release.keystore`（禁止提交此文件本身）。

## 5. 高优先级测试项

如果本次改动涉及以下功能，**必须在测试步骤中单独列出并标记为高优先级**：

- 分享 / 导出
- 备份 / 恢复
- 数据迁移 / 格式变更

## 6. 输出格式

按以下三段输出：

```
## 提交前必须修复
- 问题描述及修复建议

## 可以放二期
- 非阻塞项

## 建议的 Commit Message
<commit message 草案>
```

## 红线

- **禁止自动执行 `git commit`**。
- **禁止自动执行 `git push`**。
- 仅输出检查结果和建议，所有 Git 操作需用户确认后执行。
