from __future__ import annotations

import shutil
import sys
import unittest
from pathlib import Path
from uuid import uuid4


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from life_dairy.models import WorkImageDraft, WorkRelatedDiary, WorkRelatedSelfAnalysis
from life_dairy.work_storage import WorkStorage


class WorkStorageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.case_dir = ROOT / ".tmp_testdata" / f"work_case_{uuid4().hex}"
        self.case_dir.mkdir(parents=True, exist_ok=False)
        self.storage = WorkStorage(self.case_dir)

    def tearDown(self) -> None:
        shutil.rmtree(self.case_dir, ignore_errors=True)

    def test_save_and_reload_work_with_relations(self) -> None:
        work = self.storage.create_empty_work()
        work.title = "星际穿越"
        work.work_type = "电影"
        work.creator = "Christopher Nolan"
        work.status = "已完成"
        work.start_date = "2026-05-01"
        work.finish_date = "2026-05-01"
        work.rating = "9.5"
        work.tags = ["科幻", "亲情"]
        work.one_sentence = "宏大的宇宙故事，落点仍然是牵挂。"
        work.summary = "讲述人类寻找新家园的旅程。"
        work.liked = "音乐和时间设定很有力量。"
        work.disliked = "部分解释略直白。"
        work.touched = "父女重逢让我想到长期等待。"
        work.favorite_parts = "黑洞、书架、玉米地。"
        work.self_connection = "我也会把重要的话藏很久。"
        work.past_connection = "想到以前离开家时的犹豫。"
        work.final_review = "值得反复回看。"
        work.related_diaries.append(
            WorkRelatedDiary(entry_id="entry-1", date="2026-05-01", title="观影夜")
        )
        work.related_self_analysis.append(
            WorkRelatedSelfAnalysis(analysis_id="analysis-1", date="2026-05-01", title="亲密关系观察")
        )

        saved = self.storage.save_work(work)
        loaded = self.storage.load_work(saved.id)

        self.assertEqual("星际穿越", loaded.title)
        self.assertEqual("电影", loaded.work_type)
        self.assertEqual("已完成", loaded.status)
        self.assertEqual("9.5", loaded.rating)
        self.assertEqual(["科幻", "亲情"], loaded.tags)
        self.assertEqual("宏大的宇宙故事，落点仍然是牵挂。", loaded.one_sentence)
        self.assertEqual("父女重逢让我想到长期等待。", loaded.touched)
        self.assertEqual("entry-1", loaded.related_diaries[0].entry_id)
        self.assertEqual("analysis-1", loaded.related_self_analysis[0].analysis_id)
        self.assertTrue((self.storage.work_dir(saved.id) / "work.json").exists())
        self.assertTrue((self.storage.work_dir(saved.id) / "content.md").exists())

        loaded.final_review = "编辑后确认：依然值得反复回看。"
        edited = self.storage.save_work(loaded)
        reopened = self.storage.load_work(edited.id)
        self.assertEqual("编辑后确认：依然值得反复回看。", reopened.final_review)

    def test_list_works_can_search_title_tags_body_status_and_filter_type(self) -> None:
        first = self.storage.create_empty_work()
        first.title = "塞尔达传说"
        first.work_type = "游戏"
        first.status = "进行中"
        first.tags = ["开放世界", "探索"]
        first.touched = "自由探索让我重新想起小时候乱逛的快乐。"
        self.storage.save_work(first)

        second = self.storage.create_empty_work()
        second.title = "孤独摇滚"
        second.work_type = "动画"
        second.status = "已完成"
        second.tags = ["音乐"]
        self.storage.save_work(second)

        self.assertEqual([first.id], [item.id for item in self.storage.list_works("塞尔达")])
        self.assertEqual([first.id], [item.id for item in self.storage.list_works("开放世界")])
        self.assertEqual([first.id], [item.id for item in self.storage.list_works("小时候乱逛")])
        self.assertEqual([first.id], [item.id for item in self.storage.list_works("进行中")])
        self.assertEqual([second.id], [item.id for item in self.storage.list_works("", "动画")])
        self.assertEqual([], [item.id for item in self.storage.list_works("开放世界", "动画")])

    def test_delete_work_hides_item_from_active_list(self) -> None:
        work = self.storage.create_empty_work()
        saved = self.storage.save_work(work)

        self.storage.delete_work(saved.id)

        self.assertTrue(self.storage.work_dir(saved.id).exists())
        self.assertEqual([], self.storage.list_works())

    def test_save_reload_and_remove_images_with_label(self) -> None:
        poster = self.case_dir / "poster.jpg"
        screenshot = self.case_dir / "scene.png"
        poster.write_bytes(b"jpeg-data")
        screenshot.write_bytes(b"png-data")

        work = self.storage.create_empty_work()
        saved = self.storage.save_work(
            work,
            [
                WorkImageDraft(source_path=poster, label="海报"),
                WorkImageDraft(source_path=screenshot, label="喜欢的场景"),
            ],
        )
        loaded = self.storage.load_work(saved.id)

        self.assertEqual(["海报", "喜欢的场景"], [item.label for item in loaded.images])
        kept = loaded.images[0]
        kept_path = self.storage.resolve_image_path(saved.id, kept.file_name)
        saved_again = self.storage.save_work(
            loaded,
            [WorkImageDraft(source_path=kept_path, label=kept.label)],
        )

        self.assertEqual([kept.file_name], [item.file_name for item in saved_again.images])
        self.assertTrue(kept_path.exists())


if __name__ == "__main__":
    unittest.main()
