from __future__ import annotations

import sys
import unittest
from pathlib import Path

from docx import Document


DIARY_V2_ROOT = Path(__file__).resolve().parents[1] / "diary_v2.0"
if str(DIARY_V2_ROOT) not in sys.path:
    sys.path.insert(0, str(DIARY_V2_ROOT))

from export_service import append_footprint_record_to_docx


class FootprintWordExportTests(unittest.TestCase):
    def test_place_name_is_primary_heading_and_visit_date_is_secondary(self) -> None:
        document = Document()
        append_footprint_record_to_docx(
            document,
            {
                "id": "place-1",
                "title": "东北农业大学武术馆",
                "body": "地点描述",
                "extra": {
                    "visits": [
                        {
                            "id": "visit-1",
                            "date": "2026-06-12",
                            "thought": "访问记录",
                            "images": [],
                        }
                    ]
                },
            },
        )

        styles_by_text = {
            paragraph.text: paragraph.style.name
            for paragraph in document.paragraphs
            if paragraph.text
        }
        self.assertEqual(styles_by_text["东北农业大学武术馆"], "Heading 1")
        self.assertEqual(styles_by_text["2026-06-12"], "Heading 2")


if __name__ == "__main__":
    unittest.main()
