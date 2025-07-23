from llama_index.core.workflow import Event, StartEvent

from react_agent.structures import Action, HistoryItem, IntelligenceProvider


class RunAgentEvent(StartEvent):
    query: str
    intelligence_provider: IntelligenceProvider = IntelligenceProvider.gpt4o
    verbosity_level: int = 0


class GenerateThoughtEvent(Event):
    query: str
    history: list[HistoryItem]


class DecideActionEvent(Event):
    query: str
    history: list[HistoryItem]


class ExecuteActionEvent(Event):
    query: str
    history: list[HistoryItem]
    action: Action
