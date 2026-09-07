# confirma-fio

- **Quando:** 2026-09-03 12:34:34  (campanha de 1.6 min)
- **Codigo:** commit `4b5604b-dirty`
- **Camada:** mary, FEC rate 1/3 x1
- **Sincronismo:** varredura nas duas pontas
- **Canal:** auto-captura, enlace `wired`
- **Saida:** `alsa_output.pci-0000_00_1f.3-platform-skl_hda_dsp_generic.HiFi__Speaker__sink`
- **Entrada:** `alsa_input.pci-0000_00_1f.3-platform-skl_hda_dsp_generic.HiFi__Mic1__source`
- **Amostragem:** 48000 Hz, 100 baud
- **Bloco:** 48 bytes de payload
- **Repeticoes:** 12 por condicao, 12 gravacoes ao todo
- **Ganho:** 0.2

Repeticao exata da condicao ganho 0.20 / fecrep 1 com fio, para separar duas leituras que discordaram: a varredura de ganho (6 gravacoes) deu 6/6 blocos no gate, e o melhor caso (12 gravacoes, 4 minutos depois, niveis identicos) deu 1/12. A diferenca e grande demais para ser o ruido de amostra pequena, entao ou a sala mudou ou a primeira leitura foi sorte.

## Resultado

| condicao | n | blocos (gate) | blocos (varredura) | bits (gate) | bits (varredura) | periodo |
|---|---|---|---|---|---|---|
| unico | 12 | 3/12 | 11/12 | 95.0% | 94.0% | 479.82 |

Comparacao pareada, mesmo audio nas duas colunas: a varredura leu mais bits que o gate em 4 de 12 gravacoes.

Nivel recebido: rms 0.080, pico 0.36 (maior 0.42).

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
./venv/bin/python study.py --rescore studies/20260903-123434-confirma-fio
```
