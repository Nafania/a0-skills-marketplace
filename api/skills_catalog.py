from helpers.api import ApiHandler, Input, Output, Request, Response
from usr.plugins.skills_marketplace.helpers.skills_cli import (
    search_marketplace,
    list_installed_skills,
    read_lock,
)


class SkillsCatalog(ApiHandler):
    async def process(self, input: Input, request: Request) -> Output:
        action = input.get("action", "")

        try:
            if action == "search":
                data = await self._search(input)
            elif action == "list_installed":
                data = self._list_installed()
            else:
                raise Exception("Invalid action. Use 'search' or 'list_installed'.")

            return {
                "ok": True,
                "data": data,
            }
        except Exception as e:
            return {
                "ok": False,
                "error": str(e),
            }

    async def _search(self, input: Input):
        query = str(input.get("query", "")).strip()
        if not query:
            raise Exception("'query' parameter is required")

        ok, results, error = search_marketplace(query)
        if not ok:
            raise Exception(error or "Search failed")

        return {
            "query": query,
            "results": results,
            "count": len(results),
        }

    def _list_installed(self):
        skills = list_installed_skills()
        lock = read_lock()
        lock_entries = lock.get("skills", {})
        source_by_name: dict[str, str] = {}
        for entry in lock_entries.values():
            src = entry.get("source", "")
            if "@" in src:
                skill_name = src.rsplit("@", 1)[-1]
                source_by_name[skill_name] = src
        return {
            "skills": [
                {
                    "name": s.name,
                    "description": s.description,
                    "version": s.version,
                    "author": s.author,
                    "path": str(s.path),
                    "tags": s.tags,
                    "source": source_by_name.get(s.name, ""),
                }
                for s in skills
            ],
            "count": len(skills),
        }
