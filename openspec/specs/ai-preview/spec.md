# AI Preview Dialog — 系统规格

> 状态：**设计中**

## Overview

AI 预览弹窗是所有 AI 入口的共用确认层。它不关心调用场景，只负责展示 AI 结果并让用户选择"应用"或"取消"。

## Requirement

**R1**: AI 结果必须预览，不能直接写入正式数据。
- Scenario: 用户点击任意 AI 按钮（AI 补全计划 / AI 整理思考 / AI 评估资源 / AI 拆解为行动计划）。
- Scenario: 系统调用 DeepSeek API。
- Scenario: API 返回后，AI 结果以只读文本形式显示在预览弹窗。
- Scenario: 弹窗标题随调用场景变化（如"AI 补全计划 — 预览"、"AI 评估资源 — 预览"）。
- Scenario: 用户点击"应用"后，调用方将 AI 内容填入表单。
- Scenario: 用户点击"取消"后，弹窗关闭，表单不变。

**R2**: 当前表单已有内容时，预览弹窗显示覆盖警告。
- Scenario: 表单非空时点击 AI 按钮。
- Scenario: 预览弹窗顶部显示黄色警告条："注意：当前表单已有内容，确认应用将覆盖现有字段。"
- Scenario: 表单为空时无警告。

**R3**: 异常处理。
- Scenario: AI 返回内容不是合法 JSON 时，弹窗显示错误提示 + 原始返回文本。
- Scenario: API 超时时，弹窗显示"AI 请求超时"。
- Scenario: AI 未配置时，直接提示"请先配置 API Key"，不打开弹窗。

## State (per caller page)

```typescript
interface AIPreviewState {
  previewOpen: boolean;
  previewTitle: string;
  previewContent: string;
  previewWarning: string;
  aiLoading: boolean;
  aiError: string | null;
  aiRawResponse: string | null;   // 用于非法 JSON 时展示
}
```

## Events

OPEN_AI | AI_RESPONSE_RECEIVED | AI_RESPONSE_INVALID | AI_FAILED | CONFIRM_APPLY | CANCEL

## Invariants

- AI 结果必须预览，不能跳过
- 预览内容必须只读
- 表单已有内容时必须在弹窗中显示覆盖警告
- 非法 JSON 不崩溃，显示原始返回
- CONFIRM_APPLY 后调用方负责将内容写入 draft
