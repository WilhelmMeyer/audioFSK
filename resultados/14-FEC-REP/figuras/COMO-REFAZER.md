# fec-correcao.png -- como refazer

Figura de artigo (300 dpi, largura de coluna, segura em escala de cinza) feita
de uma gravacao desta campanha, sem numero transcrito a mao. Nao confundir com
as PNGs de diagnostico desta mesma pasta (`*-leitura.png` e os espectrogramas
por gravacao), que sao saida do `resultado.py`.

- **Codigo:** commit `633d15c`, gerada em 2026-09-07. A arvore tinha
  modificacoes nao commitadas nos scripts de figura da `07-MARY-BASE`, de outra
  sessao; `modem.py` e `fec.py`, que sao o que alinha esta figura, estavam como
  no commit.
- **Programa:** `figura_fec.py`, nesta pasta.

O script mora aqui, junto da campanha que mede, e nao na pasta do artigo:
`artigo/figuras/` guarda apenas figuras. Uma execucao grava nos dois lugares,
entao nao ha copia a sincronizar a mao. Ele acha a raiz do repositorio subindo
ate encontrar `modem.py`, logo roda de qualquer pasta.

```bash
./venv/bin/python resultados/14-FEC-REP/figuras/figura_fec.py
```

Aceita `--stem` (uma das quatro gravacoes de repeticao 1), `--recorte` (largura
em bits da faixa ampliada, 96 por omissao), `--inicio` (primeiro bit do
recorte, quando nao se quer a escolha por regra) e `--out` (repetivel).

## A gravacao

`20260903-172504-rep1-B2A`, a que o `HEADER.md` registra com 94,09% de bits.
`figura_fec.STEMS` e uma lista fechada com as quatro gravacoes do ponto de
repeticao 1, e o carregador recusa qualquer outro nome: os pontos de repeticao
2 e 4 gastam outro tempo de ar e carregam outro numero de bits codificados, e
uma delas entrar aqui por descuido daria uma figura correta em forma e falsa em
conteudo.

## De onde vem cada coisa

Nada e estimado a olho e nada e digitado a mao.

- **Os bits enviados** vem de `fec.encode(carga, repeat=1)` sobre o
  `payload_hex` do sidecar: o mesmo caminho do transmissor -- convolucional
  taxa 1/3, repeticao, entrelacamento. Nao sao os bits lidos do audio.
- **As verossimilhancas** vem de `MaryDemodulator.demodulate_soft`, alimentado
  em blocos de 2048 amostras, que e como a campanha foi pontuada. O demodulador
  e estateful e a porta early/late anda de acordo com o que ja consumiu, entao
  alimentar tudo de uma vez daria outro alinhamento.
- **O inicio do bloco** vem de `fec.find_sync`, correlacao da palavra de
  sincronismo sobre o fluxo suave. Contar simbolos nao serve, porque a porta
  early/late consome um numero diferente de amostras por simbolo conforme
  corrige.
- **A mensagem decodificada** vem de `fec.decode`, o caminho de verdade.

## O portao

O bloco tem de decodificar de volta ao `payload_hex` da gravacao, byte a byte,
ou o programa para com `SystemExit`. Uma figura de correcao de erro desenhada
sobre um bloco que nao decodifica nao mostra correcao nenhuma, e a figura nao
teria como avisar.

## Os dois eixos

As tres primeiras faixas partilham o eixo de **indice do bit codificado**, de 0
a 1169. A quarta, a mensagem decodificada, tem eixo proprio em **bytes da
mensagem**, e isso nao e escolha de desenho: `fec.encode` entrelaca depois de
repetir, entao um bit da carga nao mora numa posicao unica do bloco codificado
-- esta espalhado por `fec.interleave_index`, e com repeticao maior que 1 esta
tambem replicado. Desenhar as quatro no mesmo eixo exigiria uma correspondencia
que o codigo nao tem.

## A faixa `erros`

A faixa fina logo abaixo da verossimilhanca marca so as posicoes em que houve
erro, e nao e redundante com a faixa de cima: `CERTO` (`#1B7F79`) e `ERRADO`
(`#C43D2F`) tem luminancia quase igual -- 96 contra 100 de 255 -- entao numa
impressao em escala de cinza a faixa de cima vira uma massa unica e os 69
tracos vermelhos entre 1170 somem. Presenca numa posicao e um canal que nao e
cor. E tambem onde a dispersao dos erros ao longo do bloco se le de relance,
que e o que a figura afirma.

## O recorte

A faixa ampliada nao e escolhida a olho. `Bloco.recorte` toma a janela mais a
esquerda cuja contagem de erros e a esperada para o bloco inteiro,
arredondada -- aqui 96 bits com 6 errados, contra 5,90% no bloco. Uma janela
escolhida pela aparencia mostraria o que o desenhista quis, e o recorte existe
justamente para afirmar que o resto do bloco e assim.

## O que a figura mede

Numeros impressos pela propria execucao:

```
20260903-172504-rep1-B2A, 7,38 s gravados, 48 B de carga, repeticao 1
1170 bits codificados, 69 discordam (5,90%)
modulo medio 0,83 nos errados contra 2,47 nos que conferem
recorte em 171..267, 6 errados
bloco decodificado identico a carga: 48 de 48 bytes
```

## Ressalva sobre a gravacao de repeticao 4

A `20260903-172550-rep4-B2A` **nao** entra nesta figura, apesar de o `HEADER.md`
registra-la com 63,17% de bits certos, que pareceria o contraste ideal. Aquele
numero e um artefato do medidor, nao do canal: o quadro de repeticao 4 tem 4711
bits e a gravacao entrega 6464 valores suaves, mas o quadro so comeca no valor
1836, enquanto `resultado.best_slide` correlaciona em `mode='valid'` e portanto
so avalia deslocamentos de 0 a 1753. O inicio verdadeiro esta fora do alcance da
busca, e o melhor deslocamento *alcancavel* pontua 63,17%. No inicio correto a
concordancia e de 92,22%, em linha com as outras onze gravacoes da campanha, que
batem com esta leitura dentro de 0,3 ponto. A gravacao ficou 83 valores suaves
curta -- a captura terminou antes do fim do quadro -- e e isso, e nao um evento
acustico, o que a torna a linha destoante da tabela.

`align.bit_accuracy` tem a mesma construcao, `mode='valid'` sobre o quadro
inteiro, entao os 64,0% de "relogio travado" que o `HEADER.md` cita como
confirmacao independente nao sao uma segunda regua: sao a mesma limitacao
medida duas vezes. Qualquer gravacao que termine antes do fim do seu quadro
pontua assim nos dois marcadores offline.
