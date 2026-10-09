#!/usr/bin/env bash

# Run the four prompt variants against the same parent commit and JMH protocol.
set -euo pipefail

if [[ "$#" -ne 1 ]]; then
  echo "usage: $0 EVAL_ROOT" >&2
  exit 2
fi

eval_root=$(cd "$1" && pwd)
project_root=$(cd "$(dirname "$0")/.." && pwd)
repo="$eval_root/RoaringBitmap-34bce1b-run"
task_root="$eval_root/BenchLLMRealSE"
matrix_root="$project_root/artifacts/benchllmrealse/RoaringBitmap/34bce1b/matrix-$(date -u +%Y%m%dT%H%M%SZ)"
parent_commit=7d3eec51ef8aaa83ba058178f35e939ae1aaaac6
fix_commit=34bce1bae5591347d1992daae0cdb041a409cc1d
original_workspace="$eval_root/RoaringBitmap-34bce1b-original"
developer_workspace="$eval_root/RoaringBitmap-34bce1b-developer"
benchmark="$project_root/scripts/run_roaringbitmap_34bce1b_jmh.sh"
existing_prompt1="$project_root/artifacts/benchllmrealse/RoaringBitmap/34bce1b/prompt1-20261009T044017Z"

mkdir -p "$matrix_root"
printf '%s\n' "$matrix_root" > "$project_root/artifacts/benchllmrealse/RoaringBitmap/34bce1b/latest-matrix.txt"

prepare_workspace() {
  local workspace=$1
  local revision=$2
  if [[ ! -e "$workspace" ]]; then
    git -C "$repo" worktree add --detach "$workspace" "$revision"
  fi
  if [[ "$(git -C "$workspace" rev-parse HEAD)" != "$revision" ]]; then
    echo "wrong HEAD in $workspace" >&2
    return 1
  fi
  if [[ -n "$(git -C "$workspace" status --porcelain)" ]]; then
    echo "workspace is dirty before run: $workspace" >&2
    return 1
  fi
}

run_reference() {
  local label=$1
  local workspace=$2
  local output="$matrix_root/$label"
  mkdir -p "$output"
  printf '%s\n' "$label: verifying" > "$matrix_root/status.txt"
  if (cd "$workspace" && ./gradlew --no-daemon :RoaringBitmap:test \
      --tests org.roaringbitmap.longlong.IntegerUtilTest) \
      > "$output/verification.stdout.log" 2> "$output/verification.stderr.log"; then
    printf 'passed\n' > "$output/verification.status"
  else
    printf 'failed\n' > "$output/verification.status"
    echo "$label unit test failed" >&2
    return 1
  fi
  printf '%s\n' "$label: benchmarking" > "$matrix_root/status.txt"
  if "$benchmark" "$workspace" "$output" \
      > "$output/benchmark.stdout.log" 2> "$output/benchmark.stderr.log"; then
    printf 'passed\n' > "$output/benchmark.status"
  else
    printf 'failed\n' > "$output/benchmark.status"
    echo "$label JMH failed" >&2
    return 1
  fi
}

run_prompt() {
  local number=$1
  local workspace="$eval_root/RoaringBitmap-34bce1b-prompt$number"
  local output="$matrix_root/prompt$number"
  prepare_workspace "$workspace" "$parent_commit"
  printf '%s\n' "prompt$number: agent running" > "$matrix_root/status.txt"
  if python3 "$project_root/scripts/run_benchllm_codex.py" \
      --benchmark-root "$task_root" \
      --workspace "$workspace" \
      --repo-name RoaringBitmap \
      --commit-id 34bce1b \
      --prompt-number "$number" \
      --model deepseek-v4-pro \
      --codex "$HOME/.local/bin/codex" \
      --timeout-seconds 1800 \
      --command-timeout-seconds 3600 \
      --artifacts-dir "$output" \
      --verification-command './gradlew --no-daemon :RoaringBitmap:test --tests org.roaringbitmap.longlong.IntegerUtilTest' \
      --benchmark-command "$benchmark {workspace} {artifacts}" \
      > "$matrix_root/prompt${number}.runner.stdout.log" \
      2> "$matrix_root/prompt${number}.runner.stderr.log"; then
    printf 'succeeded\n' > "$matrix_root/prompt${number}.status"
  else
    printf 'failed\n' > "$matrix_root/prompt${number}.status"
  fi
}

printf '%s\n' "matrix root: $matrix_root"
printf '%s\n' 'original: preparing' > "$matrix_root/status.txt"
prepare_workspace "$original_workspace" "$parent_commit"
prepare_workspace "$developer_workspace" "$fix_commit"
run_reference original "$original_workspace"
run_reference developer "$developer_workspace"

if [[ ! -f "$existing_prompt1/result.json" ]] || \
   [[ "$(git -C "$repo" rev-parse HEAD)" != "$parent_commit" ]]; then
  echo "prompt1 source run or workspace baseline missing" >&2
  exit 1
fi
if ! git -C "$repo" diff --binary HEAD -- | cmp - "$existing_prompt1/agent.patch"; then
  echo "prompt1 workspace no longer matches its saved agent patch" >&2
  exit 1
fi
mkdir -p "$matrix_root/prompt1"
printf '%s\n' "$existing_prompt1" > "$matrix_root/prompt1/source-run.txt"
printf '%s\n' 'prompt1: benchmarking saved agent patch' > "$matrix_root/status.txt"
if "$benchmark" "$repo" "$matrix_root/prompt1" \
    > "$matrix_root/prompt1/benchmark.stdout.log" \
    2> "$matrix_root/prompt1/benchmark.stderr.log"; then
  printf 'succeeded\n' > "$matrix_root/prompt1.status"
else
  printf 'failed\n' > "$matrix_root/prompt1.status"
fi

for number in 2 3 4; do
  run_prompt "$number"
done

printf '%s\n' 'complete' > "$matrix_root/status.txt"
