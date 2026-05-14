## Why

用户目前导出的 Word 和 PDF 中，日记条目按旧日期在前（升序）排列，即最早写的日记在最前面。用户希望改为新日期在前（降序），让最新的日记出现在文档开头，更符合阅读习惯——打开文档就能看到最近的记录。

## What Changes

- **Word 导出排序反转**：导出 Word 文档时，日记条目从升序（旧→新）改为降序（新→旧）
- **PDF 导出排序反转**：PDF 从 Word 转换而来，随 Word 排序变化自动反转
- **存储层导出查询反转**：`list_entries_in_date_range()` 返回结果从升序改为降序
- **UI 说明文字更新**：导出对话框中的提示文字从"按旧日期在前排序"改为"按新日期在前排序"
- **测试更新**：更新测试用例以匹配新的降序排列

## Capabilities

### New Capabilities
- (无新增能力，仅修改现有行为)

### Modified Capabilities
- `word-pdf-export`: 导出排序从升序（旧→新）改为降序（新→旧）

## Impact

- `src/life_dairy/exporters.py`：修改 `export_entries_word_and_pdf()` 中的排序逻辑
- `src/life_dairy/storage.py`：修改 `list_entries_in_date_range()` 中的排序逻辑
- `src/life_dairy/diary_page.py`：更新导出提示文字
- `tests/test_exporters.py`：更新断言以验证降序排列
