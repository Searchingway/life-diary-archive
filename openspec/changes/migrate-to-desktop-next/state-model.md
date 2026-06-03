# 通用状态模型 — Desktop Next 迁移

> 本文档定义 Desktop Next 所有页面的共享状态模式。每个页面的具体状态见各 change 的 `state-model.md`。

## 通用 Reducer 模式

```typescript
type PageState = {
  // server state
  records: Record[];
  // UI state
  selectedId: string | null;
  query: string;
  loading: boolean;
  error: string | null;
  // draft state
  draft: Draft | null;
  isDirty: boolean;
  // AI state （仅 AI 页面）
  aiPreviewOpen: boolean;
  aiLoading: boolean;
  aiDraft: any;
  // dialog state （仅弹窗页面）
  editorOpen: boolean;
  deleteConfirm: string | null;
};

// 所有页面共享的 CRUD 事件前缀
type PageEvent =
  | { type: "INIT_PAGE" }
  | { type: "LOAD_SUCCESS"; records: Record[] }
  | { type: "LOAD_FAILED"; message: string }
  | { type: "SELECT"; id: string }
  | { type: "NEW" }
  | { type: "UPDATE_DRAFT"; partial: Partial<Draft> }
  | { type: "SAVE_REQUEST" }
  | { type: "SAVE_SUCCESS"; record: Record }
  | { type: "SAVE_FAILED"; message: string }
  | { type: "DELETE_REQUEST" }
  | { type: "DELETE_CONFIRM" }
  | { type: "DELETE_CANCEL" }
  | { type: "CHANGE_QUERY"; query: string };
```

## AI Event 模式

```typescript
type AIEvent =
  | { type: "OPEN_AI" }
  | { type: "AI_RESPONSE_RECEIVED"; draft: any; raw: string }
  | { type: "AI_RESPONSE_INVALID"; raw: string; message: string }
  | { type: "AI_FAILED"; message: string }
  | { type: "CONFIRM_APPLY" }
  | { type: "CANCEL_AI" };
```

## 页面状态一览

| 页面 | AI | 专属状态 |
|------|----|----------|
| Dashboard | — | modules, recent, stats |
| Diary | — | draft(标题/正文/日期), isDirty, selectedDate |
| LightPlan | ✅ | aiDraft, subtract fields |
| ActionPlan | ✅ | currentView, planEditorOpen, taskEditorOpen, taskDraft, gantt/task positions |
| LightThought | ✅ | ideas[], aiDraft |
| LightResource | ✅ | resourceItems[], aiDraft |
| InfoMemo | — | typeFilter 联动 statusFilter |
| SelfObservation | — | emotionFilter, intensityFilter |
| LessonsReflection | — | categoryFilter, severityFilter |
| SelfAnalysis | — | 12-section form |
| WorksReflection | — | workType filter |
| DataManager | — | backup/restore import/export running states |
| AISettings | ✅ | testing, testResult |
