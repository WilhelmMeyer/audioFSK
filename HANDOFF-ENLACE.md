# Handoff -- enlace no ar numa máquina só, 2026-10-27

Montagem (a máquina B e o notebook da Giselle não estavam disponíveis na maior parte do dia):
duas `saudacao.py` no mesmo notebook Linux. Chamador fala pelo alto-falante do notebook,
ouvinte pela caixa BT AL-1888 (ao lado do notebook no fim), **as duas ouvem pelo mesmo
microfone do notebook** (Mic1). Testa a lógica do protocolo, não distância nem dois
microfones independentes. Sessões em `sessoes-enlace-mesma/` e `sessoes-enlace-mesma-B/`
(ignoradas pelo git, `sessoes-*/`). Volumes no fim: notebook 1.0, BT 0.19.

## Resultado

- Sessão 5 (código antigo + Lacunas corrigido + caixa BT com chiado): 207/207 e 44/44 em
  136 s, mas depois do fim as duas pontas ficaram trocando ACK para sempre e falaram juntas
  (~209 s).
- Sessão 7 (calendário de vezes + FIM): 207/207 e 44/44, tudo entregue em 273 s, **as duas
  saíram sozinhas** (ouvinte 289 s, chamador 351 s após 3 FIM sem resposta).

## O que foi descoberto e corrigido

1. **`Lacunas` inseria silêncio falso** (saudacao.py). Pelo PulseAudio o instante do ADC
   anda em degraus (~80 ms parado, depois salto); lido bloco a bloco cada salto virava
   buraco: 420 s de silêncio em 900 s, nada legível. Agora compara no acumulado e só repõe
   um salto acima do maior `d` recente (janela 3 s). Carimbos reais: 0 s inseridos;
   perda sintética de 2,5%: repõe 8,24 de 8,28 s; relógio 3% lento: 0. O simulador
   (`Mundo`) passou a dar carimbo em degraus de 80 ms.
2. **Caixa BT engole o início de cada rajada** (não é código; memória
   `caixa-bt-engole-inicio`). Ociosa: bipe de 200 ms some ou chegam 50 ms a +1,17 s, o que
   gerou latência de eco falsa de +1,24 s, cegueira longa e marca de sondagem apagada.
   Aberta com zeros: o amplificador ainda corta ~150 ms (marca de 80 ms some, o fechamento é
   tomado pela abertura). Com chiado a -60 dBFS num fluxo à parte: inteiro. Usado nos testes:
   script fora do repo (`acordada_chiado.py`, fluxo de ruído 0.001 no bluez_output).
   **A fazer no código**: pré-rolagem ou chiado de fundo na saída, porque B (Windows) também
   usa caixa BT.
3. **Calendário de vezes** (enlace.py, pedido do usuário: o emissor dá o ritmo, o ouvinte
   nunca fala quando o emissor pode falar). Vez do ouvinte começa 2,5 s após o fim do turno
   do chamador (+ leitura de turnos longos, + acréscimo de longe), calculada igual nas duas
   pontas; ouvinte não pronto em 1,5 s ou que não leu o turno até o fim cala; chamador
   espera a vez inteira (sem sorteio 0–1 s); ACK sozinho conta como resposta; vez contada
   pelo último segmento lido.
4. **FIM explícito**: chamador manda FIM com tudo entregue, ouvinte responde e cala;
   encerrada, a estação não lê nem toca mais; `saudacao.py` sai 3 s após o último som.
   3 FIM sem resposta com tudo entregue = encerra.
5. **Cegueira começa no instante em que a estação toca** (a latência da BT varia e a marca do
   próprio quadro escapava, lida como do outro: ~136 s perdidos na sessão 6).
6. `simula_enlace.py` reprova fala sobreposta após a saudação e estação que não para;
   cenário novo `jitter_bt`. 18 cenários passam (17 + assimetrico sementes 0-3).

## Aberto

- Resposta FIM do ouvinte não foi lida pelo chamador na sessão 7 (~80 s de repetições).
- Saudação lenta no ar (80 s na sessão 7 contra 17 s na 5): primeiro OLA não passa.
- `modo_2fsk` no simulador 568 s (recomeço na primeira abertura), causa não investigada.
- Margem da vez em 2,5 s: 2,0 s quebrou `assimetrico` semente 1.
- Quadros de tamanho padrão por etapa (ideia do usuário) não foram feitos; a garantia veio do
  calendário.
- **Mudança de fio**: as duas máquinas precisam deste commit.
- Próximo: notebook da Giselle (Windows, SSH pelo Tailscale, dados em ~/infra) como B, com a
  caixa BT passada para ele; teste de verdade com dois microfones e distância.

---

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
