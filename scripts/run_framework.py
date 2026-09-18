#!/usr/bin/env python3
from __future__ import annotations

import argparse
import logging
import sys
from dataclasses import replace
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.framework.agents import FrameworkAgents  # noqa: E402
from src.framework.config import FrameworkConfig  # noqa: E402
from src.framework.evaluator import Evaluator  # noqa: E402
from src.framework.pipeline import OptimizationFramework  # noqa: E402
from src.llm.deepseek_client import DeepSeekClient  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the minimal evidence-driven performance optimization loop."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=PROJECT_ROOT / "config" / "framework_demo.yaml",
        help="Framework task YAML (default: config/framework_demo.yaml).",
    )
    parser.add_argument(
        "--experiment-runs",
        type=int,
        help="Override experiment_runs from YAML (use 1 to replace one interrupted independent run).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    try:
        config = FrameworkConfig.load(args.config, PROJECT_ROOT)
        if args.experiment_runs is not None:
            if args.experiment_runs < 1:
                raise ValueError("--experiment-runs must be at least 1")
            config = replace(config, experiment_runs=args.experiment_runs)
        client = DeepSeekClient.from_environment(
            temperature=config.temperature,
            timeout_seconds=config.timeout_seconds,
        )
        if client.model != config.model:
            raise RuntimeError(
                f"Configured model is {config.model!r}, but DEEPSEEK_MODEL is "
                f"{client.model!r}. Use the configured model for reproducibility."
            )
        framework = OptimizationFramework(
            project_root=PROJECT_ROOT,
            config=config,
            agents=FrameworkAgents(client, PROJECT_ROOT / "prompts"),
            evaluator=Evaluator(
                config.timeout_seconds,
                primary_benchmark=config.primary_benchmark,
            ),
            model_name=client.model,
        )
        run_dir = framework.run()
    except Exception as exc:
        print(f"Framework failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    print(f"Artifacts: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
