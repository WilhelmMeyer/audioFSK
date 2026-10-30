# H09: quatro formas, notebook para celular, 10 cm (2026-10-30)

**Montagem.** Notebook como chamador, tocando pela caixa Bluetooth AL-1888; Galaxy A34 como ouvinte, microfone em `VOICE_RECOGNITION`, a 10 cm. Modo manual, sem negociação: 100 baud, repetição 3, caixa 30%, confirmação ligada, tons de fábrica. Carga: 320 bytes ASCII (`texto-320.txt`), 10 pacotes de 32 bytes, 1 sessão por forma. Taxa = 320 B / tempo, do primeiro envio à última confirmação, com confirmações e esperas incluídas.

| Forma | Pacotes | Retransmissões | Tempo (s) | Taxa (B/s) | Bytes | Bits errados antes do FEC | Notebook | Celular |
|---|---|---|---|---|---|---|---|---|
| 16-FSK | 10/10 | 0 | 128,4 | 2,49 | idênticos | 0 de 29.340 | 20261030-140746 | 20261030-140742 |
| 5×2-FSK multicanal | 10/10 | 0 | 129,7 | 2,47 | idênticos | 4 de 29.400 (0,014%) | 20261030-141034 | 20261030-141029 |
| 2-FSK | 10/10 | 0 | 350,9 | 0,91 | idênticos | 8 de 29.340 (0,027%) | 20261030-141529 | 20261030-141525 |
| 5×2-FSK votada | 10/10 | 0 | 355,2 | 0,90 | idênticos | 0 de 29.340 | 20261030-155133 | 20261030-155128 |

**Ressalvas.**
- Uma sessão por forma: isto mostra que entregou, não dá estatística entre formas.
- Código não uniforme: 16-FSK e multicanal no hash `85176401`, 2-FSK em `1a44e20b`, votada em `7ec86afc`. De `1a44e20b` para `85176401` só entrou a contagem de bits. `7ec86afc` acrescenta o embaralhamento da carga, que muda o que vai ao ar; o efeito neste texto não foi medido.
- A votada rodou cerca de 1h40 depois das outras, com a montagem desfeita e refeita nesse intervalo, e o celular mexido entre as sessões.
- Bits de 16-FSK e multicanal: releitura das gravações do celular com a mesma conta. Bits de 2-FSK e votada: medidos ao vivo.
- Repetição 3 tem folga: os erros antes do FEC ficaram em até 0,03%. Por isso as taxas são baixas e não medem o limite de cada forma.

**Outras sessões da votada, guardadas e fora da tabela.**
- `votada/20261030-153542` (celular `153539`): 10/10, 0 retransmissões, 383,7 s, idêntica, 9 de 29.340 bits; celular mexido.
- `votada/sem-arquivos-do-celular/20261030-142215`: 10/10 e 385,2 s pelo notebook; sem os arquivos do celular, os bytes não foram conferidos.
- `votada/interrompida/20261030-152946`: parada aos 113 s; não vale.

As pastas `votada/repeticao/` e `votada/` guardam, respectivamente, a sessão da tabela e a de 383,7 s.

## Arquivo: bandeira do Brasil

BMP 48×34, 934 B (`figurinhas/bandeira-br-48.bmp`), 16-FSK, 100 baud, repetição 2, caixa 30%, mesma montagem. Em `resultados/H08-ARQUIVO-CELULAR/`.

| | Pacotes entregues | Retransmissões | Tempo (s) | Taxa (B/s) | Bytes | Bits errados antes do FEC |
|---|---|---|---|---|---|---|
| `bandeira/` (sem embaralhar) | 26 de 30 | 26 | 752,7 | 1,07 | 806 de 934 | 4,9% |
| `bandeira-embaralhada/` | 30 de 30 | 0 | 321,7 | 2,90 | idênticos | 5,4% (3.180 de 58.680) |

Sem embaralhar, os pacotes 24 a 28, quase só de bytes `00`, chegaram com 13% a 18% dos bits errados, quase a mesma contagem a cada tentativa, com nível e espectro inalterados; quatro foram abandonados após 6 tentativas. O embaralhamento faz XOR da carga com uma sequência sorteada pelo número do pacote, sem mudar a posição dos bytes. Na sessão embaralhada, o pior pacote teve 8,5%. A causa física do erro em tom repetido não foi comprovada, e o resultado vem de uma sessão de cada caso, em momentos diferentes.

Referência anterior: logo do IF, 1270 B, 16-FSK 100 baud repetição 2, sem embaralhar: idêntico, 491,7 s, cerca de 2,6 B/s, 1 reenvio em 41 quadros (`sessoes-enlace-celular/celular/20261030-131754`).

Logo do IF com embaralhamento, 1270 B, 16-FSK 100 baud repetição 1, mesma montagem (`resultados/H08-ARQUIVO-CELULAR/logo-rep1/`, notebook 20261030-160041, celular 20261030-160037): 40 de 40 pacotes, 0 retransmissões, 328,7 s, 3,86 B/s, bytes idênticos, 1.943 de 39.120 bits errados antes do FEC (4,97%), de 13 a 81 de 978 por pacote (1,3% a 8,3%). Uma sessão; o método anterior não mediu os erros por bit.
