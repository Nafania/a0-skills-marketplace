def install():
    import shutil
    from helpers.print_style import PrintStyle

    if not shutil.which("npx"):
        PrintStyle.warning(
            "Node.js/npx not found. Skills marketplace requires Node.js. "
            "Install from https://nodejs.org/"
        )

    _ensure_skills_symlink()
    _link_existing_npx_skills()


def uninstall():
    """Remove the ~/.agents/skills symlink if it points to our persistent dir."""
    import os
    from pathlib import Path
    from helpers import files
    from helpers.print_style import PrintStyle

    persistent_dir = Path(files.get_abs_path("usr", ".agents", "skills"))
    home_skills = Path(os.path.expanduser("~/.agents/skills"))

    if home_skills.is_symlink():
        try:
            if Path(os.readlink(str(home_skills))).resolve() == persistent_dir.resolve():
                home_skills.unlink()
                PrintStyle.standard(f"Removed skills symlink: {home_skills}")
        except OSError:
            pass


def _link_existing_npx_skills():
    """
    Symlink any skills already installed by npx into the plugin's
    skills/ directory so Agent Zero's discovery picks them up.
    Agent Zero scans usr/plugins/*/skills/ but npx installs to
    HOME/.agents/skills/ — this bridges the gap.
    """
    import os
    from pathlib import Path
    from helpers import files
    from helpers.print_style import PrintStyle

    plugin_skills = Path(files.get_abs_path("usr", "plugins", "skills_marketplace", "skills"))
    plugin_skills.mkdir(parents=True, exist_ok=True)

    for npx_root in _get_npx_skill_roots():
        npx_dir = Path(npx_root)
        if not npx_dir.is_dir():
            continue
        for child in npx_dir.iterdir():
            if not child.is_dir() or child.name.startswith("."):
                continue
            skill_md = child / "SKILL.md"
            if not skill_md.exists():
                continue
            target = plugin_skills / child.name
            if target.exists() or target.is_symlink():
                continue
            import shutil
            shutil.copytree(str(child), str(target))
            PrintStyle.standard(f"Copied marketplace skill: {child.name}")


def _get_npx_skill_roots():
    """Return paths where npx skills might have installed skills."""
    import os
    from pathlib import Path
    from helpers import files

    roots = []
    usr_dir = files.get_abs_path("usr")
    roots.append(os.path.join(usr_dir, ".agents", "skills"))
    home_skills = os.path.expanduser("~/.agents/skills")
    if home_skills not in roots:
        roots.append(home_skills)
    return roots


def _ensure_skills_symlink():
    """
    npx skills installs to /a0/usr/.agents/skills/ (persistent volume),
    but core Agent Zero scans ~/.agents/skills/ (which is /root/.agents/skills/).
    Create a symlink so the core discovery finds marketplace-installed skills.
    """
    import os
    import shutil
    from pathlib import Path
    from helpers import files
    from helpers.print_style import PrintStyle

    persistent_dir = Path(files.get_abs_path("usr", ".agents", "skills"))
    home_agents = Path(os.path.expanduser("~/.agents"))
    home_skills = home_agents / "skills"

    persistent_dir.mkdir(parents=True, exist_ok=True)

    # When HOME points to the persistent usr/ dir (e.g. /a0/usr),
    # both paths are identical — no symlink needed.
    try:
        if home_skills.resolve() == persistent_dir.resolve():
            return
    except OSError:
        pass

    if home_skills.is_symlink():
        if os.readlink(str(home_skills)) == str(persistent_dir):
            return
        home_skills.unlink()
    elif home_skills.is_dir():
        for item in home_skills.iterdir():
            target = persistent_dir / item.name
            if not target.exists():
                shutil.move(str(item), str(target))
            else:
                # Duplicate — already in persistent dir, safe to remove
                if item.is_dir():
                    shutil.rmtree(str(item))
                else:
                    item.unlink()
        home_skills.rmdir()

    home_agents.mkdir(parents=True, exist_ok=True)
    home_skills.symlink_to(persistent_dir)
    PrintStyle.standard(f"Skills symlink: {home_skills} -> {persistent_dir}")
