"""tests for fablelayer.adapters (FL5).

검증 포인트:
- export_all 이 4+ 실제 파일을 생성한다 (디스크 존재 실측)
- lmstudio JSON 의 metadata.private_prompt_included == False
- 각 export 의 필수 키 존재
- 모든 export 가 단일 소스 render_markdown(default_core()) 에서 파생 (내용 동등)
"""

import json
import tempfile
import unittest
from pathlib import Path

from fablelayer.adapters import (
    export_all,
    export_claude_plugin,
    export_lmstudio,
    export_ollama,
    export_sillytavern,
)
from fablelayer.promptcore import default_core, render_markdown


class TestExportAll(unittest.TestCase):
    def test_export_all_creates_four_plus_real_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = export_all(Path(tmp))
            self.assertGreaterEqual(len(paths), 4, "export_all 은 4개 이상 경로를 반환해야 함")
            for p in paths:
                self.assertTrue(Path(p).exists(), f"파일 미생성: {p}")
                self.assertGreater(Path(p).stat().st_size, 0, f"빈 파일: {p}")

    def test_export_all_returns_path_objects(self):
        with tempfile.TemporaryDirectory() as tmp:
            for p in export_all(Path(tmp)):
                self.assertIsInstance(p, Path)


class TestLmStudio(unittest.TestCase):
    def test_private_prompt_included_is_false(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = export_lmstudio(Path(tmp))
            data = json.loads(Path(p).read_text(encoding="utf-8"))
            self.assertIn("metadata", data)
            self.assertIn("private_prompt_included", data["metadata"])
            self.assertIs(data["metadata"]["private_prompt_included"], False)

    def test_required_keys(self):
        with tempfile.TemporaryDirectory() as tmp:
            data = json.loads(export_lmstudio(Path(tmp)).read_text(encoding="utf-8"))
            for key in ("preset_name", "system_prompt", "metadata"):
                self.assertIn(key, data, f"누락 키: {key}")

    def test_system_prompt_from_single_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            data = json.loads(export_lmstudio(Path(tmp)).read_text(encoding="utf-8"))
            self.assertEqual(data["system_prompt"], render_markdown(default_core()))


class TestSillyTavern(unittest.TestCase):
    def test_required_keys(self):
        with tempfile.TemporaryDirectory() as tmp:
            data = json.loads(export_sillytavern(Path(tmp)).read_text(encoding="utf-8"))
            for key in ("name", "description", "prompt"):
                self.assertIn(key, data, f"누락 키: {key}")
            self.assertEqual(data["prompt"], render_markdown(default_core()))


class TestOllama(unittest.TestCase):
    def test_modelfile_has_from_param_system(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = export_ollama(Path(tmp), base_model="mistral")
            text = Path(p).read_text(encoding="utf-8")
            self.assertIn("FROM mistral", text)
            self.assertIn("PARAMETER", text)
            self.assertIn("SYSTEM", text)
            # SYSTEM 본문이 단일 소스에서 파생됐는지 (핵심 머리말 토큰 확인)
            self.assertIn("PromptCore (Layer 1)", text)

    def test_empty_base_model_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                export_ollama(Path(tmp), base_model="")


class TestClaudePlugin(unittest.TestCase):
    def test_returns_list_of_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = export_claude_plugin(Path(tmp))
            self.assertIsInstance(paths, list)
            self.assertGreaterEqual(len(paths), 1)
            for p in paths:
                self.assertTrue(Path(p).exists())

    def test_plugin_json_metadata_no_private_prompt(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = export_claude_plugin(Path(tmp))
            plugin_json = next(p for p in paths if Path(p).name == "plugin.json")
            data = json.loads(Path(plugin_json).read_text(encoding="utf-8"))
            for key in ("name", "version", "description"):
                self.assertIn(key, data)
            self.assertIs(data["metadata"]["private_prompt_included"], False)


class TestSingleSourceConsistency(unittest.TestCase):
    def test_all_exports_share_one_rendered_core(self):
        core = render_markdown(default_core())
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            export_all(root)
            lm = json.loads(
                (root / "lmstudio" / "lmstudio.preset.json").read_text(encoding="utf-8")
            )
            st = json.loads(
                (root / "sillytavern" / "sillytavern.preset.json").read_text(encoding="utf-8")
            )
            plugin_md = (root / "claude-plugin" / "promptcore.md").read_text(encoding="utf-8")
            self.assertEqual(lm["system_prompt"], core)
            self.assertEqual(st["prompt"], core)
            self.assertEqual(plugin_md, core)


if __name__ == "__main__":
    unittest.main(verbosity=2)
