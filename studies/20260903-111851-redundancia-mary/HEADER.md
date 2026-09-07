# redundancia-mary

- **Quando:** 2026-09-03 11:18:51  (campanha de 3.8 min)
- **Codigo:** commit `2354117-dirty`
- **Camada:** mary, FEC rate 1/3 x2
- **Sincronismo:** varredura nas duas pontas
- **Canal:** auto-captura, enlace `bluetooth`
- **Saida:** `bluez_output.8B:36:58:74:F6:0B`
- **Entrada:** `alsa_input.pci-0000_00_1f.3-platform-skl_hda_dsp_generic.HiFi__Mic1__source`
- **Amostragem:** 48000 Hz, 100 baud
- **Bloco:** 48 bytes de payload
- **Repeticoes:** 12 por condicao, 24 gravacoes ao todo
- **Eixo varrido:** `repeat` = 1, 2

Quanta redundancia o enlace precisa, agora que o ponto de operacao esta calibrado. A resposta anterior -- rate 1/3 sozinha nao recupera praticamente nada -- foi medida a um ganho que saturava, entao vale remedir. fecrep 1 custa metade do tempo de ar de fecrep 2.

## Resultado

| repeat | n | blocos (gate) | blocos (varredura) | bits (gate) | bits (varredura) | periodo |
|---|---|---|---|---|---|---|
| 1 | 12 | 9/12 | 12/12 | 88.9% | 91.3% | 479.98 |
| 2 | 12 | 8/12 | 12/12 | 88.9% | 90.8% | 480.01 |

Comparacao pareada, mesmo audio nas duas colunas: a varredura leu mais bits que o gate em 24 de 24 gravacoes.

Nivel recebido: rms 0.111, pico 0.55 (maior 0.65).

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
./venv/bin/python study.py --rescore studies/20260903-111851-redundancia-mary
```
