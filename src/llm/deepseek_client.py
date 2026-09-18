from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from openai import OpenAI


@dataclass(frozen=True)
class DeepSeekSettings:
    api_key: str
    base_url: str
    model: str

    @classmethod
    def from_environment(cls) -> "DeepSeekSettings":
        api_key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
        model = os.environ.get("DEEPSEEK_MODEL", "").strip()
        base_url = os.environ.get(
            "DEEPSEEK_BASE_URL", "https://api.deepseek.com"
        ).strip()

        missing = []
        if not api_key:
            missing.append("DEEPSEEK_API_KEY")
        if not model:
            missing.append("DEEPSEEK_MODEL")
        if missing:
            raise RuntimeError(
                "Missing required DeepSeek environment variable(s): "
                + ", ".join(missing)
                + ". Copy .env.example and export values in your shell; the POC "
                "does not load or create a real .env file."
            )
        return cls(api_key=api_key, base_url=base_url, model=model)


@dataclass(frozen=True)
class LLMCompletion:
    content: str
    actual_model: str | None
    input_tokens: int | None
    output_tokens: int | None
    total_tokens: int | None
    cached_tokens: int | None
    reasoning_tokens: int | None

    def usage_dict(self) -> dict[str, int | None]:
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "cached_tokens": self.cached_tokens,
            "reasoning_tokens": self.reasoning_tokens,
        }


class DeepSeekClient:
    def __init__(
        self,
        settings: DeepSeekSettings,
        temperature: float = 0,
        timeout_seconds: int = 120,
    ) -> None:
        self.settings = settings
        self.temperature = temperature
        self._client = OpenAI(
            api_key=settings.api_key,
            base_url=settings.base_url,
            timeout=timeout_seconds,
        )

    @classmethod
    def from_environment(
        cls, temperature: float = 0, timeout_seconds: int = 120
    ) -> "DeepSeekClient":
        return cls(
            DeepSeekSettings.from_environment(),
            temperature=temperature,
            timeout_seconds=timeout_seconds,
        )

    @property
    def model(self) -> str:
        return self.settings.model

    @staticmethod
    def _usage_value(value: Any, name: str) -> int | None:
        result = getattr(value, name, None) if value is not None else None
        return int(result) if result is not None else None

    @classmethod
    def _to_completion(cls, response: Any) -> LLMCompletion:
        content = response.choices[0].message.content
        if not content:
            raise RuntimeError("DeepSeek returned an empty response")
        usage = getattr(response, "usage", None)
        input_details = getattr(usage, "prompt_tokens_details", None)
        output_details = getattr(usage, "completion_tokens_details", None)
        return LLMCompletion(
            content=content,
            actual_model=getattr(response, "model", None),
            input_tokens=cls._usage_value(usage, "prompt_tokens"),
            output_tokens=cls._usage_value(usage, "completion_tokens"),
            total_tokens=cls._usage_value(usage, "total_tokens"),
            cached_tokens=cls._usage_value(input_details, "cached_tokens"),
            reasoning_tokens=cls._usage_value(output_details, "reasoning_tokens"),
        )

    def complete(
        self,
        prompt: str,
        system_prompt: str | None = None,
        max_tokens: int | None = None,
    ) -> LLMCompletion:
        request: dict[str, Any] = {
            "model": self.settings.model,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                    or (
                        "You generate and repair reproducible Python pyperf "
                        "microbenchmarks. Follow the requested output format exactly."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": self.temperature,
            "stream": False,
        }
        if max_tokens is not None:
            request["max_tokens"] = max_tokens
        for attempt in range(2):
            response = self._client.chat.completions.create(**request)
            try:
                return self._to_completion(response)
            except RuntimeError as exc:
                if "empty response" not in str(exc) or attempt == 1:
                    raise
        raise RuntimeError("DeepSeek returned an empty response")

    def connectivity_test(self) -> LLMCompletion:
        response = self._client.chat.completions.create(
            model=self.settings.model,
            messages=[
                {
                    "role": "user",
                    "content": "Reply with exactly: DEEPSEEK_CONNECTION_OK",
                }
            ],
            temperature=0,
            max_tokens=32,
            stream=False,
        )
        completion = self._to_completion(response)
        return LLMCompletion(
            content=completion.content.strip(),
            actual_model=completion.actual_model,
            input_tokens=completion.input_tokens,
            output_tokens=completion.output_tokens,
            total_tokens=completion.total_tokens,
            cached_tokens=completion.cached_tokens,
            reasoning_tokens=completion.reasoning_tokens,
        )
