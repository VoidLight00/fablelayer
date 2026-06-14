"""tests for fablelayer.source_policy (FL7, FL-GAP-01)."""

import unittest

from fablelayer.source_policy import (
    CLASS,
    Source,
    audit,
    classify,
    default_ledger,
)


class TestClassify(unittest.TestCase):
    def test_leaked_is_reference_only(self):
        result = classify("blocked-prompt-source-a", "non-public-prompt", is_leaked=True)
        self.assertEqual(result, "reference-only")

    def test_leaked_overrides_permissive_license(self):
        # non-public이면 라이선스가 MIT여도 reference-only
        result = classify("x", "MIT", is_leaked=True)
        self.assertEqual(result, "reference-only")

    def test_mit_is_adapt(self):
        self.assertEqual(classify("fablize", "MIT", is_leaked=False), "adapt")

    def test_permissive_aliases_adapt(self):
        for lic in ("Apache-2.0", "BSD-3-Clause", "ISC", "The Unlicense"):
            self.assertEqual(classify("x", lic, is_leaked=False), "adapt")

    def test_unknown_license_is_unverified(self):
        for lic in ("", "unknown", "라이선스 불명확", "N/A", "TBD"):
            self.assertEqual(
                classify("x", lic, is_leaked=False),
                "unverified",
                msg=f"license={lic!r}",
            )

    def test_identified_nonpermissive_is_reference_only(self):
        # 식별 가능하지만 비허용 라이선스는 보수적으로 reference-only
        self.assertEqual(classify("x", "GPL-3.0", is_leaked=False), "reference-only")


class TestDefaultLedger(unittest.TestCase):
    def test_has_ten_sources(self):
        ledger = default_ledger()
        self.assertEqual(len(ledger), 10)

    def test_all_sources_frozen_dataclass(self):
        ledger = default_ledger()
        for src in ledger:
            self.assertIsInstance(src, Source)
            with self.assertRaises(Exception):
                src.name = "mutated"  # frozen

    def test_classifications_in_CLASS(self):
        for src in default_ledger():
            self.assertIn(src.classification, CLASS)

    def test_risk_valid(self):
        for src in default_ledger():
            self.assertIn(src.risk, ("low", "medium", "high"))

    def test_leaked_sources_are_reference_only_high(self):
        ledger = default_ledger()
        leaked = [s for s in ledger if "non-public-prompt" in s.license.lower()]
        self.assertEqual(len(leaked), 2)  # blocked-prompt-source-a, blocked-prompt-source-b
        for src in leaked:
            self.assertEqual(src.classification, "reference-only")
            self.assertEqual(src.risk, "high")

    def test_expected_source_names_present(self):
        names = {s.name for s in default_ledger()}
        expected = {
            "fablize",
            "value-for-fable",
            "supergoal",
            "context-handoff-bundle",
            "sgup/ai",
            "awesome-claude-fable-5",
            "xonovex/platform",
            "Cheswick",
            "blocked-prompt-source-a",
            "blocked-prompt-source-b",
        }
        self.assertEqual(names, expected)


class TestAudit(unittest.TestCase):
    def test_default_ledger_passes(self):
        result = audit(default_ledger())
        self.assertTrue(result.passed, msg=str(result.reasons))
        self.assertEqual(result.reasons, ())

    def test_leaked_classified_copy_fails(self):
        bad = (
            Source(
                name="blocked-prompt-source-a",
                url="https://github.com/elder-plinius/blocked-prompt-source-a",
                license="non-public-prompt",
                classification="copy",
                risk="high",
            ),
        )
        result = audit(bad)
        self.assertFalse(result.passed)
        self.assertTrue(any("copy/adapt" in r for r in result.reasons))

    def test_leaked_classified_adapt_fails(self):
        bad = (
            Source(
                name="blocked-source",
                url="https://example.com",
                license="non-public-prompt",
                classification="adapt",
                risk="high",
            ),
        )
        result = audit(bad)
        self.assertFalse(result.passed)

    def test_blocked_source_present_fails(self):
        bad = (
            Source(
                name="blocked-thing",
                url="https://example.com",
                license="MIT",
                classification="blocked",
                risk="high",
            ),
        )
        result = audit(bad)
        self.assertFalse(result.passed)
        self.assertTrue(any("blocked" in r for r in result.reasons))

    def test_invalid_classification_fails_closed(self):
        bad = (
            Source(
                name="weird",
                url="https://example.com",
                license="MIT",
                classification="frobnicate",
                risk="low",
            ),
        )
        result = audit(bad)
        self.assertFalse(result.passed)

    def test_invalid_risk_fails_closed(self):
        bad = (
            Source(
                name="weird-risk",
                url="https://example.com",
                license="MIT",
                classification="adapt",
                risk="extreme",
            ),
        )
        result = audit(bad)
        self.assertFalse(result.passed)

    def test_clean_adapt_source_passes(self):
        ok = (
            Source(
                name="fablize",
                url="https://github.com/fivetaku/fablize",
                license="MIT",
                classification="adapt",
                risk="low",
            ),
        )
        result = audit(ok)
        self.assertTrue(result.passed, msg=str(result.reasons))


if __name__ == "__main__":
    unittest.main()
