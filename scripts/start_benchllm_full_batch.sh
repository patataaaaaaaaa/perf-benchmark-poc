#!/usr/bin/env bash
set -euo pipefail
eval_root=/downloads/patataWJY/benchllm-agent-eval
previous_batch="$eval_root/artifacts/benchllmrealse/full64-p4-20261010T021000Z"
batch_dir="$eval_root/artifacts/benchllmrealse/full64-p4-retry-20261010T041500Z"
project_dir="$eval_root/perf-benchmark-poc"
if [[ -e "$batch_dir/pid.txt" ]]; then
    echo "Existing launch record; refusing a duplicate launch."
    exit 1
fi
set -a
source "$eval_root/secrets.env"
set +a
mkdir -p "$batch_dir"
cd "$project_dir"
nohup setsid python3 -u scripts/run_benchllm_full_batch.py \
    --eval-root "$eval_root" --batch-dir "$batch_dir" \
    --reuse-prepared-batch "$previous_batch" \
    --reserve-cny 2 --agent-timeout-seconds 900 \
    > "$batch_dir/runner.log" 2>&1 < /dev/null &
queue_pid=$!
printf '%s\n' "$queue_pid" > "$batch_dir/pid.txt"
echo "Queue PID: $queue_pid"
echo "Batch: $batch_dir"
