from pathlib import Path

CONDITIONS = ("direct", "reflection", "skill-prompt")

REFLECTION = """Before answering, privately draft a response, critique its assumptions and evidence, and revise it. Return only the requested final output."""


def skill_reference(root: Path) -> str:
    paths = [root / "skills/research-mode/SKILL.md"]
    paths.extend(path for path in sorted((root / "skills").glob("*/SKILL.md")) if path.parent.name != "research-mode")
    sections = []
    for path in paths:
        sections.append(f"<skill name=\"{path.parent.name}\">\n{path.read_text().strip()}\n</skill>")
    return "\n\n".join(sections)


def system_prompt(root: Path, condition: str) -> str:
    common = (root / "CLAUDE.md").read_text().strip()
    if condition == "direct":
        return common
    if condition == "reflection":
        return f"{common}\n\n{REFLECTION}"
    if condition == "skill-prompt":
        return f"""{common}

The following skills are reference instructions for this task. Use the research-mode map to select useful operations, then apply their instructions privately. Adapt their use to the requested output. There are no external tools or skill invocations in this conversation. Return only the requested final output.

{skill_reference(root)}"""
    raise ValueError(f"Unknown condition: {condition}")
