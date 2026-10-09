# H06 — enlace negociado pelo ar: primeiras sessões

2026-10-08, noite. Linux (A, chamador, alto-falante interno, `wpctl` 1,00) e Windows (B, ouvinte, `Microfone (Realtek(R) Audio)` MME), ~2 m. Sem cabo: `saudacao.py` nas duas pontas, B rodado por SSH com o `enlace.py` copiado para `~/enlace_teste` (o repositório de lá não foi tocado). O código no fim da noite é o deste commit; as sessões 1 e 2 rodaram versões intermediárias (ver abaixo).

Os WAV não vão para o git (`.gitignore`); ficam nesta pasta na máquina Linux. JSON (com o diário de cada estação) e logs vão.

## Sessões (`sessoes/`, `logs/`)

| sessão | A (Linux) | B (Windows) | resultado |
|---|---|---|---|
| 1 | `20261008-220000-enlace-chamador` | `20261008-215950-enlace-ouvinte` | 56 chamadas, nenhuma ouvida: chegavam a 0,23–0,33 contra o limiar único 0,36 |
| 2 | `20261008-230457-enlace-chamador` | `20261008-230410-enlace-ouvinte` | OLA lento passou 2×, contrato lento, sessão caiu (B desistiu do contrato após 1 turno ilegível) e recomeçou; canal aberto no fim, 19 bytes (o 1º pedaço se perdeu no recomeço) |
| 3 | `20261008-231059-enlace-chamador` | `20261008-231757-enlace-ouvinte` | **completa**: A→B 207/207 bytes (7 blocos, rep2→rep4→2-FSK), B→A 44/44, confirmados em 209 s e 97 s; `got-*-sessao3.bin` |

Entre a 1 e a 2 o microfone do Windows teve os aprimoramentos desligados pelo usuário; a sensibilidade subiu demais (+6,4 dB, 17% das amostras no teto) e foi baixada para −14 dB pelo endpoint (`scripts/micvol.ps1`), silêncio rms 0,004.

## Testes avulsos (`testes/`, `scripts/`)

Linux toca, Windows grava (`grava_tmp.py`), lido offline. `tocado*.wav` é o que foi tocado.

- `rec_tmp`: 1 kHz + 6 chamadas. Chamada a 0,28–0,33, piso 0,10; mais ganho, menos correlação.
- `rec_vol` (MME) / `rec_wdm` (WDM-KS): `toca_rodada.py`, rodada a `wpctl` 1,00 e depois 0,20 / 0,6. Alinhado (`alinhado.py`, só `rec_vol` alinha certo): quadro 0,30, sonda 0,36, chamada 0,20–0,22; OLA 2-FSK 25–35% de bits errados, **um tom de cada par comido** (2350 Hz −5,1 dB ligado/desligado, 93% de erro quando enviado; 1862 Hz 76%). `wpctl` é cúbico: 0,20 ≈ −42 dB, inaudível a 2 m — rodada inválida. As análises de cauda feitas antes do alinhamento correto estavam erradas.
- `rec_lento`: mic saturado, inválido. `rec_lento2` (mic −14 dB): `conhecido.py` nas posições certas — **OLA lento 2/2 CRC ok (9% e 8% de bits)**, 2-FSK 15% falhou, 16-FSK rep2 23% falhou; `le_lento.py` (o caminho da estação) acha as marcas de quadro a 0,23–0,26.

## O que mudou no `enlace.py` por causa disto

Limiar por marca (chamada 0,17, quadro 0,21); abordagem `16-FSK lento` (20 baud, guarda 0,3, rep2) e degrau de dados lento; ouvinte ignora chamada no meio da negociação; com o canal aberto só chamada ≥ 0,30 derruba; canal aberto mudo 120 s recomeça sozinho; espera até 3 repetições em `aguarda_*`; pedaço não confirmado volta à fila num recomeço.

## Em aberto

- **Tráfego simultâneo** na sessão 3 (o usuário ouviu as duas pontas tocando juntas): marcas "ilegíveis" 2 s depois de quadros bons e uma repetição por prazo do lado A. Cruzar as duas gravações para ver quem tocou quando.
- Depois que A parou, B gastou CPU tentando ~14 descritores em cada marca falsa e o relógio dele ficou 320 s atrás do tempo real.
- Um OLA 2-FSK foi declarado ilegível antes de qualquer tentativa (`tentou=[]`), pelo `_calou`.

## Como refazer (comandos exatos da sessão 3)

Windows (B), por SSH a partir do Linux, com o `enlace.py`/`saudacao.py` deste commit copiados para `~/enlace_teste` (depois de um `pull` no Windows dá para rodar direto do repositório):

```bash
scp enlace.py saudacao.py Home@100.114.48.25:enlace_teste/
ssh Home@100.114.48.25 "cd enlace_teste && set PYTHONPATH=C:\Users\Home\WorkSpace\audioFSK&& set \"ENLACE_DEPURA=1\" && ..\Workspace\audioFSK\venv\Scripts\python.exe -u saudacao.py --papel ouvinte --enviar \"oi do B: recebi o chamado e respondo pelo ar\" --receber-em got-B.bin --duracao 640" > enlace-B3.log 2>&1
```

Linux (A), depois que B imprimir `[saudacao] papel ouvinte`:

```bash
ENLACE_DEPURA=1 ./venv/bin/python -u saudacao.py --papel chamador --enviar "<207 bytes>" --receber-em got-A.bin --duracao 615 > enlace-A3.log 2>&1
```

Microfone do Windows (endpoint padrão de captura), ler e ajustar:

```bash
scp resultados/H06-ENLACE-AR/scripts/micvol.ps1 Home@100.114.48.25:micvol.ps1
ssh Home@100.114.48.25 "powershell -NoProfile -ExecutionPolicy Bypass -File micvol.ps1"            # lê
ssh Home@100.114.48.25 "powershell -NoProfile -ExecutionPolicy Bypass -File micvol.ps1 -set -14"   # dB
```

Teste avulso (Linux toca, Windows grava 40 s e devolve):

```bash
scp resultados/H06-ENLACE-AR/scripts/grava_tmp.py Home@100.114.48.25:grava_tmp.py
ssh Home@100.114.48.25 "Workspace\audioFSK\venv\Scripts\python.exe grava_tmp.py 40 rec.npy" &
./venv/bin/python resultados/H06-ENLACE-AR/scripts/toca_lento.py tocado_lento.npy
scp Home@100.114.48.25:rec.npy . && ./venv/bin/python resultados/H06-ENLACE-AR/scripts/le_lento.py rec.npy
```

Os scripts de `scripts/` foram escritos no scratchpad e têm caminhos absolutos dele dentro (`/tmp/claude-1000/...`); ajustar antes de reusar. Simulador do protocolo: `./venv/bin/python simula_enlace.py` (5 cenários, SUCCESS!).
