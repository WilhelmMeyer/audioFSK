#!/usr/bin/env bash
# Keep the agent side up. This machine is the follower: nobody is sitting at
# its keyboard, so a crash -- an unplugged USB-serial adapter, a PortAudio
# device disappearing, code that arrived broken -- must not end the session
# silently.
#
# A voluntary `restart` command does NOT come back through here: updater.py
# execs in place, so the process keeps the same PID and this loop never
# notices. This exists for crashes, and for the one failure updater.py cannot
# catch by itself -- code that compiles but dies on startup. Once it dies, the
# serial channel is gone and nobody can send a fix, so recovery has to be
# local: reset onto the follow ref and try again.
#
#   ./agent.sh                    # /dev/ttyUSB0
#   ./agent.sh /dev/ttyUSB1       # another port
set -u

PORT="${1:-/dev/ttyUSB0}"
FOLLOW_REF="${FOLLOW_REF:-origin/main}"
cd "$(dirname "$0")" || exit 1

fast_failures=0

while true; do
    echo "[agent.sh] $(date '+%H:%M:%S') iniciando em $PORT"
    started=$SECONDS
    ./venv/bin/python console.py --role agent --port "$PORT" "${@:2}"
    code=$?
    ran=$((SECONDS - started))

    # Ctrl+C (130) and a clean exit (0) are the operator's decision, not a
    # fault -- respect them instead of looping forever against the keyboard.
    if [ $code -eq 0 ] || [ $code -eq 130 ]; then
        echo "[agent.sh] saida limpa (codigo $code)"
        exit $code
    fi

    # Surviving a while means it ran and then something went wrong: a real
    # crash, worth retrying as-is. Dying immediately, repeatedly, means the
    # code on disk cannot start at all.
    if [ $ran -ge 20 ]; then
        fast_failures=0
    else
        fast_failures=$((fast_failures + 1))
    fi

    if [ $fast_failures -ge 3 ]; then
        echo "[agent.sh] 3 quedas imediatas -- recuperando para $FOLLOW_REF"
        git fetch --all --prune && git reset --hard "$FOLLOW_REF"
        fast_failures=0
    fi

    echo "[agent.sh] caiu com codigo $code apos ${ran}s, reiniciando em 3s"
    sleep 3
done
