#!/usr/bin/env python3
"""Read-only, compact evidence for the temporary first-three-successes monitor."""
import argparse
import json
from pathlib import Path


def inspect_batch(batch):
    status = (batch / 'status.txt').read_text().strip() if (batch / 'status.txt').exists() else 'startup'
    summary = json.loads((batch / 'summary.json').read_text()) if (batch / 'summary.json').exists() else []
    budget_path = batch / 'budget.json'
    budget = json.loads(budget_path.read_text()) if budget_path.exists() else {}
    passed, incomplete, active = [], [], []
    for output in sorted(batch.glob('tasks/*/*/prompt4')):
        task = output.parent.name
        repo = output.parent.parent.name
        result_path = output / 'result.json'
        if not result_path.exists():
            events = output / 'codex_events.jsonl'
            types = []
            if events.exists():
                # Inspect only a bounded tail; traces can grow very large.
                with events.open('rb') as stream:
                    stream.seek(max(0, events.stat().st_size - 65536))
                    recent = stream.read().decode(errors='replace')
                for line in recent.splitlines():
                    try:
                        event = json.loads(line)
                        types.append((event.get('type'), event.get('item', {}).get('type')))
                    except ValueError:
                        pass
            active.append(dict(repository=repo, task=task, recent_event_count=len(types), recent_event_types=types[-4:]))
            continue
        result = json.loads(result_path.read_text())
        usage = result.get('usage') or {}
        real_usage = any(isinstance(usage.get(k), int) and usage[k] > 0
                         for k in ('total_tokens', 'input_tokens', 'output_tokens'))
        checks = [result.get('outcome') == 'succeeded', real_usage,
                  (result.get('verification') or {}).get('returncode') == 0,
                  (result.get('benchmark') or {}).get('returncode') == 0,
                  bool((output / 'agent.patch').exists() and (output / 'agent.patch').read_text().strip()),
                  not result.get('forbidden_changes')]
        rows = []
        try:
            rows = json.loads((output / 'jmh.json').read_text())
            checks.append(isinstance(rows, list) and bool(rows))
        except (OSError, ValueError):
            checks.append(False)
        record = dict(repository=repo, task=task, outcome=result.get('outcome'),
                      elapsed_seconds=result.get('elapsed_seconds'), usage=usage,
                      jmh_rows=len(rows) if isinstance(rows, list) else 0)
        (passed if all(checks) else incomplete).append(record)
    pid_path = batch / 'pid.txt'
    pid = int(pid_path.read_text().strip()) if pid_path.exists() else None
    alive = bool(pid and (Path('/proc') / str(pid)).exists())
    return dict(batch=str(batch), status=status, queue_pid=pid, queue_alive=alive,
                processed_tasks=len(summary), agent_runs_started=max(budget.get('agent_runs_started', 0),
                    sum(bool(r.get('agent_started')) for r in summary)),
                confirmed_successes=len(passed), successes=passed, other_agent_results=incomplete,
                agents_in_progress=active)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--batch-dir', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(inspect_batch(args.batch_dir), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
