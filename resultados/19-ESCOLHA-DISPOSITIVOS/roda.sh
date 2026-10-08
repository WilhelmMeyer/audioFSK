#!/bin/bash
# Uma rodada: os dois microfones gravam, um alto-falante toca a sequência da sonda.
# uso: ./roda.sh <rotulo> <win|linux> "<nome do dispositivo de saída>"
set -e
cd "$(dirname "$0")"
R=$1; LADO=$2; SAIDA=$3
WIN=Home@100.114.48.25
WPY='C:\Users\Home\WorkSpace\audioFSK\venv\Scripts\python.exe'
PY=../../venv/bin/python
SSH="ssh -o BatchMode=yes -o LogLevel=ERROR"
$SSH $WIN "$WPY sonda.py rec --device \"Microfone (Realtek\" --seconds 28 --out $R-micwin.wav" > gravacoes/$R-micwin.log 2>&1 &
PW=$!
$PY sonda.py rec --device pipewire --seconds 28 --out gravacoes/$R-miclinux.wav > gravacoes/$R-miclinux.log 2>&1 &
PL=$!
sleep 3
if [ "$LADO" = win ]; then
  $SSH $WIN "$WPY sonda.py play --device \"$SAIDA\" --gain 0.3"
else
  $PY sonda.py play --device "$SAIDA" --gain 0.3
fi
wait $PW; wait $PL || true
scp -q -o BatchMode=yes -o LogLevel=ERROR "$WIN:$R-micwin.wav" gravacoes/
$SSH $WIN "del $R-micwin.wav"
cat gravacoes/$R-micwin.log gravacoes/$R-miclinux.log
