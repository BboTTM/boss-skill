import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class AnalyzeBossMaterialsTest(unittest.TestCase):
    def test_cli_generates_meta_and_card(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            input_path = tmp / "messages.txt"
            meta_out = tmp / "meta.json"
            card_out = tmp / "card.md"
            input_path.write_text(
                "你先别解释，先给结论。这个事情到底谁负责？今天能不能给我时间点？\n",
                encoding="utf-8",
            )
            cmd = [
                "python3",
                str(ROOT / "tools" / "analyze_boss_materials.py"),
                "--input",
                str(input_path),
                "--display-name",
                "王总",
                "--source-type",
                "real-person",
                "--meta-out",
                str(meta_out),
                "--card-out",
                str(card_out),
            ]
            result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, msg=result.stderr)

            meta = json.loads(meta_out.read_text(encoding="utf-8"))
            card = card_out.read_text(encoding="utf-8")

            self.assertEqual(meta["display_name"], "王总")
            self.assertEqual(meta["source_type"], "real-person")
            self.assertIn("archetype_guess", meta["analysis"])
            self.assertIn("## speaking_style", card)
            self.assertIn("## sample_lines", card)


if __name__ == "__main__":
    unittest.main()
