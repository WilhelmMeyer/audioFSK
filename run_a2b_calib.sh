#!/usr/bin/env bash
# Fase 1 da campanha A -> B: o que nao depende de um ganho calibrado, mais a
# propria calibracao.
#
# A ordem da tabela do TESTES.md poe o 08 (ganho) depois do 07 (linha de base
# M-aria), e a razao dada e boa: calibrar A->B por NIVEL nao e confiavel, porque
# o receptor de la parece ter controle automatico de ganho e a regua se mexe
# junto com o que ela mede. Mas o mesmo documento diz o que fazer nesse caso --
# "calibrar A->B, se for preciso, sera por taxa de erro". E isso que esta fase
# faz: varre o ganho e mede acerto de bits e blocos inteiros em cada ponto, sem
# olhar nivel nenhum. O 07 e tudo que vem depois roda no ganho que sair daqui.
#
# O custo de nao fazer assim e concreto: 07, 09, 10, 11, 12/13 e 14 sao seis
# testes, cerca de duas horas de cabo, e todos medindo a distorcao do limitador
# em vez do efeito que nomeiam, se 1.0 estiver acima do teto desta cadeia.
set -u
PY=./venv/bin/python
PORT=/dev/ttyUSB0
OUTDEV=20
A2B="$PY -u capture_a2b.py --port $PORT --out-device $OUTDEV"

run () {   # run <pasta> <rotulo> <args...>
  local dir="$1"; shift
  local label="$1"; shift
  echo "=== $label -> captures-a2b/$dir"
  $A2B --out "captures-a2b/$dir" --label "$label" "$@" \
    || { echo "!! $label incompleto, repetindo em 8s"; sleep 8;
         $A2B --out "captures-a2b/$dir" --label "$label" "$@" \
           || echo "!! $label falhou duas vezes, seguindo"; }
  # A caixa Bluetooth anuncia zero canais por um a dois segundos depois que o
  # processo anterior a solta; 6 s cobre isso com folga.
  sleep 6
}

# 01 -- piso do microfone de B, nada tocando
run 01-lvl-base lvl-base-A2B --silence 8 --trials 2

# 02 -- tom puro de 1700 Hz. Serve de sanidade da cadeia, NAO de calibracao:
# um burst M-ario troca de tom a cada simbolo e carrega ~2,5x o pico de um tom
# continuo, entao um nivel medido no tom nao diz onde o limitador corta.
run 02-lvl-tone lvl-tone-A2B --tone "1700 3" --trials 3 --gain 1.0

# 03 -- varredura, para o mapa do canal neste sentido
run 03-ch-chirp ch-chirp-A2B --chirp "300 6000 6" --trials 1 --gain 1.0

# 08 -- a calibracao, no burst e por taxa de erro. Quatro pontos, tres trials.
for g in 1.0 0.7 0.5 0.25; do
  run 08-mary-gain "mary-g$g-A2B" --mode mary --fec --repeat 1 --trials 3 --gain $g --bytes 48
done

echo "=== fase 1 pronta. Pontue 08 e escolha o ganho antes da fase 2."
