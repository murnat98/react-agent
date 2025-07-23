import os
from llama_index.core.workflow import StopEvent, Workflow, step
from react_agent.actions.search import SerpAPISearchExecutor
from react_agent.actions.wiki import WikiActionExecutor
from react_agent.consts import DECIDE_ACTION_SYSTEM_PROMPT, THOUGHT_SYSTEM_PROMPT
from react_agent.errors import InvalidActionError
from react_agent.events import (
    DecideActionEvent,
    ExecuteActionEvent,
    GenerateThoughtEvent,
    RunAgentEvent,
)
from react_agent.llm_runner import LLMQueryRunner
from react_agent.structures import (
    Action,
    ActionType,
    HistoryItem,
    IntelligenceProvider,
    Observation,
    Thought,
)


def get_serp_api_executor() -> SerpAPISearchExecutor:
    return SerpAPISearchExecutor(os.environ["SERP_API_KEY"])


class ReActAgent(Workflow):
    _ACTION_NUMBER_TO_TYPE_MAPPING = {
        1: ActionType.search,
        2: ActionType.lookup,
        3: ActionType.answer,
    }
    _ACTION_EXECUTOR_MAPPING = {
        ActionType.search: get_serp_api_executor,
        ActionType.lookup: WikiActionExecutor,
    }

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._set_params(IntelligenceProvider.gemini_flash_20, 0)

    def _set_params(
        self,
        intelligence_provider: IntelligenceProvider = IntelligenceProvider.gemini_flash_20,
        verbosity_level: int = 0,
    ) -> None:
        self._llm_runner = LLMQueryRunner(
            intelligence_provider, api_key=os.getenv("LLM_API_KEY")
        )
        self._verbosity_level = verbosity_level

    def _format_history(self, history: list[HistoryItem]) -> str | None:
        if not history:
            return None

        return "\n".join(item.format() for item in history)

    def _print(self, text: str, verbosity_level: int) -> None:
        if verbosity_level <= self._verbosity_level:
            print(text)

    def _get_user_prompt_from_history(
        self, query: str, history: list[HistoryItem]
    ) -> str:
        history_formatted = self._format_history(history)
        if history_formatted:
            return f"{history_formatted}\nQuestion: {query}"

        return query

    @step
    async def run_agent(self, ev: RunAgentEvent) -> GenerateThoughtEvent:
        self._set_params(ev.intelligence_provider, ev.verbosity_level)

        return GenerateThoughtEvent(query=ev.query, history=[])

    @step
    async def generate_thought(self, ev: GenerateThoughtEvent) -> DecideActionEvent:
        user_prompt = self._get_user_prompt_from_history(ev.query, ev.history)

        self._print(f"Generating thought\n{THOUGHT_SYSTEM_PROMPT}\n{user_prompt}", 2)

        thought = await self._llm_runner.run_query(
            user_prompt=user_prompt, system_prompt=THOUGHT_SYSTEM_PROMPT
        )

        self._print(f"\033[32mThought:\033[0m {thought}", 1)

        return DecideActionEvent(
            query=ev.query, history=ev.history + [Thought(content=thought)]
        )

    def _is_action_output_valid(self, action_output: str | dict) -> bool:
        if isinstance(action_output, str):
            return False

        if not (
            "action_number" in action_output
            and "explanation" in action_output
            and "action_input" in action_output
        ):
            return False

        if action_output["action_number"] > max(
            self._ACTION_NUMBER_TO_TYPE_MAPPING.keys()
        ) or action_output["action_number"] < min(
            self._ACTION_NUMBER_TO_TYPE_MAPPING.keys()
        ):
            return False

        return True

    @step
    async def decide_action(
        self, ev: DecideActionEvent
    ) -> ExecuteActionEvent | StopEvent:
        user_prompt = self._get_user_prompt_from_history(ev.query, ev.history)

        self._print(f"Deciding action\n{DECIDE_ACTION_SYSTEM_PROMPT}\n{user_prompt}", 2)

        action_output = await self._llm_runner.run_query(
            user_prompt=user_prompt,
            system_prompt=DECIDE_ACTION_SYSTEM_PROMPT,
            json_mode=True,
        )
        if not self._is_action_output_valid(action_output):
            raise InvalidActionError(f"Invalid action output format {action_output=}")

        action = Action(
            action_type=self._ACTION_NUMBER_TO_TYPE_MAPPING[
                action_output["action_number"]
            ],
            action_input=action_output["action_input"],
            explanation=action_output["explanation"],
        )

        self._print(
            f"\033[34mDecided action:\033[0m {action.action_type} ({action.explanation}) - {action.action_input}",
            1,
        )

        if action.action_type == ActionType.answer:
            return StopEvent(result=action.action_input)

        return ExecuteActionEvent(
            query=ev.query, history=ev.history + [action], action=action
        )

    @step
    async def execute_action(
        self, ev: ExecuteActionEvent
    ) -> GenerateThoughtEvent | StopEvent:
        executor = self._ACTION_EXECUTOR_MAPPING[ev.action.action_type]()
        observation = await executor.execute(ev.action.action_input)

        self._print(
            f"\033[36mObservation:\033[0m {observation}",
            1,
        )

        if not observation:
            return StopEvent(result="Something went wrong, no observation received.")

        return GenerateThoughtEvent(
            query=ev.query, history=ev.history + [Observation(content=observation)]
        )
