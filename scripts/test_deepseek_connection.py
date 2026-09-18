#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.llm.deepseek_client import DeepSeekClient  # noqa: E402


def main() -> int:
    try:
        client = DeepSeekClient.from_environment(temperature=0)
        reply = client.connectivity_test()
    except Exception as exc:
        print(f"DeepSeek connectivity test failed: {type(exc).__name__}: {exc}")
        return 1

    if reply.content == "DEEPSEEK_CONNECTION_OK":
        print(
            "DeepSeek connectivity test passed "
            f"(configured_model={client.model}, actual_model={reply.actual_model})."
        )
        return 0

    print(
        "DeepSeek API responded, but the sentinel did not match. "
        f"configured_model={client.model}, actual_model={reply.actual_model}, "
        f"response={reply.content!r}"
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
