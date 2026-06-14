# FableLayer Python Runtime — INTERFACE (계약 SSoT)

모든 `fablelayer/*.py` 모듈은 이 시그니처를 **정확히** 구현한다. `cli.py`·`adapters.py`·`tests/`는 이 계약에만 의존한다. Python 3.10+, **표준 라이브러리만**(외부 의존 0). 모든 데이터 타입은 `@dataclass(frozen=True)`. 모든 검증 함수는 fail-closed(불확실하면 실패).

## fablelayer/promptcore.py  (FL1)
```python
@dataclass(frozen=True)
class Section: id:str; title:str; inspired_by:tuple[str,...]; rules:tuple[str,...]
@dataclass(frozen=True)
class PromptCore: version:str; sections:tuple[Section,...]
def default_core(version:str="v2") -> PromptCore   # 9 sections: identity, verification-grounding, evidence-gate, systematic-investigation, anti-early-stop, output-structure, value-for-cost, drift-prevention, safety
def render_markdown(core:PromptCore) -> str         # deterministic; each section emits [inspired-by:...] tags
def merge(base:PromptCore, overlay:PromptCore) -> PromptCore  # dedupe rules; RAISE ValueError if any rule matches COMPRESSION_RE (FL3 압축금지)
COMPRESSION_RE = r"(압축|compress|간결하게 줄|truncate output|글자\s*수\s*제한)"
```
`core/promptcore.md`는 이 모듈이 생성한다(`render_markdown(default_core())`). 드리프트 시 `--check`가 비0.

## fablelayer/evidence_gate.py  (FL2)
```python
@dataclass(frozen=True)
class Claim: text:str; evidence:tuple[str,...]
@dataclass(frozen=True)
class GateResult: passed:bool; reasons:tuple[str,...]
ACCEPTED_EVIDENCE_RE = r"(exit\s*code|exit\s*\d|test.*(pass|fail)|grep|\d+\s*(개|matches)|/[\w./-]+\.\w+|render|스크린샷)"
COMPLETION_RE = r"(done|완료|통과|fixed|배포됨|작동(한다|함)|passed)"
def check_claim(claim:Claim) -> GateResult   # fail-closed: completion word present but evidence empty OR no token matches ACCEPTED_EVIDENCE_RE -> passed=False
def scan_text(s:str) -> GateResult           # port early-stop.sh: promise-without-doing + scope-reduction regex; passed=False on violation
```
CLI `check --file <out>` → GateResult.passed면 exit 0, 아니면 2.

## fablelayer/router.py  (FL3/FL4)
```python
@dataclass(frozen=True)
class TaskSpec: kind:str; dependency_depth:int=0; files_touched:int=0; deep_reasoning:bool=False; context_pct:float=0.0; gate_failures:int=0; explicit_opus:bool=False
@dataclass(frozen=True)
class RouteDecision: model:str; fired_signals:tuple[str,...]; note:str
ESCALATION_SIGNALS  # 6 predicates: dep_depth>=3, deep_reasoning, files>=3, context_pct>=0.8, gate_failures>=2, explicit_opus
def route(task:TaskSpec) -> RouteDecision   # default "sonnet"; any signal -> "opus"; explicit_opus never downgraded; note always carries "capability not transferable"
```

## fablelayer/source_policy.py  (FL7, FL-GAP-01)
```python
CLASS = ("copy","adapt","reference-only","blocked","unverified")
@dataclass(frozen=True)
class Source: name:str; url:str; license:str; classification:str; risk:str  # risk in {low,medium,high}
def classify(name:str, license:str, is_leaked:bool) -> str   # leaked -> "reference-only"+risk high; unknown license -> "unverified"; MIT -> "adapt"
def default_ledger() -> tuple[Source,...]   # the 10 sources from ATTRIBUTION.md (fablize, value-for-fable, supergoal, context-handoff, sgup/ai, awesome, xonovex, Cheswick, CL4R1T4S, system_prompts_leaks)
def audit(ledger:tuple[Source,...]) -> GateResult  # fail if any leaked source classified copy/adapt, or any blocked present in build
```

## fablelayer/benchmark.py  (FL6)
```python
@dataclass(frozen=True)
class BenchTask: id:str; prompt:str; rubric:tuple[str,...]
@dataclass(frozen=True)
class BenchRun: task_id:str; model:str; judge:str; score:float; raw:dict
def deterministic_judge(output:str, task:BenchTask) -> float   # judge B: rubric-keyword coverage 0..100, NO live model needed (reproducible)
def run_suite(tasks:tuple[BenchTask,...], outputs:dict[str,str]) -> tuple[BenchRun,...]
def write_raw(runs:tuple[BenchRun,...], path:str) -> None      # JSON to bench/raw.json
SENTINEL_GUARD = True  # reproduce.sh checks: if RESULTS claims a score but raw.json absent/mismatch -> exit 70
```

## fablelayer/adapters.py  (FL5)
```python
def export_ollama(target:Path, base_model:str="llama3") -> Path        # Modelfile: FROM+PARAMETER+SYSTEM=render_markdown(default_core())
def export_lmstudio(target:Path) -> Path   # JSON {preset_name, system_prompt, metadata:{private_prompt_included:False}}
def export_sillytavern(target:Path) -> Path# JSON {name, description, prompt}
def export_claude_plugin(target:Path) -> list[Path]
def export_all(target:Path, base_model:str="llama3") -> list[Path]      # all of the above; reads ONE rendered core
```
모든 export는 `promptcore.render_markdown(default_core())` 단일 소스에서 파생. `private_prompt_included:False` 메타 필수.

## fablelayer/cli.py  (FL5, FL11, 회복)
```python
def main(argv:list[str]) -> int   # subcommands: init / upgrade <model> / benchmark / check / status / resume
# init: scaffold .fablelayer/ from rendered core (dry-run default; --apply to write; .bak snapshot before overwrite)
# upgrade <model>: route(TaskSpec) -> write routing decision (no static conf)
# benchmark: run_suite on bench/fixtures -> write_raw -> print summary
# check --file <f>: evidence_gate.scan over file -> exit 0/2
# status: read latest runs/<id>/RUN_MANIFEST.json -> print phase status
# resume: from latest manifest, re-run phases where status!=done
# no-arg / --help: usage, exit 0
```
`pyproject.toml`: project name `fablelayer`, entry point `fablelayer = "fablelayer.cli:main"`, py 3.10+, deps 없음.

## tests/  (stdlib unittest, 외부 의존 0)
- `tests/test_promptcore.py`: render 결정성, merge 압축규칙 거부(ValueError), --check 드리프트
- `tests/test_evidence_gate.py`: 완료어+무증거 → fail, 증거 있으면 pass, scan 음성/양성
- `tests/test_router.py`: 각 신호 발화 → opus, 무신호 → sonnet, explicit_opus 비강등
- `tests/test_source_policy.py`: leaked → reference-only/high, MIT → adapt, audit fail-closed
- `tests/test_adapters.py`: export_all 4+ paths, lmstudio JSON private_prompt_included False, 필수키 존재
- `tests/test_benchmark.py`: deterministic_judge 재현성, write_raw JSON 스키마
- `tests/run_tests.py`: 단일 진입점, 모든 test_*.py 실행, 하나라도 실패 시 exit 1
