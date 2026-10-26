#!/bin/sh
set -eu
cd "$(dirname "$0")"
if [ -x .runtime/ollama ]; then
  if ! curl -fsS http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
    OLLAMA_MODELS="$PWD/.runtime/models" OLLAMA_HOST=127.0.0.1:11434 .runtime/ollama serve >.runtime/ollama.log 2>&1 &
    tries=0
    until curl -fsS http://127.0.0.1:11434/api/tags >/dev/null 2>&1; do
      tries=$((tries + 1))
      if [ "$tries" -ge 20 ]; then echo 'Ollama did not start; see .runtime/ollama.log'; exit 1; fi
      sleep 1
    done
  fi
fi
exec python3 server.py "$@"
