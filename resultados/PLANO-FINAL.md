# Plano da campanha final

Escrito em 2026-10-08, para ser executado por outra sessão. Aqui só fica o plano. Os resultados vão para as pastas `F*` que cada teste cria.

## Objetivo

Provar os métodos principais na mesma bancada, no mesmo dia e no mesmo commit. A ideia não é refazer a investigação: o que já foi medido e descartado (`marychord`, `marygap`, `maryband`, piso sem exclusão, o sentido A→B) fica de fora e vira uma linha no artigo citando a pasta antiga.

## Regra de execução: uma gravação por teste

- Cada teste é **uma** gravação (`--trials 1`).
- Grava, pontua **na hora** e mostra o resultado ao usuário antes de seguir.
- Se ficar ruim, avisa na hora. Só se repete o teste se o usuário pedir.
- Nunca gravar várias repetições de uma vez para só depois descobrir que nenhuma presta.

## Bancada: um sentido só, B→A

- **Transmite: B** (Windows, `console.py --role agent`), pelo próprio alto-falante do Windows. Ele já foi comparado e é o melhor, então **não há escolha de caixa nesta sessão**. Acesso remoto: `ssh Home@100.114.48.25`.
- **Grava: A** (Linux, console), com o microfone interno Mic1/Dmic0, índice PortAudio 26. Ganhos: Dmic0 45 (−5 dB) e Capture 39 (+12 dB), os mesmos de `14-FEC-REP`. **O Dmic0 volta MUTED depois de reiniciar e aí lê −99 dBFS. Confira antes de tudo.**
- **Serial:** `/dev/ttyUSB0`, só para controle. O console local tem de estar parado, porque `capture.py` e `recvfile.py` precisam ser os donos da porta.
- **Commit:** o mesmo nas duas máquinas. Anote em todo HEADER.

## Parâmetros comuns

- **Carga:** 48 bytes aleatórios.
- **Correção:** `fecrep 1` em todos os métodos com FEC, para que a tabela compare métodos e não redundâncias.
- **Números de cada teste:**
  - bloco íntegro, sim ou não;
  - taxa útil em B/s;
  - acerto de bits antes do FEC na melhor posição;
  - pico recebido.
- **Pontuar logo depois de gravar:** `./venv/bin/python resultado.py <NOME> captures/<stem> --bancada "<texto>"`.

## Sequência

Cada etapa só começa se a anterior estiver boa. Se uma der ruim, pare e avise.

### T0 — bancada

**T0.1 `F00-PISO`: piso da sala.**
```
./venv/bin/python ruido.py --device 26 --secs 8 --label f00-piso
```
- Deve ficar na ordem de `01-LVL-BASE`.

**T0.2 `F00-NIVEL`: um burst de 16-FSK + FEC.**
```
./venv/bin/python capture.py --port /dev/ttyUSB0 --mode mary --fec --repeat 1 --gain 0.5 --trials 1 --label f00-nivel
```
- O alvo é pico entre 0,4 e 0,6 e bloco íntegro.
- Fora disso, ajuste o volume de B (o mixer, não o ganho digital) e grave de novo.
- Se não fechar íntegro, pare: a cadeia não está linear.

### P — provas novas

São os métodos cuja única medição foi com a cadeia saturada (`04`, `05`, `06`).

**P1 `F01-2FSK`: 2-FSK Bell 202, sem FEC.**
```
./venv/bin/python capture.py --port /dev/ttyUSB0 --mode fsk --gain 0.5 --trials 1 --label f01-2fsk
```
- O número é a % de bytes certos.
- O resultado decide se vale implementar o 2-FSK + FEC.

**P2 `F02-5X2-VOTADA`: 5×2-FSK votada + FEC.**
```
./venv/bin/python capture.py --port /dev/ttyUSB0 --mode mfsk --fec --repeat 1 --gain <T0.2> --trials 1 --label f02-votada
```
- O acorde sai com 1/5 da amplitude. Se o pico ficar muito abaixo de 0,4, avise antes de mexer no ganho.

**P3 `F03-5X2-MULTICANAL`: 5×2-FSK multicanal + FEC.**
```
./venv/bin/python capture.py --port /dev/ttyUSB0 --mode mfsk --parallel --fec --repeat 1 --gain <igual P2> --trials 1 --label f03-multicanal
```

### R — retestes dos métodos já provados, na bancada nova

**R1 `F04-16FSK`: 16-FSK + FEC, com as varreduras.** Uma gravação dá as duas colunas: malha e varreduras.
```
./venv/bin/python capture.py --port /dev/ttyUSB0 --mode mary --fec --repeat 1 --gain <T0.2> --sync-chirp --trials 1 --label f04-16fsk
```
- Coluna da malha: `resultado.py`. Coluna das varreduras: `align.py`.
- **Para a coluna das varreduras não use o `resultado.py` nem o `bench.py`: eles não leem `sync_chirp`.**

**R2 `F05-ARQUIVO`: arquivo inteiro.**
```
./venv/bin/python -u recvfile.py --port /dev/ttyUSB0 --remote-file testcard.bmp --out f05-64.bmp \
    --fec --mode mary --gain <T0.2> --packet-size 64 --repeat 1
cmp f05-64.bmp <original>
```
- O `-u` é obrigatório se a saída for redirecionada.
- Registre pacotes, retransmissões, B/s e o resultado do `cmp`.
- A corrida com pacotes de 128 bytes fica a critério do usuário.

### I — IFK (tom de repetição), em implementação numa sessão paralela

O IFK entra no plano, mas não se espera por ele. Siga T0 → P → R normalmente e encaixe os testes de IFK assim que a implementação estiver pronta, em qualquer ponto da sequência.

**"Pronto" quer dizer:**
- commit no `main` passando no `loopback_test.py`;
- `pull` + `restart` feitos nas duas máquinas;
- o modo ou flag do IFK conferido no código. Use o nome que a sessão do IFK entregar; os comandos abaixo marcam esse nome como `<ifk>`.

**Depois do restart, refaça uma gravação do T0.2** antes de medir o IFK. O restart derruba os streams de áudio, e é preciso confirmar que pico e bloco continuam iguais.

**I1 `F06-16FSK-IFK`: 16-FSK + IFK + FEC.**
- Use o mesmo comando e o mesmo ganho do R1, mudando só o IFK. Uma gravação.
- Compare com o R1: bloco íntegro, % de bits antes do FEC, e a energia no tom excluído (a medida de eco que o IFK dá de graça).
- Se o R1 ainda não tiver sido feito, faça-o antes, para os dois saírem da mesma bancada.

**I2 `F07-2FSK-IFK`: 2-FSK por sondas + IFK + FEC.** Só se a sessão do IFK entregar essa camada.
- Uma gravação, mesma bancada.
- Compare com o P1 (Bell 202) e com o P2 (votada), que é a outra forma de 1 bit por símbolo.

## Saída para o artigo

| Teste | Vira |
|---|---|
| P1, P2, P3, R1 | **Tabela principal**: uma linha por método. Colunas: bits/símbolo, taxa útil, bloco íntegro, bits certos antes do FEC |
| R1 | Malha × varreduras sobre a mesma gravação |
| I1, I2 | Linhas do IFK na tabela principal, ao lado do método sem IFK |
| R2 | Linha do arquivo: pacotes, retransmissões, B/s, `cmp` |

## Fora deste plano, de propósito

- **2-FSK + FEC.** Depende do P1 e exige código.
- **Redundância 2 e 4, A→B, `marychord`, `marygap`, `maryband`, piso sem exclusão:** já medidos. Cite as pastas `09`, `10`, `11`, `14`, `16`, `17` e `INVESTIGACAO-A2B.md`.
