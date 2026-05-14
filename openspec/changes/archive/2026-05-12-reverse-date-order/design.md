## Context

目前 Word 和 PDF 导出时，日记条目按日期升序排列（旧→新），用户希望改为降序（新→旧）。此改动影响范围很小：核心排序逻辑在 `exporters.py` 第 52-55 行，通过 `sorted()` 实现；存储层的 `list_entries_in_date_range()` 在第 72 行也有排序。

## Goals / Non-Goals

**Goals:**
- Word 导出的条目按新日期在前排列
- PDF 导出的条目按新日期在前排列（随 Word 自动变化）
- UI 提示文字同步更新
- 测试用例改为验证降序

**Non-Goals:**
- 不改变 UI 侧边栏的排序（已经是新在前）
- 不改变 `list_entries_by_date()` 的排序（同一天的条目顺序影响不大）
- 不改变数据模型或存储格式

## Decisions

1. **在 `exporters.py` 的 `sorted()` 加 `reverse=True`** — 最直接的方式，不引入新依赖，改动量最小。
2. **在 `storage.py` 的 `list_entries_in_date_range()` 加 `reverse=True`** — 保持一致性，即使 exporters.py 会再次排序，确保存储层的返回结果也有正确的默认顺序。
3. **不修改 `list_entries_by_date()`** — 同一天内多条日记，按创建时间升序更自然（先写的先显示），且不涉及导出。

## Risks / Trade-offs

- **测试需要更新**：`test_exporters.py` 第 98 行断言 `self.assertLess(text.find("第一篇"), text.find("第二篇"))` 需要改为 `assertGreater`，以验证第一篇（旧日期）出现在第二篇（新日期）之后。
