import wikipediaapi
from react_agent.actions.base import BaseActionExecutor


class WikiActionExecutor(BaseActionExecutor):
    def __init__(self) -> None:
        self._wiki_service = wikipediaapi.Wikipedia(
            user_agent="ReAct agent", language="en"
        )

    async def execute(self, action: str) -> str | None:
        page = self._wiki_service.page(action)
        if not page.exists():
            return None

        return page.summary
