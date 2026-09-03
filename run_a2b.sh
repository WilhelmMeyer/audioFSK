#!/usr/bin/env bash
# Campanha A -> B inteira, um ponto por vez, na ordem da tabela do TESTES.md.
# Cada ponto grava em sua propria pasta captures-a2b/<teste>/ para que o
# `resultado.py` monte uma pasta por teste sem ter de separar por rotulo.
#
# A -> B: quem transmite e a maquina A (Linux, caixa Bluetooth, dev 20) e quem
# grava e a B, pelo comando `grave` do agent; a gravacao volta pelo cabo. O
# `capture.py` nao sabe fazer este sentido -- `capture_a2b.py` e o espelho dele.
set -u
PY=./venv/bin/python
PORT=/dev/ttyUSB0
OUTDEV=20
A2B="$PY -u capture_a2b.py --port $PORT --out-device $OUTDEV"

run () {   # run <pasta> <rotulo> <args...>
  local dir="$1"; shift
  local label="$1"; shift
  echo "=== $label -> captures-a2b/$dir"
  # O microfone da outra ponta as vezes nao acorda logo depois de outro
  # processo soltar o dispositivo; uma tentativa a mais custa segundos e
  # salva o ponto inteiro.
  $A2B --out "captures-a2b/$dir" --label "$label" "$@" \
    || { echo "!! $label falhou, repetindo em 6s"; sleep 6;
         $A2B --out "captures-a2b/$dir" --label "$label" "$@" \
           || echo "!! $label falhou duas vezes, seguindo"; }
  sleep 3
}

# 01 -- piso do microfone de B, nada tocando
run 01-lvl-base lvl-base-A2B --silence 8 --trials 2

# 02 -- tom puro de 1700 Hz, tres repeticoes
run 02-lvl-tone lvl-tone-A2B --tone "1700 3" --trials 3 --gain 1.0

# 03 -- varredura, para o mapa do canal neste sentido
run 03-ch-chirp ch-chirp-A2B --chirp "300 6000 6" --trials 1 --gain 1.0

# 04 -- Bell 202, sem FEC. Espera-se falha; a linha de base e o ponto.
run 04-fsk-base fsk-base-A2B --mode fsk --trials 3 --gain 1.0 --bytes 48

# 05 -- MFSK votado
run 05-mfsk-vote mfsk-vote-A2B --mode mfsk --fec --repeat 2 --trials 3 --gain 1.0 --bytes 48

# 06 -- MFSK paralelo
run 06-mfsk-par mfsk-par-A2B --mode mfsk --fec --parallel --repeat 2 --trials 3 --gain 1.0 --bytes 48

# 07 -- M-ario, linha de base. fecrep 1 para o teste discriminar.
run 07-mary-base mary-base-A2B --mode mary --fec --repeat 1 --trials 4 --gain 1.0 --bytes 48

# 08 -- ganho. Esta cadeia e outra; o ponto de operacao dela nao se deduz da outra.
for g in 1.0 0.7 0.5 0.25; do
  run 08-mary-gain "mary-g$g-A2B" --mode mary --fec --repeat 1 --trials 3 --gain $g --bytes 48
done

echo "=== primeira metade pronta (01-08)"

# 09 -- silencio entre simbolos. Ajuste do transmissor: tem de ser gravado por ponto.
for gp in 0.0 0.15 0.30; do
  run 09-mary-gap "mary-gap$gp-A2B" --mode mary --fec --repeat 1 --trials 3 --gain 1.0 --bytes 48 --gap $gp
done

# 10 -- largura da faixa por tom. E ajuste DO RECEPTOR: a mesma gravacao serve
# aos tres pontos, e re-pontuar o mesmo audio e mais honesto do que gravar a
# sala tres vezes e chamar a diferenca de "banda". Grava uma vez aqui; as
# variantes saem por rescore (ver o HEADER do teste).
run 10-mary-band mary-band-A2B --mode mary --fec --repeat 1 --trials 3 --gain 1.0 --bytes 48

# 11 -- nibble em 3 tons contra 1 tom. Ajuste do transmissor: dois pontos.
run 11-mary-chord chord-off-A2B --mode mary --fec --repeat 1 --trials 3 --gain 1.0 --bytes 48
run 11-mary-chord chord-on-A2B  --mode mary --fec --repeat 1 --trials 3 --gain 1.0 --bytes 48 --chord

# 12/13 -- gate contra as duas varreduras, bloco de 192 bytes
run 12-13-sync sync-gate-A2B  --mode mary --fec --repeat 1 --trials 4 --gain 1.0 --bytes 192
run 12-13-sync sync-sweep-A2B --mode mary --fec --repeat 1 --trials 4 --gain 1.0 --bytes 192 --sync-chirp

# 14 -- redundancia neste sentido
for r in 1 2 4; do
  run 14-fec-rep "rep$r-A2B" --mode mary --fec --repeat $r --trials 3 --gain 1.0 --bytes 48
done

echo "=== campanha A->B terminada"
