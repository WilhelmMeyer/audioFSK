# 09-MARY-GAP -- silencio entre simbolos

- **Codigo:** commit `02be235` (main).
- **Quando:** 2026-09-03, 16:59-17:00.
- **Camada:** M-ario, 16 tons, `fecrep 2`, com FEC (Viterbi de decisao suave).
  `marygap` variando; todo o resto igual a 07-MARY-BASE.
- **Direcao:** B -> A. B = Windows, caixa Bluetooth AL-667 a ~60% de volume.
  A = Linux, microfone interno Mic1/Dmic0 indice PortAudio 26, ganho de
  captura Dmic0 45 (-5 dB), Capture 39 (+12 dB). Cabo serial /dev/ttyUSB0 so
  controle.
- **Payload:** 48 bytes aleatorios, tres pontos de gap, 3 trials cada.

Pontuacao offline por `resultado.py` (`bench.py` e `align.py` rodados a
parte para reconferir, ver "Reconfirmacao" abaixo). Figuras em `figuras/`.

## Resultado

| gap | gravacoes | bits (melhor deslize) | pico | bloco |
|---|---|---|---|---|
| 0,00 (`gap0.0`) | 165900/165910/165921 | 100,00% / 99,41% / 99,41% | 0,26/0,15/0,24 | 3 de 3 |
| 0,15 (`gap0.15`) | 170024/170035/170045 | 94,10% / 99,96% / 99,92% | 0,25/0,18/0,17 | 3 de 3 |
| 0,30 (`gap0.30`) | 165939/165949/170000 | 64,57% / 100,00% / 99,79% | 0,24/0,26/0,18 | 3 de 3 |

Media por ponto: **gap 0,00 = 99,61%**, **gap 0,15 = 97,99%**, **gap 0,30 =
88,12%** dos bits. **9 blocos inteiros de 9** nos tres pontos -- o FEC
absorve a diferenca de bits nesta faixa e nenhum bloco se perde.

## Reconfirmacao

Numero conhecido do handoff (99,6% / 98,0% / 88,1%, 9 blocos de 9) foi
remedido do zero por este agente, offline, sem hardware:

- `./venv/bin/python resultado.py 09-MARY-GAP captures-gap ...` -- acerto de
  bits por gravacao no melhor deslize por forca bruta (tabela acima):
  **99,61% / 97,99% / 88,12%**, batendo com o handoff a menos de 0,1 ponto.
- `./venv/bin/python align.py captures-gap` -- media global (sem separar por
  gap) do gate: 95,2% dos bits, 9/9 blocos; relogio travado no melhor offset
  94,9%, 8/9; travado dividindo pelo ruido por tom 95,2%, 8/9. Essas colunas
  usam a posicao do `find_sync` ao vivo em vez do melhor deslize por trial, e
  por isso nao coincidem numero a numero com a tabela acima -- servem para
  conferir que nao ha colapso de sincronismo escondendo a leitura, nao para
  substituir a tabela.
- `./venv/bin/python bench.py captures-gap` -- caminho FEC ao vivo (Viterbi
  soft real, sync por correlacao, CRC): **9 gravacoes, 9 blocos inteiros,
  100%**. Confirma a coluna "bloco" acima.

Os tres numeros da tabela por ponto batem com o handoff. Nao houve
divergencia a reportar.

## Leitura

**O gap nao se paga.** De 0,00 a 0,30 o ganho em bits e de cerca de 11,5
pontos (99,6% -> 88,1%) -- e o sentido e o inverso do esperado: mais
silencio entre simbolos piorou a leitura em vez de ajudar, ao contrario da
hipotese original de que um gap protegeria contra o tom anterior competindo
com o atual. `marygap 0,30` gasta 30% a mais de tempo de ar por bloco e
entrega bits piores, nao melhores; o unico ponto que puxa a media de 0,30
para baixo e a gravacao `165939`, que caiu para 64,57% por conta propria
(as outras duas do mesmo ponto ficaram em 99-100%) -- o que sugere um
colapso pontual de sincronismo dentro daquele trial, nao um efeito
sistematico do gap em si, mas mesmo descontando esse trial o ponto 0,30
nao supera 0,00 em nenhuma das tres gravacoes. Em blocos inteiros os tres
pontos empatam em 3 de 3 -- o FEC (`fecrep 2`) absorve a diferenca inteira,
entao quem olha so para blocos nao veria custo nem beneficio.

## Ressalvas

- **Amostra pequena.** Tres trials por ponto, e um deles (165939) puxa
  sozinho a media do ponto 0,30 para baixo por quase 12 pontos. Nao dividir
  essa media sem mostrar as tres linhas -- e por isso a tabela por gravacao
  vem antes da media.
- **`bloco_ok` nao discrimina aqui.** Os tres pontos empatam em 9/9 porque
  `fecrep 2` tem folga nesta faixa de erro de bit; a leitura correta usa
  acerto de bits, nao blocos, exatamente pela regra do projeto.

## Arquivos

- `gravacao/` -- as nove gravacoes, WAV float32 mais JSON
- `llr/` -- saida soft do demodulador (4 colunas por simbolo em M-ario)
- `bits/` -- bits lidos contra bits transmitidos, alinhados no melhor deslize
- `figuras/` -- espectrograma por gravacao (`spectro.py --fundido --win 480`)
- `resultado.csv` -- uma linha por gravacao
