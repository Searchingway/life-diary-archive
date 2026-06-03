# Data Contract — 系统规格

> 状态：**设计中**

## Overview

前后端通过 HTTP REST JSON 通信。所有 API 端点返回 JSON，请求体也是 JSON。前端不直接读写文件。

## API 端点

| Path | Method | Request Body | Response | 备注 |
|------|--------|-------------|----------|------|
| `/api/overview` | GET | — | `{ data_root, modules[], recent[], dashboard_stats{} }` | 总览 |
| `/api/settings` | GET | — | `{ export_dir, ...app_settings }` | 读取设置 |
| `/api/settings` | POST | `{ key: value }` | `{ ...updated_settings }` | 保存设置 |
| `/api/modules/<key>` | GET | query: `?q=keyword` | `[{ id, title, subtitle, body, date, updated_at, status, type, extra }]` | 列表 |
| `/api/modules/<key>` | PUT | `{ id?, title, body, date, type, status, extra }` | `{ ...saved_record }` | 保存 |
| `/api/modules/<key>/<id>` | DELETE | — | `{ ok: true }` | 删除 |

## Record Response Shape

后端的 `record_from_directory()` 返回统一结构：

```typescript
interface RecordResponse {
  id: string;
  title: string;
  subtitle: string;          // type / status 拼接
  body: string;              // 正文全文
  date: string;              // YYYY-MM-DD
  updated_at: string;        // ISO timestamp
  status: string;
  type: string;
  extra: Record<string, any>; // 模块专属原始数据
}
```

解释：
- `body` 是正文全文（从 `.md` 文件或 JSON 字段读取），**不是截断**。前端负责截断显示
- `extra` 是模块的原始 JSON 数据，前端按需解构（如 `extra.images`、`extra.tasks`、`extra.resource_items`）
- `status` 和 `type` 是从 `extra` 中提取的快捷字段

## 前端写入格式

前端发 PUT 时 payload：

```typescript
interface SavePayload {
  id?: string;            // 无 id 则新建
  title: string;
  body: string;
  date?: string;
  type?: string;
  status?: string;
  extra?: Record<string, any>;  // 模块专属字段
}
```

后端 `save_generic_record()` 会：
1. 如果 `id` 存在且记录已存在 → 合并到现有数据（`{...existing, ...extra}`）
2. 如果 `id` 不存在 → 生成新 uuid
3. 写 `body` 到对应 `.md` 文件或 body_fields
4. 写 `extra` 到 JSON
5. 返回 `record_from_directory()` 作为响应

## 数据约束

| 约束 | 说明 |
|------|------|
| 软删除 | 所有模块使用 `deleted: true` + `deleted_at` |
| UUID | `uuid4().hex`（32位十六进制） |
| 时间格式 | ISO 8601（`2026-05-20T10:00:00.000000+08:00`） |
| 日期格式 | `YYYY-MM-DD` |
| 图片存储 | `data/Diary/<module>/<id>/images/<file>`，通过 `/api/modules/entries/<id>/images/<name>` 访问 |
