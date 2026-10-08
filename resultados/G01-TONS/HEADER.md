# G01-TONS: tons fixos, um por frequência

Data 2026-10-08, 17:09 a 17:16. Código `c57fc74`. B (Windows) toca cada tom, A (Linux) mede com `tom.py`: alto-falante Realtek no P2, aprimoramentos desligados, a 10 cm do mic e apontado; mic interno, Dmic0 45, Capture 39. Ganho digital do tom conforme o padrão de `tom.py`; 3 repetições de 2 s por frequência, **mediana** das três; "piso" = banda de ±25 Hz da própria frequência medida na mesma gravação sem o tom; "margem" = mediana menos piso. Posição incerta: o PC foi movido em algum momento entre 16:47 (passada A) e 17:17 (C3, já na posição 2), sem hora registrada. 22 frequências: os 16 tons do 16-FSK, o tom de repetição do IFK (3487,5), 400, 550, 4000, 4500, 5000.

Dados em `tons.csv`; `gravacao/` guarda só os 22 json (os wav, 34 MB, ficam em `captures/`, fora do git).

## Números

- Margem sobre o piso: **+38,5 a +76,5 dB**; espalhamento entre as 3 repetições no máximo 0,5 dB.
- Os 16 tons do 16-FSK (888 a 3325 Hz): +56,3 a +76,5 dB (o mais baixo é 888 Hz, +56,3; o mais alto 2350 Hz, +76,5).
- **Tom R do IFK, 3487,5 Hz: +56,3 dB** (mediana -43,9 dBFS, piso -100,2 dBFS). É o tom que o CLAUDE.md diz não ter sido medido acima de 3,5 kHz; aqui foi, e chega.
- **Acima de 4 kHz: 4000 Hz +59,5 dB, 4500 Hz +61,0 dB, 5000 Hz +60,1 dB.** Nenhum colapso. 400 Hz +67,5 dB. O ponto fraco é 550 Hz, +38,5 dB (piso -82,2 dBFS, o mais alto da lista, por ruído da sala).

## O que isto contradiz ou qualifica no CLAUDE.md (nesta bancada)

O CLAUDE.md registra, para a bancada de dois computadores a distância, que acima de 4 kHz a SNR cai para 12 dB (4000 Hz), 8 dB (4500 Hz) e cerca de 0 (5000 Hz), e conclui que ultrassom não é viável com este hardware. **Nesta bancada**, com a caixa Realtek a 10 cm do microfone, esses três pontos têm +59 a +61 dB de margem. Mudaram ao mesmo tempo a distância (10 cm), o alto-falante e o dispositivo de captura, e a causa não foi isolada; os dois lados da comparação também diferem no método (aqui a margem é sobre o piso de uma banda de ±25 Hz). Isto **não** prova que a banda larga funciona no enlace a metros de distância; só mostra que, nesta bancada, não há corte em 4 kHz. Medido por tom isolado (`tonef`), não por varredura, como o CLAUDE.md manda.

Margem sobre o piso da própria gravação não é SNR de decodificação: o piso de 10 cm aqui é o da sala parada na banda de 50 Hz, e o 16-FSK decide por energia relativa entre 16 tons.

## Refazer

    ./venv/bin/python tom.py --port <serial ou socket://...> --freq 3487.5 --secs 2 --trials 3 --label g01-tom-3487.5

(`bloco1b.log` da sessão trazia as 22 linhas; os números estão em `tons.csv`.)
