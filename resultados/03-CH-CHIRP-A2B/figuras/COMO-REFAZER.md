# varredura.png -- como refazer

Espectrograma de artigo (300 dpi, largura de coluna, cinza) da gravacao desta
pasta. Refaz o `20260903-175426-ch-chirp-A2B.png` do `spectro.py` com
resolucao de frequencia utilizavel: janela de 4096 amostras (11,7 Hz por bin)
contra os ~112 Hz por bin daquela, que engrossavam a rampa a ponto de ela
encostar nos 162 Hz que separam os tons da 16-FSK.

- **Codigo:** commit `668b706`, gerada em 2026-09-07.
- **Programa:** `figura_varredura.py`, nesta pasta.

O script mora aqui, junto da campanha que ele mede, e nao na pasta do artigo:
`artigo/figuras/` guarda apenas as figuras. Uma execucao grava nos dois
lugares, esta pasta e `artigo/figuras/`, entao nao ha copia a sincronizar a
mao. Ele acha a raiz do repositorio subindo ate encontrar `modem.py`, logo
roda de qualquer pasta.

```bash
./venv/bin/python resultados/03-CH-CHIRP-A2B/figuras/figura_varredura.py
```

## O que ele imprimiu nesta geracao

```
[varredura] /home/willj/audioFSK/resultados/03-CH-CHIRP-A2B/figuras/varredura.png, /home/willj/audioFSK/artigo/figuras/varredura.png
    300-6000 Hz em 6,0 s, começando em 1,04 s; gravação de 8,0 s
    janela 4096 amostras: 11,7 Hz por bin, 85,3 ms; salto 512 (10,7 ms)
    largura da crista a -6 dB: mediana 46,9 Hz (23,4 a 281,2), contra 162 Hz entre tons vizinhos da 16-FSK
    invade a separação em 2 de 506 colunas
    2º harmônico: mediana -30,5 dB abaixo da fundamental (-75,6 a -5,4)
    3º harmônico: mediana -42,2 dB abaixo da fundamental (-95,3 a -1,5)
    depois do fim (7,04 s), janela de 512 amostras, banda 5600-6400 Hz, piso da sala -86,7 dBFS:
      -0,05 s  -27,2 dBFS
      +0,00 s  -29,9 dBFS
      +0,05 s  -27,4 dBFS
      +0,10 s  -39,7 dBFS
      +0,20 s  -42,5 dBFS
      +0,30 s  -48,0 dBFS
      +0,50 s  -66,1 dBFS
      +0,80 s  -82,1 dBFS
```

Tres leituras que o `HEADER.md` desta campanha ainda nao registra:

1. A largura da rampa e do sinal, nao do instrumento: mediana de 46,9 Hz a
   -6 dB contra 162 Hz entre tons vizinhos, invadindo essa separacao em 2 de
   506 colunas.
2. A cadeia gera harmonicos, o segundo cerca de 30 dB e o terceiro cerca de
   42 dB abaixo da fundamental.
3. **Depois do fim da rampa o sinal nao cai direto no piso.** Medido com
   janela curta de 512 amostras, para a janela longa da figura nao fabricar
   cauda, a banda 5600-6400 Hz cai cerca de 50 dB em meio segundo e so
   alcanca o piso da sala por volta de 0,8 s. O fade do transmissor e de
   10 ms (`console._chirp`), entao nao e ele. Uma gravacao so nao separa
   sala, caixa Bluetooth e codec, entao isto e cauda medida no receptor, de
   origem nao isolada, e nao autoriza chamar de reverberacao da sala. Fica
   registrado porque conversa mal com a frase "no measurable reverberation"
   do `CLAUDE.md` da raiz, que veio de outra medida.
