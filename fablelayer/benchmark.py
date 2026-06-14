"""FableLayer benchmark (FL6).

judge B(결정론 규칙 채점): rubric 키워드 커버리지 0..100.
judge A(rubric 0-5 모사): 라이브 LLM-judge 의 rubric 채점을 결정론으로 모사한 0..100.
라이브 모델 불필요 — 동일 입력은 항상 동일 점수(재현 가능).
검증은 fail-closed: 입력이 불완전하면 점수를 후하게 주지 않고 0.0 으로 본다.

두 심판은 서로 다른 채점 논리를 쓰므로 같은 출력에서 어긋날 수 있다.
불일치는 평균으로 덮지 않고 양쪽 판정을 BenchRun.raw 에 모두 남긴다(recover 축: 실패 비삭제).
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Mapping

# RESULTS.md 의 judge B(규칙 결정론 채점)에 대응한다. 라이브 모델 호출 없이
# rubric 키워드의 출력 내 커버리지로만 채점하므로 합성 수치가 끼어들 여지가 없다.
JUDGE_NAME = "B_rule_keyword_coverage"
JUDGE_B_NAME = JUDGE_NAME

# RESULTS.md 의 judge A(rubric 0~5 정량 채점)에 대응한다. LLM-judge 를 결정론으로
# 모사하므로 라이브 모델이 필요 없고 동일 입력은 항상 동일 점수다.
JUDGE_A_NAME = "A_rubric_quality_0_5"

# A/B 정규화 점수 차이가 이 값(0..100)을 넘으면 "불일치"로 본다. 평균으로 덮지 않는다.
DISAGREE_THRESHOLD = 25.0

# reproduce.sh 의 sentinel 계약과 정합: 점수가 주장되는데 raw.json 이 없거나
# 어긋나면 재현 스크립트가 exit 70 으로 막아야 한다는 불변식.
SENTINEL_GUARD = True


@dataclass(frozen=True)
class BenchTask:
    id: str
    prompt: str
    rubric: tuple[str, ...]


@dataclass(frozen=True)
class BenchRun:
    task_id: str
    model: str
    judge: str
    score: float
    # raw 는 계약상 dict 타입이지만 frozen 보장을 위해 default_factory 로 둔다.
    # 외부에서 넘긴 dict 는 run_suite/직접 생성 시 새 dict 로 복사해 공유 변이를 막는다.
    raw: dict = field(default_factory=dict)


def _normalize(s: str) -> str:
    # 결정론을 위해 소문자화 + 연속 공백 단일화. 한국어는 lower 영향이 없으므로 안전.
    return re.sub(r"\s+", " ", s.lower()).strip()


def _keyword_hit(haystack: str, keyword: str) -> bool:
    # 키워드는 부분 문자열 매칭(정규화 후). 빈 키워드는 매칭으로 인정하지 않는다(fail-closed).
    norm_kw = _normalize(keyword)
    if not norm_kw:
        return False
    return norm_kw in haystack


def deterministic_judge(output: str, task: BenchTask) -> float:
    """rubric 키워드 커버리지를 0..100 으로 채점한다(judge B).

    fail-closed:
      - rubric 이 비어 있으면 채점 근거가 없으므로 0.0.
      - output 이 비어 있으면 어떤 키워드도 못 맞히므로 0.0.
    재현성: 동일 (output, task.rubric) 은 항상 동일 점수를 돌려준다.
    """
    if not isinstance(output, str):
        return 0.0
    rubric = task.rubric
    if not rubric:
        return 0.0

    haystack = _normalize(output)
    if not haystack:
        return 0.0

    # 빈/공백 키워드는 분모/분자 모두에서 제외(fail-closed: 공짜 점수 금지).
    valid_keywords = tuple(kw for kw in rubric if _normalize(kw))
    if not valid_keywords:
        return 0.0

    hits = sum(1 for kw in valid_keywords if _keyword_hit(haystack, kw))
    coverage = (hits / len(valid_keywords)) * 100.0
    # 부동소수 잡음 제거를 위해 소수 6자리로 고정(결정론 직렬화 안정성).
    return round(coverage, 6)


# judge A 가 "근거/검증 흔적"으로 인정하는 결정론 마커. LLM rubric 채점자가
# 단순 키워드 나열보다 실증된 답변을 후하게 보는 성향을 모사한다. 이것이 judge B(순수
# 키워드 커버리지)와 갈리는 지점이다 — 같은 출력에서 두 심판이 어긋날 수 있다.
_QUALITY_MARKER_RE = re.compile(
    r"(exit\s*code|exit\s*\d|test.*(pass|fail)|grep|\b\d+\s*(개|matches)|"
    r"/[\w./-]+\.\w+|render|스크린샷|because|왜냐하면|therefore|따라서|"
    r"step\s*\d|단계|verified|검증|reproduc|재현)",
    re.IGNORECASE,
)


def _quality_markers(haystack: str) -> int:
    # 중복 마커도 끝까지 센다(결정론). 라이브 LLM 의 "근거가 두텁다" 신호 모사.
    return len(_QUALITY_MARKER_RE.findall(haystack))


def rubric_judge_a(output: str, task: BenchTask) -> float:
    """rubric 0~5 정량 채점을 결정론으로 모사한다(judge A), 0..100 으로 환산.

    judge B(키워드 커버리지)와 의도적으로 다른 논리를 쓴다:
      - rubric 항목 충족(coverage)은 만점의 절반(0~2.5점)까지만 기여한다.
      - 나머지 절반(0~2.5점)은 근거/검증 마커(_QUALITY_MARKER_RE) 밀도로 채운다.
    따라서 키워드만 나열한 출력은 B 는 높지만 A 는 낮고, 근거는 두터우나 정확한
    키워드를 비껴간 출력은 B 는 낮지만 A 는 높다 — 두 심판이 같은 출력에서 갈린다.

    fail-closed: rubric 이 비거나 output 이 비면 0.0.
    재현성: 동일 (output, task.rubric) 은 항상 동일 점수.
    """
    if not isinstance(output, str):
        return 0.0
    rubric = task.rubric
    if not rubric:
        return 0.0

    haystack = _normalize(output)
    if not haystack:
        return 0.0

    valid_keywords = tuple(kw for kw in rubric if _normalize(kw))
    if not valid_keywords:
        return 0.0

    hits = sum(1 for kw in valid_keywords if _keyword_hit(haystack, kw))
    coverage_ratio = hits / len(valid_keywords)
    # 0~2.5 점: rubric 항목 충족.
    coverage_points = coverage_ratio * 2.5

    markers = _quality_markers(haystack)
    # 0~2.5 점: 근거/검증 밀도. rubric 항목 수만큼이면 만점(2.5)으로 포화.
    evidence_ratio = min(markers / len(valid_keywords), 1.0)
    evidence_points = evidence_ratio * 2.5

    score_0_5 = coverage_points + evidence_points  # 0..5
    score_100 = (score_0_5 / 5.0) * 100.0
    return round(score_100, 6)


def _judge_raw(output: str, task: BenchTask) -> dict:
    """A/B 양쪽 채점에 공통으로 쓰는 진단 정보(키워드/마커)를 결정론으로 만든다."""
    haystack = _normalize(output)
    valid = tuple(kw for kw in task.rubric if _normalize(kw))
    matched = tuple(kw for kw in valid if _keyword_hit(haystack, kw))
    return {
        "prompt": task.prompt,
        "rubric": list(task.rubric),
        "rubric_valid": list(valid),
        "matched_keywords": list(matched),
        "matched_count": len(matched),
        "rubric_count": len(valid),
        "quality_markers": _quality_markers(haystack),
        "output_present": bool(output),
    }


def disagree_runs(
    task: BenchTask,
    output: str,
    model: str = "deterministic",
) -> tuple[BenchRun, BenchRun]:
    """judge A 와 judge B 를 같은 출력에 적용해 두 BenchRun 을 모두 반환한다.

    평균으로 덮지 않는다 — 각 심판의 점수를 독립 BenchRun 으로 남기고, 각 raw 에
    상대 심판 점수(other_judge/other_score)와 불일치 여부(disagree/delta)를 함께
    기록한다. 두 BenchRun 의 raw 는 동일한 불일치 판정(대칭)을 담는다.
    """
    if output is None:
        output = ""
    score_a = rubric_judge_a(output, task)
    score_b = deterministic_judge(output, task)
    delta = round(abs(score_a - score_b), 6)
    disagree = delta >= DISAGREE_THRESHOLD

    base = _judge_raw(output, task)

    raw_a = {
        **base,
        "judge": JUDGE_A_NAME,
        "score": score_a,
        "other_judge": JUDGE_B_NAME,
        "other_score": score_b,
        "delta": delta,
        "disagree": disagree,
        "disagree_threshold": DISAGREE_THRESHOLD,
    }
    raw_b = {
        **base,
        "judge": JUDGE_B_NAME,
        "score": score_b,
        "other_judge": JUDGE_A_NAME,
        "other_score": score_a,
        "delta": delta,
        "disagree": disagree,
        "disagree_threshold": DISAGREE_THRESHOLD,
    }
    run_a = BenchRun(task_id=task.id, model=model, judge=JUDGE_A_NAME, score=score_a, raw=raw_a)
    run_b = BenchRun(task_id=task.id, model=model, judge=JUDGE_B_NAME, score=score_b, raw=raw_b)
    return run_a, run_b


def run_suite_dual(
    tasks: tuple[BenchTask, ...],
    outputs: Mapping[str, str],
    model: str = "deterministic",
) -> tuple[BenchRun, ...]:
    """각 task 에 judge A·B 를 모두 적용한 BenchRun 들을 반환한다(task 당 2개).

    fail-closed: 출력이 없으면 빈 문자열로 간주해 양쪽 모두 0.0 채점.
    순서: task 입력 순서대로 (A, B) 쌍을 평탄화한다(결정론). 평균 없음.
    """
    runs: list[BenchRun] = []
    for task in tasks:
        output = outputs.get(task.id, "")
        run_a, run_b = disagree_runs(task, output, model=model)
        runs.append(run_a)
        runs.append(run_b)
    return tuple(runs)


def disagreement_cases(runs: tuple[BenchRun, ...]) -> tuple[dict, ...]:
    """dual run 결과에서 A/B 가 갈린 case 만 task 단위로 추출한다(결정론).

    각 case: {task_id, score_a, score_b, delta, matched_count, rubric_count,
    quality_markers, prompt}. judge A run(other_judge==JUDGE_B_NAME)만 훑어 중복을 막는다.
    평균으로 합치지 않는다 — 양쪽 점수를 그대로 보존한다.
    """
    cases: list[dict] = []
    for r in runs:
        raw = r.raw
        if raw.get("judge") != JUDGE_A_NAME:
            continue
        if not raw.get("disagree"):
            continue
        cases.append(
            {
                "task_id": r.task_id,
                "score_a": raw.get("score"),
                "score_b": raw.get("other_score"),
                "delta": raw.get("delta"),
                "matched_count": raw.get("matched_count"),
                "rubric_count": raw.get("rubric_count"),
                "quality_markers": raw.get("quality_markers"),
                "prompt": raw.get("prompt", ""),
            }
        )
    return tuple(cases)


def run_suite(
    tasks: tuple[BenchTask, ...],
    outputs: Mapping[str, str],
    model: str = "deterministic",
) -> tuple[BenchRun, ...]:
    """각 task 에 대해 judge B 로 채점한 BenchRun 튜플을 반환한다.

    fail-closed: outputs 에 해당 task_id 출력이 없으면 빈 문자열로 간주해 0.0 채점.
    결과는 task 입력 순서를 보존한다(결정론).
    """
    runs: list[BenchRun] = []
    for task in tasks:
        output = outputs.get(task.id, "")
        if output is None:
            output = ""
        score = deterministic_judge(output, task)
        matched = tuple(
            kw for kw in task.rubric if _normalize(kw) and _keyword_hit(_normalize(output), kw)
        )
        valid = tuple(kw for kw in task.rubric if _normalize(kw))
        raw = {
            "prompt": task.prompt,
            "rubric": list(task.rubric),
            "rubric_valid": list(valid),
            "matched_keywords": list(matched),
            "matched_count": len(matched),
            "rubric_count": len(valid),
            "output_present": bool(output),
            "judge": JUDGE_NAME,
        }
        runs.append(
            BenchRun(
                task_id=task.id,
                model=model,
                judge=JUDGE_NAME,
                score=score,
                raw=raw,
            )
        )
    return tuple(runs)


def write_raw(runs: tuple[BenchRun, ...], path: str) -> None:
    """BenchRun 들을 JSON 으로 직렬화해 path(기본 bench/raw.json)에 기록한다.

    스키마: {schema_version, judge, generator, runs:[{task_id, model, judge, score, raw}]}.
    결정론 직렬화: sort_keys=True, 고정 들여쓰기. 점수가 raw 와 정합하도록 함께 기록한다
    (reproduce.sh SENTINEL_GUARD: 점수 주장 vs raw.json 정합성 검사 대상).
    """
    payload = {
        "schema_version": "1.0.0",
        "judge": JUDGE_NAME,
        "generator": "fablelayer.benchmark.write_raw",
        "sentinel_guard": SENTINEL_GUARD,
        "runs": [
            {
                "task_id": r.task_id,
                "model": r.model,
                "judge": r.judge,
                "score": r.score,
                "raw": r.raw,
            }
            for r in runs
        ],
    }
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2, sort_keys=True)
        fh.write("\n")


# RESULTS.md 의 불일치 절 헤딩. 이 절 본문만 실데이터로 교체하고 다른 절(특히 한계)은 보존한다.
_DISAGREE_HEADING = "## 심판 불일치"


def _render_disagreement_section(cases: tuple[dict, ...]) -> str:
    """A/B 불일치 case 들을 RESULTS.md 본문 마크다운으로 렌더한다(결정론).

    case 가 없으면 '미측정' 대신 'A/B 일치(불일치 0건)' 로 정직히 표기한다.
    평균으로 덮지 않고 양쪽 점수를 case 단위로 그대로 표에 남긴다.
    """
    lines: list[str] = [_DISAGREE_HEADING, ""]
    lines.append(
        "judge A(rubric 0-5 모사)와 judge B(rule 키워드 커버리지)의 판정이 어긋난 case다. "
        f"두 점수 차가 {DISAGREE_THRESHOLD:.0f}점(0..100) 이상이면 불일치로 본다. "
        "불일치는 평균으로 덮지 않고 양쪽 점수를 그대로 남긴다(recover 축: 실패 비삭제). "
        "출처 원자료는 `bench/fixtures_raw.json` 의 각 run.raw(other_judge/other_score/delta)."
    )
    lines.append("")
    if not cases:
        lines.append("현재 fixture 기준 불일치 0건(judge A/B 일치). 갈리는 case 가 생기면 자동 기록된다.")
        lines.append("")
        return "\n".join(lines)

    lines.append("| task_id | judge A (0-100) | judge B (0-100) | Δ | 근거(matched/rubric, markers) | 원인 추정 |")
    lines.append("|---|---|---|---|---|---|")
    for c in cases:
        cause = (
            "B 높고 A 낮음 → 키워드는 채웠으나 근거/검증 마커 부족(rule 과탐, rubric 엄격)"
            if (c.get("score_b") or 0.0) > (c.get("score_a") or 0.0)
            else "A 높고 B 낮음 → 근거는 두터우나 정확한 키워드 비껴감(rule 미탐, rubric 관대)"
        )
        lines.append(
            "| {tid} | {a:.2f} | {b:.2f} | {d:.2f} | matched {m}/{r}, markers {k} | {cause} |".format(
                tid=c.get("task_id", "?"),
                a=c.get("score_a") or 0.0,
                b=c.get("score_b") or 0.0,
                d=c.get("delta") or 0.0,
                m=c.get("matched_count", 0),
                r=c.get("rubric_count", 0),
                k=c.get("quality_markers", 0),
                cause=cause,
            )
        )
    lines.append("")
    lines.append(
        "해석: 위 불일치는 단일 LLM-judge 의 자기편향을 교차 검증으로 드러낸 것이다. "
        "rubric 주관성(judge A)과 rule 과탐/미탐(judge B)은 아래 '한계' 절의 judge 편향 항목과 연결된다."
    )
    lines.append("")
    return "\n".join(lines)


def update_results_disagreement(results_path: str, cases: tuple[dict, ...]) -> bool:
    """RESULTS.md 의 '## 심판 불일치' 절 본문을 불일치 실데이터로 교체한다(idempotent).

    - 다른 절(특히 '## 한계')은 절대 건드리지 않는다 — 다음 동급 헤딩 직전까지만 교체.
    - 불일치 절이 없으면 fail-closed 로 False 를 반환한다(임의 위치 삽입 금지).
    - 교체이므로 반복 실행해도 누적/중복되지 않는다(결정론).
    반환: 교체 성공 True, 절 미발견 False.
    """
    try:
        with open(results_path, "r", encoding="utf-8") as fh:
            text = fh.read()
    except OSError:
        return False

    lines = text.splitlines()
    start = None
    for idx, line in enumerate(lines):
        # placeholder 헤딩은 '## 심판 불일치 (측정 시 기록)' 처럼 접미사가 붙을 수 있어 prefix 로 찾는다.
        if line.startswith(_DISAGREE_HEADING):
            start = idx
            break
    if start is None:
        return False  # placeholder 절이 없으면 삽입하지 않는다(fail-closed)

    # 다음 '## ' 헤딩(동급) 직전까지가 이 절의 범위. 그 헤딩(예: '## 재현 절차','## 한계')은 보존.
    end = len(lines)
    for idx in range(start + 1, len(lines)):
        if lines[idx].startswith("## "):
            end = idx
            break

    section = _render_disagreement_section(cases).rstrip("\n")
    new_lines = lines[:start] + section.split("\n") + [""] + lines[end:]
    new_text = "\n".join(new_lines)
    if not new_text.endswith("\n"):
        new_text += "\n"

    with open(results_path, "w", encoding="utf-8") as fh:
        fh.write(new_text)
    return True
