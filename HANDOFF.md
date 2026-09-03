# Handoff -- campanha de medidas do link acustico

Estado em 2026-09-03 17:07. O plano completo dos testes esta em `TESTES.md`:
tabela de recursos, o que cada teste faz, e quais recursos existem em cada
camada. Leia ele e o `CLAUDE.md` antes de comecar.

## A bancada

| ponta | saida | entrada |
|---|---|---|
| **A** (Linux, console, tem teclado) | caixa Bluetooth `41:42:2B:14:D4:2A`, indice 20 | microfone interno Mic1 / Dmic0, indice PortAudio 26 |
| **B** (Windows, agent, headless) | caixa Bluetooth `AL-667`, padrao do sistema, volume ~60% | microfone interno |

- Cabo serial em `/dev/ttyUSB0`, 115200 baud. So controle, nunca dado.
- Ganho de captura em A: `Dmic0 45` (-5 dB), `Capture 39` (+12 dB).
- Ganho de transmissao em B: parametro `gain` do `capture.py`, tipicamente 1.0.
- **As duas maquinas rodam o commit `02be235`.**

Toda medida ate agora e no sentido **B -> A**: B transmite, A grava. O sentido
A -> B nunca foi medido.

## Ferramentas

```bash
./venv/bin/python capture.py --port /dev/ttyUSB0 --device 26 --mode mary --fec \
    --repeat 2 --gain 1.0 --bytes 48 --trials 3 --label <rotulo> --out <pasta>
./venv/bin/python bench.py <pasta>      # blocos inteiros por gravacao
./venv/bin/python align.py <pasta>      # acurácia de bits, varias leituras do mesmo audio
./venv/bin/python spectro.py <json> --fundido --win 480 -o <png>
./venv/bin/python rcmd.py --port /dev/ttyUSB0 "status"   # comandos ao agent, sem REPL
```

`capture.py` tambem aceita `--gap`, `--band`, `--chord`, `--parallel`,
`--sync-chirp`, `--mode fsk|mfsk|mary`.

## O que ja foi medido

Pastas prontas em `resultados/`, cada uma com `HEADER.md`, `resultado.csv`,
`gravacao/` e `figuras/`.

| teste | condicao | resultado |
|---|---|---|
| 01 `LVL-BASE` | piso de ruido, nada transmitindo | A: -52,5 dBFS (banda util 550-3600 Hz: -62,6). B: mediana -53,9 dBFS |
| 02 `LVL-TONE` | tom de 1700 Hz, 3 trials, mediana | B->A: +57,3 dB de margem. A->B: +27,6 dB. **Os dois sentidos funcionam** |
| 03 `CH-CHIRP` | varredura 300-6000 Hz | SNR negativa em quase toda a banda; contradiz o tom pisado em 77 dB. **Gravacao existe, pasta NAO montada** |
| 04 `FSK-BASE` | Bell 202, 1200 baud, sem FEC | 2,8% dos bytes, nenhum bloco, `SEM SYNC` nas seis leituras |
| 05 `MFSK-VOTE` | MFSK votado, `fecrep 2`, ganho 0.8 | 1 bloco inteiro de 3 |
| 06 `MFSK-PAR` | MFSK paralelo, `fecrep 2`, ganhos 0.8 e 1.0 | nenhum bloco inteiro em 6 |
| 07 `MARY-BASE` | M-ario, `fecrep 2`, cadeia linear | **3 blocos inteiros de 3** |
| 08 `MARY-GAIN` | ganhos 1.0 / 0.7 / 0.5 / 0.25 | 11 blocos de 12; sem tendencia com o ganho |
| 09 `MARY-GAP` | `marygap` 0 / 0,15 / 0,30 | bits 99,6% / 98,0% / 88,1%. 9 blocos de 9. **Gravacoes em `captures-gap/`, pasta NAO montada** |
| 10 `MARY-BAND` | `maryband` 0 / 20 / 40 Hz | bits 99,8% / 99,9% / 99,9%. 9 blocos de 9. **Gravacoes em `captures-band/`, pasta NAO montada** |
| 12-13 `SYNC` | bloco de 192 B, varreduras ligadas | gate 95,3% e 4/4; duas varreduras 78,1% e 0/4 |

Os testes 05, 06 e as duas primeiras baterias do 07 foram medidos antes de a
cadeia ser corrigida, e o `HEADER.md` de cada um diz isso. O 05 usou a caixa
antiga da maquina B, que foi trocada depois.

## Cada teste gera uma pasta

**Todo teste termina com `resultados/<NOME-TESTE>/` no disco.** Um numero solto
numa tabela nao e reproduzivel: uma acuracia de bits fala do decodificador
tanto quanto do canal, e este decodificador muda toda semana.

```
resultados/<NOME-TESTE>/
  HEADER.md          commit do codigo, data, bancada, ajustes fixos, trials,
                     o resultado em tabela, a leitura, e as ressalvas
  gravacao/          o .wav float32 e o .json irmao de cada trial
  figuras/           espectro por gravacao; nas M-arias tambem o painel de
                     leitura (`spectro.py --fundido --win 480`)
  resultado.csv      uma linha por trial
```

Siga o formato de `resultados/07-MARY-BASE/` e `resultados/08-MARY-GAIN/`. O
`HEADER.md` abre pelo commit. Ressalva que muda a leitura do numero vai escrita,
nao omitida -- por exemplo se a cadeia estava saturando, ou se o corpus e de
outra caixa de som.

## O que falta

### Pastas de testes ja medidos

As gravacoes existem; falta montar a pasta.

1. `resultados/03-CH-CHIRP/` -- gravacao em `captures/20260903-154600-ch-chirp-B2A.*`
2. `resultados/09-MARY-GAP/` -- gravacoes em `captures-gap/`, numeros na tabela acima
3. `resultados/10-MARY-BAND/` -- gravacoes em `captures-band/`, numeros na tabela acima

### Testes B -> A que faltam

4. **11 `MARY-CHORD`** -- `capture.py --chord`, nibble como 3 tons em vez de 1.
   Contra o padrao (1 tom). Os DOIS lados precisam do mesmo ajuste.
5. **14 `FEC-REP`** -- `capture.py --repeat 1`, `2`, `4`. Redundancia e
   propriedade do link e nunca foi remedida nesta bancada.
6. **15 `PKT-ARQ`** -- arquivo inteiro por `recvfile.py`. E a parte que hoje
   nao funciona: 1 pacote de 21 na bancada antiga.

### Sentido A -> B, inteiro

Nenhum teste foi medido neste sentido. As duas cadeias sao fisicamente
diferentes -- caixas e microfones distintos -- entao uma nao se deduz da outra.
Repetir, neste sentido, todos os que valem:

7. **01 `LVL-BASE`** -- piso do microfone de B
8. **02 `LVL-TONE`** -- ja tem uma medida por `meas` (razao +24,2 dB), mas sem
   gravacao; refazer com gravacao para ficar na mesma regua do outro sentido
9. **04 `FSK-BASE`**
10. **05 `MFSK-VOTE`**
11. **06 `MFSK-PAR`**
12. **07 `MARY-BASE`**
13. **08 `MARY-GAIN`** -- o ponto de operacao desta cadeia e outro; o `gain`
    fica no `console.py` de A, e o volume da caixa de A e a outra alavanca
14. **09 `MARY-GAP`**, **10 `MARY-BAND`**, **11 `MARY-CHORD`**
15. **12-13 `SYNC`** -- bloco de 192 bytes, `syncsweep on` nos dois lados
16. **14 `FEC-REP`**

**Como se mede A -> B.** O `capture.py` so sabe fazer B -> A. Neste sentido o
caminho e: `grave <segundos> [rotulo]` na maquina B pelo cabo serial, transmitir
daqui, e depois `baixa <stem>` no console para trazer o par WAV+JSON. Os dois
comandos existem em `02be235`. O resultado e o mesmo par de arquivos que o
`capture.py` produz, entao `bench.py`, `align.py`, `spectro.py` e `resultado.py`
pontuam sem saber a diferenca.

A 115200 baud uma gravacao de 10 s leva ~115 s para atravessar o cabo; a 921600,
~14 s. O baud e parametro dos dois lados (`--sync-baud`); se o adaptador nao
segurar a taxa alta, o fallback lento continua valendo.

## Coisas que quebram se voce nao souber

**O microfone de A as vezes nao acorda.** Logo depois de outro processo soltar
o dispositivo, ele pode entregar nada ou blocos de zero exato. O `capture.py`
tem guarda: espera audio de verdade por 3 s e aborta alto. Se abortar, esperar
4 s e repetir aquele ponto. Aconteceu em varios pontos de varredura.

**Bloco de zero exato nao e sala silenciosa, e fonte ausente.** No Linux a
causa foi a fonte MUTED no PipeWire (`wpctl status`) enquanto o `amixer`
mostrava ela aberta. Custou uma medida que reportou uma sala 10 dB mais quieta
do que ela e.

**A cadeia satura em dois lugares e isso ja falseou dois testes.** Na saida de
B (caixa Bluetooth no volume maximo entra em limitador: cortar o ganho digital
pela metade nao muda o que sai) e na entrada de A (conversor no teto). O teste
de linearidade e barato: gravar o mesmo bloco em ganho 1.0, 0.5 e 0.25 e ver
se o rms recebido cai proporcional. Hoje cai, com residuo de ~17% por passo.

**`marygap`, `maryband`, `marychord`, `fecrep`, `fecpar` e `syncsweep` tem que
ser iguais nos dois lados.** Uma divergencia e indetectavel no decodificador:
vira lixo que falha no CRC e le como canal ruim. O `capture.py` manda todos ao
agent no inicio de cada rodada.

**`--sync-chirp` precisa carimbar `sync_span_symbols` no JSON**, senao o
`align.py` nem procura o par de varreduras. Ja esta feito no `capture.py`.

**Blocos recuperados e uma medida ruim para escolher parametro fino.** Use
acuracia de bits do `align.py`, que e estavel, e deixe blocos como numero
honesto separado. Foi assim que o teste 08 mostrou que seus dois "fracassos"
eram colapso de sincronismo, com 96-97% dos bits certos.

**Conversa na sala contamina medida de piso.** Voz ocupa 100-3000 Hz. Uma
gravacao de piso com fala dentro reportou -40,4 dBFS onde a sala estava a
-52,5.

## Codigo

Main em `02be235`, mesmo commit nas duas maquinas. Quatro branches existem em
worktrees separadas e **nenhum esta mergeado**:

- `feat/mary-8n1-mfsk-frozen` -- enquadramento 8N1 no caminho de bytes do
  M-ario. Muda protocolo; as duas maquinas tem que subir juntas.
- `feat/clock-tracking` (worktree `/home/willj/audioFSK-clk`, commit `d2a3ddc`)
  -- conserto do `find_sync`, que hoje escolhe o candidato errado. Nas 30
  gravacoes M-arias de hoje: regra atual 20/30 blocos, correlacao mole 25/30,
  mole mais coerencia 29/30. **Mergear isso muda a contagem de blocos de todos
  os testes ja feitos**, entao o corpus inteiro precisa ser repontuado depois
  -- o que e barato, porque a pontuacao e offline e o audio esta guardado.

Uma sessao chamada `desenvolvimento` trabalha o codigo em worktrees separadas e
esta sob embargo de hardware: ela nao usa audio, microfone, caixa nem
`/dev/ttyUSB0`.
