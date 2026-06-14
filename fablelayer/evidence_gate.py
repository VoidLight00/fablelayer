"""FableLayer FL2 — Evidence Gate.

완결성 게이트(fail-closed). 완료 단언이 실측 증거 없이 등장하면 차단한다.
early-stop.sh(약속-미실행 / 범위-축소) 패턴을 Python 정규식으로 포팅한다.
판정은 GateResult.passed(불리언)로만 한다. 불확실하면 실패(fail-closed).
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Claim:
    text: str
    evidence: tuple[str, ...]


@dataclass(frozen=True)
class GateResult:
    passed: bool
    reasons: tuple[str, ...]


# 계약 SSoT(INTERFACE.md FL2)의 정규식 — 글자 그대로 유지한다.
ACCEPTED_EVIDENCE_RE = (
    r"(exit\s*code|exit\s*\d|test.*(pass|fail)|grep|\d+\s*(개|matches)"
    r"|/[\w./-]+\.\w+|render|스크린샷)"
)
COMPLETION_RE = r"(done|완료|통과|fixed|배포됨|작동(한다|함)|passed)"

_ACCEPTED_EVIDENCE = re.compile(ACCEPTED_EVIDENCE_RE, re.IGNORECASE)
_COMPLETION = re.compile(COMPLETION_RE, re.IGNORECASE)


# early-stop.sh 포팅 — 범위-축소 패턴. 발견 즉시 위반(증거 무관).
SCOPE_REDUCTION_PATTERNS: tuple[str, ...] = (
    r"시간 관계상",
    r"지면 관계상",
    r"나머지는 생략",
    r"이하 생략",
    r"이하 동일",
    r"여기까지만",
    r"일부만 ",
    r"간단히만",
    r"생략하겠습니다",
    r"생략합니다",
    r"omitted for brevity",
    r"truncated for brevity",
    r"left as an exercise",
    r"rest is similar",
    r"and so on",
    r"\.\.\. *$",
)

# early-stop.sh 포팅 — 약속-미실행 패턴. 완료-증거 표현이 전혀 없으면 위반.
PROMISE_PATTERNS: tuple[str, ...] = (
    r"하겠습니다",
    r"하겠음",
    r"할 것입니다",
    r"할 예정입니다",
    r"할 예정이다",
    r"다음으로 .*하겠",
    r"이제 .*하겠",
    r"진행하겠습니다",
    r"작성하겠습니다",
    r"구현하겠습니다",
    r"확인하겠습니다",
    r"시작하겠습니다",
    r"will now ",
    r"I will ",
    r"next, I'll",
    r"going to ",
    r"let me ",
)

# early-stop.sh 포팅 — 약속이 실행됨을 시사하는 완료-증거 표현(오탐 완화).
# 약속 표현 뒤에 아래 표현 또는 ACCEPTED_EVIDENCE_RE/COMPLETION_RE 시그널이
# 함께 있으면 '약속+실행'으로 보고 위반에서 제외한다(false-positive 방지).
EVIDENCE_PATTERNS: tuple[str, ...] = (
    r"exit code",
    r"exit 0",
    r"종료 코드",
    r"통과",            # '테스트 통과'·'빌드 통과'·'통과했습니다'·'통과.' 모두 포함
    r"tests passed",
    r"PASS",
    r"완료",            # '배포 완료'·'완료했습니다' 등
    r"성공",            # '빌드 성공'·'배포 성공' 등
    r"작성했",
    r"구현했",
    r"수정했",
    r"진행했",
    r"확인했",
    r"마쳤",
    r"실행 결과",
    r"검증 결과",
    r"생성됨",
    r"deployed",
    r"implemented",
    r"built",
    r"written",
    r"confirmed",
    r"WROTE ",
)

_SCOPE_REDUCTION = tuple(re.compile(p, re.MULTILINE) for p in SCOPE_REDUCTION_PATTERNS)
_PROMISE = tuple(re.compile(p) for p in PROMISE_PATTERNS)
# 명시 완료-증거 표현. 'PASS' 대문자 시그널 보존을 위해 일부는 대소문자 구분.
_EVIDENCE = tuple(re.compile(p, re.IGNORECASE) for p in EVIDENCE_PATTERNS)


def _has_completion_evidence(text: str) -> bool:
    """약속이 실제 실행으로 이어졌는지 판정.

    (a) 명시 완료-증거 표현(_EVIDENCE), 또는
    (b) 계약 SSoT 증거 정규식(ACCEPTED_EVIDENCE_RE) 매치, 또는
    (c) 완료어(COMPLETION_RE) 매치 중 하나라도 있으면 '실행됨'으로 본다.
    이는 정상 보고문의 오탐을 막되, 진짜 약속-미실행(증거 전무)은 차단한다.
    """
    if any(e.search(text) for e in _EVIDENCE):
        return True
    if _ACCEPTED_EVIDENCE.search(text):
        return True
    if _COMPLETION.search(text):
        return True
    return False


def _has_accepted_evidence(text: str) -> bool:
    return _ACCEPTED_EVIDENCE.search(text) is not None


def check_claim(claim: Claim) -> GateResult:
    """완료 단언에 실측 증거가 동반되는지 fail-closed 로 검증한다.

    완료어가 등장했는데 (a) evidence 가 비었거나 (b) 어떤 증거 토큰도
    ACCEPTED_EVIDENCE_RE 에 매치되지 않으면 passed=False.
    완료어가 없으면 게이트 대상이 아니므로 통과시킨다.
    """
    reasons: list[str] = []
    has_completion = _COMPLETION.search(claim.text) is not None

    if not has_completion:
        return GateResult(
            passed=True,
            reasons=("no completion claim; gate not applicable",),
        )

    if not claim.evidence:
        reasons.append("completion claim present but evidence empty (fail-closed)")
        return GateResult(passed=False, reasons=tuple(reasons))

    matched = tuple(e for e in claim.evidence if _has_accepted_evidence(e))
    if not matched:
        reasons.append(
            "completion claim present but no evidence token matches "
            "ACCEPTED_EVIDENCE_RE (fail-closed)"
        )
        return GateResult(passed=False, reasons=tuple(reasons))

    return GateResult(
        passed=True,
        reasons=(f"completion claim grounded by {len(matched)} evidence token(s)",),
    )


def scan_text(s: str) -> GateResult:
    """early-stop.sh 포팅 — 약속-미실행 + 범위-축소 결정론 감지.

    1) 범위-축소 패턴: 하나라도 매치하면 즉시 위반(증거 무관).
    2) 약속-미실행: 약속 표현이 있고 완료-증거 표현이 전혀 없으면 위반.
    위반이 없으면 passed=True. 입력이 비면 fail-closed(검증 불가 → 실패).
    """
    if not s:
        return GateResult(passed=False, reasons=("empty input (fail-closed)",))

    for pat in _SCOPE_REDUCTION:
        if pat.search(s):
            return GateResult(
                passed=False,
                reasons=(f"scope-reduction pattern detected: {pat.pattern}",),
            )

    promise_hit = next((p.pattern for p in _PROMISE if p.search(s)), None)
    if promise_hit is not None and not _has_completion_evidence(s):
        return GateResult(
            passed=False,
            reasons=(
                f"promise-without-execution detected: {promise_hit} "
                "(no completion evidence)",
            ),
        )

    return GateResult(passed=True, reasons=("no early-stop pattern detected",))
