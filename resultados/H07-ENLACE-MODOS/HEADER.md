# H07 — enlace negociado: correções do handshake e uma sessão por técnica de dados

2026-10-22, tarde. Linux (A, chamador, alto-falante interno, `wpctl` 1,00, Mic1 `Dmic0 45`) e Windows (B, ouvinte, `Microfone (Realtek(R) Audio)` a −14 dB, `Speakers/Headphones (Realtek)`), ~2 m, como no H06. B rodado por SSH com `enlace_b.sh inicia` (cópias em `~/enlace_teste`, MD5 conferido). Carga: A manda os mesmos 207 bytes do H06, B manda 44.

Código: as sessões 1–2 rodaram com as 4 correções do handshake (commit `b39f948`, diagnóstico da sessão 3 do H06); as sessões 3–7 com isso mais as 5×2 como modo de dados (`--modo-dados`, mesmo commit). A correção do prazo/leitura longa (commit seguinte) **não** rodou no ar.

WAVs só no disco do Linux: `sessoes-enlace/` (A) e `sessoes-enlace-B/` (B). Aqui ficam JSON (com o diário), `.diario.txt` (linha a linha com tempo de parede) e os logs.

## Sessões

| # | hora | modo de dados | A (Linux) | B (Windows) | resultado |
|---|---|---|---|---|---|
| 1 | 15:58 | auto | `155806-chamador` | `155752-ouvinte` | **descartada: gente conversando na sala.** B→A 44/44; A→B parado em 93 por 80 s, parada pelo painel (o 2-FSK já estava recuperando: 186 B no diário de B) |
| 2 | 16:11 | auto | `161117-chamador` | `161111-ouvinte` | 207/207 e 44/44 idênticos, confirmado em 302 s; 1º contrato falhou (A→B escolheu tons até 4,3–4,5 kHz), recomeçou e fechou |
| 3 | 16:35 | 16fsk | `163530-chamador` | `163524-ouvinte` | 207/207 e 44/44, **113 s** |
| 4 | 16:39 | 2fsk | `163947-chamador` | `163942-ouvinte` | 207/207 e 44/44, **251 s** |
| 5 | 16:46 | votada | `164702-chamador` | `164656-ouvinte` | 207/207 e 44/44, **190 s** |
| 6 | 16:52 | multicanal | `165227-chamador` | `165221-ouvinte` | **descartada: caixa Bluetooth do lado do Windows desligou e outra sessão do Claude estava ativa.** 44/44, 124/207, canal caiu duas vezes, 900 s |
| 7 | 17:18 | multicanal | `171805-chamador` | `171800-ouvinte` | 207/207 e 44/44, **270 s** (1º contrato falhou, 2º fechou) |

"confirmado em" é o tempo de parede de A desde o início até tudo enviado e confirmado (saudação, sondagem e contrato incluídos: 60–250 s disso é negociação). Logs: `logs/A.log` (1), `logs/A2.log` (2), `logs/seq-<modo>-A.log` (3–7; o de multicanal tem as sessões 6 e 7 em sequência), `logs/sequencia*.out`.

## O que entrou no código

- `painel.py`: áudio e diário em disco durante a sessão, `estado.json` por segundo, comandos `estado/log/segue/pausa/retoma/finaliza/para` por TCP local; `recupera` para sessão morta à força. `saudacao.py --fim-silencio` sai sozinho. A sessão 1 foi parada pelo painel sem perder nada.
- Handshake (diagnóstico do H06 sessão 3): `_calou` ignora a janela cega; lê pela abertura antes do veredito; turno novo substitui o da fila; marca forte substitui fraca a <0,15 s. Na sessão 2 em diante nenhum ilegível saiu com `tentou=[]`.
- 5×2 votada e multicanal no enlace; com modo fixo os dados nunca trocam de técnica.

## Depois das medidas

O simulador, forçando a multicanal a começar em rep4, mostrou colisão e pedaço repetido: o prazo do receptor vencia antes de a varredura de marcas cobrir o fechamento, e o começo de um quadro rep4 multicanal é um quadro rep1 válido. Corrigido no commit seguinte (prazo medido sobre `ouvido.varrido`; leituras sem fechamento do candidato mais longo ao mais curto). Não medido no ar; no simulador os casos `auto` ficaram mais curtos (limpo 163→134 s, latência 226→191 s).

## Em aberto

- Contrato A→B às vezes escolhe tons acima de 4 kHz (sessões 2, 7); hipótese para os contratos que falham na 1ª tentativa, não verificada.
- Refazer a sequência com a correção do prazo.
