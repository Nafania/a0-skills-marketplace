from helpers.tool import Tool, Response
from usr.plugins.skills_marketplace.helpers.skills_cli import (
    search_marketplace,
    install_skill,
    update_skill,
    check_updates,
    remove_skill,
    list_installed_skills,
    find_skill,
)


class SkillsMarketplace(Tool):

    async def execute(self, **kwargs):
        if self.method == "search_remote":
            return await self._search_remote(**kwargs)
        elif self.method == "install":
            return await self._install(**kwargs)
        elif self.method == "update":
            return await self._update(**kwargs)
        elif self.method == "check_updates":
            return await self._check_updates(**kwargs)
        elif self.method == "remove":
            return await self._remove(**kwargs)
        elif self.method == "list_installed":
            return await self._list_installed(**kwargs)
        return Response(
            message=f"Unknown method '{self.name}:{self.method}'. "
                    f"Available: search_remote, install, update, check_updates, remove, list_installed",
            break_loop=False,
        )

    async def _search_remote(self, query: str = "", **kwargs) -> Response:
        if not query:
            return Response(
                message="Error: 'query' parameter is required for search_remote.",
                break_loop=False,
            )

        await self.set_progress(f"Searching marketplace for '{query}'...")

        ok, results, error = search_marketplace(query)
        if not ok:
            return Response(
                message=f"Marketplace search failed: {error}",
                break_loop=False,
            )

        if not results:
            return Response(
                message=f"No skills found matching '{query}'.",
                break_loop=False,
            )

        lines = [f"Found {len(results)} skill(s) matching '{query}':", ""]
        for r in results:
            lines.append(f"  - **{r.get('name', '?')}**")
            if r.get("description"):
                lines.append(f"    {r['description']}")
            if r.get("source"):
                lines.append(f"    Source: {r['source']}")
            if r.get("author"):
                lines.append(f"    Author: {r['author']}")
            lines.append("")

        lines.append("Use `skills_marketplace:install` with the source to install a skill.")

        return Response(message="\n".join(lines), break_loop=False)

    async def _install(self, source: str = "", **kwargs) -> Response:
        if not source:
            return Response(
                message="Error: 'source' parameter is required (e.g. 'owner/repo').",
                break_loop=False,
            )

        await self.set_progress(f"Installing skill from '{source}'...")

        ok, installed_path, error = install_skill(source)
        if not ok:
            return Response(
                message=f"Installation failed: {error}",
                break_loop=False,
            )

        return Response(
            message=f"Successfully installed skill from '{source}'.\n"
                    f"Installed to: {installed_path}\n\n"
                    f"The skill is now available for use.",
            break_loop=False,
        )

    async def _update(self, source: str = "", **kwargs) -> Response:
        if not source:
            return Response(
                message="Error: 'source' parameter is required (e.g. 'owner/repo@skill').",
                break_loop=False,
            )

        await self.set_progress(f"Updating skill from '{source}'...")

        ok, installed_path, error = update_skill(source)
        if not ok:
            return Response(
                message=f"Update failed: {error}",
                break_loop=False,
            )

        return Response(
            message=f"Successfully updated skill from '{source}'.\n"
                    f"Path: {installed_path}",
            break_loop=False,
        )

    async def _check_updates(self, **kwargs) -> Response:
        await self.set_progress("Checking for skill updates...")

        ok, updates, error = check_updates()
        if not ok:
            return Response(
                message=f"Failed to check for updates: {error}",
                break_loop=False,
            )

        if not updates:
            return Response(
                message="All installed skills are up to date.",
                break_loop=False,
            )

        lines = [f"{len(updates)} update(s) available:", ""]
        for u in updates:
            lines.append(f"  - **{u.get('name', '?')}** (source: {u.get('source', '?')})")
        lines.append("")
        lines.append("Use `skills_marketplace:update` with the source to update a skill.")

        return Response(message="\n".join(lines), break_loop=False)

    async def _remove(self, skill_name: str = "", **kwargs) -> Response:
        if not skill_name:
            return Response(
                message="Error: 'skill_name' parameter is required.",
                break_loop=False,
            )

        await self.set_progress(f"Removing skill '{skill_name}'...")

        ok, message = remove_skill(skill_name)
        return Response(message=message, break_loop=False)

    async def _list_installed(self, **kwargs) -> Response:
        skills = list_installed_skills()

        if not skills:
            return Response(
                message="No marketplace skills are currently installed.",
                break_loop=False,
            )

        lines = [f"{len(skills)} marketplace skill(s) installed:", ""]
        for skill in skills:
            tags = ", ".join(skill.tags[:3]) if skill.tags else ""
            lines.append(f"  - **{skill.name}** v{skill.version}")
            if skill.description:
                lines.append(f"    {skill.description}")
            if tags:
                lines.append(f"    Tags: {tags}")
            lines.append(f"    Path: {skill.path}")
            lines.append("")

        return Response(message="\n".join(lines), break_loop=False)
