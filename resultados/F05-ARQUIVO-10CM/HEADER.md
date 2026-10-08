# F05 — arquivo inteiro, B→A a 10 cm

Commit `213366c` na 1ª corrida (posição 1) e `c57fc74` nas duas do bloco 3 (posição 2). Data: 2026-10-08.

- **Bancada:** B (Windows) toca pelo alto-falante Realtek no P2, com os aprimoramentos de áudio desligados, a 10 cm do microfone de A e apontado para ele. A (Linux) grava pelo microfone interno (Dmic0 45 = −5 dB, Capture 39 = +12 dB), dispositivo padrão. O controle vai pelo túnel SSH (`socat` PTY ↔ `ssh -R` ↔ `console.py --role agent --port socket://…`), sem cabo serial.
- **Comando:** `recvfile.py --remote-file testcard.bmp --out f05-64.bmp --fec --mode mary --gain 0.5 --packet-size 64 --repeat 1`

## Resultado

| arquivo | pacotes | retransmissões | tempo | taxa | `cmp` |
|---|---|---|---|---|---|
| `testcard.bmp`, 1334 B | 21 de 21 | 7 | 267 s | 5,0 B/s efetivos | idêntico, CRC32 24763389 |

Falharam uma vez os pacotes 3, 11, 13, 15 e 20. O pacote 14 falhou duas vezes. Nenhum pacote esgotou as 4 tentativas. O log completo está em `recvfile.log`.

## Corridas do bloco 3 (posição 2, depois do usuário mover o PC)

Mesmos comandos, mesma bancada, `--packet-size 64` e `--packet-size 128`. Logs: `recvfile-r2-64.log`, `recvfile-r2-128.log`.

| corrida | pacote | pacotes | retransmissões | tempo | taxa | `cmp` |
|---|---|---|---|---|---|---|
| 1ª (posição 1, 213366c) | 64 B | 21 de 21 | 7 | 267 s | 5,0 B/s | idêntico |
| bloco 3 | 64 B | 21 de 21 | 5 | 253 s | 5,3 B/s | idêntico, CRC32 24763389 |
| bloco 3 | 128 B | 11 de 11 | 2 | 175 s | 7,6 B/s | idêntico, CRC32 24763389 |

Bloco 3, 64 B: falharam uma vez os pacotes 7, 15 e 17; o 1 falhou duas vezes. Bloco 3, 128 B: falharam uma vez os pacotes 4 e 9. Nenhum pacote chegou ao limite de 4 tentativas. **7,6 B/s é o recorde de arquivo inteiro do repositório** (o `15-PKT-ARQ` tinha 7,2 B/s com 128 B), agora com retransmissões, o que o `15-PKT-ARQ` não tinha. Pacote maior ganhou aqui, provavelmente porque cada pacote gasta preâmbulo, varreduras e ida e volta fixos; com 128 B há 11 deles contra 21.

## Ressalvas

- No `15-PKT-ARQ`, com a AL-667, o mesmo arquivo chegou com zero retransmissões a 6,8 B/s.
- Antes da caixa ir para 10 cm (posição anterior, cauda do tom a −8 dB em um símbolo), nenhum pacote passou: o pacote 0 falhou 4 vezes em `fecrep 1` e 2 vezes em `fecrep 2`. Não era defeito no `recvfile.py`. Era a cauda do tom: um bloco de 81 bytes pelo `capture.py` leu 89% dos bits e também não fechou.
- Uma corrida por tamanho de pacote; três corridas no total, duas posições. A taxa varia com o número de retransmissões (aleatório), não só com o tamanho do pacote: 5,0 e 5,3 B/s a 64 B com 7 e 5 retransmissões é a mesma ordem, e a diferença não é significativa.
- `f05-64.bmp` e `f05-128.bmp` na raiz do repositório são as saídas das corridas do bloco 3 (`cmp` contra `testcard.bmp`: idênticos); não versionados.
