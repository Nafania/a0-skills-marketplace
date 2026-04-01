"""
Skills CLI wrapper for the skills.sh marketplace.

Wraps the `npx skills` CLI to search, install, and manage marketplace skills.
Skills are installed into this plugin's own `skills/` subdirectory, which
Agent Zero auto-discovers via the `usr/plugins/*/skills/` pattern.
"""

import json
import os
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import yaml  # type: ignore
except Exception:
    yaml = None  # type: ignore


def _plugin_root() -> Path:
    return Path(__file__).resolve().parent.parent


def get_skills_dir() -> Path:
    return _plugin_root() / "skills"


def get_lock_file() -> Path:
    return _plugin_root() / "skills-lock.json"


# ---------------------------------------------------------------------------
# Lock file management
# ---------------------------------------------------------------------------

def read_lock() -> Dict[str, Any]:
    lock_path = get_lock_file()
    if not lock_path.exists():
        return {"skills": {}}
    try:
        return json.loads(lock_path.read_text(encoding="utf-8"))
    except Exception:
        return {"skills": {}}


def write_lock(data: Dict[str, Any]) -> None:
    lock_path = get_lock_file()
    lock_path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def add_lock_entry(name: str, source: str, version: str = "") -> None:
    lock = read_lock()
    lock.setdefault("skills", {})[name] = {
        "source": source,
        "version": version,
    }
    write_lock(lock)


def remove_lock_entry(name: str) -> None:
    lock = read_lock()
    lock.get("skills", {}).pop(name, None)
    write_lock(lock)


# ---------------------------------------------------------------------------
# npx skills CLI wrapper
# ---------------------------------------------------------------------------

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def _strip_ansi(text: str) -> str:
    return _ANSI_RE.sub("", text)


def _run_npx(*args: str, timeout: int = 60) -> Tuple[bool, str, str]:
    """
    Run `npx skills <args>` and return (success, stdout, stderr).
    """
    npx = shutil.which("npx")
    if not npx:
        return False, "", "npx not found. Install Node.js from https://nodejs.org/"

    cmd = [npx, "skills", *args]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            env={**os.environ, "NO_COLOR": "1", "FORCE_COLOR": "0", "TERM": "dumb"},
        )
        stdout = _strip_ansi(result.stdout.strip())
        stderr = _strip_ansi(result.stderr.strip())
        return result.returncode == 0, stdout, stderr
    except subprocess.TimeoutExpired:
        return False, "", f"Command timed out after {timeout}s"
    except FileNotFoundError:
        return False, "", "npx not found. Install Node.js from https://nodejs.org/"
    except Exception as e:
        return False, "", str(e)


def search_marketplace(query: str) -> Tuple[bool, List[Dict[str, str]], str]:
    """
    Search the skills.sh marketplace.
    Returns (success, results_list, error_message).
    Each result: {"name": ..., "description": ..., "source": ...}
    """
    if not query or not query.strip():
        return False, [], "Search query is required"

    ok, stdout, stderr = _run_npx("search", query, "--json")

    if ok and stdout:
        try:
            data = json.loads(stdout)
            results = []
            items = data if isinstance(data, list) else data.get("results", data.get("skills", []))
            for item in items:
                if isinstance(item, dict):
                    results.append({
                        "name": item.get("name", ""),
                        "description": item.get("description", ""),
                        "source": item.get("source", item.get("repo", item.get("url", ""))),
                        "author": item.get("author", ""),
                        "version": item.get("version", ""),
                    })
            return True, results, ""
        except json.JSONDecodeError:
            pass

    if ok and stdout:
        results = _parse_text_results(stdout)
        return True, results, ""

    return False, [], stderr or "Search returned no results"


def _parse_text_results(text: str) -> List[Dict[str, str]]:
    """Parse the `npx skills search` output format.

    Expected format (after ANSI stripping):
        firecrawl/cli@firecrawl 21.5K installs
        └ https://skills.sh/firecrawl/cli/firecrawl
    """
    results = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        i += 1

        if not line or line.startswith("╔") or line.startswith("╚") or line.startswith("█"):
            continue
        if line.startswith("Install with"):
            continue

        m = re.match(r"^([a-zA-Z0-9_./-]+@[a-zA-Z0-9_.-]+)\s*(.*?)$", line)
        if not m:
            continue

        source = m.group(1)
        rest = m.group(2).strip()
        installs = ""
        installs_m = re.search(r"([\d.]+[KMB]?)\s+installs?", rest, re.IGNORECASE)
        if installs_m:
            installs = installs_m.group(1)

        name = source.split("@")[-1] if "@" in source else source.split("/")[-1]
        url = ""

        if i < len(lines):
            next_line = lines[i].strip()
            if next_line.startswith("└"):
                url = next_line.lstrip("└").strip()
                i += 1

        results.append({
            "name": name,
            "source": source,
            "description": f"{installs} installs" if installs else "",
            "author": source.split("/")[0] if "/" in source else "",
            "version": "",
        })

    return results


def install_skill(source: str) -> Tuple[bool, str, str]:
    """
    Install a skill from source (e.g. owner/repo@skill).
    Uses `npx skills add <source> -y` for non-interactive install.
    Returns (success, installed_path, error_message).
    """
    if not source or not source.strip():
        return False, "", "Source is required (e.g. owner/repo@skill)"

    skills_dir = get_skills_dir()
    skills_dir.mkdir(parents=True, exist_ok=True)

    ok, stdout, stderr = _run_npx(
        "add", source, "-y",
        timeout=120,
    )

    if not ok:
        return False, "", stderr or f"Failed to install '{source}'"

    installed_name = _extract_installed_name(stdout, source)
    installed_path = str(skills_dir / installed_name) if installed_name else str(skills_dir)

    if installed_name:
        version = _detect_installed_version(skills_dir / installed_name)
        add_lock_entry(installed_name, source, version)

    return True, installed_path, ""


def _extract_installed_name(stdout: str, source: str) -> str:
    """Try to extract the installed skill name from npx output."""
    for line in stdout.splitlines():
        m = re.search(r"installed\s+['\"]?([a-z0-9_-]+)['\"]?", line, re.IGNORECASE)
        if m:
            return m.group(1)

    if "/" in source:
        return source.split("/")[-1].strip()
    return source.strip()


def _detect_installed_version(skill_dir: Path) -> str:
    """Read version from an installed skill's SKILL.md frontmatter."""
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return ""
    try:
        text = skill_md.read_text(encoding="utf-8")
        fm, _, _ = _split_frontmatter(text)
        return str(fm.get("version", ""))
    except Exception:
        return ""


# ---------------------------------------------------------------------------
# Local skill management
# ---------------------------------------------------------------------------

@dataclass
class Skill:
    """Represents a skill loaded from SKILL.md"""
    name: str
    description: str
    path: Path
    version: str = "1.0.0"
    author: str = ""
    tags: List[str] = field(default_factory=list)
    trigger_patterns: List[str] = field(default_factory=list)
    content: str = ""


def _split_frontmatter(text: str) -> Tuple[Dict[str, Any], str, List[str]]:
    """Split a SKILL.md into (frontmatter_dict, body_text, errors)."""
    errors: List[str] = []
    lines = text.splitlines()

    start_idx = None
    for i, line in enumerate(lines):
        if line.strip() == "---":
            start_idx = i
            break
        if line.strip():
            errors.append("Frontmatter must start at the top of the file")
            return {}, text.strip(), errors

    if start_idx is None:
        errors.append("Missing YAML frontmatter")
        return {}, text.strip(), errors

    end_idx = None
    for j in range(start_idx + 1, len(lines)):
        if lines[j].strip() == "---":
            end_idx = j
            break

    if end_idx is None:
        errors.append("Unterminated YAML frontmatter")
        return {}, text.strip(), errors

    fm_text = "\n".join(lines[start_idx + 1 : end_idx]).strip()
    body = "\n".join(lines[end_idx + 1 :]).strip()

    fm: Dict[str, Any] = {}
    if yaml is not None:
        try:
            parsed = yaml.safe_load(fm_text)
            if isinstance(parsed, dict):
                fm = parsed
        except Exception:
            pass
    if not fm:
        fm = _parse_frontmatter_fallback(fm_text)

    return fm, body, errors


def _parse_frontmatter_fallback(frontmatter_text: str) -> Dict[str, Any]:
    """Minimal YAML subset parser: key: value, lists with '- item'."""
    data: Dict[str, Any] = {}
    current_key: Optional[str] = None
    for raw in frontmatter_text.splitlines():
        line = raw.rstrip()
        if not line.strip() or line.strip().startswith("#"):
            continue

        m = re.match(r"^([A-Za-z0-9_.-]+)\s*:\s*(.*)$", line)
        if m:
            key = m.group(1)
            val = m.group(2).strip()
            current_key = key
            if val == "":
                data[key] = []
            else:
                if (val.startswith('"') and val.endswith('"')) or (
                    val.startswith("'") and val.endswith("'")
                ):
                    val = val[1:-1]
                data[key] = val
            continue

        m_list = re.match(r"^\s*-\s*(.*)$", line)
        if m_list and current_key:
            item = m_list.group(1).strip()
            if (item.startswith('"') and item.endswith('"')) or (
                item.startswith("'") and item.endswith("'")
            ):
                item = item[1:-1]
            if not isinstance(data.get(current_key), list):
                data[current_key] = []
            data[current_key].append(item)
            continue
    return data


def _coerce_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    if isinstance(value, str):
        if "," in value:
            parts = [p.strip() for p in value.split(",")]
        else:
            parts = [p.strip() for p in re.split(r"\s+", value)]
        return [p for p in parts if p]
    return [str(value).strip()] if str(value).strip() else []


def parse_skill_file(skill_path: Path) -> Optional[Skill]:
    """Parse a SKILL.md file and return a Skill object."""
    try:
        content = skill_path.read_text(encoding="utf-8")
        fm, body, errors = _split_frontmatter(content)
        if errors:
            return None

        return Skill(
            name=fm.get("name", skill_path.parent.name),
            description=str(fm.get("description", "")),
            path=skill_path.parent,
            version=str(fm.get("version", "1.0.0")),
            author=str(fm.get("author", "")),
            tags=_coerce_list(fm.get("tags")),
            trigger_patterns=_coerce_list(fm.get("trigger_patterns") or fm.get("triggers")),
            content=body,
        )
    except Exception:
        return None


_GLOBAL_SKILLS_DIR = Path("/.agents/skills")


def _scan_skills_dir(base: Path, skills: List["Skill"]) -> None:
    if not base.exists():
        return
    for entry in sorted(base.iterdir()):
        if not entry.is_dir() or entry.name.startswith("."):
            continue
        skill_file = entry / "SKILL.md"
        if skill_file.exists():
            skill = parse_skill_file(skill_file)
            if skill:
                skills.append(skill)


def list_installed_skills() -> List[Skill]:
    """List skills from both the plugin's skills/ dir and the global /.agents/skills/ dir."""
    skills: List[Skill] = []
    seen_names: set = set()

    for base in [get_skills_dir(), _GLOBAL_SKILLS_DIR]:
        if not base.exists():
            continue
        for entry in sorted(base.iterdir()):
            if not entry.is_dir() or entry.name.startswith("."):
                continue
            skill_file = entry / "SKILL.md"
            if skill_file.exists():
                skill = parse_skill_file(skill_file)
                if skill and skill.name not in seen_names:
                    skills.append(skill)
                    seen_names.add(skill.name)

    return skills


def find_skill(name: str) -> Optional[Skill]:
    """Find a locally installed skill by name."""
    for skill in list_installed_skills():
        if skill.name == name or skill.path.name == name:
            return skill
    return None


def remove_skill(name: str) -> Tuple[bool, str]:
    """
    Remove a locally installed skill by name.
    Returns (success, message).
    """
    skill = find_skill(name)
    if not skill:
        return False, f"Skill '{name}' not found"

    try:
        shutil.rmtree(skill.path)
        remove_lock_entry(skill.name)
        return True, f"Removed skill '{name}' from {skill.path}"
    except Exception as e:
        return False, f"Failed to remove '{name}': {e}"


def validate_skill(skill: Skill) -> List[str]:
    """Validate a skill and return list of issues."""
    issues: List[str] = []

    if not skill.name:
        issues.append("Missing required field: name")
    else:
        if not (1 <= len(skill.name) <= 64):
            issues.append("Name must be 1-64 characters")
        if not re.match(r"^[a-z0-9-]+$", skill.name):
            issues.append(f"Invalid name format: '{skill.name}' (use lowercase letters, numbers, and hyphens)")
        if skill.name.startswith("-") or skill.name.endswith("-"):
            issues.append("Name must not start or end with a hyphen")
        if "--" in skill.name:
            issues.append("Name must not contain consecutive hyphens")

    if not skill.description:
        issues.append("Missing required field: description")
    elif len(skill.description) < 20:
        issues.append("Description is too short (minimum 20 characters)")

    if skill.content and len(skill.content) < 100:
        issues.append("Skill content is too short (minimum 100 characters)")

    return issues
