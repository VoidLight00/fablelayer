from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ProcedureModule:
    name: str
    purpose: str
    checklist: tuple[str, ...]


@dataclass(frozen=True)
class ProcedureProfile:
    name: str
    modules: tuple[ProcedureModule, ...] = field(default_factory=tuple)

    def render_markdown(self) -> str:
        sections = [f"# {self.name}", ""]
        for module in self.modules:
            sections.append(f"## {module.name}")
            sections.append("")
            sections.append(module.purpose)
            sections.append("")
            sections.extend(f"- {item}" for item in module.checklist)
            sections.append("")
        return "\n".join(sections).strip() + "\n"


def default_profile() -> ProcedureProfile:
    return ProcedureProfile(
        name="FableLayer Public Procedure Profile",
        modules=(
            ProcedureModule(
                name="verification grounding",
                purpose="Do not claim completion without measurable evidence.",
                checklist=(
                    "Attach command output, file path, or source URL to every completion claim.",
                    "Mark untested behavior as unverified.",
                    "Prefer fail-closed gates over narrative confidence.",
                ),
            ),
            ProcedureModule(
                name="investigation protocol",
                purpose="Separate scope, evidence, and decision before implementation.",
                checklist=(
                    "Map existing files before editing.",
                    "State the chosen path and the reason for rejecting risky alternatives.",
                    "Keep source provenance visible.",
                ),
            ),
            ProcedureModule(
                name="multi-pass review",
                purpose="Split creation and verification into separate passes.",
                checklist=(
                    "Run a structure pass.",
                    "Run a safety pass.",
                    "Run a completeness pass against requirements.",
                ),
            ),
            ProcedureModule(
                name="drift prevention",
                purpose="Keep work tied to the original goal and constraints.",
                checklist=(
                    "Record the run manifest before long work.",
                    "Compare artifacts against acceptance criteria before reporting.",
                    "Write recurring failures into the failure log.",
                ),
            ),
        ),
    )
