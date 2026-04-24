from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable

from docx import Document
from docx.enum.text import WD_BREAK
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

from .models import DiaryEntry


ProgressCallback = Callable[[int, str], None]


@dataclass(slots=True)
class DiaryExportItem:
    entry: DiaryEntry
    image_lookup: dict[str, Path]


class DiaryExporter:
    def __init__(self, export_root: Path | str):
        self.export_root = Path(export_root)
        self.export_root.mkdir(parents=True, exist_ok=True)

    def export_word_and_pdf(
        self,
        entry: DiaryEntry,
        image_paths: Iterable[Path | str],
        progress: ProgressCallback | None = None,
    ) -> tuple[Path, Path]:
        export_item = DiaryExportItem(
            entry=entry,
            image_lookup=self._build_image_lookup(image_paths),
        )
        return self.export_entries_word_and_pdf([export_item], progress=progress)

    def export_entries_word_and_pdf(
        self,
        export_items: list[DiaryExportItem],
        progress: ProgressCallback | None = None,
    ) -> tuple[Path, Path]:
        if not export_items:
            raise ValueError("没有可导出的日记")

        ordered_items = sorted(
            export_items,
            key=lambda item: (item.entry.date, item.entry.created_at, item.entry.updated_at),
        )

        callback = progress or (lambda _value, _message: None)
        callback(5, "准备导出路径")

        base_name = self._build_base_name(ordered_items)
        docx_path = self._unique_path(self.export_root / f"{base_name}.docx")
        pdf_path = self._unique_path(self.export_root / f"{base_name}.pdf")

        callback(10, "生成 Word 文档")
        self.export_word_entries(ordered_items, docx_path, progress=callback)

        callback(65, "按 Word 版式生成 PDF")
        self.export_pdf_from_docx(docx_path, pdf_path, progress=callback)

        callback(100, "导出完成")
        return docx_path, pdf_path

    def export_word_entries(
        self,
        export_items: list[DiaryExportItem],
        output_path: Path,
        progress: ProgressCallback | None = None,
    ) -> Path:
        callback = progress or (lambda _value, _message: None)
        document = Document()
        self._configure_word_styles(document)

        total = len(export_items)
        for index, item in enumerate(export_items, start=1):
            callback(
                10 + int(((index - 1) / max(total, 1)) * 50),
                f"写入 Word 日记 {index}/{total}",
            )
            self._append_word_entry(
                document,
                item,
                include_page_break=index > 1,
            )

        callback(60, "保存 Word 文件")
        document.save(output_path)
        return output_path

    def export_pdf_from_docx(
        self,
        docx_path: Path,
        pdf_path: Path,
        progress: ProgressCallback | None = None,
    ) -> Path:
        callback = progress or (lambda _value, _message: None)
        callback(72, "启动 Word 转换 PDF")

        script = """
$ErrorActionPreference = 'Stop'
$docPath = $env:DIARY_EXPORT_DOCX
$pdfPath = $env:DIARY_EXPORT_PDF
$word = $null
$document = $null
try {
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    $word.DisplayAlerts = 0
    $document = $word.Documents.Open($docPath, $false, $true)
    $document.ExportAsFixedFormat($pdfPath, 17)
    Write-Output 'pdf-export-ok'
}
catch {
    Write-Error $_
    exit 1
}
finally {
    if ($document -ne $null) {
        try { $document.Close($false) } catch {}
    }
    if ($word -ne $null) {
        try { $word.Quit() } catch {}
    }
}
"""

        env = os.environ.copy()
        env["DIARY_EXPORT_DOCX"] = str(docx_path)
        env["DIARY_EXPORT_PDF"] = str(pdf_path)

        result = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                script,
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=180,
            env=env,
        )

        callback(95, "完成 PDF 转换")

        # Word 在关闭 COM 对象时偶发抛出清理噪声，但 PDF 已经成功生成。
        # 这里以最终导出的文件是否存在且非空为准，确保 PDF 与 Word 使用同一份版式结果。
        if pdf_path.exists() and pdf_path.stat().st_size > 0:
            return pdf_path

        if result.returncode != 0 or not pdf_path.exists():
            stderr = (result.stderr or "").strip()
            stdout = (result.stdout or "").strip()
            details = stderr or stdout or "Word 转 PDF 失败，但没有返回详细错误。"
            raise RuntimeError(details)

        return pdf_path

    def _append_word_entry(
        self,
        document: Document,
        export_item: DiaryExportItem,
        include_page_break: bool,
    ) -> None:
        entry = export_item.entry
        image_lookup = export_item.image_lookup

        if include_page_break:
            paragraph = document.add_paragraph()
            paragraph.add_run().add_break(WD_BREAK.PAGE)

        title = document.add_heading(entry.display_title, level=0)
        self._set_run_font(title.runs, size=Pt(18), bold=True)

        meta = document.add_paragraph()
        meta.add_run(f"日期：{entry.date}")
        self._set_run_font(meta.runs, size=Pt(10))

        document.add_paragraph("")

        if entry.body.strip():
            for line in entry.body.splitlines():
                paragraph = document.add_paragraph(line)
                self._set_run_font(paragraph.runs, size=Pt(12))
        else:
            paragraph = document.add_paragraph("（正文为空）")
            self._set_run_font(paragraph.runs, size=Pt(12))

        exportable_images = [
            (image, image_lookup.get(image.file_name))
            for image in entry.images
            if image_lookup.get(image.file_name) is not None
        ]
        if exportable_images:
            heading = document.add_heading("图片", level=1)
            self._set_run_font(heading.runs, size=Pt(14), bold=True)

            for image, image_path in exportable_images:
                if image.label.strip():
                    caption = document.add_paragraph(image.label.strip())
                    self._set_run_font(caption.runs, size=Pt(11), bold=True)
                document.add_picture(str(image_path), width=Cm(15.5))
                document.add_paragraph("")

    def _build_base_name(self, export_items: list[DiaryExportItem]) -> str:
        if len(export_items) == 1:
            raw = f"{export_items[0].entry.date}_{export_items[0].entry.display_title}"
        else:
            start_date = export_items[0].entry.date
            end_date = export_items[-1].entry.date
            raw = f"{start_date}_to_{end_date}_{len(export_items)}篇日记"

        cleaned = re.sub(r'[<>:"/\\\\|?*]+', "_", raw)
        cleaned = re.sub(r"\s+", " ", cleaned).strip(" ._")
        if not cleaned:
            cleaned = "diary_export"
        return cleaned[:100]

    def _build_image_lookup(self, image_paths: Iterable[Path | str]) -> dict[str, Path]:
        return {
            Path(path).name: Path(path)
            for path in image_paths
        }

    def _unique_path(self, target: Path) -> Path:
        if not target.exists():
            return target

        counter = 1
        while True:
            candidate = target.with_name(f"{target.stem}_{counter}{target.suffix}")
            if not candidate.exists():
                return candidate
            counter += 1

    def _configure_word_styles(self, document: Document) -> None:
        normal = document.styles["Normal"]
        normal.font.name = "宋体"
        normal.font.size = Pt(12)
        normal._element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")

    def _set_run_font(self, runs, size: Pt, bold: bool = False) -> None:
        for run in runs:
            run.font.name = "宋体"
            run.font.size = size
            run.bold = bold
            run._element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")
