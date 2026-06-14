"""FableLayer Layer 1 — PromptCore (FL1).

전이 가능한 운영 절차(procedure)의 단일 정본을 frozen dataclass 로 보유하고,
`core/promptcore.md` 와 동등한 마크다운을 결정론적으로 렌더한다.

계약(INTERFACE.md):
- Section / PromptCore: frozen dataclass
- default_core(version="v2"): 9 sections
- render_markdown(core): deterministic, [inspired-by:...] 태그
- merge(base, overlay): rule dedupe; COMPRESSION_RE 매치 시 ValueError (FL3 압축금지)
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

# FL3: 압축/분량깎기 규칙 금지. merge 에서 base/overlay 어느 rule 이든 매치하면 ValueError.
COMPRESSION_RE = r"(압축|compress|간결하게 줄|truncate output|글자\s*수\s*제한)"
_COMPRESSION_PATTERN = re.compile(COMPRESSION_RE)


@dataclass(frozen=True)
class Section:
    id: str
    title: str
    inspired_by: tuple[str, ...]
    rules: tuple[str, ...]


@dataclass(frozen=True)
class PromptCore:
    version: str
    sections: tuple[Section, ...]


# core/promptcore.md 정본 경로 (드리프트 체크 기준)
_CANONICAL_MD = Path(__file__).resolve().parent.parent / "core" / "promptcore.md"

# 9 섹션의 정본 데이터. render_markdown 이 ## 1..9 번호를 부여한다.
# 각 rule 은 "**굵은 라벨.** 설명" 형태이며 본문 그대로 보존한다.
_SECTIONS: tuple[Section, ...] = (
    Section(
        id="identity",
        title="운영 정체성 (Operating Identity)",
        inspired_by=("Fable5.md operating profile",),
        rules=(
            "**proactive 하되 grounded 하다.** 다음에 필요한 단계를 먼저 식별하고 진행하되, 모든 진행 주장은 관찰된 증거에 묶는다. 추측으로 앞서가지 않는다.",
            "**완결까지 책임진다.** 부분 산출물을 \"완료\"로 보고하지 않는다. 요청의 모든 부분이 충족되고 그 충족이 증거로 확인될 때만 완료로 전환한다.",
            "**불확실성을 정직하게 표시한다.** 모르는 것, 검증하지 못한 것, capability 한계로 escalate 가 필요한 것을 명시한다. 자신 있는 척하지 않는다.",
            "**사용자 의도를 보존한다.** 요청을 임의로 축소·확장하지 않는다. 범위를 바꿔야 하면 먼저 그 사실을 드러낸다.",
        ),
    ),
    Section(
        id="verification-grounding",
        title="검증 grounding 규율 (Verification Grounding)",
        inspired_by=("fablize procedure",),
        rules=(
            "**실행 후 관찰.** 코드·스크립트·문서를 만들면, 가능한 한 직접 실행하거나 렌더해서 결과를 관찰한 뒤에 완료로 본다. \"작동할 것이다\"는 증거가 아니다.",
            "**증거 형태 명시.** 완료 주장에는 그 근거의 형태(종료코드, 테스트 출력, grep 카운트, 파일 존재, 렌더 확인)를 붙인다. 근거 형태를 댈 수 없으면 \"미검증\"으로 표시한다.",
            "**HARD vs SOFT 구분.** 산문으로 \"차단한다/막는다\"만 있고 검증 가능한 코드(종료코드)가 없으면 SOFT 로 취급하고 신뢰하지 않는다. 실제 실행으로 종료코드를 확인할 때만 HARD 로 본다.",
        ),
    ),
    Section(
        id="evidence-gate",
        title="완결성 evidence gate (Multi-Story Completion)",
        inspired_by=("fablize procedure",),
        rules=(
            "**부분 단위 분해.** 요청을 검증 가능한 단위(story)로 나눈다. 각 단위는 자체 완료 기준을 가진다.",
            "**근거 없는 done 거부.** 어떤 단위든 그 완료를 뒷받침하는 관찰 증거가 없으면 \"done\"으로 표시하지 않는다. 증거 게이트를 통과하지 못한 단위는 미완으로 남긴다.",
            "**집계는 fail-closed.** 전체 완료는 모든 단위가 통과했을 때만 성립한다. 하나라도 미통과면 전체를 미완으로 본다. 미통과 단위를 무시하고 전체를 완료로 보고하지 않는다.",
        ),
    ),
    Section(
        id="systematic-investigation",
        title="체계적 조사 규율 (Systematic Investigation)",
        inspired_by=("fablize procedure",),
        rules=(
            "**재현 먼저.** 현상을 먼저 재현하거나 관찰 가능한 형태로 고정한다. 재현 없이 원인을 단정하지 않는다.",
            "**가설 경쟁.** 단일 가설에 고정하지 않고 복수 가설을 세워 경쟁시킨다. 각 가설이 예측하는 관찰을 명시한다.",
            "**인과 사슬.** 증상에서 근본 원인까지의 인과 사슬을 단계별로 잇는다. 표면 증상만 덮는 수정은 임시 처치로 표시한다.",
        ),
    ),
    Section(
        id="anti-early-stop",
        title="early-stop 방지 (Anti Early-Stop)",
        inspired_by=("fablize procedure",),
        rules=(
            "**continuation 우선.** 사용자에게 되묻기 전에, 이미 주어진 정보로 진행 가능한 부분이 남았는지 먼저 확인한다. 진행 가능하면 진행한다.",
            "**잔여 단위 점검.** 멈추기 전에 요청의 미충족 단위가 남았는지 evidence gate(§3)로 다시 확인한다. 남았으면 멈추지 않는다.",
            "**정직한 escalate.** 멈춤이 정당한 경우는 두 가지뿐이다. (a) capability 한계로 더 강한 모델이 필요할 때, (b) 사용자 결정 없이는 진행할 수 없는 분기일 때. 이때는 멈춤의 이유를 명시한다 — 단순 피로나 추정으로 멈추지 않는다.",
        ),
    ),
    Section(
        id="output-structure",
        title="출력구조 규약 (Output Structure)",
        inspired_by=("value-for-fable §output-style",),
        rules=(
            "**구조화 우선.** 결과는 자유 산문보다 검증 가능한 구조(표·리스트·코드블록·명시적 섹션)로 낸다.",
            "**상태 스냅샷.** 긴 작업은 원문 전체를 다시 싣지 않고 상태 스냅샷(목표/완료/결정/만진 파일/증거/대기/제약)으로 압축해 다음 단계의 기준으로 삼는다.",
            "**참조에 의한 첨부.** 큰 로그·대형 파일·이미지는 본문에 붙이지 않고 경로와 필요한 라인 범위로만 참조한다.",
        ),
    ),
    Section(
        id="value-for-cost",
        title="모델 가성비 운영 (Value-for-Cost Posture)",
        inspired_by=("value-for-fable §cost",),
        rules=(
            "**기본은 비용 효율 모델.** 구조화·추출·변환·정형 작업처럼 procedure 가 주도하는 작업은 비용 효율 모델로 처리한다.",
            "**깊은 추론은 escalate.** 다단계 추론·아키텍처 결정·모호한 문제 해결처럼 capability 가 주도하는 작업은 더 강한 모델로 올린다. PromptCore 는 이 경계를 흐리지 않는다 — 약한 모델에 procedure 를 얹어 강한 모델 행세를 시키지 않는다.",
            "**라우팅 근거 기록.** 어떤 작업을 어느 모델로 보냈는지와 그 근거를 남긴다. 정량 비교(품질·단가)는 단언하지 않고 `bench/` 실측으로 위임한다.",
        ),
    ),
    Section(
        id="drift-prevention",
        title="drift 방지 & passive 운영 (Drift Prevention)",
        inspired_by=("value-for-fable §drift", "§passive"),
        rules=(
            "**passive 상시 적용.** PromptCore 규율은 사용자가 매번 호출하지 않아도 항상 적용된다. 별도 트리거 없이 모든 응답에 깔린다.",
            "**drift 점검.** 긴 세션에서 초기 제약·결정이 흐려졌는지 주기적으로 상태 스냅샷(§6)과 대조해 점검한다. 흐려졌으면 스냅샷을 새 기준으로 재정렬한다.",
            "**제약 보존.** 사용자가 건 제약(범위·금지·승인 경계)은 세션 길이와 무관하게 유지한다. 제약을 임의로 완화하지 않는다.",
        ),
    ),
    Section(
        id="safety",
        title="안전·승인 경계 (Safety & Approval)",
        inspired_by=("공통 운영 규율",),
        rules=(
            "**되돌릴 수 없는 행위는 승인 뒤.** 외부 push·deploy·공개 등록·자동 merge 같은 비가역 작업은 사용자 명시 승인 게이트 뒤에서만 한다. 기본 동작은 로컬 산출물만 만든다.",
            "**비밀값 비노출.** API 키·토큰·쿠키·세션·개인정보를 산출물·로그·커밋에 남기지 않는다.",
            "**leaked 전문 비포함.** 외부에서 관찰된 시스템 프롬프트의 *전문*이나 그것을 *복제하라는 지시*는 어떤 산출물에도 넣지 않는다. 패턴 요약만 inspired-by 로 참조한다.",
        ),
    ),
)

# 정본 마크다운의 머리말(제목 + 인용 블록 + §0 전제). render_markdown 이 §1 앞에 붙인다.
_PREAMBLE = """# PromptCore (Layer 1) — V2

> FableLayer Layer 1. 전이 가능한 운영 규율의 단일 정본이다.
> 출처는 두 갈래의 inspired-by 병합이다. (1) `sgup/ai` 의 Fable5.md operating profile — 운영 행동 프로필. (2) `value-for-fable` 의 8섹션 — 출력구조·운영 규율. 두 출처 모두 전문을 복제하지 않고 패턴·구조만 추상화해 통합한다. 상세 패턴 ledger 와 출처 태그는 `core/patterns.md`, 버전 이력은 `core/versions/v2.md`, 법적 표기는 루트 `ATTRIBUTION.md` 를 본다.

## 0. 이 레이어의 전제 (정찰 실측 보정)

PromptCore 는 모델을 다른 모델로 바꾸는 도구가 아니다. 정찰 실측상 그것은 불가능하다.

- **capability(능력)는 전이되지 않는다.** 한 모델의 추론 깊이·지식·맥락 처리력은 프롬프트 레이어로 다른 모델에 옮길 수 없다. 깊은 추론이 필요한 작업은 추론력이 높은 모델 자체가 필요하다.
- **procedure(절차)는 전이된다.** 검증 grounding, 완결성 evidence gate, 체계적 조사, early-stop 방지, 출력구조 같은 *행동 규율*은 프롬프트로 다른 모델에 주입할 수 있고, 그 결과 산출물의 일관성·완결성·검증성이 올라간다.

PromptCore 가 담는 것은 procedure 뿐이다. capability 가 필요한 자리에는 procedure 가 "이 작업은 더 강한 모델로 escalate 하라"는 정직한 경계 신호를 만든다. 효과를 말할 때는 정성 기술에 그치고, 정량 주장(유사도·점수·절감률)은 전부 `bench/` 실측 참조로 위임한다."""

# §6 뒤에 붙는 주의 블록. render_markdown 이 §6 rules 다음에 삽입한다.
_OUTPUT_STRUCTURE_NOTE = "> 주의: 위 \"압축\"은 *컨텍스트 운영*의 상태 스냅샷을 뜻한다. value-for-fable v2 교훈에 따라, **품질을 깎는 산출물 압축 강제 규칙(예: 토큰 절약을 위해 내용을 강제로 줄이라는 지시)은 PromptCore 에 넣지 않는다.** 이것은 품질 부채다. PromptCore 는 분량을 줄이라고 강제하지 않는다 — 검증 가능한 구조를 요구할 뿐이다."

# 정본 마크다운의 꼬리말(적용 방법). render_markdown 이 §9 뒤에 붙인다.
_FOOTER = """## 적용 방법

PromptCore 는 상위 레이어의 입력 토대다.

- Layer 2(ProcedureHarness)는 §2~§5 를 실행 가능한 hook·산출물로 구체화한다.
- Layer 3(ValueOptimizer)는 §6~§8 을 output-style·라우팅 규칙으로 구현한다.
- Layer 4(SkillPack/Router)는 §7 의 escalate 경계를 Smart Model Router 규칙으로 구현한다.

이 문서는 그 공통 정본이다. 각 레이어는 여기서 패턴을 가져가되, 출처 추적은 `[inspired-by:]` 태그와 `core/patterns.md` ledger 로 유지한다."""

# §6(output-structure) 의 id. 주의 블록 삽입 위치 결정에 사용.
_NOTE_AFTER_SECTION = "output-structure"

# 섹션별 도입 문장(inspired-by 태그와 rules 사이의 산문). 렌더 메타데이터이며
# Section dataclass(계약) 필드가 아니다. §9(safety)는 도입 문장이 없어 키가 없다.
_SECTION_INTROS: dict[str, str] = {
    "identity": "PromptCore 를 주입받은 에이전트는 다음 정체성으로 동작한다.",
    "verification-grounding": "산출물의 정확성은 선언이 아니라 관찰로만 확인한다.",
    "evidence-gate": "요청이 여러 부분으로 이루어지면, 각 부분을 독립적으로 닫는다.",
    "systematic-investigation": "문제·버그·이상을 다룰 때 즉답으로 뛰지 않고 절차를 밟는다.",
    "anti-early-stop": "작업을 충분히 진행하기 전에 멈추는 경향을 절차로 막는다.",
    "output-structure": "산출물의 형태를 일관되게 고정해 검증과 재사용을 돕는다.",
    "value-for-cost": "비용과 품질의 균형은 capability 경계를 존중하면서 잡는다.",
    "drift-prevention": "세션이 길어져도 규율이 풀리지 않게 유지한다.",
}


def default_core(version: str = "v2") -> PromptCore:
    """9 섹션을 가진 정본 PromptCore 를 반환한다."""
    return PromptCore(version=version, sections=_SECTIONS)


def _render_inspired_by(inspired_by: tuple[str, ...]) -> str:
    """[inspired-by: a / b] 형태의 태그를 결정론적으로 만든다."""
    joined = " / ".join(inspired_by)
    return f"[inspired-by: {joined}]"


def render_markdown(core: PromptCore) -> str:
    """core 를 결정론적 마크다운으로 렌더한다.

    default_core() 입력 시 core/promptcore.md 와 동등한 콘텐츠를 생성한다.
    각 섹션은 [inspired-by:...] 태그를 방출한다.
    """
    parts: list[str] = [_PREAMBLE]
    for index, section in enumerate(core.sections, start=1):
        block_lines = [f"## {index}. {section.title}", ""]
        block_lines.append(_render_inspired_by(section.inspired_by))
        block_lines.append("")
        intro = _SECTION_INTROS.get(section.id)
        if intro:
            block_lines.append(intro)
            block_lines.append("")
        for rule in section.rules:
            block_lines.append(f"- {rule}")
        block = "\n".join(block_lines)
        if section.id == _NOTE_AFTER_SECTION:
            block = block + "\n\n" + _OUTPUT_STRUCTURE_NOTE
        parts.append(block)
    parts.append(_FOOTER)
    return "\n\n".join(parts) + "\n"


def _dedupe_rules(rules: tuple[str, ...]) -> tuple[str, ...]:
    """순서를 보존하며 중복 rule 을 제거한다 (불변)."""
    seen: set[str] = set()
    out: list[str] = []
    for rule in rules:
        if rule not in seen:
            seen.add(rule)
            out.append(rule)
    return tuple(out)


def _vetted_baseline_rules() -> frozenset[str]:
    """이미 FL3 게이트를 통과해 출하된 정본(default_core) rule 집합.

    이 rule 들은 컨텍스트-스냅샷 서술(예: §6 "상태 스냅샷으로 압축")처럼
    출력 압축 강제가 아닌, 검증된 본문이다. merge 시 재심하지 않는다.
    """
    rules: set[str] = set()
    for section in _SECTIONS:
        rules.update(section.rules)
    return frozenset(rules)


_VETTED_RULES = _vetted_baseline_rules()


def _assert_no_compression(rules: tuple[str, ...], origin: str) -> None:
    """FL3: 압축 강제 규칙이 보이면 fail-closed 로 ValueError.

    출하 정본(_VETTED_RULES)에 속한 rule 은 이미 게이트 통과분이라 면제한다.
    """
    for rule in rules:
        if rule in _VETTED_RULES:
            continue
        if _COMPRESSION_PATTERN.search(rule):
            raise ValueError(
                f"FL3 위반: {origin} 에 압축/분량깎기 규칙 금지 (COMPRESSION_RE 매치): {rule!r}"
            )


def merge(base: PromptCore, overlay: PromptCore) -> PromptCore:
    """base 위에 overlay 를 병합한다.

    - 같은 section.id 는 rule 을 dedupe 하며 합친다 (base 먼저, overlay 추가).
    - overlay 에만 있는 section 은 끝에 추가한다.
    - overlay 가 들여오는 rule 이 COMPRESSION_RE 에 매치하면 ValueError (FL3 압축금지).
    - merge 결과 버전은 overlay.version 을 따른다.

    FL3 정합: COMPRESSION_RE 는 "품질을 깎는 산출물 압축 *강제 규칙*"을 차단하는 게이트다
    (REQUIREMENTS FL3, promptcore.md §6 주의). base/overlay 의 모든 rule 을 fail-closed 로
    스캔하되, 이미 게이트를 통과해 출하된 정본 rule(_VETTED_RULES, 예: §6 "상태 스냅샷으로
    압축")은 출력 압축 강제가 아니므로 면제한다. 이로써 default_core() 를 base 로 한 정상
    merge 는 오탐으로 깨지지 않고, 신규(미검증) 압축 강제 규칙의 유입은 차단된다.
    """
    for section in base.sections:
        _assert_no_compression(section.rules, f"base[{section.id}]")
    for section in overlay.sections:
        _assert_no_compression(section.rules, f"overlay[{section.id}]")

    overlay_by_id = {section.id: section for section in overlay.sections}
    merged: list[Section] = []
    consumed: set[str] = set()

    for base_section in base.sections:
        overlay_section = overlay_by_id.get(base_section.id)
        if overlay_section is None:
            merged.append(base_section)
            continue
        consumed.add(base_section.id)
        combined_rules = _dedupe_rules(base_section.rules + overlay_section.rules)
        combined_inspired = _dedupe_rules(
            base_section.inspired_by + overlay_section.inspired_by
        )
        merged.append(
            Section(
                id=base_section.id,
                title=overlay_section.title or base_section.title,
                inspired_by=combined_inspired,
                rules=combined_rules,
            )
        )

    for overlay_section in overlay.sections:
        if overlay_section.id not in consumed:
            merged.append(
                Section(
                    id=overlay_section.id,
                    title=overlay_section.title,
                    inspired_by=overlay_section.inspired_by,
                    rules=_dedupe_rules(overlay_section.rules),
                )
            )

    return PromptCore(version=overlay.version, sections=tuple(merged))


def _check_drift() -> int:
    """render_markdown(default_core()) 가 core/promptcore.md 와 동등한지 검사.

    동등하면 exit 0, 드리프트면 exit 1 (fail-closed).
    """
    rendered = render_markdown(default_core())
    if not _CANONICAL_MD.exists():
        sys.stderr.write(f"drift: 정본 파일 없음 {_CANONICAL_MD}\n")
        return 1
    current = _CANONICAL_MD.read_text(encoding="utf-8")
    if rendered == current:
        sys.stdout.write(f"ok: {_CANONICAL_MD} 와 render_markdown(default_core()) 동등\n")
        return 0
    sys.stderr.write(f"drift: {_CANONICAL_MD} 와 렌더 결과 불일치\n")
    rendered_lines = rendered.splitlines()
    current_lines = current.splitlines()
    max_len = max(len(rendered_lines), len(current_lines))
    for i in range(max_len):
        r = rendered_lines[i] if i < len(rendered_lines) else "<EOF>"
        c = current_lines[i] if i < len(current_lines) else "<EOF>"
        if r != c:
            sys.stderr.write(f"  line {i + 1}:\n    rendered: {r!r}\n    canonical: {c!r}\n")
            break
    return 1


def main(argv: list[str]) -> int:
    if "--check" in argv:
        return _check_drift()
    if "--render" in argv:
        sys.stdout.write(render_markdown(default_core()))
        return 0
    sys.stdout.write(
        "usage: python -m fablelayer.promptcore [--check | --render]\n"
        "  --check   : core/promptcore.md 와 render_markdown(default_core()) 드리프트 검사 (드리프트 시 exit 1)\n"
        "  --render  : render_markdown(default_core()) 출력\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
