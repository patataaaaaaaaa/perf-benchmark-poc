from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from src.llm.deepseek_client import DeepSeekClient
from src.target.loader import TargetContext


@dataclass(frozen=True)
class GeneratedCandidate:
    raw_response: str
    code: str | None
    skip_reason: str | None
    actual_model: str | None = None
    usage: dict[str, int | None] | None = None

    @property
    def skipped(self) -> bool:
        return self.skip_reason is not None


def extract_candidate(
    response: str,
    actual_model: str | None = None,
    usage: dict[str, int | None] | None = None,
) -> GeneratedCandidate:
    stripped = response.strip()
    skip_match = re.match(r"^SKIP\s*:\s*(.+)$", stripped, flags=re.I | re.S)
    if skip_match:
        return GeneratedCandidate(
            raw_response=response,
            code=None,
            skip_reason=skip_match.group(1).strip(),
            actual_model=actual_model,
            usage=usage,
        )

    fence = re.search(r"```(?:python|py)?\s*\n(.*?)```", stripped, flags=re.I | re.S)
    code = fence.group(1).strip() if fence else stripped
    if not code:
        raise ValueError("The model response contained neither SKIP nor Python code")
    return GeneratedCandidate(
        raw_response=response,
        code=code + "\n",
        skip_reason=None,
        actual_model=actual_model,
        usage=usage,
    )


class BenchmarkGenerator:
    def __init__(
        self,
        client: DeepSeekClient | None,
        generate_template: Path,
        repair_template: Path,
    ) -> None:
        self.client = client
        self.generate_template = generate_template.read_text(encoding="utf-8")
        self.repair_template = repair_template.read_text(encoding="utf-8")

    @staticmethod
    def _target_fields(context: TargetContext) -> dict[str, str]:
        return {
            "target_name": context.spec.target,
            "qualified_name": context.spec.qualified_name,
            "module": context.spec.module,
            "description": context.spec.description,
            "source_code": context.source_code,
        }

    def render_generate_prompt(self, context: TargetContext) -> str:
        return self.generate_template.format(**self._target_fields(context))

    def generate(self, context: TargetContext) -> GeneratedCandidate:
        if self.client is None:
            raise RuntimeError("Cannot generate without an LLM client")
        prompt = self.render_generate_prompt(context)
        completion = self.client.complete(prompt)
        return extract_candidate(
            completion.content,
            actual_model=completion.actual_model,
            usage=completion.usage_dict(),
        )

    def repair(
        self,
        context: TargetContext,
        benchmark_code: str,
        validation_stage: str,
        command: str,
        return_code: int | None,
        stdout: str,
        stderr: str,
    ) -> GeneratedCandidate:
        if self.client is None:
            raise RuntimeError("Cannot repair without an LLM client")
        prompt = self.repair_template.format(
            **self._target_fields(context),
            benchmark_code=benchmark_code,
            validation_stage=validation_stage,
            command=command,
            return_code="not run" if return_code is None else return_code,
            stdout=stdout or "(empty)",
            stderr=stderr or "(empty)",
        )
        completion = self.client.complete(prompt)
        return extract_candidate(
            completion.content,
            actual_model=completion.actual_model,
            usage=completion.usage_dict(),
        )
