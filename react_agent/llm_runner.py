import json
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
from react_agent.errors import LLMQueryError

from react_agent.structures import IntelligenceProvider
from llama_index.llms.openai import OpenAI
from llama_index.llms.gemini import Gemini
from llama_index.core.llms import LLM
from llama_index.core.base.llms.types import (
    ChatMessage,
    MessageRole,
)


class LLMQueryRunner:
    def __init__(self, provider: IntelligenceProvider, api_key: str | None = None):
        self._api_key = api_key
        self._provider = provider
        self._llm_factory_map: dict[IntelligenceProvider, callable] = {
            IntelligenceProvider.gpt4o: self._create_openai_llm,
            IntelligenceProvider.gemini_flash_20: self._create_gemini_llm,
        }

    def _initialize_llm(
        self,
        temperature: float,
        json_mode: bool,
    ) -> LLM:
        factory = self._llm_factory_map[self._provider]
        return factory(self._provider.value, temperature, json_mode)

    def _create_openai_llm(
        self, model: str, temperature: float, json_mode: bool
    ) -> OpenAI:
        return OpenAI(
            model=model,
            temperature=temperature,
            is_chat_model=True,
            additional_kwargs={"response_format": {"type": "json_object"}}
            if json_mode
            else {},
            api_key=self._api_key,
        )

    def _create_gemini_llm(self, model: str, temperature: float, _: bool) -> Gemini:
        return Gemini(
            model=model,
            temperature=temperature,
        )

    def _is_valid_response(self, response: str, json_mode: bool) -> bool:
        if json_mode:
            try:
                json.loads(response)
                return True
            except json.JSONDecodeError:
                return False
        return bool(response and response.strip())

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(LLMQueryError),
        reraise=True,
    )
    async def run_query(
        self,
        user_prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        json_mode: bool = False,
    ) -> str | dict:
        llm = self._initialize_llm(
            temperature=temperature,
            json_mode=json_mode,
        )

        if llm.metadata.is_chat_model:
            messages = []
            if system_prompt:
                messages.append(
                    ChatMessage(role=MessageRole.SYSTEM, content=system_prompt)
                )
            messages.append(ChatMessage(role=MessageRole.USER, content=user_prompt))
            response = await llm.achat(messages)
            output = response.message.content
        else:
            prompt = (
                f"{system_prompt}\n\n{user_prompt}" if system_prompt else user_prompt
            )
            response = await llm.acomplete(prompt)
            output = response.text

        if not self._is_valid_response(output, json_mode):
            raise LLMQueryError("Invalid or empty LLM response.")

        return json.loads(output) if json_mode else output
