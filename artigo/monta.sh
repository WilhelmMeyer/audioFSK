#!/usr/bin/env bash
# Monta o artigo no Linux e no macOS. A logica esta em monta.py, que o
# monta.cmd do Windows tambem chama; aqui so' se escolhe o interpretador.
set -euo pipefail

AQUI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$AQUI/monta.py" "$@"
