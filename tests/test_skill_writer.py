import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class SkillWriterTest(unittest.TestCase):
    def run_cmd(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["python3", str(ROOT / "tools" / "skill_writer.py"), *args],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )

    def test_create_import_update_refresh_and_rollback(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            base_dir = tmp / "bosses"
            meta_file = tmp / "meta.json"
            card_file = tmp / "card.md"
            material_file = tmp / "notes.txt"
            correction_file = tmp / "correction.json"

            meta_file.write_text(
                json.dumps(
                    {
                        "display_name": "李总",
                        "source_type": "real-person",
                        "core_persona": "高压老板",
                        "default_mode": "immersive",
                        "default_intensity": "high",
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            card_file.write_text(
                "## 核心人格\n\n高压老板。\n\n## speaking_style\n\n- 先问结论\n",
                encoding="utf-8",
            )
            material_file.write_text(
                "先给结论，不要把背景讲成小说。这个事情谁负责？什么时候完成？\n",
                encoding="utf-8",
            )
            correction_file.write_text(
                json.dumps(
                    {
                        "dimension": "speaking_style",
                        "wrong": "直接爆粗口",
                        "correct": "先冷下来，再上升到准备不足",
                        "reason": "更像冷处理而不是爆发",
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            create = self.run_cmd(
                "--action",
                "create",
                "--slug",
                "boss-li",
                "--meta-file",
                str(meta_file),
                "--card-file",
                str(card_file),
                "--base-dir",
                str(base_dir),
            )
            self.assertEqual(create.returncode, 0, msg=create.stderr)

            import_result = self.run_cmd(
                "--action",
                "import-material",
                "--slug",
                "boss-li",
                "--material-file",
                str(material_file),
                "--material-kind",
                "notes",
                "--base-dir",
                str(base_dir),
            )
            self.assertEqual(import_result.returncode, 0, msg=import_result.stderr)

            update_result = self.run_cmd(
                "--action",
                "update",
                "--slug",
                "boss-li",
                "--update-kind",
                "correction",
                "--correction-file",
                str(correction_file),
                "--base-dir",
                str(base_dir),
            )
            self.assertEqual(update_result.returncode, 0, msg=update_result.stderr)

            meta = json.loads((base_dir / "boss-li" / "meta.json").read_text(encoding="utf-8"))
            card = (base_dir / "boss-li" / "boss-card.md").read_text(encoding="utf-8")
            corrections = (base_dir / "boss-li" / "corrections.jsonl").read_text(encoding="utf-8")

            self.assertEqual(meta["slug"], "boss-li")
            self.assertGreaterEqual(meta["corrections_count"], 1)
            self.assertIn("materials", meta)
            self.assertIn("source_updates", card)
            self.assertIn("corrections", card)
            self.assertIn("先冷下来，再上升到准备不足", corrections)

            rollback = self.run_cmd(
                "--action",
                "rollback",
                "--slug",
                "boss-li",
                "--version",
                "v1",
                "--base-dir",
                str(base_dir),
            )
            self.assertEqual(rollback.returncode, 0, msg=rollback.stderr)
            rolled_meta = json.loads((base_dir / "boss-li" / "meta.json").read_text(encoding="utf-8"))
            self.assertEqual(rolled_meta["version"], "v1")


if __name__ == "__main__":
    unittest.main()
