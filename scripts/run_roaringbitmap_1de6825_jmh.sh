#!/usr/bin/env bash

set -euo pipefail

if [[ "$#" -ne 2 ]]; then
  echo "usage: $0 WORKSPACE ARTIFACTS_DIR" >&2
  exit 2
fi

workspace=$(cd "$1" && pwd)
artifacts_dir=$(mkdir -p "$2" && cd "$2" && pwd)
fix_commit=1de68254774c3d1932ee025cb331f60dd4e904d0
benchmark_rel=jmh/src/jmh/java/org/roaringbitmap/IntermediateByteArrayBenchmark.java
benchmark_file="$workspace/$benchmark_rel"

if [[ -e "$benchmark_file" ]]; then
  echo "refusing to overwrite existing benchmark source: $benchmark_file" >&2
  exit 2
fi

mkdir -p "$(dirname "$benchmark_file")"
git -C "$workspace" show "$fix_commit:$benchmark_rel" > "$benchmark_file"

cleanup() {
  rm -f "$benchmark_file"
}
trap cleanup EXIT

cd "$workspace"
./gradlew --no-daemon :jmh:shadowJar
java -jar jmh/build/libs/benchmarks.jar ".*IntermediateByteArrayBenchmark.*" \
  -wi 10 \
  -i 50 \
  -f 1 \
  -r 1s \
  -w 1s \
  -rf json \
  -rff "$artifacts_dir/jmh.json"
