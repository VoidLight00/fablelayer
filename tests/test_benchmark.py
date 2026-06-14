"""tests/test_benchmark.py — judge 재현성 + write_raw JSON 스키마 (FL6).

stdlib unittest only. 라이브 모델 호출 없음(judge B 는 결정론).
write_raw 는 임시 파일에만 쓴다 — 큐레이트된 bench/raw.json placeholder 를 건드리지 않는다.
"""

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fablelayer.benchmark import (  # noqa: E402
    DISAGREE_THRESHOLD,
    JUDGE_A_NAME,
    JUDGE_B_NAME,
    JUDGE_NAME,
    SENTINEL_GUARD,
    BenchRun,
    BenchTask,
    deterministic_judge,
    disagree_runs,
    disagreement_cases,
    rubric_judge_a,
    run_suite,
    run_suite_dual,
    update_results_disagreement,
    write_raw,
)


class TestDeterministicJudge(unittest.TestCase):
    def test_reproducible_same_input_same_score(self):
        task = BenchTask(
            id="t1",
            prompt="root cause를 찾아라",
            rubric=("root cause", "fix", "test", "verify"),
        )
        output = "The root cause is an off-by-one; the fix passes the test after verify."
        scores = [deterministic_judge(output, task) for _ in range(10)]
        # 10회 호출 모두 동일해야 한다(재현성).
        self.assertEqual(len(set(scores)), 1)
        # 4개 키워드 전부 매칭(test/verify/fix/root cause) → 100.0
        self.assertEqual(scores[0], 100.0)

    def test_partial_coverage_math(self):
        task = BenchTask(id="t2", prompt="p", rubric=("alpha", "beta", "gamma", "delta"))
        # 2/4 매칭 → 50.0
        self.assertEqual(deterministic_judge("alpha and beta only", task), 50.0)
        # 1/4 매칭 → 25.0
        self.assertEqual(deterministic_judge("only gamma here", task), 25.0)
        # 0/4 매칭 → 0.0
        self.assertEqual(deterministic_judge("nothing relevant", task), 0.0)

    def test_score_range_0_to_100(self):
        task = BenchTask(id="t3", prompt="p", rubric=("x", "y", "z"))
        for out in ["", "x", "x y", "x y z", "x x x y y z"]:
            s = deterministic_judge(out, task)
            self.assertGreaterEqual(s, 0.0)
            self.assertLessEqual(s, 100.0)

    def test_case_and_whitespace_insensitive(self):
        task = BenchTask(id="t4", prompt="p", rubric=("Root Cause",))
        self.assertEqual(deterministic_judge("the   ROOT   cause here", task), 100.0)

    def test_failclosed_empty_rubric(self):
        # rubric 이 비면 채점 근거 없음 → 0.0 (공짜 점수 금지).
        task = BenchTask(id="t5", prompt="p", rubric=())
        self.assertEqual(deterministic_judge("anything at all", task), 0.0)

    def test_failclosed_empty_output(self):
        task = BenchTask(id="t6", prompt="p", rubric=("a", "b"))
        self.assertEqual(deterministic_judge("", task), 0.0)
        self.assertEqual(deterministic_judge("    ", task), 0.0)

    def test_failclosed_blank_keywords_excluded(self):
        # 공백 키워드는 분모에서도 제외돼야 한다(공짜 분자 금지).
        task = BenchTask(id="t7", prompt="p", rubric=("real", "", "   "))
        # 유효 키워드 1개(real)만 분모. 매칭 1/1 → 100.0
        self.assertEqual(deterministic_judge("real thing", task), 100.0)
        # 유효 키워드 전무면 0.0
        blank = BenchTask(id="t7b", prompt="p", rubric=("", "  "))
        self.assertEqual(deterministic_judge("real thing", blank), 0.0)


class TestRunSuite(unittest.TestCase):
    def _tasks(self):
        return (
            BenchTask(id="dbg-001", prompt="debug", rubric=("root cause", "fix")),
            BenchTask(id="ext-001", prompt="extract", rubric=("action", "owner", "decision")),
        )

    def test_run_suite_order_and_judge(self):
        tasks = self._tasks()
        outputs = {
            "dbg-001": "root cause found, fix applied",
            "ext-001": "action and owner listed, decision recorded",
        }
        runs = run_suite(tasks, outputs)
        self.assertEqual(len(runs), 2)
        # 입력 순서 보존(결정론).
        self.assertEqual(runs[0].task_id, "dbg-001")
        self.assertEqual(runs[1].task_id, "ext-001")
        for r in runs:
            self.assertIsInstance(r, BenchRun)
            self.assertEqual(r.judge, JUDGE_NAME)
        self.assertEqual(runs[0].score, 100.0)
        self.assertEqual(runs[1].score, 100.0)

    def test_run_suite_failclosed_missing_output(self):
        tasks = self._tasks()
        # ext-001 출력 누락 → 빈 문자열 취급 → 0.0
        runs = run_suite(tasks, {"dbg-001": "root cause and fix"})
        by_id = {r.task_id: r for r in runs}
        self.assertEqual(by_id["dbg-001"].score, 100.0)
        self.assertEqual(by_id["ext-001"].score, 0.0)
        self.assertFalse(by_id["ext-001"].raw["output_present"])

    def test_run_suite_reproducible(self):
        tasks = self._tasks()
        outputs = {"dbg-001": "root cause", "ext-001": "action owner"}
        runs_a = run_suite(tasks, outputs)
        runs_b = run_suite(tasks, outputs)
        self.assertEqual(
            [(r.task_id, r.score) for r in runs_a],
            [(r.task_id, r.score) for r in runs_b],
        )

    def test_benchrun_frozen(self):
        run = BenchRun(task_id="x", model="m", judge="j", score=1.0)
        with self.assertRaises(Exception):
            run.score = 2.0  # type: ignore[misc]


class TestWriteRaw(unittest.TestCase):
    def _runs(self):
        tasks = (
            BenchTask(id="dbg-001", prompt="debug", rubric=("root cause", "fix")),
        )
        return run_suite(tasks, {"dbg-001": "root cause and fix"})

    def test_write_raw_valid_json_and_schema(self):
        runs = self._runs()
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "raw.json")
            write_raw(runs, path)
            self.assertTrue(os.path.exists(path))
            with open(path, encoding="utf-8") as fh:
                data = json.load(fh)
            # 최상위 필수 키.
            for key in ("schema_version", "judge", "generator", "sentinel_guard", "runs"):
                self.assertIn(key, data)
            self.assertEqual(data["sentinel_guard"], SENTINEL_GUARD)
            self.assertEqual(data["judge"], JUDGE_NAME)
            self.assertIsInstance(data["runs"], list)
            self.assertEqual(len(data["runs"]), 1)
            entry = data["runs"][0]
            for key in ("task_id", "model", "judge", "score", "raw"):
                self.assertIn(key, entry)
            self.assertEqual(entry["task_id"], "dbg-001")
            self.assertEqual(entry["score"], 100.0)

    def test_write_raw_score_matches_raw_sentinel_guard(self):
        # SENTINEL_GUARD 정합: 직렬화된 score 가 raw 의 매칭 카운트와 어긋나지 않아야 한다.
        runs = self._runs()
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "raw.json")
            write_raw(runs, path)
            with open(path, encoding="utf-8") as fh:
                data = json.load(fh)
            entry = data["runs"][0]
            raw = entry["raw"]
            expected = round((raw["matched_count"] / raw["rubric_count"]) * 100.0, 6)
            self.assertEqual(entry["score"], expected)

    def test_write_raw_deterministic_bytes(self):
        # 동일 runs → 동일 바이트(sort_keys 결정론).
        runs = self._runs()
        with tempfile.TemporaryDirectory() as d:
            p1 = os.path.join(d, "a.json")
            p2 = os.path.join(d, "b.json")
            write_raw(runs, p1)
            write_raw(runs, p2)
            with open(p1, "rb") as f1, open(p2, "rb") as f2:
                self.assertEqual(f1.read(), f2.read())


class TestJudgeA(unittest.TestCase):
    """judge A(rubric 0-5 모사) 결정성·논리."""

    def test_reproducible(self):
        task = BenchTask(id="a1", prompt="p", rubric=("root cause", "fix", "test"))
        out = "root cause found via exit code 0; fix verified by test pass"
        scores = [rubric_judge_a(out, task) for _ in range(10)]
        self.assertEqual(len(set(scores)), 1)

    def test_keyword_only_caps_at_half(self):
        # 근거 마커가 없으면 coverage 만점이어도 A 는 50.0 (2.5/5) 으로 묶인다.
        task = BenchTask(id="a2", prompt="p", rubric=("alpha", "beta", "gamma"))
        out = "alpha beta gamma listed but nothing demonstrated."
        self.assertEqual(deterministic_judge(out, task), 100.0)
        self.assertEqual(rubric_judge_a(out, task), 50.0)

    def test_failclosed_empty(self):
        task = BenchTask(id="a3", prompt="p", rubric=("x",))
        self.assertEqual(rubric_judge_a("", task), 0.0)
        empty_rubric = BenchTask(id="a4", prompt="p", rubric=())
        self.assertEqual(rubric_judge_a("anything", empty_rubric), 0.0)

    def test_score_range(self):
        task = BenchTask(id="a5", prompt="p", rubric=("x", "y"))
        for out in ["", "x", "x y", "x y verified exit code test pass /a/b.py"]:
            s = rubric_judge_a(out, task)
            self.assertGreaterEqual(s, 0.0)
            self.assertLessEqual(s, 100.0)


class TestDisagreementPreservation(unittest.TestCase):
    """recover 축: A/B 불일치를 평균으로 덮지 않고 둘 다 남기는지 검증."""

    def _split_task(self):
        # 키워드는 전부 채우나 근거 마커가 없는 출력 → B 100, A 50 (Δ=50, 불일치).
        return BenchTask(
            id="disagree-x",
            prompt="alpha beta gamma delta — listed without reasoning.",
            rubric=("alpha", "beta", "gamma", "delta"),
        )

    def test_both_verdicts_kept_not_averaged(self):
        task = self._split_task()
        out = task.prompt
        run_a, run_b = disagree_runs(task, out)
        # 두 개의 독립 BenchRun(A, B), 점수가 서로 다르다(평균으로 합치지 않음).
        self.assertEqual(run_a.judge, JUDGE_A_NAME)
        self.assertEqual(run_b.judge, JUDGE_B_NAME)
        self.assertEqual(run_b.score, 100.0)
        self.assertEqual(run_a.score, 50.0)
        self.assertNotEqual(run_a.score, run_b.score)
        # 평균(75.0)으로 덮이지 않았음을 명시 검증.
        self.assertNotIn(75.0, (run_a.score, run_b.score))

    def test_raw_carries_cross_judge_and_disagree(self):
        task = self._split_task()
        run_a, run_b = disagree_runs(task, task.prompt)
        # 각 raw 가 상대 심판 점수를 보존한다(불일치 추적 가능).
        self.assertEqual(run_a.raw["other_judge"], JUDGE_B_NAME)
        self.assertEqual(run_a.raw["other_score"], run_b.score)
        self.assertEqual(run_b.raw["other_judge"], JUDGE_A_NAME)
        self.assertEqual(run_b.raw["other_score"], run_a.score)
        # 불일치 판정이 대칭이고 임계 이상이다.
        self.assertTrue(run_a.raw["disagree"])
        self.assertTrue(run_b.raw["disagree"])
        self.assertEqual(run_a.raw["delta"], run_b.raw["delta"])
        self.assertGreaterEqual(run_a.raw["delta"], DISAGREE_THRESHOLD)

    def test_agreement_not_flagged(self):
        # A 와 B 가 가까우면 불일치 아님.
        task = BenchTask(id="agree", prompt="p", rubric=("x", "y"))
        out = "x y"  # B=100; A=coverage 2.5 + markers 0 → 50; Δ=50 ... 일부러 가까운 케이스 사용
        # 가까운 케이스: 근거 마커가 충분해 A 가 B 에 근접하도록 구성.
        out2 = "x y because verified via exit code test pass /a/b.py step 1"
        ra, rb = disagree_runs(task, out2)
        self.assertEqual(rb.score, 100.0)
        self.assertEqual(ra.score, 100.0)  # markers 충분 → A 도 만점
        self.assertFalse(ra.raw["disagree"])

    def test_run_suite_dual_two_runs_per_task(self):
        tasks = (
            BenchTask(id="t1", prompt="p1", rubric=("a", "b")),
            BenchTask(id="t2", prompt="p2", rubric=("c",)),
        )
        runs = run_suite_dual(tasks, {"t1": "a b", "t2": "c"})
        self.assertEqual(len(runs), 4)  # task 당 A, B 2개
        judges = [r.judge for r in runs]
        self.assertEqual(judges, [JUDGE_A_NAME, JUDGE_B_NAME, JUDGE_A_NAME, JUDGE_B_NAME])
        # 순서: task 입력 순서 보존.
        self.assertEqual(runs[0].task_id, "t1")
        self.assertEqual(runs[2].task_id, "t2")

    def test_run_suite_dual_failclosed_missing_output(self):
        tasks = (BenchTask(id="t1", prompt="p", rubric=("a",)),)
        runs = run_suite_dual(tasks, {})  # 출력 없음 → 양쪽 0.0
        self.assertEqual([r.score for r in runs], [0.0, 0.0])

    def test_disagreement_cases_extraction(self):
        split = self._split_task()
        agree = BenchTask(id="agree", prompt="p", rubric=("z",))
        runs = run_suite_dual(
            (split, agree),
            {split.id: split.prompt, "agree": "z because verified via exit code test pass step 1"},
        )
        cases = disagreement_cases(runs)
        ids = [c["task_id"] for c in cases]
        self.assertIn(split.id, ids)
        self.assertNotIn("agree", ids)
        # case 는 양쪽 점수를 그대로 보존(평균 없음).
        c = next(c for c in cases if c["task_id"] == split.id)
        self.assertEqual(c["score_b"], 100.0)
        self.assertEqual(c["score_a"], 50.0)
        self.assertGreaterEqual(c["delta"], DISAGREE_THRESHOLD)


class TestUpdateResultsDisagreement(unittest.TestCase):
    """RESULTS.md '## 심판 불일치' 절만 실데이터로 교체하고 '## 한계' 는 보존."""

    _DOC = (
        "# RESULTS\n\n"
        "## 채점 방법론\n\n본문.\n\n"
        "## 심판 불일치 (측정 시 기록)\n\n현재는 미측정이라 기록 없음.\n\n"
        "## 재현 절차\n\n절차.\n\n"
        "## 한계\n\n이 섹션은 필수다.\n"
    )

    def _write_doc(self, d):
        path = os.path.join(d, "RESULTS.md")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(self._DOC)
        return path

    def _cases(self):
        return (
            {
                "task_id": "disagree-x",
                "score_a": 50.0,
                "score_b": 100.0,
                "delta": 50.0,
                "matched_count": 4,
                "rubric_count": 4,
                "quality_markers": 0,
                "prompt": "p",
            },
        )

    def test_replaces_section_and_preserves_limits(self):
        with tempfile.TemporaryDirectory() as d:
            path = self._write_doc(d)
            ok = update_results_disagreement(path, self._cases())
            self.assertTrue(ok)
            with open(path, encoding="utf-8") as fh:
                text = fh.read()
            # 실데이터 행이 들어갔다.
            self.assertIn("| disagree-x |", text)
            # placeholder 문구는 사라졌다.
            self.assertNotIn("현재는 미측정이라 기록 없음.", text)
            # '## 한계' 절과 본문은 그대로 보존(게이트 요구).
            self.assertIn("## 한계", text)
            self.assertIn("이 섹션은 필수다.", text)
            # '## 재현 절차' 도 보존.
            self.assertIn("## 재현 절차", text)
            self.assertIn("절차.", text)

    def test_idempotent_no_duplicate(self):
        with tempfile.TemporaryDirectory() as d:
            path = self._write_doc(d)
            update_results_disagreement(path, self._cases())
            update_results_disagreement(path, self._cases())
            with open(path, encoding="utf-8") as fh:
                text = fh.read()
            self.assertEqual(text.count("## 심판 불일치"), 1)
            self.assertEqual(text.count("| disagree-x |"), 1)
            self.assertEqual(text.count("## 한계"), 1)

    def test_failclosed_no_section(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "RESULTS.md")
            with open(path, "w", encoding="utf-8") as fh:
                fh.write("# RESULTS\n\n## 한계\n\n필수.\n")
            # 불일치 절이 없으면 삽입하지 않고 False(다른 절 오염 방지).
            ok = update_results_disagreement(path, self._cases())
            self.assertFalse(ok)
            with open(path, encoding="utf-8") as fh:
                text = fh.read()
            self.assertNotIn("disagree-x", text)
            self.assertIn("## 한계", text)

    def test_empty_cases_renders_zero_honestly(self):
        with tempfile.TemporaryDirectory() as d:
            path = self._write_doc(d)
            ok = update_results_disagreement(path, tuple())
            self.assertTrue(ok)
            with open(path, encoding="utf-8") as fh:
                text = fh.read()
            self.assertIn("불일치 0건", text)
            self.assertIn("## 한계", text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
