#!/usr/bin/env bash
# Monta a pasta de resultado de cada ponto A->B ja gravado.
#
# Separado do `run_a2b.sh` de proposito: a gravacao ocupa a sala e o cabo, a
# pontuacao nao ocupa nada. Rodar a segunda enquanto a primeira ainda anda
# custaria CPU no meio de uma medida; rodar depois deixa a campanha inteira
# repontuavel quantas vezes for preciso sobre o mesmo audio.
set -u
PY=./venv/bin/python
BANCADA="A->B. A (Linux, console, transmite): caixa Bluetooth 41:42:2B:14:D4:2A, dev PortAudio 20. B (Windows, agent, grava): caixa Bluetooth AL-667 desligada durante a medida, microfone interno do notebook. Gravacao trazida pelo cabo serial /dev/ttyUSB0 a 115200 em int16; o cabo e so controle e transporte, o payload viaja pelo ar."

mount () {   # mount <NOME-RESULTADO> <pasta-de-captura> <nota>
  local nome="$1" dir="$2" nota="$3"
  if ! ls "captures-a2b/$dir"/*.json >/dev/null 2>&1; then
    echo "-- $nome: sem gravacao em captures-a2b/$dir, pulando"
    return
  fi
  echo "=== $nome"
  $PY -u resultado.py "$nome" "captures-a2b/$dir"/*.json \
      --bancada "$BANCADA" --note "$nota" || { echo "!! $nome falhou"; return; }
  # A figura de leitura so faz sentido nas camadas com simbolo M-ario; nas
  # outras o spectro.py sai sozinho pelo resultado.py e basta.
  for j in "resultados/$nome/gravacao"/*.json; do
    s=$(basename "$j" .json)
    $PY spectro.py "$j" --fundido --win 480 \
        -o "resultados/$nome/figuras/$s-leitura.png" >/dev/null 2>&1 \
      || echo "   (sem figura de leitura para $s)"
  done
}

mount 01-LVL-BASE-A2B   01-lvl-base  "Piso do microfone da maquina B, nada tocando em nenhuma das pontas."
mount 02-LVL-TONE-A2B   02-lvl-tone  "Tom puro de 1700 Hz saindo de A, medido no microfone de B. Tres repeticoes."
mount 03-CH-CHIRP-A2B   03-ch-chirp  "Varredura 300-6000 Hz de A para B, para o mapa do canal neste sentido."
mount 04-FSK-BASE-A2B   04-fsk-base  "Bell 202, 1200 baud, 8N1, sem FEC. Linha de base; espera-se falha."
mount 05-MFSK-VOTE-A2B  05-mfsk-vote "MFSK 10 tons, 5 pares, voto, fecrep 2."
mount 06-MFSK-PAR-A2B   06-mfsk-par  "MFSK paralelo, cada par com seu bit, fecrep 2."
mount 07-MARY-BASE-A2B  07-mary-base "M-aria 16 tons, fecrep 1 para o teste discriminar."
mount 08-MARY-GAIN-A2B  08-mary-gain "Ganho de saida de A em 1.0, 0.7, 0.5 e 0.25. O ponto de operacao desta cadeia nao se deduz do outro sentido."
mount 09-MARY-GAP-A2B   09-mary-gap  "marygap 0, 0.15 e 0.30. Ajuste do transmissor, gravado por ponto."
mount 10-MARY-BAND-A2B  10-mary-band "maryband: ajuste do RECEPTOR. Gravado uma vez; as variantes saem por repontuacao do mesmo audio."
mount 11-MARY-CHORD-A2B 11-mary-chord "Nibble em 3 tons contra 1 tom, os dois pontos gravados no mesmo par de minutos."
mount 12-13-SYNC-A2B    12-13-sync   "Gate early/late contra as duas varreduras, bloco de 192 bytes, pareado sobre condicoes iguais."
mount 14-FEC-REP-A2B    14-fec-rep   "fecrep 1, 2 e 4. Redundancia e propriedade do enlace, e esta cadeia e outra."

echo "=== montagem terminada"
