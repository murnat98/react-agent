from abc import ABC, abstractclassmethod


class BaseActionExecutor(ABC):
    @abstractclassmethod
    async def execute(self, action: str) -> str | None:
        pass
