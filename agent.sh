#!/usr/bin/env bash
# Keep the agent side up. This machine is the follower: nobody is sitting at
# its keyboard, so a crash -- an unplugged USB-serial adapter, a PortAudio
# device disappearing -- must not end the session silently.
#
# A voluntary `restart` command does NOT come back through here: updater.py
# execs in place, so the process keeps the same PID and this loop never
# notices. This exists only for the crashes.
#
#   ./agent.sh                    # /dev/ttyUSB0
#   ./agent.sh /dev/ttyUSB1       # another port
set -u

PORT="${1:-/dev/ttyUSB0}"
cd "$(dirname "$0")" || exit 1

while true; do
    echo "[agent.sh] $(date '+%H:%M:%S') iniciando em $PORT"
    ./venv/bin/python console.py --role agent --port "$PORT" "${@:2}"
    code=$?
    # Ctrl+C (130) and a clean exit (0) are the operator's decision, not a
    # fault -- respect them instead of looping forever against the keyboard.
    if [ $code -eq 0 ] || [ $code -eq 130 ]; then
        echo "[agent.sh] saida limpa (codigo $code)"
        exit $code
    fi
    echo "[agent.sh] caiu com codigo $code, reiniciando em 3s"
    sleep 3
done
