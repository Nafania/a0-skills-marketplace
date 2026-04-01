from helpers.api import ApiHandler, Input, Output, Request, Response
from usr.plugins.skills_marketplace.helpers.skills_cli import (
    install_skill,
    remove_skill,
)


class SkillInstall(ApiHandler):
    async def process(self, input: Input, request: Request) -> Output:
        action = input.get("action", "install")

        try:
            if action == "install":
                data = self._install(input)
            elif action == "remove":
                data = self._remove(input)
            else:
                raise Exception("Invalid action. Use 'install' or 'remove'.")

            return {
                "ok": True,
                "data": data,
            }
        except Exception as e:
            return {
                "ok": False,
                "error": str(e),
            }

    def _install(self, input: Input):
        source = str(input.get("source", "")).strip()
        if not source:
            raise Exception("'source' parameter is required (e.g. owner/repo)")

        ok, installed_path, error = install_skill(source)
        if not ok:
            raise Exception(error or f"Failed to install '{source}'")

        return {
            "source": source,
            "installed_path": installed_path,
        }

    def _remove(self, input: Input):
        skill_name = str(input.get("skill_name", "")).strip()
        if not skill_name:
            raise Exception("'skill_name' parameter is required")

        ok, message = remove_skill(skill_name)
        if not ok:
            raise Exception(message)

        return {
            "skill_name": skill_name,
            "message": message,
        }
