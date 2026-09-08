# 18-FEC-SIM

- **Codigo:** commit `cd8a08b-dirty` (arvore suja: modificacoes pendentes em `.gitignore`, `recording.py`, `requirements.txt`, `resultado.py`, e um conflito de merge nao resolvido em `artigo/artigo_modem.md`; nenhum desses arquivos foi tocado por este script nem pelo `fec.py` usado aqui).
- **Quando:** 2026-09-07

## Canal

**Isto e SIMULACAO, nao ar.** Nao ha caixa, microfone, sala nem link acustico
nenhum neste teste. E um numero artificial injetado direto nos bits codificados,
para isolar o que a camada de correcao de erro consegue tolerar, em separado de
tudo que o canal acustico real acrescenta por cima (comb de frequencia, limitador,
deriva de relogio, sincronismo). Qualquer comparacao com uma linha da bancada de
ar tem que passar por essa ressalva primeiro.

## Modelo de ruido

BPSK antipodal (bit b -> x = 2b-1) em AWGN com sigma = 1/Qinv(p), de modo que o
sinal de y inverte com probabilidade exatamente p. LLR suave = y (o Viterbi e
invariante a escala); decisao abrupta = sign(y). A fracao de inversoes realizada
seguiu p de perto: desvio de ate 0,001 na maior parte da grade e um unico ponto
(BER nominal 0,40) com desvio de 0,002. A ressalva original desta campanha dizia
"abaixo de 0,001" para todos os pontos; o re-teste mostrou que isso vale para 37
dos 39 pontos e nao para o extremo superior da grade -- registrado aqui para nao
repassar um numero que a propria reexecucao contradisse.

## Metodo

- **Semente:** `np.random.default_rng([20260907, variant_idx, ber_idx])`, deterministica por ponto (variante x BER), portanto reprodutivel exatamente.
- **200 trials por ponto**, carga de 64 bytes aleatorios nova a cada trial, `depth=16`.
- `fec.find_sync` foi deliberadamente excluido deste teste: o limiar de 0,55 sobre correlacao de sinal falha a partir de BER ~0,22 e dominaria toda a linha de BER alta, escondendo o que o Viterbi por si so tolera.
- **Eixo:** BER por bit codificado, 0,02 a 0,40 em passos de 0,01 (39 pontos).
- **Variantes:** taxa 1/2 decisao abrupta, taxa 1/2 decisao suave, taxa 1/3 decisao suave, taxa 1/3 decisao suave com repeticao 2. Todas com `depth=16`.

## Ressalvas

- **As linhas NAO tem o mesmo tempo de ar.** 1036 bits de canal por bloco na taxa 1/2, 1554 na taxa 1/3, 3108 na taxa 1/3 com repeticao 2. Comparar variantes pelo eixo de BER sozinho ignora que cada uma gasta um numero diferente de simbolos para carregar os mesmos 64 bytes.
- **O entrelacamento esta presente no `fec.encode`/`fec.decode` mas e inocuo contra erros independentes**; este teste injeta ruido i.i.d. por bit e portanto nao exercita a razao de ser do entrelacador, que e espalhar erros em rajada.
- **"100% integro" quer dizer 200 de 200 observados, nao probabilidade 1.** E a coluna mais ruidosa da tabela: um unico trial a mais ou a menos no ponto de corte desloca a leitura.
- **O `CLAUDE.md` da raiz registra 8% / 8% / 13% / 25% de tolerancia a erro de bit para taxa 1/2 (abrupta e suave) e taxa 1/3 (suave e suave-repeticao-2, aproximadamente).** Os numeros desta simulacao sao mais baixos em toda a linha. A ordem entre as quatro variantes e as magnitudes relativas concordam; a diferenca vem do modelo de canal (aqui, AWGN i.i.d. calibrado para produzir exatamente a BER nominal; la, nao declarado) e do criterio de aprovacao (aqui, 200 de 200 blocos de 64 bytes byte-identicos; la, nao declarado), nenhum dos dois descrito no `CLAUDE.md`. Isto nao invalida nenhum dos dois numeros -- sao duas medidas de coisas ligeiramente diferentes.

## Resultado

| variante | BER ate 100% integro | BER ate 90% integro |
|---|---|---|
| taxa 1/2, decisao abrupta | < 0,02 | 0,04 |
| taxa 1/2, decisao suave | 0,05 | 0,09 |
| taxa 1/3, decisao suave | 0,10 | 0,14 |
| taxa 1/3, decisao suave, repeticao 2 | 0,19 | 0,23 |

**Nota sobre o "< 0,02":** nao e colapso. A taxa 1/2 abrupta ja da 199 de 200 no
primeiro ponto varrido (0,02) e 198 de 200 em 0,03; ela simplesmente nunca chega
a 200 de 200 dentro da grade testada. Preencher essa celula exigiria pontos
abaixo de 0,02, que nao foram varridos.

## Reproducao

`./venv/bin/python resultados/18-FEC-SIM/fecsweep.py` reexecuta a campanha
inteira (39 pontos x 4 variantes x 200 trials, paralelizado em 12 processos) e
regrava `resultado.csv`. A reexecucao feita para esta campanha reproduziu a
tabela acima e as quatro linhas de contagem (200 de 200 por ponto) exatamente,
carater por carater, incluindo o autoteste sem ruido no inicio da saida.

## Arquivos

- `fecsweep.py` -- script da simulacao, copiado do original com um gravador de CSV minimo acrescentado (nao alterou a semente nem a logica de simulacao).
- `resultado.csv` -- uma linha por (variante, BER): colunas `variante`, `ber`, `trials`, `integros` (blocos de 64 bytes recuperados byte-identicos de 200 trials).
