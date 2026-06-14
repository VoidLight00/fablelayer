"""router.py (FL3/FL4) 검증.

각 신호 발화 → opus, 무신호 → sonnet, explicit_opus 비강등,
note 의 'capability not transferable' 보장.
"""

import unittest

from fablelayer.router import (
    CAPABILITY_NOTE,
    DEFAULT_MODEL,
    ESCALATED_MODEL,
    ESCALATION_SIGNALS,
    RouteDecision,
    TaskSpec,
    route,
)


class TestEscalationSignals(unittest.TestCase):
    def test_exactly_six_signals(self):
        self.assertEqual(len(ESCALATION_SIGNALS), 6)

    def test_signal_names_match_contract(self):
        names = {sig.name for sig in ESCALATION_SIGNALS}
        expected = {
            "dep_depth>=3",
            "deep_reasoning",
            "files>=3",
            "context_pct>=0.8",
            "gate_failures>=2",
            "explicit_opus",
        }
        self.assertEqual(names, expected)


class TestNoSignal(unittest.TestCase):
    def test_baseline_routes_to_sonnet(self):
        d = route(TaskSpec(kind="trivial"))
        self.assertEqual(d.model, DEFAULT_MODEL)
        self.assertEqual(d.model, "sonnet")
        self.assertEqual(d.fired_signals, ())

    def test_just_below_thresholds_stays_sonnet(self):
        d = route(
            TaskSpec(
                kind="edge",
                dependency_depth=2,
                files_touched=2,
                context_pct=0.79,
                gate_failures=1,
                deep_reasoning=False,
                explicit_opus=False,
            )
        )
        self.assertEqual(d.model, "sonnet")
        self.assertEqual(d.fired_signals, ())


class TestEachSignalEscalates(unittest.TestCase):
    def test_dep_depth(self):
        d = route(TaskSpec(kind="k", dependency_depth=3))
        self.assertEqual(d.model, ESCALATED_MODEL)
        self.assertIn("dep_depth>=3", d.fired_signals)

    def test_deep_reasoning(self):
        d = route(TaskSpec(kind="k", deep_reasoning=True))
        self.assertEqual(d.model, "opus")
        self.assertIn("deep_reasoning", d.fired_signals)

    def test_files_touched(self):
        d = route(TaskSpec(kind="k", files_touched=3))
        self.assertEqual(d.model, "opus")
        self.assertIn("files>=3", d.fired_signals)

    def test_context_pct(self):
        d = route(TaskSpec(kind="k", context_pct=0.8))
        self.assertEqual(d.model, "opus")
        self.assertIn("context_pct>=0.8", d.fired_signals)

    def test_gate_failures(self):
        d = route(TaskSpec(kind="k", gate_failures=2))
        self.assertEqual(d.model, "opus")
        self.assertIn("gate_failures>=2", d.fired_signals)

    def test_explicit_opus(self):
        d = route(TaskSpec(kind="k", explicit_opus=True))
        self.assertEqual(d.model, "opus")
        self.assertIn("explicit_opus", d.fired_signals)


class TestExplicitOpusNotDowngraded(unittest.TestCase):
    def test_explicit_opus_alone_stays_opus(self):
        d = route(TaskSpec(kind="k", explicit_opus=True))
        self.assertEqual(d.model, "opus")

    def test_explicit_opus_with_no_other_signal_not_downgraded(self):
        # 다른 모든 신호가 임계값 아래여도 explicit_opus 면 opus 유지
        d = route(
            TaskSpec(
                kind="k",
                dependency_depth=0,
                files_touched=0,
                context_pct=0.0,
                gate_failures=0,
                deep_reasoning=False,
                explicit_opus=True,
            )
        )
        self.assertEqual(d.model, "opus")
        self.assertEqual(d.fired_signals, ("explicit_opus",))


class TestNoteAlwaysCarriesCapabilityNotice(unittest.TestCase):
    def test_note_on_escalation(self):
        d = route(TaskSpec(kind="k", deep_reasoning=True))
        self.assertIn(CAPABILITY_NOTE, d.note)
        self.assertIn("capability not transferable", d.note)

    def test_note_on_default(self):
        d = route(TaskSpec(kind="k"))
        self.assertIn(CAPABILITY_NOTE, d.note)


class TestDeterminismAndImmutability(unittest.TestCase):
    def test_route_is_deterministic(self):
        spec = TaskSpec(kind="k", files_touched=5, deep_reasoning=True)
        self.assertEqual(route(spec), route(spec))

    def test_fired_signals_ordered_by_signal_order(self):
        d = route(
            TaskSpec(
                kind="k",
                dependency_depth=3,
                files_touched=3,
                explicit_opus=True,
            )
        )
        # ESCALATION_SIGNALS 순서: dep_depth, deep_reasoning, files, context, gate, explicit
        self.assertEqual(d.fired_signals, ("dep_depth>=3", "files>=3", "explicit_opus"))

    def test_dataclasses_frozen(self):
        spec = TaskSpec(kind="k")
        with self.assertRaises(Exception):
            spec.kind = "other"  # type: ignore[misc]
        dec = RouteDecision(model="sonnet", fired_signals=(), note="n")
        with self.assertRaises(Exception):
            dec.model = "opus"  # type: ignore[misc]


if __name__ == "__main__":
    unittest.main()
