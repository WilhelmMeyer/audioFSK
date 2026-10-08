# G03-LINEARIDADE: tom de 1000 Hz e burst 16-FSK em quatro ganhos

Data 2026-10-08, 17:16 a 17:22. Código `c57fc74`. Bancada: B Windows alto-falante Realtek P2 sem aprimoramentos, 10 cm do mic e apontado -> A mic interno Linux (dispositivo padrão, Mic1), Dmic0 45, Capture 39, túnel SSH. **Posição 2** (a mesma das rodadas r1 a r4): os dois bursts têm o tom anterior a −10,8 e −11,0 dB um símbolo depois, a assinatura da posição 2 (−14,6 dB na posição 1). O PC já tinha sido movido às 17:17.

## C3a: tom de 1000 Hz (`harmonicas.csv`)

Quatro gravações de 4,8 s, o tom nos últimos ~3 s; nível e harmônicas medidos no trecho estável de 1,5 a 4,0 s, FFT com janela Blackman, pico em ±20 Hz de cada harmônica, relativo ao pico da fundamental (dBc).

| ganho digital | nível do tom (rms, dBFS) | margem sobre o piso (`tom.py`) | H2 | H3 | H4 |
|---|---|---|---|---|---|
| 0,125 | -49,0 | +46,4 dB | -36,9 | -54,7 | -64,4 |
| 0,25 | -43,1 | +52,0 dB | -42,9 | -59,7 | -68,0 |
| 0,5 | -37,1 | +58,1 dB | -45,1 | -53,8 | -72,4 |
| 1,0 | -31,1 | +65,8 dB | -38,3 | -55,8 | -64,5 |

- O nível do tom sobe **5,9 / 6,0 / 6,0 dB por dobra** do ganho (previsto: 6,02). A cadeia é linear de 0,125 a 1,0 em amplitude do tom.
- As harmônicas **não crescem com o ganho**. Numa não linearidade (limitador, saturação), H2 e H3 em dBc subiriam com o nível; aqui H2 vai -36,9, -42,9, -45,1, -38,3, e H3 fica entre -53,8 e -59,7. É uma distorção que não depende da amplitude, ou algo na banda de 2 kHz (o alto-falante ou o ruído da sala não foram separados). O que se pode afirmar é só: sem sinal de compressão até o ganho 1,0.
- H2 em -37 a -45 dBc é alto em termos absolutos (cerca de 1 a 1,4 % de amplitude) e vale registrar, mas o 16-FSK usa um tom por vez e não soma as harmônicas na decisão.

## C3b: burst 16-FSK + FEC, `fecrep 1`, 48 B (`resultado.csv`)

| ganho | pico rx | rms rx | bits (melhor deslizamento) | bloco |
|---|---|---|---|---|
| 0,25 | 0,098 | 0,018 | 95,92 % | **não** |
| 0,5 (passada A, F00, 16:47) | 0,22 | 0,051 | 99,67 % | OK |
| 1,0 | 0,361 | 0,069 | 97,00 % | OK |

- Entre 0,25 e 1,0 o rms recebido vai de 0,018 a 0,069 (razão 3,84; previsto 4): linear. O pico do burst chega a 0,36 em ganho 1,0, longe de 1,0: **não há saturação** na cadeia nesta bancada, ao contrário do CLAUDE.md (que pede `gain 0,5` por limitador do alto-falante distante). Aqui o ganho digital não precisa ser o limitador.
- **O ganho não muda o resultado.** Os bits ficam em 96 a 100 % nos três ganhos e o bloco só falha no menor, onde o pico é 0,098 e o sinal fica menos acima do piso. Para comparar com o ganho 0,5 use o F00 da passada A (outra hora, mais próxima: rms 0,051, não 0,035); a linha de 0,5 acima não é do mesmo bloco de tempo, e a razão de rms com ela não vale como teste de linearidade.
- Uma gravação por ganho. Bits de 95,9 % estão na faixa em que o F00 fecha e falha (92,9 % não, 95,5 % não, 95,3 % sim, 98,3 % sim): a falha em 0,25 não separa o efeito do ganho do acaso.
- Achado de bancada: a queda do tom 1 símbolo depois é o que decide o bloco, não o ganho (ver `../RESUMO-CAMPANHA-FINAL.md`).

## Arquivos

`gravacao/` (wav + json dos 2 bursts e dos 4 tons), `resultado.csv`, `harmonicas.csv`, `llr/`, `bits/`, `figuras/` (dos 2 bursts).

## Refazer

    ./venv/bin/python tom.py --port <serial> --freq 1000 --label g03-tom1000-g<g>   # ganho do agente ajustado antes: gain <g>
    ./venv/bin/python capture.py --port <serial> --mode mary --fec --repeat 1 --gain <g> --trials 1 --label g03-burst-g<g>
    ./venv/bin/python resultado.py G03-LINEARIDADE gravacao/*burst*.json --bancada "..."

As harmônicas: FFT Blackman de `s[1,5 s : 4,0 s]` de cada wav de tom, pico em f0*n +-20 Hz dividido pelo pico em 1000 Hz.
