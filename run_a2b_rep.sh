#!/usr/bin/env bash
# Fase 2a da campanha A -> B: so o teste 14, e pela mesma razao que pos o 08
# antes do 07.
#
# O varrimento de ganho mediu 80-84% dos bits e ZERO blocos inteiros de doze,
# em todos os quatro ganhos. 16 a 20% de bits errados passa do que a taxa 1/3
# sozinha aguenta, entao `fecrep 1` neste sentido nao e um ajuste que
# discrimina -- e um ajuste que zera tudo. Uma campanha inteira de zeros nao
# compara gap com gap, acorde com acorde, nem gate com varredura: mede so que o
# canal esta abaixo do degrau, e isso ja esta medido.
#
# O TESTES.md manda rodar o 07 em `fecrep 1` "para o teste discriminar", e o
# raciocinio continua valendo -- e o ponto de operacao que ele discrimina que
# muda de sentido para sentido. Aqui a redundancia que discrimina e outra, e
# quem diz qual e este teste.
set -u
PY=./venv/bin/python
A2B="$PY -u capture_a2b.py --port /dev/ttyUSB0 --out-device 20"
GAIN=1.0        # o melhor dos quatro em bits, e o mais alto em nivel; ver 08

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

for r in 1 2 4; do
  run 14-fec-rep "rep$r-A2B" --mode mary --fec --repeat $r --trials 3 --gain $GAIN --bytes 48
done

echo "=== fase 2a pronta. Escolha o fecrep antes da fase 2b."
