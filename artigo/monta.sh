#!/usr/bin/env bash
set -euo pipefail

AQUI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONVERSOR="${SIMECA_MD:-$AQUI/simeca-md}"

if [ ! -f "$CONVERSOR/simeca_md/__main__.py" ]; then
    echo "conversor vazio em $CONVERSOR; rode: git submodule update --init" >&2
    exit 1
fi

cd "$CONVERSOR"
exec python3 -m simeca_md \
    "$AQUI/artigo_modem.md" \
    -m modelos/simeca-vii/modelo.docx \
    -o "$AQUI/artigo_modem.docx" \
    --pdf "$@"
