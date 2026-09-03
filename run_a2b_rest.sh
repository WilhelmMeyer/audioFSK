#!/usr/bin/env bash
# Fase 2 da campanha A -> B: as camadas e os ajustes, no ganho que a fase 1
# escolheu. Recebe o ganho M-ario como primeiro argumento.
#
#     ./run_a2b_rest.sh 0.7
#
# As camadas de acorde (04, 05, 06) ficam em 1.0 de proposito e nao no ganho
# M-ario: um acorde de cinco tons ja sai com um quinto da amplitude por tom, e
# o ponto de operacao de uma camada nao e o da outra. E a mesma razao pela qual
# `gain 0.5` no lado A e `gain 0.5` no lado B nao sao o mesmo numero.
set -u
GAIN="${1:?uso: run_a2b_rest.sh <ganho-mary>}"
PY=./venv/bin/python
PORT=/dev/ttyUSB0
OUTDEV=20
# `--serial-only` porque a rede nao passou: as duas maquinas ficam na mesma
# sub-rede e nao se alcancam, o que sobrou como ponto de acesso isolando
# clientes depois que a regra de ufw foi aberta. Sem isto cada trial gasta
# alguns segundos provando uma rota que nao existe -- e sao ~50 trials.
# Tire a opcao quando `rede <url>` responder `pong` da outra ponta.
A2B="$PY -u capture_a2b.py --port $PORT --out-device $OUTDEV --serial-only"

run () {
  local dir="$1"; shift
  local label="$1"; shift
  echo "=== $label -> captures-a2b/$dir"
  $A2B --out "captures-a2b/$dir" --label "$label" "$@" \
    || { echo "!! $label incompleto, repetindo em 8s"; sleep 8;
         $A2B --out "captures-a2b/$dir" --label "$label" "$@" \
           || echo "!! $label falhou duas vezes, seguindo"; }
  sleep 6
}

# 04 -- Bell 202, sem FEC. Linha de base; espera-se falha.
run 04-fsk-base fsk-base-A2B --mode fsk --trials 3 --gain 1.0 --bytes 48

# 05 -- MFSK votado
run 05-mfsk-vote mfsk-vote-A2B --mode mfsk --fec --repeat 2 --trials 3 --gain 1.0 --bytes 48

# 06 -- MFSK paralelo
run 06-mfsk-par mfsk-par-A2B --mode mfsk --fec --parallel --repeat 2 --trials 3 --gain 1.0 --bytes 48

# 07 -- M-aria, linha de base, no ganho calibrado. fecrep 1 para discriminar.
run 07-mary-base mary-base-A2B --mode mary --fec --repeat 1 --trials 4 --gain "$GAIN" --bytes 48

# 09 -- silencio entre simbolos. Ajuste do transmissor: gravado por ponto.
for gp in 0.0 0.15 0.30; do
  run 09-mary-gap "mary-gap$gp-A2B" --mode mary --fec --repeat 1 --trials 3 --gain "$GAIN" --bytes 48 --gap $gp
done

# 10 -- largura da faixa por tom. E ajuste DO RECEPTOR: a mesma gravacao serve
# aos tres pontos, e repontuar o mesmo audio e mais honesto do que gravar a sala
# tres vezes e chamar a diferenca de "banda".
run 10-mary-band mary-band-A2B --mode mary --fec --repeat 1 --trials 3 --gain "$GAIN" --bytes 48

# 11 -- nibble em 3 tons contra 1 tom, os dois pontos no mesmo par de minutos.
run 11-mary-chord chord-off-A2B --mode mary --fec --repeat 1 --trials 3 --gain "$GAIN" --bytes 48
run 11-mary-chord chord-on-A2B  --mode mary --fec --repeat 1 --trials 3 --gain "$GAIN" --bytes 48 --chord

# 12/13 -- gate contra as duas varreduras, bloco de 192 bytes
run 12-13-sync sync-gate-A2B  --mode mary --fec --repeat 1 --trials 4 --gain "$GAIN" --bytes 192
run 12-13-sync sync-sweep-A2B --mode mary --fec --repeat 1 --trials 4 --gain "$GAIN" --bytes 192 --sync-chirp

# 14 -- redundancia neste sentido
for r in 1 2 4; do
  run 14-fec-rep "rep$r-A2B" --mode mary --fec --repeat $r --trials 3 --gain "$GAIN" --bytes 48
done

echo "=== campanha A->B terminada"
