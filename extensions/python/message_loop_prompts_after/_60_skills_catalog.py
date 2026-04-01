from helpers.extension import Extension
from plugins._skills_marketplace.helpers.skills_cli import list_installed_skills


class SkillsCatalogPrompt(Extension):

    def execute(self, **kwargs):
        config = self._get_config()
        if not config.get("marketplace_enabled", True):
            return

        skills = list_installed_skills()
        if not skills:
            return

        prompt = kwargs.get("prompt", "")
        catalog_section = self._build_catalog_section(skills)

        if catalog_section:
            kwargs["prompt"] = prompt + catalog_section

    def _get_config(self) -> dict:
        try:
            from helpers import plugins
            return plugins.get_plugin_config("_skills_marketplace", agent=self.agent) or {}
        except Exception:
            return {}

    def _build_catalog_section(self, skills) -> str:
        lines = [
            "",
            "## Marketplace Skills",
            "The following skills are installed from the skills.sh marketplace:",
            "",
        ]

        for skill in skills:
            desc = skill.description or "No description"
            lines.append(f"- **{skill.name}**: {desc}")
            if skill.trigger_patterns:
                triggers = ", ".join(skill.trigger_patterns)
                lines.append(f"  Triggers: {triggers}")

        lines.extend([
            "",
            "Use `skills_marketplace:search_remote` to find more skills, "
            "or `skills_marketplace:install` to add new ones.",
            "",
        ])

        return "\n".join(lines)
