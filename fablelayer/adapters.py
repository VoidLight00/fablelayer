"""FableLayer Layer 5 — Adapters (FL5).

배포 형태별 export 생성기. 모든 export 는 단일 소스
`promptcore.render_markdown(default_core())` 에서 파생한다 (드리프트 차단).

계약(INTERFACE.md):
- export_ollama(target, base_model="llama3") -> Path        # Modelfile
- export_lmstudio(target) -> Path                           # JSON, metadata.private_prompt_included=False
- export_sillytavern(target) -> Path                        # JSON {name, description, prompt}
- export_claude_plugin(target) -> list[Path]
- export_all(target, base_model="llama3") -> list[Path]     # 위 전부, ONE rendered core
"""

from __future__ import annotations

import json
from pathlib import Path

from .promptcore import default_core, render_markdown

_PRESET_NAME = "FableLayer PromptCore"
_DESCRIPTION = (
    "FableLayer PromptCore — a discipline layer (verification grounding, "
    "completion evidence gate, systematic investigation, early-stop prevention, "
    "value output structure). Procedure transfers; capability does not."
)


def _rendered_core() -> str:
    """단일 정본 소스. 모든 export 가 이 한 결과에서 파생한다."""
    return render_markdown(default_core())


def _ensure_dir(target: Path) -> Path:
    """target 디렉토리를 보장하고 Path 로 정규화해 반환한다 (fail-closed)."""
    path = Path(target)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _write_text(path: Path, content: str) -> Path:
    path.write_text(content, encoding="utf-8")
    return path


def _write_json(path: Path, payload: dict) -> Path:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return path


def export_ollama(target: Path, base_model: str = "llama3", *, core_md: str | None = None) -> Path:
    """Ollama Modelfile 생성: FROM + PARAMETER + SYSTEM=rendered core."""
    if not base_model:
        raise ValueError("base_model 비어있음 (fail-closed)")
    out_dir = _ensure_dir(target)
    system = _rendered_core() if core_md is None else core_md
    # Modelfile SYSTEM 은 멀티라인을 """..."" 로 감싼다.
    lines = [
        "# FableLayer PromptCore — Ollama Modelfile",
        "# 단일 소스: promptcore.render_markdown(default_core())",
        f"FROM {base_model}",
        "",
        "PARAMETER temperature 0.4",
        "PARAMETER num_ctx 8192",
        "",
        'SYSTEM """',
        system.rstrip("\n"),
        '"""',
        "",
    ]
    return _write_text(out_dir / "Modelfile", "\n".join(lines))


def export_lmstudio(target: Path, *, core_md: str | None = None) -> Path:
    """LM Studio preset JSON. metadata.private_prompt_included 은 항상 False."""
    out_dir = _ensure_dir(target)
    system = _rendered_core() if core_md is None else core_md
    payload = {
        "preset_name": _PRESET_NAME,
        "system_prompt": system,
        "metadata": {
            "private_prompt_included": False,
            "source": "promptcore.render_markdown(default_core())",
            "note": "leaked prompt 전문 미포함. inspired-by 패턴만 반영.",
        },
    }
    return _write_json(out_dir / "lmstudio.preset.json", payload)


def export_sillytavern(target: Path, *, core_md: str | None = None) -> Path:
    """SillyTavern preset JSON {name, description, prompt}."""
    out_dir = _ensure_dir(target)
    system = _rendered_core() if core_md is None else core_md
    payload = {
        "name": _PRESET_NAME,
        "description": _DESCRIPTION,
        "prompt": system,
    }
    return _write_json(out_dir / "sillytavern.preset.json", payload)


def export_claude_plugin(target: Path, *, core_md: str | None = None) -> list[Path]:
    """Claude Code plugin 형태 산출: plugin.json + system prompt 마크다운."""
    out_dir = _ensure_dir(target)
    system = _rendered_core() if core_md is None else core_md
    prompt_path = _write_text(out_dir / "promptcore.md", system)
    plugin_payload = {
        "name": "fablelayer-promptcore",
        "version": "0.1.0",
        "description": _DESCRIPTION,
        "license": "AGPL-3.0",
        "system_prompt": "./promptcore.md",
        "metadata": {
            "private_prompt_included": False,
            "source": "promptcore.render_markdown(default_core())",
        },
    }
    plugin_path = _write_json(out_dir / "plugin.json", plugin_payload)
    return [plugin_path, prompt_path]


def export_all(target: Path, base_model: str = "llama3") -> list[Path]:
    """모든 형태를 한 번에 export 한다. rendered core 를 한 번만 읽어 전체에 공유."""
    out_dir = _ensure_dir(target)
    core_md = _rendered_core()  # ONE rendered core, 전 export 공유

    paths: list[Path] = []
    paths.append(export_ollama(out_dir / "ollama", base_model=base_model, core_md=core_md))
    paths.append(export_lmstudio(out_dir / "lmstudio", core_md=core_md))
    paths.append(export_sillytavern(out_dir / "sillytavern", core_md=core_md))
    paths.extend(export_claude_plugin(out_dir / "claude-plugin", core_md=core_md))
    return paths
