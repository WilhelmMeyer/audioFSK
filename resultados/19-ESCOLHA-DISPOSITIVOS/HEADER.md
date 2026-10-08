# 19 — Qual direção usar: Windows → Linux ou Linux → Windows

Commit do código: `b722110`. Data: 2026-10-08.

## O que foi medido

Relação sinal/ruído por tom nas 16 frequências do M-ary (888–3325 Hz), em dB acima
da mesma frequência em silêncio, mediana de três voltas. `sonda.py` gera, toca e
pontua; `roda.sh` faz uma rodada (os dois microfones gravam, um alto-falante toca),
controlando o Windows por SSH via Tailscale, sem cabo serial.

- Windows: notebook `desktop-4rfdqjo`, caixa AL-1888 **no cabo P2** (saída
  "Speakers/Headphones (Realtek)"), microfone interno Realtek.
- Linux: alto-falante interno (`pipewire`, sink padrão Speaker), microfone
  Digital Microphone (Dmic0 em +1 dB).
- Ganho digital 0.3 nos dois lados; volumes do sistema como estavam.
- Uma rodada por direção.

## Resultado (pares cruzados, que são os que valem para o link)

| direção | pior tom | mediana | tons < 10 dB | pico recebido |
|---|---|---|---|---|
| **Windows (caixa P2) → mic Linux** | **40.7 dB** | **46.0 dB** | 0 | 0.181 |
| Linux (alto-falante interno) → mic Windows | 26.5 dB | 34.6 dB | 0 | 0.100 |

Windows → Linux ganha por 14 dB no pior tom e 11 dB na mediana. Nenhuma
gravação satura.

Os pares do mesmo notebook (`*-micwin` com a caixa do Windows, `*-miclinux` com o
alto-falante do Linux) estão em `resultados.jsonl` e não entram na decisão: o
microfone está colado na fonte. Um detalhe deles: o microfone do Windows leu o
tom de 888 Hz da caixa ao lado **abaixo** do silêncio (−4.4 dB), o que sugere
processamento de voz (supressão de ruído) no microfone do Windows. Não
verificado; é mais um motivo para o Windows não ser o lado que recebe.

## Ressalvas

- Uma rodada por direção. A diferença (14 dB) é muito maior que a variação entre
  voltas, mas é uma sala num momento.
- A AL-1888 por Bluetooth no Windows não foi medida: a ligação caía
  repetidamente, e a causa não foi isolada.

## Como refazer

    cd resultados/19-ESCOLHA-DISPOSITIVOS
    scp sonda.py Home@100.114.48.25:sonda.py
    ./roda.sh wl-caixa win "Speakers/Headphones (Realtek"
    ./roda.sh lw-interno linux pipewire
    for f in gravacoes/*.wav; do ../../venv/bin/python sonda.py score $f; done > resultados.jsonl
