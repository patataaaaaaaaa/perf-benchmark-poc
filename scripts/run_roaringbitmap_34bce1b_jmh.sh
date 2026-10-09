#!/usr/bin/env bash

set -euo pipefail

if [[ "$#" -ne 2 ]]; then
  echo "usage: $0 WORKSPACE ARTIFACTS_DIR" >&2
  exit 2
fi

workspace=$(cd "$1" && pwd)
artifacts_dir=$(mkdir -p "$2" && cd "$2" && pwd)
script_dir=$(cd "$(dirname "$0")" && pwd)
fix_commit=34bce1bae5591347d1992daae0cdb041a409cc1d
benchmark_rel=jmh/src/jmh/java/org/roaringbitmap/longlong/ShiftLeftFromSpecifiedPositionBenchmark.java
benchmark_file="$workspace/$benchmark_rel"

injected=false
if [[ -e "$benchmark_file" ]]; then
  if [[ "$(git -C "$workspace" rev-parse HEAD)" != "$fix_commit" ]] || \
     ! git -C "$workspace" diff --quiet "$fix_commit" -- "$benchmark_rel"; then
    echo "benchmark source differs from the fixed evaluation version: $benchmark_file" >&2
    exit 2
  fi
else
  mkdir -p "$(dirname "$benchmark_file")"
  git -C "$workspace" show "$fix_commit:$benchmark_rel" > "$benchmark_file"
  injected=true
fi

cleanup() {
  if [[ "$injected" == true ]]; then
    rm -f "$benchmark_file"
  fi
}
trap cleanup EXIT

cd "$workspace"
./gradlew --no-daemon :jmh:shadowJar
for pair in 0:1 0:2 2:1; do
  pos=${pair%:*}
  count=${pair#*:}
  java -jar jmh/build/libs/benchmarks.jar ".*ShiftLeftFromSpecifiedPositionBenchmark.*" \
    -p "pos=$pos" \
    -p "count=$count" \
    -wi 5 \
    -i 10 \
    -f 2 \
    -r 1s \
    -w 1s \
    -rf json \
    -rff "$artifacts_dir/jmh-pos${pos}-count${count}.json"
done

python3 "$script_dir/validate_roaringbitmap_34bce1b_jmh.py" "$artifacts_dir"
