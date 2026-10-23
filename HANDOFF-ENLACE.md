# Handoff -- enlace pela simulação, 2026-10-23

Sessão só de simulação (a máquina B não estava na bancada). Nada foi ao ar.

## Commitado

- `d1d9691` -- marca de sondagem não é apagada pela de quadro (regressão de
  `ebda203`: `limpo` falhava, 93/120 em 240 s, contrato no pior degrau).

## Sem commit (tudo junto: `saudacao.py` usa a nova assinatura de `simula_enlace.Ar`)

`enlace.py`
- `_retransmite`: CONTRATO repetido sem confirmação vai no formato do contrato
  medido (CTRL_N), não na abordagem de controle. Cenário `meio_aberto`: antes 0
  bytes e "canal perdido" em 295 s (a assinatura do ar de 2026-10-22), depois
  120/120 e 60/60 em 100 s.
- Sondagem de longe ganha uma 5ª sonda a 100 baud g0,45 (`SONDA_G_LONGE[-1]`,
  `res[len(GANHOS)]`): inteira e < 7% → aquele sentido contrata 16-FSK rep2.
  **Mudança de fio**: as duas máquinas precisam do mesmo código.
- Guarda `MARGEM_FORA` (-3 dB): sondagem com margem mediana negativa e nenhuma
  sonda de ganho achada = lida fora do lugar → ilegível, espera repetição.
  Com a regressão de ebda203 reintroduzida, `limpo` passa (129 s).
- `ESPERA_SONDA`: marca de sonda só é aceita em sondando/aguarda_sonda/
  aguarda_contrato (uma falsa no meio dos DADOS pulava ~40 s de quadros).
- `_segmento(..., inicio=)`: o primeiro segmento *lido* de um turno re-ancora
  `ouve_ate` (só cresce). Re-ancorar em ilegíveis alongava `longe` 350→514 s.
- Linhas de depuração (`ENLACE_DEPURA`): âncora da sondagem, abertura e fim de turno.

`saudacao.py`
- `--simulado <cenario>`: as duas pontas no mesmo processo, tempo real, mesmo
  laço (painel 7110 e 7111, pasta `<out>-parceiro`). `AUDIOFSK_SIM_RAPIDO=1`
  roda sem relógio de parede.
- `Lacunas`: entrada perdida reposta como silêncio (instante do ADC; parede só
  após transbordo avisado). Diário diz se há ADC e quantos transbordos.
  Hipótese, não medida: B (Windows) perdeu 27 s em 900; pode ser relógio lento.
- Motivo do fim sempre no diário.

`painel.py`: `fecha()` fecha o servidor. `visor.py`: `--simulado`; recusa o
Iniciar real numa pasta de sessões simuladas; mostra "SIMULADA". `visor/index.html`:
contador "entrada perdida". `simula_enlace.py`: `--semente=N`; cenários `perdas`,
`rajadas`, `meio_aberto`, `assimetrico`. `CLAUDE.md` atualizado.

Painel e visor testados pelo navegador com a sessão simulada: Iniciar, Pausar
(24 s no meio dos dados, recuperou), Retomar, Finalizar, Parar já; WAV/JSON gravados.

## Aberto

1. **`assimetrico` falha nas sementes 1 e 3** (passa 0 e 2). Sentido fraco de
   longe (B→A): marcas de sonda a 0,26-0,30, fechamento não achado; semente 1
   termina com A em `sondando` e B em `aguarda_contrato`; semente 3 com B
   recebendo 89/60 (pedaço duplicado após recomeço) e, numa versão anterior,
   5 s de fala sobreposta -- a única sobreposição reproduzida até agora.
   Rodar: `ENLACE_DEPURA=1 ./venv/bin/python -u simula_enlace.py assimetrico -v --semente=1`.
2. Pedaço duplicado após recomeço (`_abre_canal` repõe `pendente_tx`): troca
   documentada, mas aparece no `assimetrico`.
3. Prazo de espera mais curto que a resposta lenta do outro lado (mecanismo 1
   do relatório das sessões de 2026-10-22) -- não atacado.
4. Multicanal rep4 duplicado: não conferido (docstring de `_le_candidatos` diz
   que foi tratado).
5. Antes de ir ao ar: `transbordos` no diário de B decide se `Lacunas` se aplica.
