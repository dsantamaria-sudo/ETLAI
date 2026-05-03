def load_skill(path: str) -> str:
    from pathlib import Path
    p = Path(path)
    if p.is_dir():
        p = p / "SKILL.md"
    with open(p, "r", encoding="utf-8") as f:
        return f.read()


def extract_section(skill_content: str, section_title: str) -> str:
    lines = skill_content.splitlines()
    collecting = False
    result = []
    for line in lines:
        if line.strip() == f"## {section_title}":
            collecting = True
            continue
        if collecting:
            if line.startswith("## "):
                break
            result.append(line)
    return "\n".join(result).strip()


def replace_section(skill_content: str, section_title: str, new_content: str) -> str:
    header = f"## {section_title}"
    lines = skill_content.splitlines()

    header_idx = next((i for i, l in enumerate(lines) if l.strip() == header), None)
    if header_idx is None:
        raise ValueError(f"Section '## {section_title}' not found in skill content")

    next_section_idx = next(
        (i for i in range(header_idx + 1, len(lines)) if lines[i].startswith("## ")),
        len(lines),
    )

    result = (
        lines[: header_idx + 1]
        + ["", new_content.rstrip(), ""]
        + lines[next_section_idx:]
    )
    return "\n".join(result)
