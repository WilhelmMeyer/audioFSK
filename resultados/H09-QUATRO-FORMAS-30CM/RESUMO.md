# H09: quatro formas, notebook para celular, 30 cm (2026-10-30)

**Montagem.** A mesma de `H09-QUATRO-FORMAS-10CM/`, com o Galaxy A34 a 30 cm: caixa Bluetooth AL-1888, microfone em `VOICE_RECOGNITION`, modo manual, 100 baud, repetição 3, caixa 30%, confirmação ligada, tons de fábrica. Carga: 320 bytes ASCII (`texto-320.txt`), 10 pacotes de 32 bytes, 1 sessão por forma. Taxa = 320 B / tempo, do primeiro envio à última confirmação. Todas no hash `7ec86afc`.

| Forma | Pacotes | Retransmissões | Tempo (s) | Taxa (B/s) | Bytes | Bits errados antes do FEC | Notebook | Celular |
|---|---|---|---|---|---|---|---|---|
| 16-FSK | 10/10 | 0 | 148,9 | 2,15 | idênticos | 1.071 de 29.340 (3,65%) | 20261030-161401 | 20261030-161357 |
| 5×2-FSK multicanal | 10/10 | 0 | 118,4 | 2,70 | idênticos | 3.063 de 29.400 (10,42%) | 20261030-162252 | 20261030-162248 |
| 2-FSK | 10/10 | 0 | 379,9 | 0,84 | idênticos | 150 de 29.340 (0,51%) | 20261030-164557 | 20261030-164553 |
| 5×2-FSK votada | 10/10 | 0 | 354,2 | 0,90 | idênticos | 11 de 29.340 (0,04%) | 20261030-163602 | 20261030-163559 |

**Contra 10 cm** (`H09-QUATRO-FORMAS-10CM/RESUMO.md`):

| Forma | Taxa, 10 → 30 cm (B/s) | Retransmissões, 10 → 30 cm | Bits errados, 10 → 30 cm |
|---|---|---|---|
| 16-FSK | 2,49 → 2,15 | 0 → 0 | 0% → 3,65% |
| 5×2-FSK multicanal | 2,47 → 2,70 | 0 → 0 | 0,014% → 10,42% |
| 2-FSK | 0,91 → 0,84 | 0 → 0 | 0,027% → 0,51% |
| 5×2-FSK votada | 0,90 → 0,90 | 0 → 0 | 0% → 0,04% |

**Ressalvas.**
- Uma sessão por forma: isto mostra que entregou, não dá estatística entre formas.
- Código: a 30 cm tudo em `7ec86afc`. A 10 cm, só a votada; 16-FSK e multicanal estão em `85176401` e 2-FSK em `1a44e20b`, ambos sem o embaralhamento da carga. A comparação de bits mistura distância e versão nessas três linhas.
- O tempo varia sem retransmissão: a multicanal ficou mais rápida a 30 cm (118,4 × 129,7 s), o que não é efeito da distância. Causa não apurada.

**As duas sessões do 2-FSK.** A da tabela é a repetição, pedida pelo autor (`repeticao/2fsk/`): de 0% a 2,8% de bits errados por pacote; cerca de 29 s do tempo são a espera entre os seq 0 e 1, sem retransmissão, causa não apurada. A primeira (`2fsk/`, notebook 20261030-162536, celular 20261030-162532), mesma montagem, menos de 20 minutos antes: 10/10, 4 retransmissões, 555,4 s, 0,58 B/s, bytes idênticos, 1.983 de 29.340 bits errados (6,76%, só dos quadros lidos; os 4 ilegíveis não entram), com seq 0 a 4 entre 0,1% e 25,4% e seq 5 a 8 entre 0,4% e 2,6%; causa não apurada. A variação entre sessões da mesma forma, sem mudar a montagem, é maior que a diferença entre 10 e 30 cm nessa forma; as outras linhas, com uma sessão cada, não a separam da distância.

**Sessão fora da tabela.** `multicanal/sem-arquivos-do-celular/20261030-161719`: 10/10 e 124,7 s pelo notebook; o celular não salvou a sessão, porque o toque em Parar caiu na cortina de notificações aberta pelo script, e os bytes não foram conferidos. Uma tentativa de 2-FSK foi parada aos 36 s, por decisão do operador, e não vale (`sessoes-enlace-celular/`, celular 20261030-162008).
