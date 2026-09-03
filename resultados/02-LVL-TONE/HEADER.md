# 02-LVL-TONE -- um tom puro, medido na outra ponta

- **Codigo:** commit `0718f2c` mais `ruido.py`, `rcmd.py`, `tom.py`, `resultado.py`
  e `spectro.py` corrigido, nenhum deles commitado ainda
- **Quando:** 2026-09-03 15:24 (B->A) e 15:29 (A->B)
- **Frequencia:** 1700 Hz, 3 s por tom, 3 trials por direcao, mediana
- **A:** Linux, caixa Bluetooth na saida, microfone interno Mic1 (indice 26)
- **B:** Windows, caixa em P2 na saida, microfone interno, ganho de saida 0.8

Mede uma frequencia mandando aquela frequencia. Varredura responde outra
pergunta e ja respondeu errado neste hardware: pos 1700 Hz a -27 dB, o pior
ponto da varredura, onde o tom pisado da +57 dB de margem.

**As duas direcoes foram medidas com reguas diferentes, e nao da para junta-las.**
B->A e uma gravacao aqui, em dBFS contra o piso da mesma banda. A->B e o comando
`meas` do agent, cuja escala em dB vem de uma FFT sem normalizacao -- so a
**razao banda/larga** dele e transportavel. Comparar -21,8 dBFS com +24,2 dB
seria comparar coisas diferentes.

## Resultado

### B -> A (B toca, A grava)

| trial | 1700 Hz | banda larga | pico | margem sobre o piso |
|---|---|---|---|---|
| 1 | -26,5 dBFS | -27,2 | 0,117 | +52,6 dB |
| 2 | -19,4 dBFS | -19,7 | 0,219 | +59,7 dB |
| 3 | -21,8 dBFS | -21,9 | 0,144 | +57,3 dB |

Piso em 1700 Hz: **-79,1 dBFS**. Mediana **-21,8 dBFS**, margem **+57,3 dB**,
espalhamento entre trials **7,1 dB**.

### A -> B (A toca, B mede com `meas`)

| trial | banda | larga | razao |
|---|---|---|---|
| piso | -7,4 | -4,0 | **-3,4 dB** |
| 1 | 44,3 | 20,1 | +24,2 dB |
| 2 | 36,6 | 12,5 | +24,1 dB |
| 3 | 45,0 | 20,8 | +24,2 dB |

Mediana **+24,2 dB**, ganho sobre o piso **+27,6 dB**.

### Harmonicos, na gravacao B->A

| trial | 1700 Hz | 3400 Hz | 5100 Hz |
|---|---|---|---|
| 1 | -26,5 | -62,6 | -75,4 |
| 2 | -19,4 | -62,1 | -77,3 |
| 3 | -21,8 | -61,9 | -75,8 |

## Leitura

**As duas direcoes funcionam, e nivel nao e o problema deste link.** +57 dB de
margem num sentido, +27,6 dB no outro. Era o que precisava ser sabido antes de
gastar tempo em teste de dados: o link ja teve o caso de funcionar so num
sentido, e por motivo que nao era acustico.

**A varredura estava errada sobre 1700 Hz, o canal nao.** O pior ponto do chirp
e o ponto com 57 dB de margem no tom pisado. Regra confirmada mais uma vez.

**No sentido A->B a razao e travada e o nivel nao.** Razao 24,2 / 24,1 / 24,2 dB
-- um decimo de dB. Banda absoluta 44,3 / 36,6 / 45,0 e banda larga 20,1 / 12,5
/ 20,8: **8,4 dB de oscilacao, com as duas andando em bloco.** Ruido somando na
sala nao faz banda estreita e banda larga se moverem juntas com essa fidelidade;
alguma coisa esta multiplicando o sinal inteiro. Controle automatico de ganho no
microfone de B e a explicacao direta, e o piso de B oscilando 18 dB no teste 01
aponta para o mesmo lugar. **Consequencia para o 08 `MARY-GAIN`: calibrar ganho
de transmissao lendo nivel em B nao vai funcionar** -- o AGC come exatamente a
variacao que a calibracao quer ver. Ou se desliga o AGC no Windows, ou aquele
sentido se calibra por taxa de erro.

**O 2o harmonico existe, esta 36-43 dB abaixo do fundamental, e nao acompanha
ele.** -62 dBFS em 3400 Hz nos tres trials (espalhamento 0,7 dB) enquanto o
fundamental varia 7,1 dB. Se a variacao do fundamental fosse ganho no caminho,
o harmonico teria variado junto -- entao no sentido B->A a causa **nao** e a
mesma do sentido A->B. Fica em aberto. O 3o harmonico, em 5100 Hz, esta no piso.
Isso e material para as camadas de acorde: o projeto escolhe os tons MFSK contra
harmonicos *cruzados*, e 36 dB abaixo e pouco para ignorar sem medir.

## Aberto

- A causa dos 7,1 dB de espalhamento em B->A. Nao e ganho comum no caminho
  (o harmonico ficaria junto) e nao foi investigada.
- Se o AGC do Windows esta ligado em B. Nunca foi verificado nesta bancada.

## Arquivos

- `gravacao/` -- a gravacao B->A: 1,5 s de piso e os 3 tons em seguida
- `figuras/` -- espectro cru em cima, contraste embaixo (50-6000 Hz)
- A->B nao tem gravacao: quem mediu foi o agent, e ele nao grava.
