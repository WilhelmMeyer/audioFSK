# H05-ERROS-POR-TOM -- os erros da 16-FSK se concentram em poucos tons?

Pergunta: nas gravações 16-FSK (`mode mary`) da cadeia **linear** de duas
máquinas, os erros de símbolo caem em poucos tons transmitidos ou se espalham
pelos 16? Decide se vale construir um mapa adaptativo de tons que evite os
tons "de sombra".

- **Código:** análise rodada em `835584099dd8` com alterações locais em
  `modem.py`/`fec.py`/`console.py`/`resultado.py`, que durante o trabalho
  viraram o commit `4617b4fd04ab22073b4a4de0c56b776f86a7733a` (HEAD agora).
  Esse commit só **acrescenta** funções ao `modem.py` (`sweep_soft`) e ao
  `fec.py`; `MaryDemodulator`, `spectro.py` e `recording.py` são idênticos
  nos dois, e o script não usa nada do que foi acrescentado. Os números valem
  para os dois commits.
- **Quando:** análise offline em 2026-10-08; gravações de 2026-09-03. Nada foi
  tocado ou gravado.
- **Corpus** (nenhuma com `ifk`; só `mode mary`, `kind fec`):
  - **B->A, 28 gravações, 24 615 símbolos de corpo:** `08-MARY-GAIN` (12;
    ganho 0.25/0.5/0.7/1.0, `fecrep 2`), `14-FEC-REP` (12; `fecrep` 1/2/4,
    ganho 1.0), `12-13-SYNC` (4; bloco de 192 B, `fecrep 2`, varreduras).
    Picos 0.06-0.21: nenhuma perto do limitador.
  - **A->B, 9 gravações, 2 700 símbolos:** `17-SPK-LEVEL-A2B`, só as
    `spk20-*` (caixa de A em 0.20, o joelho linear). As `spk10` (sem sinal) e
    `08-MARY-GAIN-A2B`, `08B`, `16-SPK-A2B` (caixa a 0.45/1.0, cadeia
    comprimindo) ficaram de fora.
  - As direções **nunca** são somadas.

## Método (uma régua para todas as gravações)

1. Sequência transmitida = `spectro.tx_tone_indices(payload, fecrep)`, que
   já devolve o **índice do tom no ar** (`_GRAY[valor]`). Tudo aqui é por tom
   transmitido / frequência, nunca por valor.
2. Início grosso por `spectro.find_start` + `spectro.align_mary`.
3. Relógio congelado no melhor ponto de uma grade período × deslocamento
   (479.70-480.30 amostras/símbolo, passo 0.05; ±24 amostras, passo 4),
   pontuada por argmax bruto no corpo -- a mesma grade em todas. O período
   nominal de 480 deriva até ~100 amostras num quadro de 2450 símbolos entre
   duas máquinas, mais que a guarda de 72; acerto da 1ª e da 2ª metade do
   corpo por gravação está em `por-gravacao.csv`: sem rampa sistemática
   (a pior, `200444-A2B`, vai de 63% para 55%).
4. Decisões finais de `MaryDemodulator(steer=False, skip, period)` com os
   padrões do código (piso corrente, `floor_top=1`): é o que o receptor decide.
5. Conta só o **corpo codificado** (símbolos 120.. até o fim do quadro):
   fora o preâmbulo de dois tons, que inflaria esses dois tons, e a cauda.
6. Hipótese nula por permutação: dentro de cada gravação, embaralha os rótulos
   de tom mantendo quais símbolos erraram. Com 16 estimativas ruidosas os 3
   piores sempre passam de 3/16; a nula diz quanto.

## Resultado

| | B->A | A->B |
|---|---|---|
| SER geral | **9.9%** | **26.4%** |
| erros em que saiu o tom do símbolo anterior (ISI, mapa não resolve) | 28% | 28% |
| 3 piores tons | 1538, 1700, 2025 Hz | 1050, 3162, 2675 Hz |
| fração dos erros nos 3 piores (uniforme 18.8%) | **49.1%** (nula 20.7%, p95 21.5%) | **48.9%** (nula 21.9%, p95 23.8%) |
| 5 piores | + 2675, 1862 | + 1212, 2188 |
| fração dos erros nos 5 piores (uniforme 31.2%) | **70.0%** (nula 33.9%) | **70.2%** (nula 35.4%) |
| SER sem os 3 piores, in-sample | 6.2% | 16.7% |
| SER sem os 5 piores, in-sample | 4.3% | 11.4% |

Concentração forte e muito além da nula nas duas direções. SER por tom em
`por-tom.csv` e na figura `fig-ser-por-tom.png`: em B->A vai de 0.1% (1375,
3325 Hz) a 31% (1538 Hz); em A->B de 0% (1700 Hz) a 82% (1050 Hz). Os tons
ruins não são confundidos com um vizinho só (`confusao-*.csv`); em A->B os
erros caem sobretudo em 1212/1375 Hz, que têm taxa de vitória falsa de
5.7%/4.7% contra ~1% nos outros.

### O tom ruim é estável? Dentro da sessão sim; entre sessões, não

| conjunto | Spearman médio entre gravações (SER por tom) | 3 piores |
|---|---|---|
| B->A, tudo junto | 0.21 (nula 0.00) | sobreposição média dos 3 piores 0.94 (acaso 0.56) |
| `14-FEC-REP` | 0.91 | 1538, 1700, 1862 |
| `12-13-SYNC` | 0.82 | 2025, 2675, 2512 |
| `08-MARY-GAIN` | 0.25 (ganho varia 4x, SER baixa) | 2675, 2838, 2188 |
| A->B `17-SPK-LEVEL` | 0.77 | 1050, 3162, 2675 |

As três sessões B->A foram gravadas no mesmo dia, entre 16:29 e 17:27, mesmas
máquinas, e os piores tons **mudam** de uma para outra. Isso decide o tipo de
mapa:

- **Mapa fixo, aprendido em outras sessões** (fora-uma-campanha, B->A):
  piora ou não muda -- 6.4%->6.6%, 14.7%->17.8%, 8.4%->10.4% com os 3 piores
  das outras duas sessões. Spearman treino/teste -0.10 a 0.38.
- **Mapa de contrato, medido na própria sessão**: piores tons de **uma**
  gravação (300 a 2320 símbolos de corpo; cada gravação da sessão por vez), aplicados
  às demais da mesma sessão. Média (faixa entre as escolhas de treino):

  | sessão | SER hoje | sem os 3 piores | sem os 5 piores |
  |---|---|---|---|
  | B->A `14-FEC-REP` | 14.7% | **2.0%** (1.6-4.4) | 0.6% (0.5-1.4) |
  | B->A `12-13-SYNC` | 8.4% | **3.6%** (2.6-4.7) | 1.3% (0.5-2.1) |
  | B->A `08-MARY-GAIN` | 6.4% | 5.6% (4.3-7.6) | 4.8% (3.4-7.3) |
  | A->B `17-SPK-LEVEL` | 26.4% | **18.1%** (16.0-20.3) | 13.1% (11.3-16.3) |

  Treinando só na primeira gravação, em ordem cronológica: 14.8%->1.8%,
  8.7%->2.7%, 6.2%->5.4%, 27.2%->17.5%.
- Validação cruzada por gravação misturando sessões (400 partições):
  B->A 9.9% -> 7.4% (3 piores), 5.5% (5); A->B 26.4% -> 17.2% / 11.8%.

## Ressalvas

- **O contrafactual é otimista.** "SER com o mapa" = SER dos 13 (ou 11) tons
  que sobram, isto é, supõe que os tons de reposição se comportam como a
  média dos bons. Não conta que tirar um tom ruim também remove as vitórias
  falsas dele, nem que as frequências de reposição (fora da grade atual, ou
  com espaçamento menor) não foram medidas. Um 16-FSK precisa de 16 tons:
  "evitar" é trocar de frequência, não descartar.
- 28% dos erros, nas duas direções, são o tom do símbolo anterior (ISI);
  nenhum mapa de tons resolve esses, e eles também se concentram nos tons
  ruins (barras claras da figura).
- A->B tem uma sessão só, 9 gravações curtas (~300 símbolos de corpo, ~19 por
  tom por gravação): a estabilidade entre sessões lá não pode ser medida.
- Relógio de força bruta sabendo a resposta: é um teto de sincronismo, não o
  que o gate entrega. A SER aqui é a do detector com sincronismo ideal.
- Cada gravação tem payload próprio (todos os `payload_hex` distintos), então
  a estabilidade dentro da sessão não é a mesma sequência de tons repetida.
- As três sessões B->A não registram mudança de bancada (mesma caixa AL-667 a
  ~60%, mesmo microfone e ganho de captura) mas foram montadas em momentos
  diferentes do dia; não dá para separar "o tempo passou" de "alguém mexeu na
  caixa/posição". Os vales do pente (CLAUDE.md) mudam com a geometria, e isso
  é consistente com os tons ruins se moverem entre sessões.
- `08-MARY-GAIN` mistura quatro ganhos; dentro dela o tom pior pode estar
  mudando com o nível, o que também conta contra um mapa fixo.

## Veredito

Os erros se concentram: 3 tons levam ~49% e 5 tons ~70% dos erros, nas duas
direções, muito acima do acaso. Mas os tons ruins mudam de sessão para sessão,
então só um mapa **medido no contrato de cada sessão** paga; um mapa fixo
piora. Com essa medição (uma gravação de sondagem basta), o otimista é cair, em
B->A, de 8-15% para 2-4% nas duas sessões com SER alta (e quase nada na de
SER baixa), e em A->B de 26% para ~18% (3 tons) ou ~13% (5 tons) -- antes
de pagar o tempo de ar da sondagem e sem contar os 28% de erros que são ISI.

Arquivos: `erros_por_tom.py` (script), `simbolos.json` (sequências por
gravação), `por-gravacao.csv`, `por-tom.csv`, `confusao-B2A.csv`,
`confusao-A2B.csv`, `resultado.json`, `saida.txt`, `fig-ser-por-tom.png`.
Como refazer: `COMO-REFAZER.md`.
