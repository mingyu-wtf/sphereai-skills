#!/usr/bin/env bash
# 스레드 자동 운영 러너 (macOS·Linux cron이 10분마다 실행)
# 할 일이 없으면 Claude를 부르지 않고 끝낸다. 겹쳐 실행되지 않게 잠금 파일을 쓴다.
# 작업 폴더 = 이 파일의 상위 폴더(config.json이 있는 곳).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export PYTHONIOENCODING=utf-8
PY="${PYTHON:-python3}"

LOGDIR="$ROOT/$("$PY" -c 'import json;print(json.load(open("config.json",encoding="utf-8"))["paths"]["run_log_dir"])')"
mkdir -p "$LOGDIR"
LOG="$LOGDIR/run_$(date +%Y%m%d).log"
LOCK="$ROOT/run.lock"

if [ -f "$LOCK" ] && [ -n "$(find "$LOCK" -mmin -60 2>/dev/null)" ]; then exit 0; fi

DUE="$("$PY" scripts/due.py)"
if [ -z "$DUE" ] || [ "$DUE" = "[]" ]; then exit 0; fi

date "+%Y-%m-%d %H:%M" > "$LOCK"
trap 'rm -f "$LOCK"' EXIT
printf '\n==== %s due: %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$DUE" >> "$LOG"

PROMPT_FILE="$ROOT/$("$PY" -c 'import json;print(json.load(open("config.json",encoding="utf-8"))["paths"]["prompt"])')"
TOOLS=()
while IFS= read -r t; do TOOLS+=("$t"); done < <("$PY" -c 'import json;[print(t) for t in json.load(open("config.json",encoding="utf-8"))["claude_allowed_tools"]]')

{ cat "$PROMPT_FILE"; printf '\n\n## 지금 할 일\n%s\n' "$DUE"; } \
  | claude -p --permission-mode acceptEdits --allowedTools "${TOOLS[@]}" >> "$LOG" 2>&1 || true
