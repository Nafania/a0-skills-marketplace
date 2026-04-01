def install():
    import shutil
    from helpers.print_style import PrintStyle

    if not shutil.which("npx"):
        PrintStyle.warning(
            "Node.js/npx not found. Skills marketplace requires Node.js. "
            "Install from https://nodejs.org/"
        )

    _ensure_skills_symlink()


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
