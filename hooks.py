def install():
    import shutil
    from helpers.print_style import PrintStyle
    if not shutil.which("npx"):
        PrintStyle.warning(
            "Node.js/npx not found. Skills marketplace requires Node.js. "
            "Install from https://nodejs.org/"
        )
