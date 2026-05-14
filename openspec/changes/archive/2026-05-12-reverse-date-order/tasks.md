## 1. 导出排序反转

- [x] 1.1 在 `exporters.py` 的 `export_entries_word_and_pdf()` 中，给 `sorted()` 添加 `reverse=True` 参数
- [x] 1.2 在 `storage.py` 的 `list_entries_in_date_range()` 中，给 `items.sort()` 添加 `reverse=True` 参数

## 2. UI 与测试更新

- [x] 2.1 更新 `diary_page.py` 导出对话框提示文字，将"按旧日期在前排序"改为"按新日期在前排序"
- [x] 2.2 更新 `test_exporters.py` 第 98 行，将 `assertLess` 改为 `assertGreater`，验证降序排列
