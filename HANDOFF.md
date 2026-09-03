# Handoff -- campanha de medidas do link acustico

Estado em 2026-09-03 19:10. O plano dos testes esta em `TESTES.md`. Leia ele e
o `CLAUDE.md` antes de comecar. Este arquivo substitui a versao das 17:07.

## Por que esta sessao parou

O modo automatico do Claude Code passou a bloquear a execucao de comandos, e o
bloqueio vale para o resto daquela sessao -- ate `git commit`. Nada quebrou na
bancada. Para retomar: sessao nova, ou o modo de permissao padrao.

**Primeiro comando da sessao nova, antes de qualquer medida:** commitar o que
ficou solto na arvore, que e trabalho pronto e nao commitado --

```bash
git add netlink.py serial_link.py HANDOFF.md run_a2b_rest.sh run_a2b_rep.sh
git commit
```

**Nao commite `modem.py` nem `bench.py` junto.** Os dois estao modificados por
uma investigacao que ficou pela metade e nunca reportou (ver "O achado que ainda
esta aberto"). Rode `loopback_test.py` primeiro: se nao imprimir `SUCCESS!`,
`git checkout modem.py bench.py`.

## A bancada

| ponta | saida | entrada |
|---|---|---|
| **A** (Linux, console, tem teclado) | caixa Bluetooth `41:42:2B:14:D4:2A`, indice 20 | microfone interno Mic1 / Dmic0, indice PortAudio 26 |
| **B** (Windows, agent, headless) | caixa Bluetooth `AL-667`, ~60% de volume | microfone interno |

- Cabo serial em `/dev/ttyUSB0`, 115200. So controle, nunca dado.
- Ganho de captura em A: `Dmic0 45` (-5 dB), `Capture 39` (+12 dB).
- **A caixa de A estava no volume 1.00 do PipeWire e comprimindo.** Baixada
  para **0.45** durante o teste 16 (`wpctl set-volume 92 0.45`). Confira com
  `wpctl status` antes de medir qualquer coisa neste sentido -- o numero volta
  ao maximo se o dispositivo reconectar.
- As duas maquinas rodam `9acc715` ou mais novo. B foi atualizada por `pull` e
  `restart` e responde.

## O que esta fechado

### Sentido B -> A: os quinze testes, todos com pasta em `resultados/`

| teste | resultado |
|---|---|
| 01 `LVL-BASE` | A: -52,5 dBFS (banda util -62,6) |
| 02 `LVL-TONE` | +57,3 dB de margem |
| 03 `CH-CHIRP` | 74 de 76 bins com SNR negativa; contradiz o tom pisado em 76 dB |
| 04 `FSK-BASE` | 2,8% dos bytes, nenhum bloco |
| 05 `MFSK-VOTE` | 1 bloco de 3 (corpus anterior a correcao da cadeia) |
| 06 `MFSK-PAR` | nenhum bloco em 6 (idem) |
| 07 `MARY-BASE` | 3 blocos de 3 |
| 08 `MARY-GAIN` | 11 blocos de 12 |
| 09 `MARY-GAP` | 99,6 / 98,0 / 88,1% de bits, 9/9 -- o gap piora |
| 10 `MARY-BAND` | 99,8 / 99,9 / 99,9%, 9/9 -- nao move nada |
| 11 `MARY-CHORD` | acorde e pior: -4,3 dB de nivel, -1,2 ponto de bits |
| 12-13 `SYNC` | gate 95,31% 4/4; duas varreduras 95,68% 4/4 (repontuado) |
| 14 `FEC-REP` | 12 blocos de 12 em `fecrep` 1, 2 e 4. **`fecrep 1` = 11,3 B/s** |
| 15 `PKT-ARQ` | **21/21 pacotes, 0 retransmissoes, arquivo identico** |

Dois desses derrubaram linhas do `CLAUDE.md`, ja reescritas la: a taxa 1/3
sozinha recupera tudo nesta cadeia (a tabela antiga descrevia uma cadeia
saturada), e a transferencia de arquivo funciona -- sem mudar protocolo, so o
nivel analogico. **Linearidade valeu mais que qualquer mudanca de codigo.**

### Sentido A -> B: 01, 02, 03 e 08 fechados

| teste | resultado |
|---|---|
| 01 `LVL-BASE-A2B` | piso de B: -52,3 dBFS (banda util -55,0) |
| 02 `LVL-TONE-A2B` | +51,6 dB de margem |
| 03 `CH-CHIRP-A2B` | 76 de 76 bins positivos -- o oposto do outro sentido |
| 08 `MARY-GAIN-A2B` | 80-84% dos bits nos quatro ganhos, **0 de 12 blocos** |

## Os problemas encontrados e o que foi feito

1. **`capture.py` so ligava ajustes, nunca desligava.** `marychord` e
   `mfskgroup` ficavam grudados no agent e envenenavam o teste seguinte, com o
   JSON dizendo o contrario. Corrigido: manda os quatro explicitos sempre.
2. **O span das varreduras era contado duas vezes com arredondamentos
   diferentes.** Sobre o mesmo audio, span errado deu 78,1% dos bits e 0 de 4
   blocos; o certo, 95,7% e 4 de 4. Era isso, e nao o canal, que fazia as
   varreduras parecerem piores que o gate. Uma funcao so agora,
   `fec.frame_symbols`. Corpus recarimbado e repontuado; tres conclusoes da
   redacao anterior do 12-13 foram **retiradas por escrito**.
3. **`resultado.py` dava "bloco inteiro" para gravacao de silencio** -- payload
   vazio decodifica vazio e `b'' == b''`. Corrigido: `--` e fora do
   denominador.
4. **`resultado.py` e `bench.py` nao leem `sync_chirp`; so o `align.py` le.**
   Pontuar uma gravacao com varredura por eles mede o risco da varredura, nao o
   beneficio. **Nao consertado de proposito** -- mexer no pontuador no meio da
   campanha move a regua debaixo dos numeros. Fica como trabalho.
5. **`console.py fetch_recording` nao separava caminho do Windows**, e o arquivo
   caia como `captures\2026...wav` no diretorio corrente.
6. **Seis defeitos no `capture_a2b.py`** achados em revisao, o pior deles uma
   falha macia saindo com codigo 0 -- o retry do driver nunca disparava e um
   ponto virava diretorio vazio sem ninguem notar.

## O achado que ainda esta aberto

**A cadeia A -> B e muito pior: 16-20% de bits errados contra 3-5% em B -> A**,
e nenhum ganho entrega bloco. Duas pistas, e elas nao se excluem:

- **A caixa de A estava comprimindo.** Com ela no maximo, cortar o ganho digital
  de 1.0 para 0.25 quase nao mexia no pico recebido (0,515-0,562 para pouco
  menos). Com ela em 0.45, o mesmo corte leva o pico de 0,345-0,375 para
  0,117-0,172, que e proporcional. As gravacoes do teste 16 estao em
  `captures-a2b/16-spk/` e **ainda nao foram pontuadas** -- e o primeiro
  comando a rodar na proxima sessao.
- **O estimador cego de piso trabalha mal neste sentido.** No `align.py`, em
  B -> A o estimador cego empata com o oraculo de ruido (90,7% contra 90,7%);
  em A -> B ha 5 pontos de diferenca (82,6% contra 87,6%) e eles valem 4 blocos.
  Uma investigacao ficou no meio e deixou `modem.py` e `bench.py` modificados na
  arvore, **nao commitados e nao verificados**. Rode `loopback_test.py` antes de
  confiar neles; se nao imprimir `SUCCESS!`, `git checkout modem.py bench.py`.

Note que a distorcao **nao** acompanha o ganho: em A -> B o excesso entre tons
foi de +0,4 a +6,8 dB e o ganho 1.0 deu os *menores* excessos. Se a caixa
estivesse ceifando em 1.0, seria o contrario. Entao "esta alto" e verdade e
pode nao ser a causa inteira.

## Transferencia da gravacao: pelo cabo ou pela rede

O `puxa` anda a 8,1 kB/s -- dois minutos por gravacao de dez segundos, ou seja
horas movendo arquivo e minutos medindo. `netlink.py` resolve: servidor HTTP da
stdlib no lado do console, `urllib` do outro, e **a maquina remota empurra**
(conexao para fora, sem esbarrar no firewall de entrada do Windows). O cabo
carrega a URL, entao nenhum lado precisa saber o endereco do outro.

Estado: **implementado, nao validado.** Faltou uma coisa so, e ela ja foi feita
pelo usuario: `sudo ufw allow 8765/tcp`. O `ufw` de A estava ativo e descartava
a entrada em silencio, o que le como timeout e e indistinguivel de isolamento
de clientes no ponto de acesso.

Para conferir em um comando, com o console parado:

```bash
./venv/bin/python -c "
import netlink, subprocess, os
os.makedirs('/tmp/rx', exist_ok=True)
with netlink.Receiver('/tmp/rx') as rx:
    print('url', rx.url)
    print(subprocess.run(['./venv/bin/python','rcmd.py','--port','/dev/ttyUSB0',
                          '--timeout','40', f'rede {rx.url}'],
                         capture_output=True, text=True).stdout)
"
```

Se ainda der timeout, as duas maquinas estao numa rede que isola clientes.
**Os scripts da campanha ja estao com `--serial-only`** por isso: o
`capture_a2b.py` cai para o cabo sozinho, mas a prova gasta alguns segundos por
trial e sao cerca de cinquenta trials. Tire a opcao de `run_a2b_rest.sh` e
`run_a2b_rep.sh` no dia em que `rede <url>` responder `pong` da outra ponta.

O que ja se sabe, para nao refazer o diagnostico: antes da regra de `ufw` as
duas maquinas nao se alcancavam nem estando na mesma sub-rede, em nenhuma das
duas direcoes, e A alcancava o gateway normalmente. Isso deixou duas causas
possiveis com o mesmo sintoma -- `ufw` descartando entrada em silencio, e o
ponto de acesso isolando clientes. A regra elimina a primeira; **so o teste
acima separa as duas**, e ele nunca chegou a rodar.

Uma alternativa comecada e nao terminada: subir o baud do cabo para 921600, com
reversao automatica (o agent volta a 115200 se ninguem falar na taxa nova em
25 s, para que uma taxa que o adaptador nao segure nao leve o canal junto).
`serial_link.Control.set_baud` ja existe; o comando `baud` no `console.py`
**nao foi escrito**.

## O que falta medir

Sentido A -> B, com a caixa de A em 0.45 e depois de pontuar o teste 16:

1. **Pontuar `captures-a2b/16-spk/`** e decidir o ganho. Se a caixa era o
   problema, refazer o 08 inteiro no volume novo.
2. **14 `FEC-REP`** -- ha 7 gravacoes em `captures-a2b/14-fec-rep/` (3 em rep 1,
   3 em rep 2, 1 em rep 4), todas no volume ANTIGO da caixa. `fecrep 1` e
   `fecrep 2` deram **0 blocos**. Ou refazer no volume novo, ou manter como o
   corpus da cadeia comprimida e dizer isso.
3. Depois: **04, 05, 06, 07, 09, 10, 11 e 12-13** neste sentido. O
   `run_a2b_rest.sh <ganho>` roda todos em sequencia.

**Uma decisao que ficou para o usuario.** Se nem `fecrep 4` entregar bloco, a
metrica principal da tabela (blocos inteiros) e zero em todo ponto e nao
discrimina nada. A campanha continua legitima em *bits* -- o `TESTES.md` manda
usar bits para ajuste fino, com blocos como numero honesto separado -- mas
seria uma tabela de zeros ao lado de percentuais. Vale escolher entre medir
assim ou atacar a causa antes de medir.

**O 15 `PKT-ARQ` nao existe no sentido A -> B.** O `recvfile.py` puxa com o
receptor dirigindo, e o receptor precisa de audio e serial ao mesmo tempo, que
e o lado do console. Faria falta um `sendfile.py`, ou ensinar o agent a
receber. E trabalho de codigo, nao de medida, e nunca esteve no plano.

## Coisas que quebram se voce nao souber

**O microfone de A as vezes nao acorda.** Logo depois de outro processo soltar o
dispositivo ele entrega zeros. O `capture.py` aborta alto; espere 4 s e repita
o ponto. Aconteceu uma vez nesta campanha, no `fecrep 2` do teste 14 B -> A.

**A caixa Bluetooth anuncia zero canais por um a dois segundos** depois de
liberada. O `capture_a2b.py` tenta quatro vezes com 3 s entre elas.

**`grave` satura em 120 s sem avisar.** O `capture_a2b.py` agora aborta o trial
em vez de gravar uma janela truncada. O maior ponto da campanha e o MFSK votado
com 48 bytes em `fecrep 2`, 27,6 s.

**Bloco de zero exato nao e sala silenciosa, e fonte ausente.**

**Conversa na sala contamina medida de piso.** Voz ocupa 100-3000 Hz.

**Blocos recuperados e uma medida ruim para escolher parametro fino.** Use
acuracia de bits do `align.py`, que e estavel, e deixe blocos como numero
honesto separado.

**`marygap`, `maryband`, `marychord`, `fecrep`, `fecpar` e `syncsweep` tem que
ser iguais nos dois lados.** O `capture.py` manda todos, ligados ou desligados,
no inicio de cada rodada -- e passou a mandar os desligados por causa do defeito
1 acima.

## Codigo

Main em `9acc715` mais o que estiver por commitar. As quatro branches em
worktrees continuam sem merge; ver a versao anterior deste arquivo no git para
a descricao delas. `feat/clock-tracking` continua valendo a pena: nas 30
gravacoes M-arias de hoje a regra atual deu 20/30 blocos e a correlacao mole
com coerencia deu 29/30. Mergear muda a contagem de todos os testes ja feitos,
o que e barato -- a pontuacao e offline e o audio esta guardado.
