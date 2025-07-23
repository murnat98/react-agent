import aiohttp
from react_agent.actions.base import BaseActionExecutor


class SerpAPISearchExecutor(BaseActionExecutor):
    def __init__(
        self, api_key: str, base_url: str = "https://serpapi.com/search"
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url

    async def execute(self, action: str) -> str | None:
        params = {
            "engine": "google",
            "q": action,
            "api_key": self._api_key,
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(self._base_url, params=params) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()

                organic_results = data.get("organic_results", [])
                if not organic_results:
                    return None

                first_result = organic_results[0]
                return first_result.get("snippet")
