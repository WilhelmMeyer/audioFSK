# ganho-fio

- **Quando:** 2026-09-03 12:25:22  (campanha de 3.3 min)
- **Codigo:** commit `4b5604b-dirty`
- **Camada:** mary, FEC rate 1/3 x1
- **Sincronismo:** varredura nas duas pontas
- **Canal:** auto-captura, enlace `wired`
- **Saida:** `alsa_output.pci-0000_00_1f.3-platform-skl_hda_dsp_generic.HiFi__Speaker__sink`
- **Entrada:** `alsa_input.pci-0000_00_1f.3-platform-skl_hda_dsp_generic.HiFi__Mic1__source`
- **Amostragem:** 48000 Hz, 100 baud
- **Bloco:** 48 bytes de payload
- **Repeticoes:** 6 por condicao, 24 gravacoes ao todo
- **Eixo varrido:** `gain` = 0.1, 0.2, 0.3, 0.45

Calibracao do ponto de operacao no caminho com fio (alto-falante interno), que e o canal deliberadamente BOM. O corpus anterior foi gravado com o canal degradado de proposito -- ganho acima do teto do limitador -- porque um canal limpo demais nao deixa margem para uma melhoria de sincronismo aparecer. Agora que o sistema existe e foi validado sob degradacao, vale medir o outro extremo.

## Resultado

| gain | n | blocos (gate) | blocos (varredura) | bits (gate) | bits (varredura) | periodo |
|---|---|---|---|---|---|---|
| 0.1 | 6 | 5/6 | 6/6 | 97.4% | 97.1% | 479.87 |
| 0.2 | 6 | 6/6 | 6/6 | 98.6% | 97.9% | 479.82 |
| 0.3 | 6 | 5/6 | 6/6 | 97.6% | 94.5% | 479.94 |
| 0.45 | 6 | 4/6 | 6/6 | 97.7% | 92.8% | 480.00 |

Comparacao pareada, mesmo audio nas duas colunas: a varredura leu mais bits que o gate em 3 de 24 gravacoes.

Nivel recebido: rms 0.104, pico 0.53 (maior 1.00).

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
especifico -- com enlace `wired`, as duas pontas dividem o clock da placa, entao a deriva de taxa de amostragem -- parte do que o gate existe para corrigir -- esta ausente e os numeros de sincronismo saem otimistas.
Nao misturar corpora de enlaces diferentes na mesma media.

## Arquivos

- `results.csv`, `results.json` -- uma linha por gravacao
- `recordings/` -- wav 32-bit float + json, formato de `recording.py`
- `figures/` -- espectrogramas e o grafico de resumo

Reproduzir a pontuacao sem gravar de novo:

```bash
./venv/bin/python study.py --rescore studies/20260903-122522-ganho-fio
```
