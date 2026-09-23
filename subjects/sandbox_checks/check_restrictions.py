#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import socket
from pathlib import Path


def main() -> None:
    results: dict[str, object] = {
        "uid": os.getuid(),
        "non_root": os.getuid() != 0,
        "deepseek_key_visible": any(
            name.startswith("DEEPSEEK_") for name in os.environ
        ),
    }

    try:
        Path("/workspace/sandbox_write_probe.txt").write_text(
            "should not be writable", encoding="utf-8"
        )
    except OSError as exc:
        results["workspace_read_only"] = True
        results["workspace_write_error"] = type(exc).__name__
    else:
        results["workspace_read_only"] = False

    interface_names = sorted(name for _index, name in socket.if_nameindex())
    results["network_interfaces"] = interface_names
    route_path = Path("/proc/net/route")
    route_lines = route_path.read_text(encoding="utf-8").splitlines()[1:]
    has_default_route = any(
        len(columns := line.split()) >= 4
        and columns[1] == "00000000"
        and int(columns[3], 16) & 1
        for line in route_lines
    )
    results["has_default_route"] = has_default_route
    try:
        connection = socket.create_connection(("1.1.1.1", 53), timeout=1)
    except OSError as exc:
        outbound_failed = True
        results["network_error"] = type(exc).__name__
    else:
        connection.close()
        outbound_failed = False
    results["outbound_connection_failed"] = outbound_failed
    results["network_blocked"] = not has_default_route and outbound_failed

    print(json.dumps(results, sort_keys=True))
    required = (
        bool(results["non_root"]),
        not bool(results["deepseek_key_visible"]),
        bool(results.get("workspace_read_only")),
        bool(results.get("network_blocked")),
    )
    if not all(required):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
