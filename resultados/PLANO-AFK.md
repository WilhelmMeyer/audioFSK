# Plano AFK — campanha final, segunda parte

Escrito em 2026-10-08, depois da primeira passada da campanha (`F*-10CM`). O usuário fica longe e não pode mexer na caixa. Começa quando ele mandar "começe" pelo celular.

## Bancada (fixa, não muda durante o plano)

- **B→A.** B (Windows) toca pelo alto-falante Realtek no P2, com os aprimoramentos desligados, a **10 cm** do microfone de A e apontado para ele. A (Linux) grava pelo microfone interno, dispositivo padrão (Mic1 via pipewire). Dmic0 45 (−5 dB), Capture 39 (+12 dB).
- **Controle:** túnel SSH (`socat` PTY ↔ `ssh -R 7001` ↔ `console.py --role agent --port socket://127.0.0.1:7001`).
- **Commit** `213366c` nas duas máquinas.
- **Comuns:** 48 bytes, `fecrep 1` e ganho digital 0,5, salvo onde está dito outro valor.

## Proteções (antes e depois de cada gravação)

| condição | ação |
|---|---|
| microfone mudo ou Dmic0 diferente de 45 | corrige, registra e segue |
| rms ≤ 0,004 (a caixa não tocou) | reinicia o agente do Windows uma vez e regrava; se repetir, **para** |
| pico ≥ 0,95 (saturação) | **para** |
| piso 6 dB acima do inicial (ar-condicionado, conversa) | **para** e avisa |

Parou: avisa num resumo curto e espera. Não improvisa outra bancada.

## Sequência

**0. Piso inicial.** `ruido.py`, 8 s → `G00-PISO`.

**1. Caracterização do canal** (uns 8 min)
- **C1, tons fixos.** `tom.py`, 3 repetições cada, nos 16 tons da 16-FSK, no tom R do IFK (3487,5 Hz, nunca medido no ar) e nas bordas 400, 550, 4000, 4500 e 5000 Hz → `G01-TONS`.
- **C2, varredura 400–4200 Hz em 10 s.** `capture.py --chirp`, mais `channel.py` e a resposta ao impulso pelo filtro casado (caminho direto, reflexões, cauda) → `G02-VARREDURA`.
- **C3, linearidade.** Tom de 1000 Hz com ganho 0,125, 0,25, 0,5 e 1,0: a 2ª e a 3ª harmônica em relação ao fundamental. Um burst 16-FSK + FEC com ganho 0,25 e 1,0, analisado com `distortion.py`. O de 0,5 já existe → `G03-LINEARIDADE`.

**2. Repetições da tabela principal** (uns 15 min). São 4 rodadas, intercaladas. Cada rodada grava 16-FSK, votada, multicanal, 16-FSK com varreduras, 16-FSK com varreduras e IFK, e Bell 202, uma vez cada. Com a passada anterior, cada método fica com 5 gravações. A coluna das varreduras vem do `align.py`. O IFK é comparado em pares com o 16-FSK com varreduras da mesma rodada → as pastas `F*-10CM` ganham as linhas novas.

**3. Arquivo** (uns 10 min). `recvfile.py` com pacote de 64 bytes (segunda corrida) e com 128 bytes; `cmp` nos dois → `F05-ARQUIVO-10CM`.

**4. Piso final.** Mostra se a sala mudou durante a campanha → `G00-PISO`.

## Em paralelo, offline (agentes, sem tocar na sala)

- **Figuras para o artigo**, cada uma com dados, script e COMO-REFAZER na própria pasta:
  - F-A: eco na posição antiga contra 10 cm, com a resposta ao impulso e a queda do tom por símbolo.
  - F-B: para onde vão os erros, sem e com IFK.
  - F-C: o piso com e sem ar-condicionado.
  - F-D: espectrogramas com eco, a 10 cm e com IFK.
  - F-E: a deriva de relógio medida pelas varreduras.
- **Receptor que subtrai a cauda:** variante só de leitura, testada nas gravações com eco de hoje, contra o receptor atual e contra o IFK.
- **Organização:** o `decay.py` vai para o repositório, os HEADERs são corrigidos (o microfone era o padrão, não o 26) e sai um `RESUMO.md` da campanha.

## Fim

Commit local no `main`, sem push. Resumo curto, para ler no celular.

## Fora deste plano, de propósito

Depende de mexer na caixa ou de mudar o formato do sinal no ar:
- distâncias de 20 e 40 cm;
- IFK pareado numa bancada com eco;
- IFK de dois símbolos;
- A→B.
