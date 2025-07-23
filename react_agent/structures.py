from dataclasses import dataclass
from enum import Enum, StrEnum, auto


class IntelligenceProvider(StrEnum):
    gpt4o = "gpt-4o"
    gemini_flash_20 = "models/gemini-pro"


class HistoryType(Enum):
    thought = auto()
    action = auto()
    observation = auto()
    answer = auto()


class ActionType(Enum):
    search = auto()
    lookup = auto()
    answer = auto()


@dataclass(frozen=True)
class HistoryItem:
    def format(self) -> str:
        raise NotImplementedError


@dataclass(frozen=True)
class Action(HistoryItem):
    action_type: ActionType
    action_input: str
    explanation: str

    def format(self) -> str:
        return f"Action: {self.action_type.value}[{self.action_input}]"


@dataclass(frozen=True)
class Thought(HistoryItem):
    content: str

    def format(self) -> str:
        return f"Thought: {self.content}"


@dataclass(frozen=True)
class Observation(HistoryItem):
    content: str

    def format(self) -> str:
        return f"Observation: {self.content}"


@dataclass(frozen=True)
class Answer(HistoryItem):
    content: str

    def format(self) -> str:
        return f"Answer: {self.content}"
