# G02-VARREDURA: resposta em frequência por varredura, 10 cm

Data 2026-10-08, 17:08. Código `c57fc74`. Mesma bancada do G01 (B Realtek P2 -> A mic interno, 10 cm, posição incerta: o PC foi movido entre 16:47 e 17:17, sem hora registrada). `capture.py --chirp "400 4200 10"`, varredura de 400 a 4200 Hz em 10 s, 1,8 s de silêncio depois, mediada em 76 faixas de 50 Hz por `channel.py --bins 76`.

Arquivos: `channel-saida.txt` (saída integral), `resposta.csv` (freq, nível relativo ao melhor ponto, SNR contra a sala em silêncio), `gravacao/` (wav + json).

## Números

- SNR contra a sala em silêncio: **43,5 a 61,3 dB**, mediana 55,1. Melhor faixa: 1925 Hz (61,3 dB). Pior: 625 Hz (43,5).
- Por região, mediana do SNR: 400-1000 Hz 48,8; 1000-2000 Hz 54,1; 2000-3000 Hz 57,6; 3000-3500 Hz 58,0; 3500-4200 Hz 54,5.
- Nível relativo: de 0 a -19,5 dB (faixa de 19,5 dB). Vizinhos de 50 Hz diferem 2,1 dB na mediana e até 10,4 dB no máximo. É a resposta em pente do CLAUDE.md, mas bem mais rasa que os "13-18 dB entre bins vizinhos" medidos a distância.
- Não há colapso em 4 kHz: 3975 Hz tem 59,9 dB de SNR; as faixas acima de 4 kHz ficam em 47,8 a 57,8 dB (até o limite da varredura, 4200 Hz).

## Ressalvas

- O CLAUDE.md alerta que uma varredura relata faixas abaixo do piso onde tons isolados mostram margem enorme (a 1700 Hz, -27 dB contra +50 dB). Aqui não aconteceu: 1675 Hz tem 58,5 dB. Os tons isolados do `G01-TONS` dão margens ainda maiores por serem medidos sobre o piso de uma banda estreita (±25 Hz), não sobre a faixa de 50 Hz da varredura. Use os dois como ordem de grandeza, não como a mesma grandeza.
- `capture.py` abortou com "falhou em g02-varredura" ao final, mas o wav e o json foram gravados e têm 12,1 s (581 632 amostras); a varredura e os 1,8 s de silêncio estão inteiros. A saída do `channel.py` confere.
- Uma gravação, uma posição.

## Refazer

    ./venv/bin/python capture.py --port <serial> --chirp "400 4200 10" --label g02-varredura
    ./venv/bin/python channel.py captures/20261008-170850-g02-varredura.json --bins 76
