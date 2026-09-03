# 15-PKT-ARQ -- arquivo inteiro, stop-and-wait

- **Codigo:** commit `02be235-dirty` (ver ressalvas)
- **Quando:** 2026-09-03, 17:30-17:42
- **Bancada:** B -> A. B (Windows, agent): caixa Bluetooth AL-667 a ~60% de
  volume. A (Linux, console): microfone interno Mic1/Dmic0, dev PortAudio 26,
  Dmic0 45 (-5 dB), Capture 39 (+12 dB). Cabo serial `/dev/ttyUSB0` a 115200,
  so controle -- os bytes do arquivo viajam **so pelo ar**.
- **Camada:** M-aria 16 tons, 100 baud, FEC convolucional K=7 taxa 1/3,
  `fecrep 1`, Viterbi de decisao suave, `syncsweep off`.
- **Ganho de transmissao (em B):** 1.0
- **Arquivo:** `testcard.bmp`, 1334 bytes.
- **Ferramenta:** `recvfile.py`, ARQ stop-and-wait puxado por A.

## Resultado

| condicao | pacotes | tempo | taxa util | retransmissoes | CRC32 | arquivo |
|---|---|---|---|---|---|---|
| carga de 64 bytes | **21 de 21** | 197 s | 6,8 B/s | **0** | confere | identico |
| carga de 128 bytes | **11 de 11** | 186 s | 7,2 B/s | 3 | confere | identico |

`cmp` e `md5sum` contra o original: identicos nos dois casos
(`0b4d566a771ec7a0feec546f4cbfff22`).

## Leitura principal

**A transferencia de arquivo passou a funcionar, e este e o resultado mais
importante da bancada.** O `CLAUDE.md` registra este mesmo teste como "a parte
que hoje nao funciona: 1 pacote de 21 com pacotes de 81 bytes". Agora sao 21 de
21 sem uma unica retransmissao, no mesmo tamanho de pacote e no mesmo arquivo.

Nada mudou no `recvfile.py` nem no `xfer.py`. O que mudou foi a **cadeia
analogica**: a caixa de B saiu do volume maximo (onde o limitador achatava o
sinal) e o ganho de captura de A desceu de +5 dB para -5 dB. O teste 07 ja tinha
mostrado que linearidade vale mais que amplitude -- 3 blocos de 3 com pico 0,14
a 0,20, contra 1 de 3 com pico 1,000 e 10% das amostras ceifadas. O teste 15 e a
consequencia dessa mesma correcao no nivel de arquivo: um protocolo que retenta
ate desistir precisa de uma taxa de erro por pacote baixa, e com a cadeia
saturada nenhum numero de retentativas alcancava.

**O pacote maior amortiza o preambulo, e quase empata.** Cada pacote paga 120
simbolos de preambulo M-ario, entao 128 bytes de carga rendem 7,2 B/s contra 6,8
B/s com 64. Mas o bloco maior tambem falha mais -- 3 retransmissoes contra
nenhuma -- e as duas coisas quase se cancelam: 6% de ganho liquido. Num canal
um pouco pior a conta inverte, porque uma retransmissao custa o pacote inteiro.
**64 bytes e a escolha conservadora e 128 e defensavel; nao ha diferenca que
justifique arriscar.**

**A taxa util do arquivo e menor que a da camada, e isso e esperado.** O teste 14
mediu 11,3 B/s para o bloco M-ario cru em `fecrep 1`. Aqui saem 6,8-7,2 B/s. A
diferenca e o custo do protocolo: preambulo por pacote, cabecalho e CRC do
`xfer`, e o round trip de controle pela serial entre um pacote e o proximo
(cerca de 3 s por pacote, visiveis no log entre "remoto envia tx N" e o "OK"
seguinte). Nao e perda no ar.

## Ressalvas

- **Um arquivo, duas condicoes, sem repeticao.** Cada linha da tabela e uma
  unica transferencia. Zero retransmissoes em 21 pacotes e um resultado forte,
  mas nao mede a taxa de falha por pacote com precisao -- so diz que ela esta
  bem abaixo de 1/21. Para um numero de confiabilidade seria preciso repetir a
  transferencia varias vezes.
- **Nao ha gravacao de audio para este teste.** O `recvfile.py` decodifica ao
  vivo e nao guarda o audio, entao esta pasta tem `log/` em vez de `gravacao/`,
  e nao ha `figuras/` nem `llr/`. Isso e uma lacuna real do ferramental: o unico
  teste da campanha cujo resultado nao pode ser re-pontuado offline e justamente
  o de mais alto nivel. Fica anotado como trabalho futuro (`recvfile.py` guardar
  o audio por pacote, como o `console.py` ja faz em `fec_audio`).
- **`fecrep 1` foi escolhido a partir do teste 14**, que mediu 12 blocos inteiros
  de 12 nos tres pontos de redundancia nesta bancada. Com `fecrep 2` a
  transferencia levaria cerca de 1,7x mais tempo sem nada em troca aqui.
- **`syncsweep off` e obrigatorio neste caminho**, e o proprio `recvfile.py`
  manda o comando no setup: `fecpkt` monta o quadro pelo mesmo `_fec_frame` do
  `fecsend`, e uma ponta com as varreduras ligadas poria 80 ms de tom varrido
  onde o receptor espera os primeiros simbolos de preambulo.
- **Correcao de exibicao feita durante o teste.** A barra de progresso contava
  os bytes recebidos com `xfer.PAYLOAD_SIZE` (32) em vez de `args.packet_size`,
  entao mostrava "672/1334 bytes" ao mesmo tempo que "100% 21/21 pacotes". Era
  so o texto; o arquivo, o CRC e a contagem de pacotes sempre estiveram certos.
  Corrigido em `recvfile.py`. O log de 64 bytes guardado aqui foi gravado
  **antes** da correcao e mostra o defeito; o de 128 bytes tambem, porque a
  corrida ja estava em andamento.
- Commit anotado `02be235-dirty`: a arvore tinha as pastas de resultado nao
  commitadas, a correcao do `capture.py` descrita em `11-MARY-CHORD`, a correcao
  de exibicao acima, e o `capture_a2b.py` novo (que nao participa deste teste).
  O DSP (`modem.py`, `fec.py`, `xfer.py`) esta em `02be235` intacto.

## Arquivos

- `log/pkt64-rep1-B2A.log` e `log/pkt128-rep1-B2A.log` -- a corrida inteira,
  pacote a pacote, com as tentativas
- `arquivo/testcard-original.bmp` -- o que estava na maquina B
- `arquivo/got-B2A.bmp`, `arquivo/got-B2A-128.bmp` -- o que chegou pelo ar
- `resultado.csv` -- uma linha por condicao
