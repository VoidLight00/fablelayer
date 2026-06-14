"""cli.py (FL5, FL11, 회복) — memory 축 검증.

대상: resume RETRO carry(실행 간 학습) + status 산출물 교차검증(자가기재 불신).
모든 테스트는 임시 디렉토리만 사용한다(파괴적 쓰기 없음). cli.PRODUCT_ROOT 를
임시 루트로 일시 패치하고 항상 원복한다.
"""

from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from pathlib import Path

from fablelayer import cli


# ---------------------------------------------------------------------------
# 헬퍼: PRODUCT_ROOT 일시 패치(원복 보장)
# ---------------------------------------------------------------------------
@contextmanager
def _patched_root(root: Path):
    original = cli.PRODUCT_ROOT
    cli.PRODUCT_ROOT = root
    try:
        yield
    finally:
        cli.PRODUCT_ROOT = original


def _args(command: str, *, run_id: str = "", apply: bool = False) -> cli.Args:
    return cli.Args(
        command=command,
        positionals=tuple(),
        apply=apply,
        target="",
        file="",
        run_id=run_id,
    )


def _write_manifest(run_dir: Path, manifest: dict) -> Path:
    run_dir.mkdir(parents=True, exist_ok=True)
    path = run_dir / "RUN_MANIFEST.json"
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# RETRO '다음 액션' 파싱
# ---------------------------------------------------------------------------
class TestParseRetroNextActions(unittest.TestCase):
    def _retro(self, body: str) -> Path:
        d = Path(self._tmp.name)
        p = d / "RETRO.md"
        p.write_text(body, encoding="utf-8")
        return p

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)

    def test_parses_numbered_section(self):
        retro = self._retro(
            "# RETRO\n\n## 결정\n- 무관 항목\n\n## 다음 액션\n"
            "1. 라이브 벤치 실측\n2. GitHub 등록은 승인 후\n3. P1 CI 배선\n\n"
            "## 증거 (실측)\n- selftest PASS\n"
        )
        actions = cli._parse_retro_next_actions(retro)
        self.assertEqual(
            actions,
            ("라이브 벤치 실측", "GitHub 등록은 승인 후", "P1 CI 배선"),
        )

    def test_does_not_bleed_into_next_section(self):
        retro = self._retro("## 다음 액션\n1. 액션A\n## 증거\n- 증거항목\n")
        actions = cli._parse_retro_next_actions(retro)
        self.assertEqual(actions, ("액션A",))
        self.assertNotIn("증거항목", actions)

    def test_strips_bullet_markers(self):
        retro = self._retro("## 다음 액션\n- 불릿 액션\n* 별 액션\n+ 플러스 액션\n")
        actions = cli._parse_retro_next_actions(retro)
        self.assertEqual(actions, ("불릿 액션", "별 액션", "플러스 액션"))

    def test_missing_file_returns_empty(self):
        actions = cli._parse_retro_next_actions(Path(self._tmp.name) / "nope.md")
        self.assertEqual(actions, ())

    def test_missing_section_returns_empty(self):
        retro = self._retro("# RETRO\n\n## 결정\n- 항목\n\n## 증거\n- 항목\n")
        self.assertEqual(cli._parse_retro_next_actions(retro), ())

    def test_paren_numbered_marker(self):
        retro = self._retro("## 다음 액션\n1) 첫째\n2) 둘째\n")
        self.assertEqual(cli._parse_retro_next_actions(retro), ("첫째", "둘째"))


class TestStripListMarker(unittest.TestCase):
    def test_variants(self):
        self.assertEqual(cli._strip_list_marker("12. 본문"), "본문")
        self.assertEqual(cli._strip_list_marker("3) 본문"), "본문")
        self.assertEqual(cli._strip_list_marker("- 본문"), "본문")
        self.assertEqual(cli._strip_list_marker("* 본문"), "본문")
        self.assertEqual(cli._strip_list_marker("마커 없는 본문"), "마커 없는 본문")


# ---------------------------------------------------------------------------
# phase 교차검증 헬퍼
# ---------------------------------------------------------------------------
class TestCrosscheckPhase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)

    def test_done_with_artifact_present_ok(self):
        (self.root / "REQUIREMENTS.md").write_text("x", encoding="utf-8")
        with _patched_root(self.root):
            verdict, _ = cli._crosscheck_phase("0-context", "done")
        self.assertEqual(verdict, "ok")

    def test_done_with_artifact_missing_mismatch(self):
        # 산출물 없는데 done 주장 -> 자가기재 불신(fail-closed)
        with _patched_root(self.root):
            verdict, detail = cli._crosscheck_phase("0-context", "done")
        self.assertEqual(verdict, "mismatch")
        self.assertIn("REQUIREMENTS.md", detail)

    def test_not_done_skips_crosscheck(self):
        with _patched_root(self.root):
            verdict, _ = cli._crosscheck_phase("0-context", "in_progress")
        self.assertEqual(verdict, "ok")

    def test_unmapped_phase_unverifiable(self):
        with _patched_root(self.root):
            verdict, _ = cli._crosscheck_phase("3-gates", "done")
        self.assertEqual(verdict, "unverifiable")


# ---------------------------------------------------------------------------
# build resume manifest (carried_actions 주입)
# ---------------------------------------------------------------------------
class TestBuildResumeManifest(unittest.TestCase):
    def test_injects_carried_actions_and_metadata(self):
        prev = {
            "run_id": "20260614-x",
            "input": "원래 입력",
            "phases": {"0-context": "done", "5-report": "in_progress"},
        }
        carried = ("액션A", "액션B")
        m = cli._build_resume_manifest(prev, "20260614-x-resume", carried)
        self.assertEqual(m["carried_actions"], ["액션A", "액션B"])
        self.assertEqual(m["resumed_from"], "20260614-x")
        self.assertEqual(m["input"], "원래 입력")
        self.assertEqual(m["mode"], "resume")
        self.assertEqual(m["phases"], prev["phases"])

    def test_does_not_mutate_prev(self):
        prev = {"run_id": "r", "phases": {"0-context": "done"}}
        snapshot = json.dumps(prev, sort_keys=True)
        cli._build_resume_manifest(prev, "r-resume", ("a",))
        self.assertEqual(json.dumps(prev, sort_keys=True), snapshot)


class TestWriteResumeManifest(unittest.TestCase):
    def test_writes_valid_json(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        path = Path(tmp.name) / "r-resume" / "RUN_MANIFEST.json"
        manifest = {"run_id": "r-resume", "carried_actions": ["a", "b"]}
        wrote = cli._write_resume_manifest(path, manifest)
        self.assertEqual(wrote, path)
        self.assertTrue(path.is_file())
        loaded = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(loaded["carried_actions"], ["a", "b"])


# ---------------------------------------------------------------------------
# cmd_resume 통합 — RETRO carry end-to-end (임시 루트)
# ---------------------------------------------------------------------------
class TestCmdResumeCarry(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        # 산출물 placeholder — _rerun_phase 가 참조하는 것들을 모두 만들어 통과 보장.
        (self.root / "REQUIREMENTS.md").write_text("x", encoding="utf-8")
        (self.root / "INTERFACE.md").write_text("x", encoding="utf-8")
        (self.root / "core").mkdir()
        from fablelayer import promptcore
        rendered = promptcore.render_markdown(promptcore.default_core())
        (self.root / "core" / "promptcore.md").write_text(rendered, encoding="utf-8")
        (self.root / "bench").mkdir()
        (self.root / "bench" / "RESULTS.md").write_text("x", encoding="utf-8")
        # prior run + RETRO
        run_dir = self.root / "runs" / "r1"
        manifest = {
            "run_id": "r1",
            "mode": "new",
            "input": "원래 입력",
            "phases": {p: "done" for p in cli.CANONICAL_PHASES},
        }
        _write_manifest(run_dir, manifest)
        (run_dir / "RETRO.md").write_text(
            "## 다음 액션\n1. 라이브 벤치\n2. 승인 후 publish\n\n## 증거\n- x\n",
            encoding="utf-8",
        )

    def test_apply_writes_new_manifest_with_carried_actions(self):
        out = io.StringIO()
        with _patched_root(self.root), redirect_stdout(out):
            rc = cli.cmd_resume(_args("resume", apply=True))
        self.assertEqual(rc, cli.EXIT_OK)
        new_path = self.root / "runs" / "r1-resume" / "RUN_MANIFEST.json"
        self.assertTrue(new_path.is_file())
        loaded = json.loads(new_path.read_text(encoding="utf-8"))
        self.assertEqual(loaded["carried_actions"], ["라이브 벤치", "승인 후 publish"])
        self.assertEqual(loaded["resumed_from"], "r1")
        self.assertEqual(loaded["input"], "원래 입력")

    def test_dry_run_does_not_write(self):
        out = io.StringIO()
        with _patched_root(self.root), redirect_stdout(out):
            rc = cli.cmd_resume(_args("resume", apply=False))
        self.assertEqual(rc, cli.EXIT_OK)
        self.assertFalse((self.root / "runs" / "r1-resume").exists())
        self.assertIn("dry-run", out.getvalue())

    def test_carried_actions_printed(self):
        out = io.StringIO()
        with _patched_root(self.root), redirect_stdout(out):
            cli.cmd_resume(_args("resume", apply=False))
        text = out.getvalue()
        self.assertIn("라이브 벤치", text)
        self.assertIn("carried_actions", text)


# ---------------------------------------------------------------------------
# cmd_status 통합 — 산출물 교차검증 fail-closed (임시 루트)
# ---------------------------------------------------------------------------
class TestCmdStatusCrosscheck(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)

    def _make_run(self, phases: dict, *, with_artifacts: bool) -> None:
        if with_artifacts:
            (self.root / "REQUIREMENTS.md").write_text("x", encoding="utf-8")
            (self.root / "INTERFACE.md").write_text("x", encoding="utf-8")
            (self.root / "core").mkdir(exist_ok=True)
            from fablelayer import promptcore
            rendered = promptcore.render_markdown(promptcore.default_core())
            (self.root / "core" / "promptcore.md").write_text(rendered, encoding="utf-8")
            (self.root / "bench").mkdir(exist_ok=True)
            (self.root / "bench" / "RESULTS.md").write_text("x", encoding="utf-8")
        _write_manifest(
            self.root / "runs" / "r1",
            {"run_id": "r1", "mode": "new", "phases": phases},
        )

    def test_mismatch_when_done_but_no_artifacts(self):
        # 모든 phase done 주장하나 산출물 전무 -> 교차검증 실패 exit 2
        self._make_run({p: "done" for p in cli.CANONICAL_PHASES}, with_artifacts=False)
        out, err = io.StringIO(), io.StringIO()
        with _patched_root(self.root), redirect_stdout(out), redirect_stderr(err):
            rc = cli.cmd_status(_args("status"))
        self.assertEqual(rc, cli.EXIT_USAGE)
        self.assertIn("CROSS-CHECK FAIL", err.getvalue())
        self.assertIn("mismatch", out.getvalue())

    def test_ok_when_done_and_artifacts_present(self):
        self._make_run({p: "done" for p in cli.CANONICAL_PHASES}, with_artifacts=True)
        out, err = io.StringIO(), io.StringIO()
        with _patched_root(self.root), redirect_stdout(out), redirect_stderr(err):
            rc = cli.cmd_status(_args("status"))
        self.assertEqual(rc, cli.EXIT_OK)
        self.assertNotIn("CROSS-CHECK FAIL", err.getvalue())

    def test_in_progress_not_flagged_as_mismatch(self):
        # done 미주장 phase 는 산출물 없어도 mismatch 아님(미완 주장은 정직)
        self._make_run(
            {"0-context": "in_progress", "1-spec": "missing",
             "2-build": "todo", "3-gates": "todo",
             "4-bench": "todo", "5-report": "todo"},
            with_artifacts=False,
        )
        out, err = io.StringIO(), io.StringIO()
        with _patched_root(self.root), redirect_stdout(out), redirect_stderr(err):
            rc = cli.cmd_status(_args("status"))
        self.assertEqual(rc, cli.EXIT_OK)
        self.assertNotIn("CROSS-CHECK FAIL", err.getvalue())


if __name__ == "__main__":
    unittest.main()
