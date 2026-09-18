from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.framework.patching import extract_unified_diff
from src.llm.deepseek_client import DeepSeekClient


@dataclass(frozen=True)
class AgentOutput:
    content: str
    actual_model: str | None
    usage: dict[str, int | None]
    prompt: str
    system_prompt: str


def extract_python_code(response: str) -> str:
    match = re.search(
        r"```(?:python|py)?\s*\n(.*?)```", response, flags=re.I | re.S
    )
    code = match.group(1).strip() if match else response.strip()
    if not code:
        raise ValueError("Patch Generator returned no source code")
    return code + "\n"


class FrameworkAgents:
    def __init__(self, client: DeepSeekClient, prompts_root: Path) -> None:
        self.client = client
        self.analyze_template = (prompts_root / "analyze_performance.txt").read_text(
            encoding="utf-8"
        )
        self.patch_template = (prompts_root / "generate_optimization_patch.txt").read_text(
            encoding="utf-8"
        )
        self.reflect_template = (prompts_root / "reflect_optimization.txt").read_text(
            encoding="utf-8"
        )
        self.benchmark_template = (prompts_root / "generate_framework_benchmark.txt").read_text(
            encoding="utf-8"
        )
        self.benchmark_repair_template = (
            prompts_root / "repair_framework_benchmark.txt"
        ).read_text(encoding="utf-8")

    def _complete(self, prompt: str, system_prompt: str) -> AgentOutput:
        completion = self.client.complete(prompt, system_prompt=system_prompt)
        return AgentOutput(
            content=completion.content,
            actual_model=completion.actual_model,
            usage=completion.usage_dict(),
            prompt=prompt,
            system_prompt=system_prompt,
        )

    def generate_benchmark(
        self,
        *,
        target_symbol: str,
        source_context: str,
        tests_context: str,
    ) -> tuple[AgentOutput, str]:
        prompt = self.benchmark_template.format(
            target_symbol=target_symbol,
            source_context=source_context,
            tests_context=tests_context,
        )
        output = self._complete(
            prompt,
            "You design reproducible Python pyperf workloads for a real repository. Follow the required module contract exactly.",
        )
        return output, extract_python_code(output.content)

    def repair_benchmark(
        self,
        *,
        target_symbol: str,
        source_context: str,
        tests_context: str,
        benchmark_code: str,
        failure: dict[str, Any],
    ) -> tuple[AgentOutput, str]:
        prompt = self.benchmark_repair_template.format(
            target_symbol=target_symbol,
            source_context=source_context,
            tests_context=tests_context,
            benchmark_code=benchmark_code,
            failure=failure,
        )
        output = self._complete(
            prompt,
            "You repair a Python pyperf benchmark from concrete validation evidence. Preserve the workload intent and required module contract.",
        )
        return output, extract_python_code(output.content)

    def analyze(
        self,
        *,
        target_symbol: str,
        target_file: str,
        source_context: str,
        tests_context: str,
        baseline: dict[str, Any],
        memory: list[dict[str, Any]],
    ) -> AgentOutput:
        prompt = self.analyze_template.format(
            target_symbol=target_symbol,
            target_file=target_file,
            source_context=source_context,
            tests_context=tests_context,
            baseline=baseline,
            memory=memory,
        )
        return self._complete(
            prompt,
            "You are a conservative Python performance analyst. Base every suggestion on the supplied code and measurements.",
        )

    def generate_patch(
        self,
        *,
        target_symbol: str,
        target_file: str,
        source_context: str,
        tests_context: str,
        diagnosis: str,
        memory: list[dict[str, Any]],
    ) -> tuple[AgentOutput, str]:
        prompt = self.patch_template.format(
            target_symbol=target_symbol,
            target_file=target_file,
            source_context=source_context,
            tests_context=tests_context,
            diagnosis=diagnosis,
            memory=memory,
        )
        output = self._complete(
            prompt,
            "You are a careful Python optimization engineer. Preserve behavior and modify only the allowed source file.",
        )
        return output, extract_unified_diff(output.content)

    def reflect(
        self,
        *,
        target_symbol: str,
        diagnosis: str,
        evaluation: dict[str, Any],
    ) -> AgentOutput:
        prompt = self.reflect_template.format(
            target_symbol=target_symbol,
            diagnosis=diagnosis,
            evaluation=evaluation,
        )
        return self._complete(
            prompt,
            "Summarize optimization evidence concisely. Never invent measurements.",
        )
