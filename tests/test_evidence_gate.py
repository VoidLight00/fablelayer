"""FL2 evidence_gate 셀프테스트 (stdlib unittest, 외부 의존 0)."""

import re
import unittest

from fablelayer.evidence_gate import (
    ACCEPTED_EVIDENCE_RE,
    COMPLETION_RE,
    Claim,
    GateResult,
    check_claim,
    scan_text,
)


class TestContractRegex(unittest.TestCase):
    def test_regex_strings_match_contract(self):
        # 계약 SSoT(INTERFACE.md FL2) 글자 일치 확인.
        self.assertEqual(
            ACCEPTED_EVIDENCE_RE,
            r"(exit\s*code|exit\s*\d|test.*(pass|fail)|grep|\d+\s*(개|matches)"
            r"|/[\w./-]+\.\w+|render|스크린샷)",
        )
        self.assertEqual(
            COMPLETION_RE,
            r"(done|완료|통과|fixed|배포됨|작동(한다|함)|passed)",
        )

    def test_regex_compile(self):
        # 정규식이 컴파일 가능해야 한다(잘못된 이스케이프 회귀 방지).
        re.compile(ACCEPTED_EVIDENCE_RE)
        re.compile(COMPLETION_RE)


class TestCheckClaim(unittest.TestCase):
    def test_completion_without_evidence_fails(self):
        # 완료어 있음 + evidence 비어있음 -> fail-closed.
        r = check_claim(Claim(text="구현 완료", evidence=()))
        self.assertIsInstance(r, GateResult)
        self.assertFalse(r.passed)
        self.assertTrue(any("empty" in x for x in r.reasons))

    def test_completion_with_nonmatching_evidence_fails(self):
        # 완료어 있음 + 증거가 ACCEPTED_EVIDENCE_RE 미매치 -> fail.
        r = check_claim(Claim(text="done", evidence=("그냥 했어요", "믿어주세요")))
        self.assertFalse(r.passed)

    def test_completion_with_valid_evidence_passes(self):
        # 완료어 + 유효 증거(exit code / 파일경로) -> pass.
        r = check_claim(
            Claim(text="배포됨", evidence=("exit 0", "/path/to/out.json"))
        )
        self.assertTrue(r.passed)

    def test_evidence_grep_count_render_screenshot_pass(self):
        # 다양한 accepted 증거 토큰이 통과해야 한다.
        cases = [
            ("3 개 matches found", "통과"),
            ("grep -c returned 5", "passed"),
            ("render 확인됨", "작동한다"),
            ("스크린샷 첨부", "fixed"),
            ("test suite pass", "done"),
        ]
        for ev, claim in cases:
            with self.subTest(ev=ev):
                r = check_claim(Claim(text=claim, evidence=(ev,)))
                self.assertTrue(r.passed, msg=f"evidence {ev!r} should pass")

    def test_no_completion_claim_is_not_applicable(self):
        # 완료어 없음 -> 게이트 비대상, 통과.
        r = check_claim(Claim(text="작업을 살펴보는 중", evidence=()))
        self.assertTrue(r.passed)


class TestScanTextNegative(unittest.TestCase):
    def test_clean_text_passes(self):
        r = scan_text("코드를 작성했습니다. exit 0 으로 확인했습니다.")
        self.assertTrue(r.passed)

    def test_promise_with_evidence_passes(self):
        # 약속 표현이 있어도 완료-증거가 함께 있으면 통과(오탐 완화).
        r = scan_text("이제 구현하겠습니다. 구현했습니다. tests passed.")
        self.assertTrue(r.passed)

    def test_plain_descriptive_text_passes(self):
        r = scan_text("이 함수는 입력을 검증하고 결과를 반환한다.")
        self.assertTrue(r.passed)

    # --- 오탐 방지: 약속+실행 동반 문장은 통과해야 한다 (한국어) ---
    def test_promise_then_exit0_passes(self):
        r = scan_text("모듈을 구현하겠습니다. 구현했습니다. exit 0.")
        self.assertTrue(r.passed, msg=r.reasons)

    def test_promise_then_build_passed_passes(self):
        # '빌드 통과'는 '테스트 통과'가 아니어도 완료-증거로 인정해야 한다.
        r = scan_text("다음으로 빌드를 시작하겠습니다. 시작했고 빌드 통과.")
        self.assertTrue(r.passed, msg=r.reasons)

    def test_promise_then_bare_passed_passes(self):
        r = scan_text("테스트하겠습니다. 통과.")
        self.assertTrue(r.passed, msg=r.reasons)

    def test_promise_then_build_success_passes(self):
        r = scan_text("수정하겠습니다. 빌드 성공.")
        self.assertTrue(r.passed, msg=r.reasons)

    def test_promise_then_deploy_complete_passes(self):
        r = scan_text("배포하겠습니다. 배포 완료.")
        self.assertTrue(r.passed, msg=r.reasons)

    def test_promise_then_grep_count_passes(self):
        r = scan_text("검증하겠습니다. 검증 결과 정상이며 grep 으로 0건 확인.")
        self.assertTrue(r.passed, msg=r.reasons)

    def test_promise_then_filepath_passes(self):
        r = scan_text("확인하겠습니다. /path/to/file.py 생성됨.")
        self.assertTrue(r.passed, msg=r.reasons)

    def test_promise_then_match_count_passes(self):
        r = scan_text("구현하겠습니다. 5 개 matches.")
        self.assertTrue(r.passed, msg=r.reasons)

    def test_promise_then_screenshot_passes(self):
        r = scan_text("실행하겠습니다. 스크린샷 첨부.")
        self.assertTrue(r.passed, msg=r.reasons)

    def test_promise_then_render_passes(self):
        r = scan_text("리뷰하겠습니다. render 확인.")
        self.assertTrue(r.passed, msg=r.reasons)

    def test_promise_then_done_passes(self):
        # COMPLETION_RE 완료어(done)도 실행 신호로 인정한다.
        r = scan_text("처리하겠습니다. done.")
        self.assertTrue(r.passed, msg=r.reasons)

    def test_promise_then_progress_done_passes(self):
        r = scan_text("리팩토링을 진행하겠습니다. 진행했고 종료 코드 0 으로 확인했습니다.")
        self.assertTrue(r.passed, msg=r.reasons)

    # --- 오탐 방지: 약속+실행 동반 문장은 통과해야 한다 (영어) ---
    def test_english_promise_then_exit_code_passes(self):
        r = scan_text("I will run it. exit code 0.")
        self.assertTrue(r.passed, msg=r.reasons)

    def test_english_promise_then_grep_passes(self):
        r = scan_text("Let me grep. grep returned 3 matches.")
        self.assertTrue(r.passed, msg=r.reasons)

    def test_english_promise_then_pass_passes(self):
        r = scan_text("Going to test. PASS.")
        self.assertTrue(r.passed, msg=r.reasons)

    def test_english_promise_then_written_file_passes(self):
        r = scan_text("I'll write the file. /tmp/out.json written.")
        self.assertTrue(r.passed, msg=r.reasons)

    def test_english_promise_then_deployed_passes(self):
        r = scan_text("will now deploy. deployed successfully. exit 0.")
        self.assertTrue(r.passed, msg=r.reasons)

    # --- 오탐 방지: 과거형 완료 + 증거 동반 정상 보고문 ---
    def test_past_completion_with_evidence_passes(self):
        cases = (
            "코드를 작성했습니다. exit 0 으로 확인했습니다.",
            "버그를 고쳤습니다. 테스트 통과했습니다.",
            "구현을 마쳤습니다. 3 개 matches 확인.",
            "리포트를 작성했습니다. /reports/out.md render 확인.",
        )
        for c in cases:
            with self.subTest(text=c):
                self.assertTrue(scan_text(c).passed, msg=c)

    # --- 오탐 방지: 약속/축소 표현이 없는 순수 설명/보고문 ---
    def test_plain_reports_pass(self):
        cases = (
            "라우터는 신호가 하나라도 발화하면 opus 로 라우팅한다.",
            "게이트는 fail-closed 이며 불확실하면 실패한다.",
            "현재 98개 테스트가 통과한다.",
            "이 기능은 사용자가 요청하면 작동한다.",
            "The function returns the result when validation succeeds.",
            "Let me know if anything is missing.",
            "This component validates input and renders output.",
        )
        for c in cases:
            with self.subTest(text=c):
                self.assertTrue(scan_text(c).passed, msg=c)


class TestScanTextPositive(unittest.TestCase):
    def test_scope_reduction_blocked(self):
        r = scan_text("핵심만 보여드리고 나머지는 생략")
        self.assertFalse(r.passed)
        self.assertTrue(any("scope-reduction" in x for x in r.reasons))

    def test_scope_reduction_english_blocked(self):
        r = scan_text("def foo(): pass  # rest is similar")
        self.assertFalse(r.passed)

    def test_omitted_for_brevity_blocked(self):
        r = scan_text("output omitted for brevity")
        self.assertFalse(r.passed)

    def test_trailing_ellipsis_blocked(self):
        r = scan_text("결과는 다음과 같다 ...")
        self.assertFalse(r.passed)

    def test_promise_without_evidence_blocked(self):
        # 약속 표현 + 완료-증거 전무 -> 차단.
        r = scan_text("이제 모듈을 작성하겠습니다.")
        self.assertFalse(r.passed)
        self.assertTrue(any("promise-without-execution" in x for x in r.reasons))

    def test_english_promise_without_evidence_blocked(self):
        r = scan_text("I will implement the parser shortly.")
        self.assertFalse(r.passed)

    def test_genuine_promises_still_blocked(self):
        # 증거 확장 후에도 진짜 약속-미실행은 여전히 차단(오검출 0 유지).
        cases = (
            "이제 모듈을 작성하겠습니다.",
            "다음으로 테스트를 진행하겠습니다.",
            "구현하겠습니다.",
            "확인하겠습니다.",
            "let me start the build.",
            "going to refactor the router.",
            "will now write the file.",
            "I will describe the three escalation signals below.",
        )
        for c in cases:
            with self.subTest(text=c):
                r = scan_text(c)
                self.assertFalse(r.passed, msg=f"should be blocked: {c}")
                self.assertTrue(
                    any("promise-without-execution" in x for x in r.reasons),
                    msg=r.reasons,
                )

    def test_empty_input_fail_closed(self):
        r = scan_text("")
        self.assertFalse(r.passed)
        self.assertTrue(any("empty" in x for x in r.reasons))


class TestFrozenDataclasses(unittest.TestCase):
    def test_claim_frozen(self):
        c = Claim(text="x", evidence=())
        with self.assertRaises(Exception):
            c.text = "y"  # type: ignore[misc]

    def test_gateresult_frozen(self):
        g = GateResult(passed=True, reasons=())
        with self.assertRaises(Exception):
            g.passed = False  # type: ignore[misc]


if __name__ == "__main__":
    unittest.main(verbosity=2)
