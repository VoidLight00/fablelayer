"""FableLayer CLI (FL5, FL11, 회복).

INTERFACE.md 계약을 구현하는 단일 진입점이다.

subcommands:
  init                  rendered core 에서 .fablelayer/ scaffold (dry-run 기본; --apply 시 쓰기)
  upgrade <model>       router.route(TaskSpec) 로 라우팅 결정 작성 (static conf 금지)
  benchmark             bench/fixtures 로 run_suite -> write_raw -> summary
  check --file <f>      evidence_gate.scan_text over file -> exit 0/2
  status                최신 runs/<id>/RUN_MANIFEST.json phase 출력
  resume                최신 manifest 에서 status!=done phase 재실행
  (no-arg / --help)     usage, exit 0

정직성 경계(FL9): capability 는 전이되지 않는다. 이 CLI 가 설치/적용하는 것은
전이 가능한 절차·출력구조 레이어뿐이다. 성능 수치는 bench/RESULTS.md 참조.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

# core 5모듈 (이미 구현됨). cli 는 INTERFACE 계약에만 의존한다.
from fablelayer import benchmark, evidence_gate, promptcore, router, source_policy

# adapters(FL5) 는 별도 엔지니어 산출물이라 부재할 수 있다.
# import 실패가 cli 로드를 깨뜨리지 않도록 방어적으로 받는다(부재 시 None).
try:  # pragma: no cover - 환경 의존
    from fablelayer import adapters as _adapters
except Exception:  # pragma: no cover
    _adapters = None

PROG = "fablelayer"
VERSION = "0.1.1"

# FL11 canonical phase enum — 이 순서만 사용한다.
CANONICAL_PHASES: tuple[str, ...] = (
    "0-context",
    "1-spec",
    "2-build",
    "3-gates",
    "4-bench",
    "5-report",
)
DONE_STATUS = "done"

# 제품 루트(이 파일은 <root>/fablelayer/cli.py 에 위치).
PRODUCT_ROOT = Path(__file__).resolve().parent.parent

# 전이 가능한 절차 레이어 디렉토리(capability 아님).
LAYER_DIRS: tuple[str, ...] = ("core", "styles", "skills", "agents", "adapters")

# Wheel/venv 설치처럼 소스 체크아웃의 bench/fixtures 디렉토리가 없는 환경에서도
# `python -m fablelayer.cli benchmark` 가 바로 작동하도록 하는 최소 내장 fixture.
# 소스 체크아웃에서는 여전히 bench/fixtures/*.json 을 우선 사용한다.
FALLBACK_BENCH_TASKS: tuple[benchmark.BenchTask, ...] = (
    benchmark.BenchTask(
        id="dbg-001",
        prompt=(
            "A pagination helper returns one fewer item on the last page. "
            "A failing test is provided. Reproduce the failure, identify the root cause, "
            "propose the fix, and state how you verified it (test pass / exit code)."
        ),
        rubric=("root cause", "off-by-one", "reproduce", "fix", "test", "verify"),
    ),
    benchmark.BenchTask(
        id="disagree-001",
        prompt="action item, decision, owner, deadline, summary, status — these are listed but with no reasoning shown.",
        rubric=("action item", "decision", "owner", "deadline", "summary", "status"),
    ),
    benchmark.BenchTask(
        id="extract-001",
        prompt=(
            "Extract action items, decisions, and owners from the meeting transcript into the provided JSON schema. "
            "Cite the line each item comes from; do not invent owners or due dates."
        ),
        rubric=("action item", "decision", "owner", "line", "cite", "json"),
    ),
)

EXIT_OK = 0
EXIT_USAGE = 2  # check 위반·인자 오류·미존재 자원 등 fail-closed
EXIT_ERROR = 1


@dataclass(frozen=True)
class Args:
    """파싱된 CLI 인자(불변)."""

    command: str
    positionals: tuple[str, ...]
    apply: bool
    target: str
    file: str
    run_id: str


# ---------------------------------------------------------------------------
# 출력 헬퍼
# ---------------------------------------------------------------------------
def _out(line: str = "") -> None:
    sys.stdout.write(line + "\n")


def _err(line: str) -> None:
    sys.stderr.write(line + "\n")


def usage() -> None:
    _out(
        f"""{PROG} {VERSION} — FableLayer CLI

  Fable is a discipline, not a capability transplant.
  This CLI installs the transferable procedure/output-structure layer.
  It does NOT transfer model capability. 성능 수치는 bench/RESULTS.md 참조.

usage:
  {PROG} <command> [args]

commands:
  init                  rendered PromptCore 에서 .fablelayer/ 절차 레이어 scaffold
                        (기본 dry-run; 실제 쓰기는 --apply; 덮어쓰기 전 .bak snapshot)
  upgrade <model>       <model>=opus|sonnet|local 라우팅 결정 작성
                        (router.route 사용 — static conf 금지)
  benchmark             bench/fixtures 로 deterministic judge 실행 -> raw 기록 -> summary
  check --file <f>      파일에 evidence_gate.scan_text 적용 (위반 시 exit 2)
  status                최신 runs/<id>/RUN_MANIFEST.json phase 상태 출력
  resume                최신 manifest 에서 status!=done phase 재실행

options:
  --apply               init 의 파괴적 동작(파일 쓰기)을 실제 수행 (없으면 dry-run)
  --target DIR          init 대상 디렉토리 (기본: 현재 작업 디렉토리)
  --file PATH           check 대상 파일
  --run-id ID           status/resume 대상 run_id (기본: 최신)
  -h, --help            이 도움말
  -V, --version         버전

notes:
  - 외부 push/deploy/marketplace 등록은 이 CLI 가 수행하지 않는다(FL15 승인 게이트).
  - 전이되는 것은 절차(verification grounding, evidence gate, systematic
    investigation, early-stop 방지, VFF 출력구조)뿐이다. capability 는 전이 불가."""
    )


# ---------------------------------------------------------------------------
# 인자 파싱
# ---------------------------------------------------------------------------
def _parse(argv: list[str]) -> tuple[Args | None, int | None]:
    """argv 를 Args 로 파싱한다.

    반환: (Args, None) 정상 / (None, exit_code) usage·version·오류로 즉시 종료.
    """
    if not argv:
        return None, EXIT_OK  # no-arg -> usage exit 0

    first = argv[0]
    if first in ("-h", "--help"):
        return None, EXIT_OK
    if first in ("-V", "--version"):
        _out(f"{PROG} {VERSION}")
        return None, EXIT_OK

    command = first
    rest = argv[1:]

    positionals: list[str] = []
    apply_flag = False
    target = ""
    file_path = ""
    run_id = ""

    i = 0
    while i < len(rest):
        tok = rest[i]
        if tok == "--apply":
            apply_flag = True
        elif tok == "--target":
            i += 1
            if i >= len(rest):
                _err("ERROR: --target 에 디렉토리가 필요합니다")
                return None, EXIT_USAGE
            target = rest[i]
        elif tok.startswith("--target="):
            target = tok[len("--target="):]
        elif tok == "--file":
            i += 1
            if i >= len(rest):
                _err("ERROR: --file 에 경로가 필요합니다")
                return None, EXIT_USAGE
            file_path = rest[i]
        elif tok.startswith("--file="):
            file_path = tok[len("--file="):]
        elif tok in ("--run-id", "--run_id"):
            i += 1
            if i >= len(rest):
                _err("ERROR: --run-id 에 값이 필요합니다")
                return None, EXIT_USAGE
            run_id = rest[i]
        elif tok.startswith("--run-id="):
            run_id = tok[len("--run-id="):]
        elif tok in ("-h", "--help"):
            return None, EXIT_OK
        elif tok.startswith("--"):
            _err(f"ERROR: 알 수 없는 옵션 '{tok}'")
            return None, EXIT_USAGE
        else:
            positionals.append(tok)
        i += 1

    args = Args(
        command=command,
        positionals=tuple(positionals),
        apply=apply_flag,
        target=target,
        file=file_path,
        run_id=run_id,
    )
    return args, None


# ---------------------------------------------------------------------------
# init — rendered core 에서 .fablelayer/ scaffold
# ---------------------------------------------------------------------------
def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _backup_if_exists(path: Path) -> Path | None:
    """기존 파일이 있으면 .bak 스냅샷을 만들고 그 경로를 반환한다."""
    if not path.exists():
        return None
    backup = path.with_suffix(path.suffix + ".bak")
    backup.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    return backup


def cmd_init(args: Args) -> int:
    """rendered PromptCore 를 단일 소스로 .fablelayer/ 를 scaffold 한다.

    dry-run 기본: 무엇을 쓸지 미리보기만 한다.
    --apply: 실제 쓰기. 기존 파일은 덮어쓰기 전 .bak snapshot.
    """
    dest = Path(args.target).expanduser() if args.target else Path.cwd()
    if not dest.exists():
        _err(f"ERROR: 대상 디렉토리가 없습니다: {dest}")
        return EXIT_USAGE
    dest = dest.resolve()

    install_dir = dest / ".fablelayer"
    core_md = install_dir / "promptcore.md"
    manifest_md = install_dir / "MANIFEST"

    # 단일 소스: rendered core. 모든 산출물이 여기서 파생된다.
    rendered = promptcore.render_markdown(promptcore.default_core())

    _out(f"{PROG} init")
    _out(f"대상 프로젝트 : {dest}")
    _out(f"설치 위치     : {install_dir}/")
    _out("절차 레이어 (capability 아님, procedure 임): " + ", ".join(LAYER_DIRS))
    _out("")

    if not args.apply:
        _out("[dry-run] 실제로 수행할 작업:")
        _out(f"  1) mkdir -p {install_dir}")
        _out(f"  2) write {core_md}  (render_markdown(default_core()) 단일 소스)")
        _out(f"  3) write {manifest_md}  (설치 메타 + 절차 항목)")
        _out("")
        _out(f"실행하려면 --apply 를 붙이세요:  {PROG} init --apply")
        return EXIT_OK

    # --- 실제 쓰기 (--apply) ---
    try:
        install_dir.mkdir(parents=True, exist_ok=True)

        bak = _backup_if_exists(core_md)
        if bak is not None:
            _out(f"snapshot: {bak}")
        core_md.write_text(rendered, encoding="utf-8")
        _out(f"wrote: {core_md}")

        bak2 = _backup_if_exists(manifest_md)
        if bak2 is not None:
            _out(f"snapshot: {bak2}")
        manifest_md.write_text(_init_manifest_body(), encoding="utf-8")
        _out(f"wrote: {manifest_md}")
    except OSError as exc:
        _err(f"ERROR: init 쓰기 실패: {exc}")
        return EXIT_ERROR

    _out("")
    _out("완료: .fablelayer/ scaffold 작성 (rendered core 단일 소스).")
    return EXIT_OK


def _init_manifest_body() -> str:
    lines = [
        "# FableLayer install manifest",
        f"installed_at: {_utc_stamp()}",
        f"source_root: {PRODUCT_ROOT}",
        f"cli_version: {VERSION}",
        "source: render_markdown(default_core())  # 단일 소스",
        "note: capability 비전이 — 절차·출력구조 레이어만 설치됨. 성능 수치는 bench/RESULTS.md 참조.",
        "applied_procedures:",
        "  - verification-grounding",
        "  - evidence-gate",
        "  - systematic-investigation",
        "  - anti-early-stop",
        "  - output-structure (VFF v2)",
        "  - drift-prevention",
        "compression_rules: off  # value-for-fable v2 교훈 — 품질 부채",
    ]
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# upgrade <model> — router.route(TaskSpec) 기반 라우팅 결정 (static conf 금지)
# ---------------------------------------------------------------------------
_MODEL_TO_TASKSPEC = {
    # 각 대상별 대표 TaskSpec. 결정은 router.route 가 내린다(정적 매핑 금지).
    "opus": router.TaskSpec(kind="upgrade:opus", explicit_opus=True),
    "sonnet": router.TaskSpec(kind="upgrade:sonnet"),
    "local": router.TaskSpec(kind="upgrade:local"),
}


def cmd_upgrade(args: Args) -> int:
    """router.route 를 사용해 라우팅 결정을 만든다(static conf 금지)."""
    if not args.positionals:
        _err("ERROR: upgrade 에 모델이 필요합니다. <model>=opus|sonnet|local")
        return EXIT_USAGE

    model = args.positionals[0]
    spec = _MODEL_TO_TASKSPEC.get(model)
    if spec is None:
        _err(f"ERROR: 지원하지 않는 모델 '{model}'. opus|sonnet|local 중 하나.")
        return EXIT_USAGE

    decision = router.route(spec)

    _out(f"{PROG} upgrade {model}")
    _out(f"target_model_request : {model}")
    _out(f"routed_model         : {decision.model}")
    _out("fired_signals        : " + (", ".join(decision.fired_signals) or "(none)"))
    _out(f"note                 : {decision.note}")
    _out("")
    _out("# router.route(TaskSpec) 가 모델 등급을 선택했다(정적 conf 아님).")
    _out("# 전이되는 것은 절차뿐이다 — capability 는 전이되지 않는다.")
    return EXIT_OK


# ---------------------------------------------------------------------------
# benchmark — bench/fixtures 로 run_suite -> write_raw -> summary
# ---------------------------------------------------------------------------
def _load_fixture_tasks() -> tuple[tuple[benchmark.BenchTask, ...], tuple[str, ...]]:
    """bench/fixtures/*.json 을 BenchTask 로 로드한다.

    반환: (tasks, errors). 파싱 실패 fixture 는 errors 에 모은다(fail-closed: 채점 제외).
    """
    fixtures_dir = PRODUCT_ROOT / "bench" / "fixtures"
    tasks: list[benchmark.BenchTask] = []
    errors: list[str] = []
    if not fixtures_dir.is_dir():
        return FALLBACK_BENCH_TASKS, (f"source fixtures dir not found; using packaged fallback fixtures: {fixtures_dir}",)

    for path in sorted(fixtures_dir.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"{path.name}: parse error ({exc})")
            continue
        task_id = data.get("id")
        prompt = data.get("prompt")
        rubric = data.get("rubric")
        if not isinstance(task_id, str) or not isinstance(prompt, str) or not isinstance(rubric, list):
            errors.append(f"{path.name}: missing id/prompt/rubric")
            continue
        tasks.append(
            benchmark.BenchTask(
                id=task_id,
                prompt=prompt,
                rubric=tuple(str(k) for k in rubric),
            )
        )
    return tuple(tasks), tuple(errors)


def _fixture_outputs(tasks: tuple[benchmark.BenchTask, ...]) -> dict[str, str]:
    """라이브 모델 없이 재현 가능한 출력을 만든다.

    judge B(결정론)는 라이브 모델이 필요 없다. fixture 의 prompt 자체를 출력으로
    사용하면 합성 점수가 끼어들지 않고(prompt 에 우연히 들어간 키워드만 매칭),
    동일 입력이 항상 동일 점수를 낸다.
    """
    return {t.id: t.prompt for t in tasks}


def cmd_benchmark(args: Args) -> int:
    """bench/fixtures 로 judge A·B 를 모두 돌리고 raw 를 기록한 뒤 summary 를 낸다.

    두 심판(A=rubric 0-5 모사, B=rule 키워드 커버리지)을 같은 출력에 적용하고,
    불일치는 평균으로 덮지 않고 양쪽 BenchRun 을 fixtures_raw.json 에 모두 남긴다.
    갈린 case 는 RESULTS.md '## 심판 불일치' 절에 실데이터로 자동 반영한다.

    주의: 큐레이트된 placeholder bench/raw.json 은 건드리지 않는다.
    deterministic 산출물은 bench/fixtures_raw.json 에 별도로 기록한다.
    """
    tasks, errors = _load_fixture_tasks()
    for e in errors:
        _err(f"WARN: {e}")

    if not tasks:
        _err("ERROR: 채점할 fixture task 가 없습니다 (fail-closed).")
        return EXIT_ERROR

    outputs = _fixture_outputs(tasks)
    runs = benchmark.run_suite_dual(tasks, outputs)

    source_bench_dir = PRODUCT_ROOT / "bench"
    if (source_bench_dir / "fixtures").is_dir():
        raw_path = source_bench_dir / "fixtures_raw.json"
        results_path: Path | None = source_bench_dir / "RESULTS.md"
    else:
        # 설치된 wheel/site-packages 안에 쓰지 않는다. 사용자가 실행한 프로젝트 아래에
        # 안전한 산출물 디렉토리를 만들면 `pip install fablelayer && fablelayer benchmark`
        # 경험이 바로 작동한다.
        raw_path = Path.cwd() / ".fablelayer" / "bench" / "fixtures_raw.json"
        results_path = None

    try:
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        benchmark.write_raw(runs, str(raw_path))
    except OSError as exc:
        _err(f"ERROR: raw 기록 실패: {exc}")
        return EXIT_ERROR

    cases = benchmark.disagreement_cases(runs)
    updated = False
    if results_path is not None:
        updated = benchmark.update_results_disagreement(str(results_path), cases)
    if results_path is not None and not updated:
        # 절이 없으면 자동 삽입하지 않는다(fail-closed). 다른 절 오염 방지.
        _err(f"WARN: RESULTS.md 에 '## 심판 불일치' 절이 없어 자동 반영을 건너뜀: {results_path}")

    _out(f"{PROG} benchmark")
    _out(f"judges       : {benchmark.JUDGE_A_NAME} + {benchmark.JUDGE_B_NAME} (deterministic, no live model)")
    _out(f"raw written  : {raw_path}")
    _out(f"tasks scored : {len(tasks)}  (runs: {len(runs)} = task x 2 judges)")
    _out("")
    # task 단위로 A/B 점수를 나란히 보여준다(평균으로 합치지 않음).
    by_task: dict[str, dict] = {}
    for r in runs:
        slot = by_task.setdefault(r.task_id, {})
        slot[r.judge] = r

    _out("summary (task_id  judge A  judge B  Δ  disagree):")
    total_a = 0.0
    total_b = 0.0
    disagree_n = 0
    for t in tasks:
        slot = by_task.get(t.id, {})
        ra = slot.get(benchmark.JUDGE_A_NAME)
        rb = slot.get(benchmark.JUDGE_B_NAME)
        sa = ra.score if ra else 0.0
        sb = rb.score if rb else 0.0
        delta = ra.raw.get("delta", abs(sa - sb)) if ra else abs(sa - sb)
        dis = bool(ra and ra.raw.get("disagree"))
        if dis:
            disagree_n += 1
        total_a += sa
        total_b += sb
        _out(f"  {t.id:<14} {sa:>6.2f}  {sb:>6.2f}  {delta:>6.2f}  {'YES' if dis else 'no'}")

    n = len(tasks)
    mean_a = round(total_a / n, 2) if n else 0.0
    mean_b = round(total_b / n, 2) if n else 0.0
    _out("")
    _out(f"mean A       : {mean_a:.2f}   mean B : {mean_b:.2f}  (0..100; 두 심판 점수는 합치지 않음)")
    if results_path is None:
        disagreement_note = f"raw 기록만 수행 (설치 모드: {raw_path})"
    else:
        disagreement_note = "bench/RESULTS.md '## 심판 불일치' 자동 반영" if updated else "bench/RESULTS.md '## 심판 불일치' 절 미발견"
    _out(
        f"disagreements: {disagree_n}/{n} task(s) → {disagreement_note}"
    )
    _out("note         : 두 심판은 서로 다른 논리이며 점수를 평균으로 덮지 않는다(불일치 보존).")
    _out("               capability 주장이 아니며, 성능 비교는 bench/RESULTS.md 의 '## 한계' 와 함께만 해석한다.")
    return EXIT_OK


# ---------------------------------------------------------------------------
# check --file <f> — evidence_gate.scan_text over file -> exit 0/2
# ---------------------------------------------------------------------------
def cmd_check(args: Args) -> int:
    """파일 내용을 evidence_gate.scan_text 로 검사한다. 위반 시 exit 2(fail-closed)."""
    if not args.file:
        _err("ERROR: check 에 --file <경로> 가 필요합니다")
        return EXIT_USAGE

    path = Path(args.file).expanduser()
    if not path.is_file():
        _err(f"ERROR: 파일을 찾을 수 없습니다: {path}")
        return EXIT_USAGE

    try:
        content = path.read_text(encoding="utf-8")
    except OSError as exc:
        _err(f"ERROR: 파일 읽기 실패: {exc}")
        return EXIT_USAGE

    result = evidence_gate.scan_text(content)

    _out(f"{PROG} check --file {path}")
    _out(f"passed: {result.passed}")
    for reason in result.reasons:
        _out(f"  - {reason}")

    if result.passed:
        return EXIT_OK
    return EXIT_USAGE  # 2


# ---------------------------------------------------------------------------
# runs/ manifest 헬퍼 (status / resume 공용)
# ---------------------------------------------------------------------------
def _runs_dir() -> Path:
    return PRODUCT_ROOT / "runs"


def _list_manifests() -> tuple[Path, ...]:
    """runs/*/RUN_MANIFEST.json 경로를 run_id 기준 정렬해 반환한다."""
    runs = _runs_dir()
    if not runs.is_dir():
        return tuple()
    found = [
        d / "RUN_MANIFEST.json"
        for d in sorted(runs.iterdir())
        if d.is_dir() and (d / "RUN_MANIFEST.json").is_file()
    ]
    return tuple(found)


def _resolve_manifest(run_id: str) -> Path | None:
    """run_id 지정 시 해당 manifest, 아니면 최신(이름순 마지막) manifest 를 반환한다."""
    manifests = _list_manifests()
    if not manifests:
        return None
    if run_id:
        target = _runs_dir() / run_id / "RUN_MANIFEST.json"
        return target if target.is_file() else None
    return manifests[-1]


def _load_manifest(path: Path) -> tuple[dict | None, str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return None, f"manifest 읽기/파싱 실패: {exc}"
    if not isinstance(data, dict):
        return None, "manifest 최상위가 객체가 아님 (fail-closed)"
    return data, ""


# RETRO.md "다음 액션" 섹션 헤딩(정확 일치). 한국어 정본.
RETRO_NEXT_HEADING = "## 다음 액션"


def _parse_retro_next_actions(retro_path: Path) -> tuple[str, ...]:
    """RETRO.md 의 '## 다음 액션' 섹션을 파싱해 액션 항목 튜플을 반환한다.

    fail-closed: 파일 부재·읽기 실패·섹션 부재면 빈 튜플(주입할 학습 없음).
    섹션은 RETRO_NEXT_HEADING 다음 줄부터 다음 '## ' 헤딩 직전까지.
    번호/불릿 마커(1. , - , * )는 제거하고 본문만 보존한다.
    """
    if not retro_path.is_file():
        return tuple()
    try:
        text = retro_path.read_text(encoding="utf-8")
    except OSError:
        return tuple()

    lines = text.splitlines()
    in_section = False
    actions: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not in_section:
            if stripped == RETRO_NEXT_HEADING:
                in_section = True
            continue
        # 섹션 진입 후 다음 '## ' 헤딩에서 종료(fail-closed: 다음 섹션 침범 금지).
        if stripped.startswith("## "):
            break
        if not stripped:
            continue
        actions.append(_strip_list_marker(stripped))
    return tuple(a for a in actions if a)


def _strip_list_marker(s: str) -> str:
    """선행 번호/불릿 마커(1. , 2) , - , * )를 제거하고 본문을 반환한다."""
    body = s
    # 순서 리스트: '12.' 또는 '12)'
    j = 0
    while j < len(body) and body[j].isdigit():
        j += 1
    if j > 0 and j < len(body) and body[j] in ".)":
        return body[j + 1:].strip()
    # 비순서 리스트: '- ' '* ' '+ '
    if body[:2] in ("- ", "* ", "+ "):
        return body[2:].strip()
    return body.strip()


def _ordered_phases(phases: dict) -> tuple[tuple[str, str], ...]:
    """canonical enum 순서로 (phase, status) 를 반환한다.

    manifest 에 없는 canonical phase 는 'missing' 으로, canonical 이 아닌 키는
    뒤에 'non-canonical' 표시로 붙인다(fail-closed: 무시하지 않음).
    """
    ordered: list[tuple[str, str]] = []
    for phase in CANONICAL_PHASES:
        status = phases.get(phase, "missing")
        ordered.append((phase, str(status)))
    for key, status in phases.items():
        if key not in CANONICAL_PHASES:
            ordered.append((key + " (non-canonical)", str(status)))
    return tuple(ordered)


# ---------------------------------------------------------------------------
# phase cross-check — 자가기재 status 를 실제 산출물 존재로 검증
# ---------------------------------------------------------------------------
# 각 canonical phase 가 done 이려면 존재해야 하는 산출물(상대경로). cross-check
# 가능한 phase 만 매핑한다. 매핑 없는 phase 는 ('unverifiable') 로 보고한다.
_PHASE_ARTIFACTS: dict[str, tuple[str, ...]] = {
    "0-context": ("REQUIREMENTS.md",),
    "1-spec": ("INTERFACE.md",),
    "2-build": ("core/promptcore.md",),
    "5-report": ("bench/RESULTS.md",),
}


def _crosscheck_phase(phase: str, claimed: str) -> tuple[str, str]:
    """자가기재 status 를 실제 산출물 존재로 교차검증한다.

    반환: (verdict, detail).
      verdict in {"ok","mismatch","unverifiable"}.
      - claimed==done & 산출물 모두 존재 -> ok
      - claimed==done & 산출물 누락      -> mismatch (자가기재 불신, fail-closed)
      - claimed!=done                    -> ok (미완 주장은 교차검증 대상 아님)
      - 매핑 없는 phase                  -> unverifiable
    """
    artifacts = _PHASE_ARTIFACTS.get(phase)
    if artifacts is None:
        return "unverifiable", "교차검증 가능한 산출물 매핑 없음"
    if claimed != DONE_STATUS:
        return "ok", "done 미주장 — 교차검증 생략"
    missing = [a for a in artifacts if not (PRODUCT_ROOT / a).is_file()]
    if missing:
        return "mismatch", "done 주장이나 산출물 누락: " + ", ".join(missing)
    return "ok", "산출물 존재 확인: " + ", ".join(artifacts)


# ---------------------------------------------------------------------------
# status — 최신 manifest phase 상태 출력
# ---------------------------------------------------------------------------
def cmd_status(args: Args) -> int:
    manifest_path = _resolve_manifest(args.run_id)
    if manifest_path is None:
        if args.run_id:
            _err(f"ERROR: run_id '{args.run_id}' 의 RUN_MANIFEST.json 을 찾을 수 없습니다")
        else:
            _err("ERROR: runs/<id>/RUN_MANIFEST.json 이 없습니다")
        return EXIT_USAGE

    data, msg = _load_manifest(manifest_path)
    if data is None:
        _err(f"ERROR: {msg}")
        return EXIT_USAGE

    run_id = str(data.get("run_id", manifest_path.parent.name))
    mode = str(data.get("mode", "?"))
    phases = data.get("phases", {})
    if not isinstance(phases, dict):
        _err("ERROR: manifest 'phases' 가 객체가 아님 (fail-closed)")
        return EXIT_USAGE

    _out(f"{PROG} status")
    _out(f"run_id   : {run_id}")
    _out(f"mode     : {mode}")
    _out(f"manifest : {manifest_path}")
    _out("phases   :  (status = 자가기재 / xcheck = 산출물 교차검증)")
    incomplete = 0
    mismatches = 0
    for phase, status in _ordered_phases(phases):
        mark = "ok" if status == DONE_STATUS else "..."
        if status != DONE_STATUS:
            incomplete += 1
        # canonical phase 만 산출물로 교차검증한다(non-canonical 표시는 그대로).
        base_phase = phase.split(" ")[0]
        verdict, detail = _crosscheck_phase(base_phase, status)
        if verdict == "mismatch":
            mismatches += 1
        _out(f"  [{mark}] {phase:<24} {status:<12} xcheck={verdict}  {detail}")
    _out("")
    if incomplete == 0:
        _out("all canonical phases done (자가기재 기준).")
    else:
        _out(f"{incomplete} phase(s) not done — `{PROG} resume` 로 재개 가능.")
    if mismatches:
        # 자가기재 status 가 실제 산출물과 모순 — 신뢰 불가, fail-closed.
        _err(f"CROSS-CHECK FAIL: {mismatches} phase(s) 가 done 주장이나 산출물 누락 (fail-closed).")
        return EXIT_USAGE
    return EXIT_OK


# ---------------------------------------------------------------------------
# resume — status!=done phase 재실행
# ---------------------------------------------------------------------------
# 각 phase 의 재실행 동작. 라이브 빌드 대신 결정론적 검증 동작에 매핑한다
# (cli 책임 범위: 절차 재개를 관찰 가능하게 만든다). 미정의 phase 는 no-op 보고.
def _rerun_phase(phase: str) -> tuple[bool, str]:
    """phase 를 재실행하고 (성공여부, 메시지) 를 반환한다(결정론)."""
    if phase == "0-context":
        ok = PRODUCT_ROOT.joinpath("REQUIREMENTS.md").is_file()
        return ok, "REQUIREMENTS.md 존재 확인" if ok else "REQUIREMENTS.md 없음"
    if phase == "1-spec":
        ok = PRODUCT_ROOT.joinpath("INTERFACE.md").is_file()
        return ok, "INTERFACE.md 존재 확인" if ok else "INTERFACE.md 없음"
    if phase == "2-build":
        # core 렌더가 정본과 드리프트 없는지 결정론 확인.
        rendered = promptcore.render_markdown(promptcore.default_core())
        canonical = PRODUCT_ROOT / "core" / "promptcore.md"
        ok = canonical.is_file() and canonical.read_text(encoding="utf-8") == rendered
        return ok, "core 렌더 == promptcore.md" if ok else "core 렌더 드리프트"
    if phase == "3-gates":
        # source policy audit 를 결정론으로 재집행.
        res = source_policy.audit(source_policy.default_ledger())
        return res.passed, "source_policy.audit PASS" if res.passed else (
            "source_policy.audit FAIL: " + "; ".join(res.reasons)
        )
    if phase == "4-bench":
        tasks, errors = _load_fixture_tasks()
        ok = bool(tasks) and not errors
        return ok, f"fixtures {len(tasks)}개 로드" if ok else ("fixture 문제: " + "; ".join(errors))
    if phase == "5-report":
        ok = PRODUCT_ROOT.joinpath("bench", "RESULTS.md").is_file()
        return ok, "bench/RESULTS.md 존재 확인" if ok else "bench/RESULTS.md 없음"
    return False, "unknown phase (fail-closed)"


def cmd_resume(args: Args) -> int:
    """최신 manifest 에서 status!=done 인 phase 를 canonical 순서로 재실행한다."""
    manifest_path = _resolve_manifest(args.run_id)
    if manifest_path is None:
        if args.run_id:
            _err(f"ERROR: run_id '{args.run_id}' 의 RUN_MANIFEST.json 을 찾을 수 없습니다")
        else:
            _err("ERROR: runs/<id>/RUN_MANIFEST.json 이 없습니다")
        return EXIT_USAGE

    data, msg = _load_manifest(manifest_path)
    if data is None:
        _err(f"ERROR: {msg}")
        return EXIT_USAGE

    phases = data.get("phases", {})
    if not isinstance(phases, dict):
        _err("ERROR: manifest 'phases' 가 객체가 아님 (fail-closed)")
        return EXIT_USAGE

    run_id = str(data.get("run_id", manifest_path.parent.name))
    _out(f"{PROG} resume")
    _out(f"run_id   : {run_id}")
    _out(f"manifest : {manifest_path}")

    # 실행 간 학습 carry: 직전 run 의 RETRO.md '다음 액션' 을 파싱한다.
    retro_path = manifest_path.parent / "RETRO.md"
    carried = _parse_retro_next_actions(retro_path)
    if carried:
        _out(f"carried_actions ({len(carried)}) — 직전 RETRO '다음 액션' 주입:")
        for a in carried:
            _out(f"  · {a}")
    else:
        _out("carried_actions: (없음 — RETRO 부재/섹션 부재)")
    _out("")

    pending = [p for p in CANONICAL_PHASES if str(phases.get(p, "missing")) != DONE_STATUS]

    failures = 0
    if not pending:
        _out("재개할 phase 없음 — 모든 canonical phase 가 done 입니다.")
    else:
        _out("재개 대상 phase: " + ", ".join(pending))
        _out("")
        for phase in pending:
            ok, note = _rerun_phase(phase)
            mark = "done" if ok else "FAIL"
            _out(f"  [{mark}] {phase:<10} {note}")
            if not ok:
                failures += 1
        _out("")

    # 새 RUN_MANIFEST 작성(carried_actions 주입). 기본 dry-run; --apply 시 실제 쓰기.
    new_run_id = run_id + "-resume"
    new_manifest = _build_resume_manifest(data, new_run_id, carried)
    new_path = _runs_dir() / new_run_id / "RUN_MANIFEST.json"
    if args.apply:
        wrote = _write_resume_manifest(new_path, new_manifest)
        if wrote is None:
            _err("ERROR: 새 RUN_MANIFEST 쓰기 실패 (fail-closed).")
            return EXIT_ERROR
        _out(f"wrote: {wrote}  (carried_actions={len(carried)})")
    else:
        _out(f"[dry-run] 새 RUN_MANIFEST 미작성. 작성하려면 --apply: {new_path}")

    if failures == 0:
        if pending:
            _out(f"resume 완료: {len(pending)} phase 재실행 모두 통과.")
        return EXIT_OK
    _err(f"resume 미완: {failures}/{len(pending)} phase 실패 (fail-closed).")
    return EXIT_ERROR


def _build_resume_manifest(prev: dict, new_run_id: str, carried: tuple[str, ...]) -> dict:
    """직전 manifest 를 기반으로 새 resume manifest dict 를 만든다(불변 입력 비변경)."""
    prev_phases = prev.get("phases", {})
    phases = dict(prev_phases) if isinstance(prev_phases, dict) else {}
    prev_input = prev.get("input", "")
    return {
        "run_id": new_run_id,
        "mode": "resume",
        "input": prev_input,
        "resumed_from": str(prev.get("run_id", "")),
        "carried_actions": list(carried),
        "phases": phases,
        "created_at": _utc_stamp(),
    }


def _write_resume_manifest(path: Path, manifest: dict) -> Path | None:
    """새 run 디렉토리에 RUN_MANIFEST.json 을 쓴다. 실패 시 None."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    except OSError:
        return None
    return path


# ---------------------------------------------------------------------------
# main dispatch
# ---------------------------------------------------------------------------
_COMMANDS = {
    "init": cmd_init,
    "upgrade": cmd_upgrade,
    "benchmark": cmd_benchmark,
    "check": cmd_check,
    "status": cmd_status,
    "resume": cmd_resume,
}


def main(argv: list[str] | None = None) -> int:
    """FableLayer CLI 진입점.

    no-arg / --help -> usage, exit 0. 알 수 없는 명령 -> exit 2.
    """
    if argv is None:
        argv = sys.argv[1:]
    args, early_exit = _parse(argv)
    if args is None:
        if early_exit == EXIT_OK and not (argv and argv[0] in ("-V", "--version")):
            usage()
        return early_exit if early_exit is not None else EXIT_OK

    handler = _COMMANDS.get(args.command)
    if handler is None:
        _err(f"ERROR: 알 수 없는 명령 '{args.command}'")
        _err("")
        usage()
        return EXIT_USAGE

    return handler(args)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
