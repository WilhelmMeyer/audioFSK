#!/usr/bin/env bash
# Roda o enlace uma vez por técnica de dados, uma sessão depois da outra.
#
#   ./sequencia_enlace.sh                       16fsk 2fsk votada multicanal
#   ./sequencia_enlace.sh votada multicanal     só essas, nessa ordem
#
# Cada sessão é completa e independente: saudação, sondagem e contrato
# próprios, e os dados só na técnica da vez (`--modo-dados`, sem descer para
# outra). Nada é misturado: o que uma técnica entrega não depende do que a
# anterior combinou. B (Windows) é o ouvinte e manda 44 bytes; A (este Linux)
# é o chamador e manda os 207 de `sessoes-enlace/carga-A.txt`.
#
# Saída em sessoes-enlace/ (A) e sessoes-enlace-B/ (B), mais um resumo por
# sessão em sessoes-enlace/sequencia.txt. Cada sessão pode ser acompanhada e
# parada pelo painel como sempre (`painel.py estado`, `./enlace_b.sh para`).
set -uo pipefail
cd "$(dirname "$0")"

MODOS=${*:-16fsk 2fsk votada multicanal}
CARGA_A=sessoes-enlace/carga-A.txt
TEXTO_B="oi do B: recebi o chamado e respondo pelo ar"
DURACAO=${DURACAO:-900}
SILENCIO=${SILENCIO:-45}
RESUMO=sessoes-enlace/sequencia.txt

[ -f "$CARGA_A" ] || { echo "falta $CARGA_A"; exit 1; }

b_vivo() { ./enlace_b.sh estado >/dev/null 2>&1; }

for modo in $MODOS; do
  t0=$(date +%s)
  echo "=== $(date +%H:%M:%S) sessão $modo" | tee -a "$RESUMO"
  ./enlace_b.sh inicia --papel ouvinte --enviar "$TEXTO_B" --receber-em "got-B-$modo.bin" \
      --duracao "$DURACAO" --fim-silencio "$SILENCIO" --modo-dados "$modo" > /dev/null
  for _ in $(seq 30); do b_vivo && break; sleep 2; done
  b_vivo || { echo "B não subiu; parando a sequência" | tee -a "$RESUMO"; exit 1; }

  rm -f "sessoes-enlace/got-A-$modo.bin"
  ENLACE_DEPURA=1 ./venv/bin/python -u saudacao.py --papel chamador --enviar-arquivo "$CARGA_A" \
      --receber-em "sessoes-enlace/got-A-$modo.bin" --duracao "$DURACAO" \
      --fim-silencio "$SILENCIO" --modo-dados "$modo" --log "sessoes-enlace/seq-$modo-A.log"

  # A saiu; B sai pelo próprio silêncio ou pela duração. Se passar disso, para.
  for _ in $(seq 90); do b_vivo || break; sleep 2; done
  b_vivo && { ./enlace_b.sh para > /dev/null; sleep 8; }
  ./enlace_b.sh puxa sessoes-enlace-B > /dev/null
  scp -q -o LogLevel=ERROR "Home@100.114.48.25:enlace_teste/got-B-$modo.bin" \
      "sessoes-enlace-B/got-B-$modo.bin" 2>/dev/null

  a=$(cmp -s "sessoes-enlace/got-A-$modo.bin" <(printf '%s' "$TEXTO_B") && echo "44/44 idênticos" \
      || echo "$(stat -c %s "sessoes-enlace/got-A-$modo.bin" 2>/dev/null || echo 0)/44")
  b=$(cmp -s "sessoes-enlace-B/got-B-$modo.bin" "$CARGA_A" && echo "207/207 idênticos" \
      || echo "$(stat -c %s "sessoes-enlace-B/got-B-$modo.bin" 2>/dev/null || echo 0)/207")
  conf=$(grep -o "tudo enviado e confirmado em [0-9.]*s" "sessoes-enlace/seq-$modo-A.log" | head -1)
  echo "    $modo: B->A $a; A->B $b; ${conf:-A não concluiu}; $(( $(date +%s) - t0 )) s de sessão" \
      | tee -a "$RESUMO"
  sleep 10
done
echo "=== $(date +%H:%M:%S) sequência terminada" | tee -a "$RESUMO"
