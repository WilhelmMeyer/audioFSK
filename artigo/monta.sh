#!/usr/bin/env bash
# Monta o artigo no Linux, no macOS e no Git Bash do Windows. A logica esta em
# monta.py, que o monta.cmd do Windows tambem chama; aqui so' se escolhe o
# interpretador.
#
# O nome nao basta para escolher: no Windows o `python3` do PATH costuma ser o
# atalho da Microsoft Store, que nao e' interpretador nenhum. Ele imprime um
# convite a instalar e sai com erro, e o convite aparece no lugar do artigo.
# Por isso cada candidato roda um -c antes de receber o trabalho, o que de
# quebra recusa um Python mais velho que o 3.11 exigido pelo conversor.
set -euo pipefail

AQUI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

serve() {
    "$@" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' \
        >/dev/null 2>&1
}

for CANDIDATO in "python3" "py -3" "python"; do
    # shellcheck disable=SC2086
    if serve $CANDIDATO; then
        # shellcheck disable=SC2086
        exec $CANDIDATO "$AQUI/monta.py" "$@"
    fi
done

echo "nenhum Python 3.11 ou mais novo encontrado (tentados: python3, py -3, python)." >&2
echo "No Linux instale o pacote python3; no Windows use o artigo\monta.cmd," >&2
echo "ou instale por python.org ou pela Microsoft Store." >&2
exit 1
