# ganho-mary

- **Quando:** 2026-09-03 11:11:05  (campanha de 3.3 min)
- **Codigo:** commit `2354117-dirty`
- **Camada:** mary, FEC rate 1/3 x1
- **Sincronismo:** varredura nas duas pontas
- **Canal:** auto-captura, enlace `bluetooth`
- **Saida:** `bluez_output.8B:36:58:74:F6:0B`
- **Entrada:** `alsa_input.pci-0000_00_1f.3-platform-skl_hda_dsp_generic.HiFi__Mic1__source`
- **Amostragem:** 48000 Hz, 100 baud
- **Bloco:** 48 bytes de payload
- **Repeticoes:** 6 por condicao, 24 gravacoes ao todo
- **Eixo varrido:** `gain` = 0.2, 0.25, 0.3, 0.38

Calibracao do ponto de operacao. fecrep 1 de proposito: a rate-1/3 sozinha deixa o enlace falhando parte do tempo, que e a unica faixa onde uma diferenca de ganho aparece. Com fecrep 2 todas as condicoes acertam tudo e a varredura nao mede nada.

## Resultado

| gain | n | blocos (gate) | blocos (varredura) | bits (gate) | bits (varredura) | periodo |
|---|---|---|---|---|---|---|
| 0.2 | 6 | 3/6 | 6/6 | 88.2% | 90.8% | 480.00 |
| 0.25 | 6 | 2/6 | 5/6 | 88.1% | 90.7% | 479.96 |
| 0.3 | 6 | 5/6 | 6/6 | 90.1% | 91.5% | 480.00 |
| 0.38 | 6 | 5/6 | 6/6 | 88.2% | 89.9% | 480.01 |

Comparacao pareada, mesmo audio nas duas colunas: a varredura leu mais bits que o gate em 23 de 24 gravacoes.

Nivel recebido: rms 0.101, pico 0.51 (maior 0.70).

## Como ler

Acuracia de bit e sempre medida no melhor deslizamento por forca bruta,
na linha do gate tanto quanto na da varredura. Medir cada uma onde ela
por acaso caiu compara duas reguas, e foi o que uma vez fez a pior
configuracao reportar a maior acuracia. Blocos inteiros fica como o
numero honesto separado: e o que o enlace entregou, e com poucas
gravacoes ele e ruidoso.

## Ressalvas

Auto-captura: alto-falante e microfone na mesma maquina, pelo ar. O ar,
o pente da sala, o limitador e o microfone sao reais. O que falta e
especifico -- com enlace `bluetooth`, a caixa tem cristal proprio e a deriva de taxa de amostragem esta presente, ao custo de um codec com perda que o enlace real nao tem.
Nao misturar corpora de enlaces diferentes na mesma media.

## Arquivos

- `results.csv`, `results.json` -- uma linha por gravacao
- `recordings/` -- wav 32-bit float + json, formato de `recording.py`
- `figures/` -- espectrogramas e o grafico de resumo

Reproduzir a pontuacao sem gravar de novo:

```bash
./venv/bin/python study.py --rescore studies/20260903-111105-ganho-mary
```
