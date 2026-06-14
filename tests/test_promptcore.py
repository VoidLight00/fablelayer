"""tests/test_promptcore.py — PromptCore (FL1) 계약 검증.

검증 범위:
- render 결정성 (반복 호출 동일 출력)
- merge 압축규칙 거부 (COMPRESSION_RE 매치 시 ValueError)
- default_core 9 섹션
- render_markdown(default_core()) == core/promptcore.md (드리프트 없음)
- --check 종료코드(드리프트 없으면 0)
"""

import re
import sys
import unittest
from pathlib import Path

# 직접 실행(python3 tests/test_promptcore.py) 시 리포 루트를 import 경로에 추가.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fablelayer.promptcore import (
    COMPRESSION_RE,
    PromptCore,
    Section,
    default_core,
    main,
    merge,
    render_markdown,
)

_CANONICAL_MD = Path(__file__).resolve().parent.parent / "core" / "promptcore.md"


class TestDefaultCore(unittest.TestCase):
    def test_nine_sections(self):
        core = default_core()
        self.assertEqual(len(core.sections), 9)

    def test_section_ids_in_order(self):
        core = default_core()
        ids = tuple(s.id for s in core.sections)
        self.assertEqual(
            ids,
            (
                "identity",
                "verification-grounding",
                "evidence-gate",
                "systematic-investigation",
                "anti-early-stop",
                "output-structure",
                "value-for-cost",
                "drift-prevention",
                "safety",
            ),
        )

    def test_version_default_and_override(self):
        self.assertEqual(default_core().version, "v2")
        self.assertEqual(default_core("v3").version, "v3")

    def test_every_section_has_inspired_by_and_rules(self):
        for section in default_core().sections:
            self.assertTrue(section.inspired_by, section.id)
            self.assertTrue(section.rules, section.id)

    def test_frozen_dataclasses(self):
        section = default_core().sections[0]
        with self.assertRaises(Exception):
            section.id = "mutated"  # type: ignore[misc]
        core = default_core()
        with self.assertRaises(Exception):
            core.version = "mutated"  # type: ignore[misc]


class TestRenderDeterminism(unittest.TestCase):
    def test_render_is_deterministic(self):
        core = default_core()
        first = render_markdown(core)
        second = render_markdown(core)
        self.assertEqual(first, second)

    def test_render_emits_inspired_by_tag_per_section(self):
        rendered = render_markdown(default_core())
        # 9 섹션 각각 정확히 하나의 내용 있는 [inspired-by: ...] 태그.
        # (footer 의 빈 `[inspired-by:]` 문서 언급은 내용이 없어 제외된다.)
        tags = re.findall(r"^\[inspired-by: .+\]$", rendered, flags=re.MULTILINE)
        self.assertEqual(len(tags), 9)

    def test_render_has_numbered_section_headers(self):
        rendered = render_markdown(default_core())
        for n in range(1, 10):
            self.assertIn(f"## {n}. ", rendered)

    def test_render_matches_canonical_md(self):
        rendered = render_markdown(default_core())
        canonical = _CANONICAL_MD.read_text(encoding="utf-8")
        self.assertEqual(rendered, canonical)


class TestMergeCompression(unittest.TestCase):
    def test_merge_combines_and_dedupes_rules(self):
        base = PromptCore(
            version="v2",
            sections=(
                Section(
                    id="identity",
                    title="Identity",
                    inspired_by=("a",),
                    rules=("rule-1", "rule-2"),
                ),
            ),
        )
        overlay = PromptCore(
            version="v3",
            sections=(
                Section(
                    id="identity",
                    title="Identity",
                    inspired_by=("b",),
                    rules=("rule-2", "rule-3"),  # rule-2 중복
                ),
                Section(
                    id="extra",
                    title="Extra",
                    inspired_by=("c",),
                    rules=("rule-4",),
                ),
            ),
        )
        result = merge(base, overlay)
        self.assertEqual(result.version, "v3")
        ids = tuple(s.id for s in result.sections)
        self.assertEqual(ids, ("identity", "extra"))
        identity = result.sections[0]
        self.assertEqual(identity.rules, ("rule-1", "rule-2", "rule-3"))  # dedupe
        self.assertEqual(identity.inspired_by, ("a", "b"))

    def test_merge_raises_on_compression_rule_in_overlay(self):
        base = default_core()
        bad_overlay = PromptCore(
            version="v2",
            sections=(
                Section(
                    id="identity",
                    title="Identity",
                    inspired_by=("x",),
                    rules=("출력을 압축해서 토큰을 절약하라.",),
                ),
            ),
        )
        with self.assertRaises(ValueError):
            merge(base, bad_overlay)

    def test_merge_raises_on_compression_rule_in_base(self):
        bad_base = PromptCore(
            version="v2",
            sections=(
                Section(
                    id="output-structure",
                    title="Output",
                    inspired_by=("x",),
                    rules=("truncate output to save cost",),
                ),
            ),
        )
        with self.assertRaises(ValueError):
            merge(bad_base, default_core())

    def test_merge_raises_on_english_compress_keyword(self):
        base = default_core()
        overlay = PromptCore(
            version="v2",
            sections=(
                Section(
                    id="x",
                    title="X",
                    inspired_by=("y",),
                    rules=("Always compress the final answer.",),
                ),
            ),
        )
        with self.assertRaises(ValueError):
            merge(base, overlay)

    def test_merge_raises_on_char_limit_keyword(self):
        base = default_core()
        overlay = PromptCore(
            version="v2",
            sections=(
                Section(
                    id="x",
                    title="X",
                    inspired_by=("y",),
                    rules=("응답은 500 글자 수 제한을 둔다.",),
                ),
            ),
        )
        with self.assertRaises(ValueError):
            merge(base, overlay)

    def test_clean_merge_does_not_raise(self):
        base = default_core()
        overlay = PromptCore(
            version="v2",
            sections=(
                Section(
                    id="identity",
                    title="운영 정체성 (Operating Identity)",
                    inspired_by=("추가 출처",),
                    rules=("**검증 우선.** 모든 주장은 증거에 묶는다.",),
                ),
            ),
        )
        result = merge(base, overlay)
        # base 9 섹션 유지, overlay identity rule 추가.
        self.assertEqual(len(result.sections), 9)


class TestCompressionRegex(unittest.TestCase):
    def test_compression_re_constant_present(self):
        self.assertIn("압축", COMPRESSION_RE)
        self.assertIn("compress", COMPRESSION_RE)
        self.assertIn("truncate output", COMPRESSION_RE)


class TestCheckCli(unittest.TestCase):
    def test_check_returns_zero_when_no_drift(self):
        self.assertEqual(main(["--check"]), 0)

    def test_no_arg_returns_zero(self):
        self.assertEqual(main([]), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
