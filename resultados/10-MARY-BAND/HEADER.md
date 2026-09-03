# 10-MARY-BAND -- largura da janela de medida por tom

- **Codigo:** commit `02be235` (main).
- **Quando:** 2026-09-03, 17:05-17:07.
- **Camada:** M-ario, 16 tons, `fecrep 2`, com FEC (Viterbi de decisao suave).
  `maryband` variando; todo o resto igual a 07-MARY-BASE.
- **Direcao:** B -> A. B = Windows, caixa Bluetooth AL-667 a ~60% de volume.
  A = Linux, microfone interno Mic1/Dmic0 indice PortAudio 26, ganho de
  captura Dmic0 45 (-5 dB), Capture 39 (+12 dB). Cabo serial /dev/ttyUSB0 so
  controle.
- **Payload:** 48 bytes aleatorios, tres pontos de banda, 3 trials cada.

Pontuacao offline por `resultado.py` (`bench.py` e `align.py` rodados a
parte para reconferir, ver "Reconfirmacao" abaixo). Figuras em `figuras/`.

## Resultado

| band (Hz) | gravacoes | bits (melhor deslize) | pico | bloco |
|---|---|---|---|---|
| 0 (`band0`) | 170535/170545/170556 | 99,70% / 100,00% / 99,83% | 0,17/0,18/0,20 | 3 de 3 |
| 20 (`band20`) | 170613/170624/170634 | 99,79% / 99,83% / 100,00% | 0,18/0,18/0,19 | 3 de 3 |
| 40 (`band40`) | 170651/170702/170712 | 99,83% / 100,00% / 100,00% | 0,17/0,18/0,19 | 3 de 3 |

Media por ponto: **band 0 = 99,84%**, **band 20 = 99,87%**, **band 40 =
99,94%** dos bits. **9 blocos inteiros de 9** nos tres pontos.

## Reconfirmacao

Numero conhecido do handoff (99,8% / 99,9% / 99,9%, 9 blocos de 9) foi
remedido do zero por este agente, offline, sem hardware:

- `./venv/bin/python resultado.py 10-MARY-BAND captures-band ...` -- acerto
  de bits por gravacao no melhor deslize por forca bruta (tabela acima):
  **99,84% / 99,87% / 99,94%**, batendo com o handoff a menos de 0,1 ponto.
- `./venv/bin/python align.py captures-band` -- media global do gate: 99,9%
  dos bits, 9/9 blocos; relogio travado no melhor offset, dividindo pelo
  ganho ou pelo ruido por tom: 100,0% nas tres, 9/9. Coerente com a tabela
  acima -- neste corpus, ao contrario do 09-MARY-GAP, o gate ao vivo ja
  praticamente empata com o melhor deslize por forca bruta.
- `./venv/bin/python bench.py captures-band` -- caminho FEC ao vivo (Viterbi
  soft real, sync por correlacao, CRC): **9 gravacoes, 9 blocos inteiros,
  100%**. Confirma a coluna "bloco" acima.

Os tres numeros da tabela por ponto batem com o handoff. Nao houve
divergencia a reportar.

## Leitura

**A largura da janela de medida por tom nao mexe em nada nesta faixa.** De
0 a 40 Hz de banda a acurácia de bits fica dentro de 0,1 ponto (99,84% a
99,94%) e blocos inteiros empatam em 3 de 3 em todos os pontos -- ao
contrario do 09-MARY-GAP, aqui nem os bits nem os blocos mostram tendencia.
Com apenas 9 gravacoes e uma faixa de 0,1 ponto entre os extremos, isto e
indistinguivel de ruido de medida: nao ha evidencia, nesta bancada, de que
alargar a janela de 0 a 40 Hz ajude ou atrapalhe. Nao extrapolar para
valores de banda maiores sem medir.

## Ressalvas

- **Faixa testada e estreita.** So 0/20/40 Hz foram medidos; nada garante
  que a curva continue plana fora desse intervalo, e o proprio `TESTES.md`
  observa que banda estreita demais perde o tom que derivou e larga demais
  deixa entrar ruido do vizinho -- nenhum desses efeitos apareceu aqui
  porque nao se chegou perto dos extremos.
- **9 blocos de 9 nao discrimina.** Com `fecrep 2` e um canal ja limpo (pico
  0,17-0,20, sem saturacao) todos os blocos passam de qualquer forma; quem
  quiser decidir este parametro tem que olhar bits, nao blocos -- e mesmo
  em bits a diferenca aqui e desprezivel.

## Arquivos

- `gravacao/` -- as nove gravacoes, WAV float32 mais JSON
- `llr/` -- saida soft do demodulador (4 colunas por simbolo em M-ario)
- `bits/` -- bits lidos contra bits transmitidos, alinhados no melhor deslize
- `figuras/` -- espectrograma por gravacao (`spectro.py --fundido --win 480`)
- `resultado.csv` -- uma linha por gravacao
