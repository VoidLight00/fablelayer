"""FableLayer source policy (FL7, FL-GAP-01).

소스 라이선스 분류와 non-public prompt 정책을 fail-closed로 강제한다.
GateResult 는 evidence_gate 의 정본을 재사용하되, 아직 모듈이 없으면
INTERFACE.md 와 동일한 계약으로 폴백 정의한다(계약 일치 보장).
"""

from __future__ import annotations

from dataclasses import dataclass

try:  # GateResult 정본 재사용 (evidence_gate.py)
    from fablelayer.evidence_gate import GateResult
except Exception:  # 아직 미구현 시 계약 동일 폴백

    @dataclass(frozen=True)
    class GateResult:
        passed: bool
        reasons: tuple[str, ...]


CLASS = ("copy", "adapt", "reference-only", "blocked", "unverified")

_RISK = ("low", "medium", "high")


@dataclass(frozen=True)
class Source:
    name: str
    url: str
    license: str
    classification: str
    risk: str  # risk in {low, medium, high}


def _normalize_license(license: str) -> str:
    return (license or "").strip().lower()


def _is_unknown_license(license: str) -> bool:
    norm = _normalize_license(license)
    if not norm:
        return True
    unknown_tokens = (
        "unknown",
        "불명확",
        "불명",
        "모호",
        "none",
        "n/a",
        "na",
        "tbd",
    )
    return any(tok in norm for tok in unknown_tokens)


def _is_permissive_license(license: str) -> bool:
    norm = _normalize_license(license)
    permissive = ("mit", "apache", "bsd", "isc", "unlicense")
    return any(tok in norm for tok in permissive)


def classify(name: str, license: str, is_leaked: bool) -> str:
    """소스 분류를 결정한다.

    - non-public -> 'reference-only' (전문 포함 금지, risk high)
    - unknown license -> 'unverified' (fail-closed: 검증 전 채택 금지)
    - MIT/permissive -> 'adapt'
    - 그 외 식별 가능한 라이선스 -> 'reference-only' (보수적)
    """
    if is_leaked:
        return "reference-only"
    if _is_unknown_license(license):
        return "unverified"
    if _is_permissive_license(license):
        return "adapt"
    return "reference-only"


def classify_risk(classification: str, is_leaked: bool) -> str:
    if is_leaked:
        return "high"
    if classification == "unverified":
        return "high"
    if classification == "reference-only":
        return "medium"
    if classification == "adapt":
        return "low"
    if classification == "blocked":
        return "high"
    return "high"  # 미지의 분류는 보수적으로 high


def _make_source(name: str, url: str, license: str, is_leaked: bool) -> Source:
    classification = classify(name, license, is_leaked)
    risk = classify_risk(classification, is_leaked)
    return Source(
        name=name,
        url=url,
        license=license,
        classification=classification,
        risk=risk,
    )


def default_ledger() -> tuple[Source, ...]:
    """ATTRIBUTION.md 의 10개 소스를 데이터로 표현한다."""
    return (
        _make_source(
            "fablize",
            "https://github.com/fivetaku/fablize",
            "MIT",
            False,
        ),
        _make_source(
            "value-for-fable",
            "https://github.com/itsinseong/value-for-fable",
            "MIT",
            False,
        ),
        _make_source(
            "supergoal",
            "https://github.com/robzilla1738/supergoal",
            "MIT",
            False,
        ),
        _make_source(
            "context-handoff-bundle",
            "https://github.com/ucsandman/context-handoff-bundle",
            "MIT",
            False,
        ),
        _make_source(
            "sgup/ai",
            "https://github.com/sgup/ai",
            "unknown",
            False,
        ),
        _make_source(
            "awesome-claude-fable-5",
            "https://github.com/Anil-matcha/awesome-claude-fable-5",
            "unknown",
            False,
        ),
        _make_source(
            "xonovex/platform",
            "https://github.com/xonovex/platform",
            "unknown",
            False,
        ),
        _make_source(
            "Cheswick",
            "https://github.com/CheswickDEV/claude-fable-5-prompt-optimizer",
            "unknown",
            False,
        ),
        _make_source(
            "blocked-prompt-source-a",
            "https://example.invalid/blocked-prompt-source-a",
            "non-public-prompt",
            True,
        ),
        _make_source(
            "blocked-prompt-source-b",
            "https://example.invalid/blocked-prompt-source-b",
            "non-public-prompt",
            True,
        ),
    )


def audit(ledger: tuple[Source, ...]) -> GateResult:
    """원장 정책 위반을 fail-closed로 검사한다.

    위반:
    - leaked 추정 소스가 copy/adapt 로 분류 -> fail
    - blocked 분류 존재 -> fail (빌드에 포함 불가)
    - 알 수 없는 classification / risk 값 -> fail (fail-closed)
    """
    reasons: tuple[str, ...] = ()

    for src in ledger:
        if src.classification not in CLASS:
            reasons = reasons + (
                f"{src.name}: invalid classification '{src.classification}'",
            )
            continue
        if src.risk not in _RISK:
            reasons = reasons + (
                f"{src.name}: invalid risk '{src.risk}'",
            )

        leaked_like = _is_leaked_like(src)
        if leaked_like and src.classification in ("copy", "adapt"):
            reasons = reasons + (
                f"{src.name}: non-public source must not be copy/adapt "
                f"(got '{src.classification}')",
            )

        if src.classification == "blocked":
            reasons = reasons + (
                f"{src.name}: blocked source present in build",
            )

    passed = len(reasons) == 0
    return GateResult(passed=passed, reasons=reasons)


def _is_leaked_like(src: Source) -> bool:
    """소스가 non-public 성격인지 판정(보수적)."""
    normalized_license = _normalize_license(src.license)
    if "non-public" in normalized_license or "leaked" in normalized_license:
        return True
    if src.classification == "reference-only" and src.risk == "high":
        return True
    return False
