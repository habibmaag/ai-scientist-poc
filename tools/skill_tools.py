"""
skill_tools.py

Utilities for loading the scientific workflow instructions
stored in skills/*/SKILL.md.

The skills provide workflow scaffolding for the AI Scientist.

Plain-English architecture:

SKILL.md
    ↓
workflow instructions
    ↓
Claude
    ↓
tool selection
    ↓
deterministic Python tools
"""

from pathlib import Path


# ============================================================
# CONFIGURATION
# ============================================================

SKILLS_DIR = Path("skills")


# ============================================================
# LOAD ONE SKILL
# ============================================================

def load_skill(
    skill_name: str,
) -> str:
    """
    Load one SKILL.md file.

    Parameters
    ----------
    skill_name:
        Directory name under skills/.

    Returns
    -------
    str
        Contents of the SKILL.md file.

    Plain English:
        "Give Claude the workflow instructions for this
        scientific task."
    """

    skill_path = (
        SKILLS_DIR
        / skill_name
        / "SKILL.md"
    )

    if not skill_path.exists():
        raise FileNotFoundError(
            f"Skill not found: {skill_path}"
        )

    return skill_path.read_text(
        encoding="utf-8"
    )


# ============================================================
# LOAD MULTIPLE SKILLS
# ============================================================

def load_skills(
    skill_names: list[str],
) -> dict[str, str]:
    """
    Load multiple skills.

    Returns a dictionary:

        {
            "paper_extraction": "...",
            "reproduction": "...",
        }
    """

    return {
        skill_name: load_skill(skill_name)
        for skill_name in skill_names
    }


# ============================================================
# BUILD AGENT CONTEXT
# ============================================================

def build_skill_context(
    skill_names: list[str],
) -> str:
    """
    Combine selected skills into one prompt section.

    Plain English:
        "Give Claude the workflow rules it needs for this task."
    """

    skills = load_skills(
        skill_names
    )

    sections = [
        "## Scientific Workflow Skills",
        "",
        "Follow the relevant workflow instructions below.",
        "Treat these as procedural guidance, not as evidence.",
        "",
    ]

    for skill_name, content in skills.items():

        sections.append(
            f"### Skill: {skill_name}"
        )

        sections.append(
            content
        )

        sections.append("")

    return "\n".join(
        sections
    )


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    context = build_skill_context(
        [
            "paper_discovery",
            "paper_extraction",
            "dataset_analysis",
            "reproduction",
            "verification",
        ]
    )

    print(context)