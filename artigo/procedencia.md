<!--
PROCEDENCIA. De onde veio cada citacao e cada numero das secoes ja redigidas do artigo.
Escrito em 2026-09-07, ao fim da sessao que redigiu a introducao, a 2.1 e a 2.2, a pedido do autor:
"verifique se tudo o que foi feito nessa sessao e rastreavel".
Nao e resumo da sessao, e o rastro. Cada linha diz a fonte e se ela foi CONFERIDA, e como conferir de novo.
Ler junto com referencias.md, que tem as entradas ABNT e onde cada PDF foi obtido.
-->

# Procedência do que está escrito

## Como esta auditoria foi feita

Os números da 2.2 foram conferidos **importando `modem.py`** e comparando com o texto, não relendo comentários. Os da 2.1 foram conferidos **recalculando a varredura** de `resultados/03-CH-CHIRP-A2B/`. Os das citações vieram de PDF lido, nunca de resumo de busca.

## Citações: onze ocorrências, quatro fontes

Todas as quatro têm entrada ABNT em `referencias.md` e **todas foram lidas em PDF**. Nenhuma fonte não lida entrou no texto.

| fonte | onde é citada | o que sustenta |
|---|---|---|
| FINNEGAN; BENSON (2014) | introdução, 1× | tons 1200/2200 Hz, 1200 símbolos/s, origem AT&T |
| WU (2023) | introdução, 1× | HART sobre a malha de 4 a 20 mA, FSK a 1200 bps |
| LOPES; AGUIAR (2001) | introdução 1×, 2.1 1×, 2.2 2× | reflexões e amplitude; as duas famílias M-árias; detecção não coerente |
| PUTZ *et al.* (2026) | introdução 1×, 2.1 4× | 87000×, dezenas de ms, banda de 22 kHz, 75% do volume, ruído ambiente |

As frases exatas de origem, em inglês, estão nos comentários da introdução e da 2.1, dentro do próprio `artigo_modem.md`.

**Falha de rastreabilidade conhecida:** os PDFs estão em `artigo/referencias-pdf/`, que é ignorada pelo git por serem textos de terceiros. Quem clonar não os tem. As URLs estão em `referencias.md`, e três das oito fontes levantadas ficam atrás de assinatura.

## Números da 2.2: 21 de 21 conferidos contra o código

Conferidos em 2026-09-07 importando `modem.py` e lendo os *defaults* das assinaturas, não constantes de módulo. Zero divergências.

Cobre: tons 1200/2200 Hz e 1200 baud da 2-FSK; centro do discriminador em 1700 Hz e atraso de 7 amostras a 48 kHz; cinco pares, dez tons, 200 Hz dentro do par, limiar de presença 1,3, 100 baud; médias dos acordes em 1620 e 1660 Hz; os pares 0, 2 e 4 com o tom grave valendo 0; dezesseis tons de 888 a 3325 Hz, 4 bits, 100 baud; e o intervalo de guarda.

**Correção feita nesta sessão:** o guarda é **15%**, não 35%. O padrão é `guard=0.15` em `MFSKDemodulator` e `MaryDemodulator`. Os 35% existem só em `loopback_test.py`, num caso ajustado de propósito para reverberação, e em `console.py`, numa varredura de diagnóstico. **O `CLAUDE.md` da raiz ainda descreve os 35% como se fossem o comportamento entregue, e não foi corrigido.**

Única imprecisão remanescente, pequena: o texto diz "espaçados 162 Hz" e o espaçamento real alterna 162 e 163 Hz por arredondamento.

## Números da 2.1: dois NÃO se sustentam

Da literatura, todos conferidos em PDF lido: 343 m/s, 44,1 e 48 kHz, 22 kHz, 4 kHz, 75% do volume máximo, dezenas de milissegundos. **Sólidos.**

Da varredura A→B, recalculados hoje sobre `resultados/03-CH-CHIRP-A2B/gravacao/`, em 114 bins de 50 Hz:

| o texto diz | reproduzido hoje | veredito |
|---|---|---|
| varia 28 dB entre melhor e pior ponto | 27,6 dB | confere |
| degrau entre vizinhos, mediana 2,5 dB | 2,6 dB | confere |
| degrau chega a 13 dB | **10,6 dB** | **não confere** |
| acima de 3500 Hz o nível cai de 12 a 20 dB | **1,8 a 9,3 dB** | **não confere** |

**O "13 dB" é instável, não errado.** Deslocando o início da análise em 480 amostras, 10 ms sobre uma varredura de 6 s, o degrau máximo vai de 10,2 a 13,2 dB e o tom mais fraco de −26,8 a −29,7 dB. Os extremos dependem de onde `channel.find_onset` decide que a varredura começa; a mediana não se move. **Citar mediana é seguro, citar extremo não é.**

**O "12 a 20 dB" contradiz a própria varredura e o próprio comentário da seção**, que já registra que os melhores pontos ficam entre 4,1 e 4,4 kHz. Medido, a faixa de 4000 a 4500 Hz está apenas 1,8 dB abaixo da faixa útil. Essa frase atravessou três reescritas nesta sessão sem ser conferida, e é o erro que esta auditoria achou.

**Contexto que pesa:** a máquina remota declarou sem lastro, no comentário da seção 4, a banda de 550 a 3500 Hz, o colapso acima de 4 kHz e o descarte do ultrassom. A auditoria dá razão a ela quanto ao colapso acima de 4 kHz.

## Como refazer a conferência dos números da 2.1

Duas coisas impedem hoje, e as duas são pequenas:

1. **`figura_canal.py` não lê FLAC.** Ele chama `recording.read_wav`, e o repositório passou a arquivar as gravações em FLAC. `recording.read_flac` existe e resolve; falta o desvio por extensão. O WAV float32 original era local e não está versionado.
2. **`soundfile` está em `requirements.txt` mas não está instalado nesta venv.** Sem ele não se lê o FLAC. `venv/Scripts/python.exe -m pip install -r requirements.txt` resolve.

Contornando as duas, a conferência é:

```python
import json, numpy as np, channel, modem, recording
base, stem = "resultados/03-CH-CHIRP-A2B/gravacao", "20260903-175426-ch-chirp-A2B"
meta = json.load(open(f"{base}/{stem}.json"))
s = recording.read_flac(f"{base}/{stem}.flac")
f0, f1, secs = meta["chirp"]; fs = meta["fs"]
rows = channel.response(s[channel.find_onset(s, fs):], fs, f0, f1, secs, 114)
pico = max(r[1] for r in rows)
freq = np.array([r[0] for r in rows])
niv = np.array([20*np.log10(max(r[1], 1e-30)/pico) for r in rows])
faixa = (freq >= 550) & (freq <= 3500)
print(niv[faixa].max() - niv[faixa].min())            # excursao
deg = np.abs(np.diff(niv[faixa]))
print(np.median(deg), np.percentile(deg, 90), deg.max())
```

## O que fica pendente

- Decidir o "13 dB" e o "12 a 20 dB" da 2.1. O primeiro vira "chega a mais de 10 dB" ou sai; o segundo não tem como ficar como está.
- Corrigir os 35% para 15% no `CLAUDE.md` da raiz.
- Resolver as quatro contradições entre a 2.1 e a seção 4, listadas no comentário da 2.1.
- `figura_canal.py` lendo FLAC, e `soundfile` instalado, sem o que nenhum número da 2.1 se reconfere.
