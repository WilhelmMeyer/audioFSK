# audioFSK

Link de dados acústico em Python. Duas máquinas, sem rede: uma toca som pelo alto-falante, a outra escuta pelo microfone e recupera os bytes.

Começou como um modem Bell 202 puro e hoje é mais que isso: **três camadas físicas diferentes, uma camada de correção de erro e um fluxo de trabalho de medição**. As três camadas existem porque a primeira não funcionou no ar — e qual usar é pergunta medida, não preferência.

## O que funciona hoje

Medido no ar, entre duas máquinas na mesma sala, com blocos protegidos por correção de erro:

| Caminho | Taxa útil | Blocos íntegros |
|---|---|---|
| Bell 202 8N1, 1200 baud | 120 B/s no papel | **nunca entregou uma mensagem** |
| MFSK votado + FEC | ~1,8 B/s | 4 de 4 |
| MFSK paralelo + FEC | ~5,9 B/s | 5 de 9 |
| **M-ária 16 tons + FEC, ganho 0,5** | **~9,4 B/s** | **9 de 11** |

**Os nomes desta tabela, do código e do resto deste arquivo são os do projeto, não os da literatura.** O artigo em `artigo/` usa os da literatura e o código não é renomeado. Correspondência: Bell 202 é a **2-FSK**; MFSK votado é a **5×2-FSK votada** (cinco canais binários com o mesmo bit, decisão por maioria); MFSK paralelo é a **5×2-FSK multicanal** (um bit distinto por canal); M-ária 16 tons é a **16-FSK**. No artigo, *M-ária* é a modulação de ordem M e abrange as quatro, inclusive a binária; *MFSK* expande como *multiple frequency shift keying* e abrange as com mais de duas frequências, 5×2-FSK e 16-FSK. Ou seja, "MFSK" aqui (cinco pares) e no artigo (mais de dois tons) são conjuntos diferentes, e "M-ária" aqui (só a de dezesseis) é mais estreita que lá. Vale para `TESTES.md`, `HANDOFF.md` e os `HEADER.md` de `resultados/`, que são registros de campanha e ficam como estão. A tabela completa está no `CLAUDE.md`, seção "Nomes no código e nomes no artigo".

Esses números são do enlace de duas máquinas, e é o único acervo que entra nesta tabela. Há também um acervo de **auto-captura** — uma máquina só, alto-falante e microfone no mesmo computador — com números melhores, 10,7 B/s a 12 blocos de 12. Ele é outro canal e mais fácil; veja *Sincronismo* abaixo e leia a ressalva ali antes de citá-lo.

Uma saudação de 58 caracteres atravessou íntegra pela M-ária. **A transferência de arquivo inteiro ainda não funciona**: 1 pacote de 21 com pacotes de 81 bytes, enquanto blocos isolados de 24 a 58 bytes decodificaram 9 de 11 no mesmo link. O suspeito é o comprimento do bloco — mais símbolos entre re-sincronizações, e a M-ária é implacável com escorregão de relógio.

## Requisitos

- Python 3.10+
- PortAudio no sistema (`sudo apt install libportaudio2` no Debian/Ubuntu) — necessário só para as ferramentas que tocam áudio

```bash
python -m venv venv
./venv/bin/pip install -r requirements.txt
```

O teste de bancada roda sem PortAudio nenhum:

```bash
./venv/bin/python loopback_test.py
```

Ele é a suíte inteira: um script, sem framework, imprime `SUCCESS!` ou `FAILED`. Não julga contra ruído gaussiano genérico, e sim contra as degradações realmente medidas neste link — inclinação de −16 dB nos agudos, o envelope do limitador de saída, reverberação de 80 ms.

## As três camadas físicas

### Bell 202 — rápida no papel

1200 baud, mark 1200 Hz, space 2200 Hz, enquadramento UART 8N1, demodulação por *delay-and-multiply*. É o modem clássico de telefone.

**O que ela troca:** velocidade por robustez, e no ar perdeu a aposta. Ela decide o bit pelo *sinal* de um discriminador, então qualquer canal que enfraqueça um tom em relação ao outro enviesa todas as decisões para o mesmo lado. Uma portadora contínua `0x55` atravessa limpa a 110 B/s de 120 teóricos — mas uma mensagem de verdade nunca chegou. Tom periódico atinge estado estacionário e engana; dado aperiódico não.

**Para que serve:** é o único caminho que expõe o canal como linha serial burra (`app.py --pty`), então continua sendo a camada certa quando o acoplamento é bom — cabo, ou dois aparelhos encostados.

### MFSK — cinco pares de tons, 100 baud

Dez tons em cinco **pares**, cada par com 200 Hz entre seus dois membros para que o canal os trate igual. Duas leituras do mesmo sinal:

**Votação** (padrão): todos os cinco pares carregam o *mesmo* bit e a maioria decide. Um par que caiu numa cova do canal carrega exatamente um voto e os outros quatro o superam. Isso é o ponto inteiro de tocar cinco frequências ao mesmo tempo — somar a energia dos acordes, que é o que o código fazia antes, deixa a amplitude comprar a resposta: num link real um acorde chegou com o dobro da energia do outro e o detector chamou quase tudo de símbolo mais alto, 27% dos bytes certos.

**Paralelo** (`fecpar on`): cada par carrega o *seu próprio* bit. Cinco bits por símbolo, cerca de 4× mais rápido. Custa a diversidade — cada bit passa a depender de um par só.

A polaridade alterna ao longo da banda (nos pares 0, 2 e 4 o tom grave significa 0; nos pares 1 e 3 significa 1), então os dois acordes têm quase a mesma frequência média (1620 contra 1660 Hz) e um canal inclinado não favorece nenhum bit. Não "arrume" isso para todos-graves-são-zero.

**O que o paralelismo não faz:** criar robustez. O que protege um bit é o número de observações independentes dele. Votação com repetição 2 dá dez observações por bit e gasta seis símbolos; paralelo com repetição 10 dá dez observações e gasta os mesmos seis. É um botão, não um ganho — serve para gastar menos redundância quando o canal permite.

### M-ária — 16 tons, um por vez

Na literatura em inglês isto é *M-ary FSK* com M = 16, ou 16-FSK; em português, **modulação M-ária**,
formada como binário, ternário e quaternário. A rigor M-ária é a modulação de ordem M e a binária também é uma (M = 2); o artigo em `artigo/` usa o termo nesse sentido amplo e chama esta camada de 16-FSK. No código o modo se chama `mary`
e as classes são `MaryModulator`/`MaryDemodulator` — o nome do identificador,
não do conceito, e ele também está gravado como `"mode": "mary"` nos JSON do
acervo, então renomear quebraria a leitura das gravações.

Dezesseis tons entre 888 e 3325 Hz, **exatamente um soando por vez**, e qual deles é nomeia quatro bits. Codificação Gray, porque tons vizinhos são os que o canal confunde e assim a confusão custa um bit em vez de até quatro.

**Por que ela ganha: potência.** Um acorde de cinco tons precisa ser dividido por cinco para caber na mesma amplitude de pico, então cada tom sai do alto-falante 14 dB abaixo. Foi isso que produziu os 2 a 7 dB de contraste medidos entre um tom transmitido e o mesmo tom quando não era transmitido — e daí os 15 a 30% de erro por par. Um tom por vez recupera esses 14 dB inteiros, e isso apareceu direto no microfone: o `rms` recebido pulou de 0,07–0,09 dos acordes para 0,13–0,15.

**O que ela troca:** um tom parado numa cova do canal nunca ganha a comparação, então aquele símbolo nunca é detectado. A defesa é que com 16 tons cada um fica calado 15/16 do tempo, então sua energia média *é* o piso de ruído naquela frequência. Dividir por ele antes de comparar é um detector calibrado por frequência — e, ao contrário da normalização que falhou nos acordes, a estimativa não é contaminada pelo sinal que ela deveria medir. O vencedor fica de fora de cada atualização pelo mesmo motivo.

**Onde ela é pior:** reverberação. O rastro do tom *anterior* compete de frente com o atual, em vez de desvanecer os dois acordes juntos. Com 80 ms de cauda simulada, um terço dos símbolos cai errado, e alargar o intervalo de guarda não ajuda. Isso pesa menos do que parece neste link, que **não tem reverberação mensurável** — mas pesaria em outra sala.

## Correção de erro

`fec.py`. Código convolucional de comprimento de restrição 7 com os polinômios padrão da Voyager, decodificador Viterbi de **decisão suave**, entrelaçamento, repetição opcional e uma palavra de sincronismo de 31 bits (sequência de comprimento máximo).

**Por que ela é obrigatória:** o link entrega entre 10% e 25% dos bits errados. Isso não é canal que um CRC resgate — um CRC só informa que o bloco está arruinado — e é muito além do que retransmissão sustenta, já que a essa taxa quase todo bloco está arruinado. Os bits precisam ser consertáveis onde caem.

O que cada ajuste sobrevive, medido contra erros simulados em blocos de 64 bytes:

| Configuração | Blocos recuperados |
|---|---|
| taxa 1/2, decisão rígida | falha acima de 8% de bits errados |
| taxa 1/2, decisão suave | segura até 8%, marginal em 10% |
| taxa 1/3, decisão suave | 100% até 13%, 90% em 16% |
| **taxa 1/3, repetição 2** | **100% até 25%, 90% em 30%** |

**Duas dessas colunas são de graça.**

A decisão suave não custa nada além de guardar um número que o demodulador já calculava. Decidir cada par como 0 ou 1 e contar votos joga fora *quanta* confiança cada par tinha; um par que dividiu 51/49 valia o mesmo que um que dividiu 99/1. Só essa diferença move a taxa de erro tolerável de 8% para 13%. A repetição combina somando log-verossimilhanças, que é ótimo, então não precisa de polinômio adivinhado.

**O 8N1 é abandonado dentro do bloco**, e isso remove um modo de falha inteiro em vez de mitigá-lo. Sob 8N1 um único start ou stop bit corrompido desloca todos os bytes seguintes, então um bit ruim destrói o resto do bloco. Um bloco de comprimento fixo não tem o que deslocar.

**O bloco começa numa palavra de sincronismo, não num deslocamento contado.** Contar não sobrevive a este receptor: o ajuste early/late consome um número diferente de amostras por símbolo conforme corrige, então o início do bloco escorrega ao longo de um preâmbulo — e um bloco que começa um bit atrasado não decodifica nada. Isso foi visto: os casos com reverberação recuperavam 1 byte de 24 com deslocamento contado e 24 de 24 com sincronismo correlacionado.

Uma armadilha da API: `frame`, `encode` e `decode` usam taxa 1/3 por padrão, mas as funções de baixo nível `encode_bits` e `decode_soft` usam 1/2. Se você chamar as de baixo nível direto, passe `POLYS_R13` explicitamente.

## Sincronismo: varredura nas duas pontas do quadro

O receptor precisa saber onde cada símbolo começa. O que o código sempre fez foi um ajuste early/late guiado pelo contraste da própria decisão — ele corrige aos poucos enquanto ouve, e isso é circular: para saber onde está a fronteira já é preciso estar decidindo bem.

A alternativa é dar a ele algo para **adquirir** em vez de algo para convergir. `syncsweep on` põe um tom varrido de 80 ms em cada ponta do quadro M-ário codificado, e o receptor acha os dois por filtro casado. O primeiro pico dá o início do quadro como índice absoluto de amostra; o intervalo entre os dois, dividido pelos símbolos que ele abrange, dá o período **medido** em vez de rastreado. O relógio deixa de ser estimado e passa a ser lido.

**Os picos são ordenados por posição, nunca por altura.** As duas varreduras são idênticas e é o canal que decide qual chega mais forte: medido, a do fim ganhou quatro vezes em oito, por margens abaixo de 2%. Tomar a mais alta como sendo a primeira invertia o par metade das vezes — e um par invertido não é detecção fraca, é resposta errada com confiança.

**O receptor relê o áudio guardado, e não tem escolha.** O caminho streaming demodula cada bloco conforme ele chega, corrigindo enquanto anda, então um deslocamento descoberto depois não se aplica a decisões já tomadas. `AudioNode._sweep_llr` redemodula o áudio que ficou guardado, com o relógio travado no que as varreduras mediram.

**O padrão é desligado, e o padrão é a proteção.** As varreduras mudam o formato do quadro, então as duas máquinas têm de concordar. Um receptor que espera varredura e não acha cai de volta no gate e só perde a melhoria; mas um transmissor que manda varredura para um receptor que não procura põe 80 ms de tom varrido onde deviam estar os primeiros símbolos do preâmbulo. O perigo não é a divergência em si, é como ela chega — `pull` alcança uma máquina de cada vez, e na seguidora o canal serial é feito dos arquivos que estão sendo substituídos. Desligado por padrão, um `pull` que chega só numa ponta não muda nada; `b syncsweep on` liga as duas de uma vez.

### O que elas compram

Um canal limpo não deixa margem para uma melhoria de sincronismo aparecer — tudo decodifica de qualquer jeito e a comparação não mede nada. Por isso o mecanismo foi desenvolvido contra um canal **degradado de propósito**: ganho acima do teto do limitador, onde parte das gravações chega saturada. Isso é estressor deliberado, não erro de calibração, e precisa ser dito ao lado do número — distorção não é ruído, e um resultado lido ali não transfere sozinho para um enlace com folga.

**Ressalva, e ela vem antes dos números: isto é auto-captura, uma máquina só.** O mesmo computador toca pela caixa Bluetooth e grava pelo microfone interno. O ar, o pente da sala, o limitador e o microfone são reais; o que falta é específico — a caixa tem cristal próprio, então a deriva de taxa de amostragem está presente, ao custo de um codec com perda que o enlace real não tem. Nada disso entra na tabela principal deste README antes de ser revalidado nas duas máquinas.

Sessenta gravações no ponto de operação calibrado (ganho 0,30). As colunas gate e varredura saem do **mesmo** áudio, então a comparação não tem sala nem momento diferente dentro dela:

| Alinhamento | Bits certos | Blocos íntegros |
|---|---|---|
| gate early/late | 88,8% | 43/60 |
| **varredura nas duas pontas** | **90,8%** | **59/60** |

A varredura lê mais bits em **59 das 60** gravações — comparação pareada, mesmo áudio nas duas colunas, o que é bem mais forte que a diferença de duas médias.

**O que ela compra é seguro contra colapso, não caso médio.** O gate fica cerca de um ponto abaixo do melhor deslocamento possível na maioria das vezes; o problema é quando ele erra feio. Numa gravação leu 49,0% dos bits onde um relógio travado no lugar certo leu 84,9%. Taxa de código nenhuma conserta um bloco cujos símbolos nunca foram amostrados onde os símbolos estavam — por isso a diferença aparece inteira na coluna de blocos e quase não aparece na de bits.

**Bits e blocos não são a mesma régua, e não devem ser lidos como se fossem.** Acerto de bit é medido no melhor deslizamento achado por força bruta contra o payload conhecido — é um oráculo, serve para diagnosticar. Bloco recuperado é medido onde o alinhamento de fato caiu, e é o que o enlace entrega.

### Redundância: com as varreduras, `fecrep 1` basta

Com o ponto de operação calibrado e as varreduras ligadas, no acervo Bluetooth a repetição 1 recupera os mesmos **12 blocos de 12** que a repetição 2, em 4,49 s contra 7,41 s por bloco de 48 bytes — 10,7 B/s contra 6,5. A redundância extra não compra nada ali e custa 40% do tempo no ar.

Isso **não aposenta a tabela de `fecrep`** do enlace de duas máquinas, que é outro canal e mais difícil. O que fica aposentado é a suposição de que taxa 1/3 sozinha é inviável *em geral*: essa leitura veio do acervo degradado de propósito e descreve aquele estressor, não a camada.

## Fluxo de medição

**Esta é a parte mais fácil de perder e a que mais rendeu.** Julgar uma ideia transmitindo-a mede a ideia e a sala ao mesmo tempo, e a sala não fica parada: uma cadeira se move, o volume oscila, e duas execuções do mesmo código discordam. Pior, testar uma mudança de uma linha custa uma ida e volta com a segunda máquina.

Então **grave uma vez e guarde**. Uma gravação é um canal fixo: dez ideias podem ser pontuadas contra os mesmos segundos de áudio real, e os números são comparáveis porque o áudio é literalmente idêntico.

```bash
# grave a outra máquina transmitindo uma carga conhecida
# (pare o console antes: a porta serial aceita um dono só)
./venv/bin/python capture.py --port /dev/ttyUSB0 --mode mary --fec \
    --gain 0.5 --repeat 1 --bytes 32 --trials 6 --label o-que-mudou

# ou uma mensagem legível, para uma demonstração que se lê
./venv/bin/python capture.py --port /dev/ttyUSB0 --mode mary --fec \
    --gain 0.5 --repeat 1 --text "Ola! 16 tons, quatro bits por nota"

# pontue variações de demodulação contra o acervo inteiro, offline
./venv/bin/python bench.py
./venv/bin/python bench.py --detail          # mostra também o que voltou
./venv/bin/python bench.py --only contraste  # só as variantes com esse nome
```

Uma ideia nova é **uma entrada na lista `VARIANTS` do `bench.py`** e custa segundos, sem envolver a outra máquina.

### Uma máquina só, quando a segunda não está na mesa

`selfcapture.py` grava esta máquina transmitindo para ela mesma pelo ar: alto-falante, sala, microfone, sem cabo serial e sem lado remoto. Escreve o mesmo par WAV+JSON que o `capture.py`, com as mesmas chaves de metadado, então `bench.py` e `align.py` pontuam sem distinguir de onde veio.

```bash
./venv/bin/python selfcapture.py --mode mary --fec --sync-chirp --trials 8 \
    --gain 0.30 --in-device Mic1 --out-device <sink> --link bluetooth

./venv/bin/python align.py captures-self   # quanto do erro é sincronismo, quanto é canal
```

`align.py` é a sonda que separa essas duas coisas: força o deslocamento de símbolo por força bruta e entrega ao detector divisores que ele não teria como calcular sozinho. Serve para responder "vale a pena construir isto" **antes** de construir. Foi ele que matou metade de um esquema proposto — um piloto por tom pontuou 80,9% dos bits contra 88,3% da estimativa cega que já estava no código, porque dividir pelo *ganho* do canal é a operação errada: a decisão "este tom está presente" quer energia sobre o **ruído** daquela frequência, não sobre o sinal.

Leia o `--link` antes de comparar duas gravações de auto-captura: alto-falantes diferentes são canais diferentes, e a ressalva está na seção *Sincronismo*.

### Uma campanha, uma pasta

Uma porcentagem num caderno não é medição. O áudio de onde ela veio, os ajustes que a produziram e o commit do código que a leu têm de sobreviver juntos, ou reproduzir a figura significa rodar a sala de novo — e a sala não fica parada. `study.py` roda uma campanha e deixa tudo numa pasta datada:

```
studies/<quando>-<nome>/
    HEADER.md      o que foi medido, em que hardware, com quais ajustes fixos, e as ressalvas
    results.csv    uma linha por gravação
    results.json   o mesmo, com os metadados completos
    recordings/    os pares WAV+JSON
    figures/       espectrogramas e o gráfico de resumo
```

```bash
./venv/bin/python -u study.py --name melhor-caso --trials 12 --sync-chirp \
    --gain 0.30 --repeat 1 --link bluetooth --in-device Mic1 --out-device <sink>

./venv/bin/python -u study.py --name ganho --sweep gain=0.20,0.25,0.30,0.38

./venv/bin/python study.py --rescore studies/<pasta>   # repontua sem tocar na sala
```

O `HEADER.md` abre com o commit em que o código estava, e isso não é burocracia: acerto de bit é afirmação sobre o decodificador tanto quanto sobre o canal, e este decodificador muda toda semana. **Um eixo varrido por vez** — dois eixos multiplicam as gravações, e este enlace precisa mais de repetições do que de largura.

### Medir o canal, em vez de supor

```bash
# a outra máquina toca uma varredura de frequência, este lado grava
./venv/bin/python capture.py --port /dev/ttyUSB0 --chirp "400 4200 10" --label varredura
./venv/bin/python channel.py captures/<stem>.json --bins 76
```

Toda escolha de tom neste projeto tinha vindo de uma banda tomada por fé — 700 a 2900 Hz, porque é onde a fala vive e alto-falantes pequenos deveriam funcionar. Medido, o tom de 700 Hz **não carregava informação nenhuma**: chegava 0,8 dB *mais fraco* quando transmitido do que quando não era. Um dos cinco votos que decidiam cada bit era uma moeda.

### Armadilhas já pagas

- **O `loopback_test.py` não vê falha de sincronismo.** O quadro sintético dele abre com preâmbulo alternado em nível de bit, que entrega o travamento pronto antes da carga começar. Uma regressão que zerou o link real passou nele sem reclamar. Toda mudança que toque em temporização precisa passar pelo acervo, não só pelo loopback.
- **Recuperação de bytes é métrica abrupta.** Com poucas gravações, variações de 8% a 22% entre parâmetros vizinhos aparecem sem tendência nenhuma — é ruído. Para decidir ajuste fino, meça acerto de *bits* com alinhamento por força bruta, que é estável, ou grave muito mais.
- **Acerto de bit e bloco recuperado não medem a mesma coisa, e não podem ser lidos na mesma régua.** Acerto de bit é medido no melhor deslizamento por força bruta, que é escolhido para favorecer; bloco recuperado é medido onde o receptor de fato caiu. Um gate pode ler 95% dos bits e perder o bloco, e a coluna de bits não mostra por quê. Meça as duas, sempre no mesmo critério em todas as linhas.
- **Poucas gravações não são um resultado.** Configurações vizinhas já pontuaram 8% e 22% sem tendência nenhuma, só por quais blocos calharam de cair. Para decidir um ajuste fino, meça acerto de bit num alinhamento forçado, que é estável, ou grave muito mais.

## O canal, medido

Números desta sala, deste par de máquinas. Meça de novo se qualquer um dos dois mudar.

| Faixa | Situação |
|---|---|
| 550–3500 Hz | banda útil |
| 4000 Hz | SNR já caindo |
| 5000 Hz | ~0 dB |
| **acima de 6 kHz** | **SNR negativo** |

Acima de 9 kHz o nível trava e não muda mais: isso é o piso de ruído, não sinal atenuado. **Ultrassom não é viável neste hardware.** O raciocínio a favor está certo — a sala é silenciosa no agudo e a banda é larga — mas o alto-falante e o microfone simplesmente não entregam lá. Precisaria de tweeter e microfone de medição.

**A resposta é um pente, não uma curva suave.** Com resolução de 50 Hz há covas de 13 a 18 dB entre células vizinhas. Picos em 775, 975 e 1175 Hz, espaçados 200 Hz, indicam uma reflexão com cerca de 5 ms de atraso. A consequência prática: um par de tons com um pé numa cova vota sempre no mesmo bit. Foi o que aconteceu com o par (700, 900) — 850 Hz é cova — e com (2160, 1960) — 2150 Hz é cova. Os dois deram cerca de 50% de erro.

**Não há reverberação mensurável.** O rastro depois da rajada não decai; ele estaciona no piso de ruído, 11 a 13 dB abaixo do pico. A premissa de "eco de 80 ms" que orientou parte do desenho não se sustenta neste link — ela é uma propriedade do teste sintético, não da sala.

## Ganho: importa, e depende da camada

**A M-ária precisa de `gain 0.5`.** Ela toca um tom sozinho com a amplitude inteira, enquanto um acorde de cinco tons saía com um quinto disso. Com 0,8 ela bate no limitador da saída — e o sintoma engana, porque os blocos falham de forma aleatória, sem relação com tamanho nem com redundância.

| Ganho de saída | Blocos íntegros | Pico recebido |
|---|---|---|
| 0,25 | 2 de 4 | 0,20 |
| **0,50** | **4 de 4** | 0,52 |
| 0,80 | 5 de 15 | 0,82 |

Sintoma de saturação: pico recebido ≥ 0,8 com blocos falhando sem padrão. Os acordes nunca sofriam disso.

## Uso: uma máquina

Modem ao vivo, modo terminal:

```bash
./venv/bin/python app.py
```

Modo PTY — expõe um dispositivo serial virtual:

```bash
./venv/bin/python app.py --pty
# [+] Created PTY: /dev/pts/N
picocom -b 1200 /dev/pts/N
```

Qualquer programa que fale com porta serial (picocom, minicom, `pppd`, scripts com pyserial) enxerga o canal acústico como `/dev/pts/N`.

Calibração de nível, quando um link real desanda — **é a primeira coisa a tentar**, porque nível quase sempre é a culpa, não o DSP:

```bash
./venv/bin/python app.py --tune tx    # máquina A transmite padrão
./venv/bin/python app.py --tune rx    # máquina B mede
```

| Status | Causa | O que fazer |
|---|---|---|
| `LOCK` | Enlace bom | Nada. |
| `no signal` | Nada chegando | Verifique se A transmite, e o microfone de B. |
| `TOO WEAK - raise TX volume` | Portadora abaixo do squelch | Aumente o volume de A ou o ganho de B. |
| `CLIPPING - lower the volume` | Entrada saturando | Baixe o volume de A ou o ganho de B. |
| `NOISY - no carrier in band` | Energia fora da banda | Ruído ambiente dominando. |
| `carrier, no bytes` | Sinal na banda, nada decodifica | Baud ou tons diferentes entre as pontas. |

## Uso: duas máquinas

O cabo serial é canal de controle **fora de banda**. Ele nunca carrega dados: cada byte pontuado atravessa o ar, que continua sendo a coisa sob teste.

Lado sem teclado:

```bash
./venv/bin/python -u console.py --role agent --port /dev/ttyUSB0
./agent.sh    # o mesmo, supervisionado: reinicia depois de um crash
```

**Use `-u` sempre que a saída não for direto para o terminal.** Num terminal,
Python usa buffer de linha e você vê tudo na hora; redirecionado para arquivo
ou pipe, ele passa a buffer de bloco e a saída fica muda por minutos. Isso vale
para qualquer coisa demorada aqui — o agent, o `recvfile.py`, o `capture.py` —
e o estrago não é estético: **saída muda é indistinguível de um processo que
não subiu**. Custou uma tarde neste projeto, duas vezes, uma delas
diagnosticada como "o `restart` remoto falhou" quando ele tinha funcionado.

O `agent.sh` já passa `-u`. Pelo mesmo motivo, `updater.restart` re-executa com
`sys.orig_argv` e não `sys.argv`: `sys.argv` descarta as flags do
interpretador, então um `restart` devolveria o processo sem o `-u` que ele
tinha.

Lado com o teclado (REPL):

```bash
./venv/bin/python console.py --role console --port COM4
```

Prefixe `r ` para agir na outra máquina, `b ` para as duas. Um `AudioNode` e um `execute()` rodam nos **dois** papéis, então adicionar um comando num lugar dá o comando aos dois lados.

Três desses ajustes precisam bater nas **duas** pontas, e nenhum deles avisa quando não bate — o decodificador só produz lixo, que se lê como canal ruim: `fecrep`, `marygap` e `syncsweep`. Ligue-os com `b `, nunca com `r `.

Comandos que importam:

```
mode fsk|mfsk|mary   camada fisica
gain <0..1>          amplitude de saida (0.5 para mary)
fecsend <texto>      transmite com correcao de erro
fecrep <n>           repeticoes de cada bit codificado
fecpar on|off        mfsk paralelo: 5 bits por simbolo
syncsweep on|off     varredura de sincronismo nas duas pontas do quadro mary
fecpkt <arq> <n>     pacote n de um arquivo, com correcao de erro
chirp [f0 f1 seg]    varredura, para medir a resposta do canal
dev out auto         volta ao dispositivo padrao do sistema
level / meter        medidor de nivel
pull / restart       atualiza o codigo e reinicia, pela serial
```

### Atualizar a máquina remota

`pull` busca o código e `restart` re-executa o processo, tudo pela serial. `pull` faz **hard reset**, não merge — a árvore da máquina seguidora não é onde o trabalho acontece, e um conflito de merge numa máquina sem ninguém no teclado é beco sem saída. Por isso é destrutivo, e uma árvore suja aborta o pull a menos que você passe `pull force`.

Um `pull` que não roda desfaz a si mesmo: `updater._broken()` compila `console.py`, `serial_link.py`, `modem.py` e `updater.py` depois do reset, e reverte se algum falhar. A assimetria é o ponto — naquela máquina o canal serial é a única entrada, e ele é feito dos mesmos arquivos que estão sendo substituídos.

### Índice de dispositivo apodrecido

Um índice de dispositivo fixo é a coisa certa até deixar de ser. A numeração muda quando algo é plugado ou removido, e um índice velho falha com erros que parecem hardware quebrado — cinco índices numa máquina deram `Invalid device`, `Device unavailable`, `Invalid sample rate` e um erro de DirectSound, com o áudio dela funcionando perfeitamente.

**Erros diferentes em dispositivos diferentes significa índice velho, não hardware.** `dev out auto` devolve a escolha ao sistema.

### Teste pontuado

```bash
./venv/bin/python linktest.py --check --port /dev/ttyUSB0      # só a fiação serial
./venv/bin/python linktest.py --role rx --port /dev/ttyUSB0    # comece por este lado
./venv/bin/python linktest.py --role tx --port COM4 --trials 5 # na outra máquina
```

### Transferir um arquivo

ARQ pare-e-espere dirigido inteiramente pela ponta receptora. A outra máquina fica sem estado: mandam nela `fecpkt <arquivo> <n>` e ela toca aquele pacote, nada mais. Este lado decide o que pedir e quando pedir de novo, e é isso que faz um pacote perdido custar uma retransmissão em vez do arquivo todo.

```bash
./venv/bin/python -u recvfile.py --port /dev/ttyUSB0 \
    --remote-file testcard.bmp --out recebida.bmp \
    --fec --mode mary --packet-size 64 --repeat 1 --retries 3
```

**`--repeat` tem de bater com o que a outra máquina usa.** O `recvfile.py` manda `fecrep` no setup justamente por isso — um decodificador não tem como detectar essa incompatibilidade, ele só produz lixo que falha no CRC, indistinguível de canal ruim.

Pelo mesmo motivo ele manda **`syncsweep off`**: o `fecpkt` passa pelo mesmo `_fec_frame` do `fecsend`, então uma máquina deixada com a varredura ligada poria 80 ms de tom varrido em cada ponta de todo pacote — e este receptor não procura por eles. Uma ida e volta na serial no setup compra essa falha de saída. Ensinar o `recvfile.py` a *usar* as varreduras vale a pena e ainda não foi medido.

**`--packet-size` importa mais do que parece.** Cada pacote paga o próprio preâmbulo para o receptor travar o relógio de símbolo, e esse preâmbulo dura 1,2 s: 28% do tempo no ar com pacotes de 32 bytes, 19% com 64, 12% com 128. Para a mesma imagem de 1334 bytes isso é 3,0 minutos contra 1,8.

O `--gain` padrão é 0,5, que é o que a M-ária mede melhor — veja a seção sobre
ganho acima. Era 0,35, herdado da era MFSK, e foi trocado quando a medição
mostrou que aquele valor não serve para um tom sozinho em amplitude cheia.

## A porta serial aceita um dono só

`console.py`, `capture.py`, `recvfile.py` e `linktest.py` todos querem a porta. **Pare o console antes de rodar qualquer um dos outros.** Ao trocar de processo, dê alguns segundos: o adaptador USB-serial não libera a porta no instante em que o processo morre, e abrir cedo demais falha de um jeito que parece a outra máquina não responder.

## O artigo

O artigo do VII SIMECA vive em `artigo/`, escrito em markdown (`artigo/artigo_modem.md`) e montado em docx e pdf por um conversor que preenche o modelo do evento. Monta-se de qualquer pasta, e nos dois sistemas, porque a lógica está num arquivo só (`artigo/monta.py`) e os dois scripts abaixo apenas escolhem o interpretador:

```bash
./artigo/monta.sh                 # docx e pdf, com figuras
./artigo/monta.sh --sem-figuras   # só as legendas, para revisar o texto
./artigo/monta.sh --verifica      # só confere o que já foi gerado
```

```bat
artigo\monta.cmd
artigo\monta.cmd --sem-figuras
artigo\monta.cmd --verifica
```

O conversor está em `artigo/simeca-md`, versionado dentro deste repositório: não há passo de submódulo, nem `pip install`, e ele não usa a `venv` do projeto nem biblioteca de terceiros. Pede Python 3.11 ou mais novo, pandoc para as equações, e LibreOffice ou Word só para o PDF. Instalação, mensagens de erro e o caso do Windows estão em `artigo/MONTAGEM.md`.

## Arquivos

| Arquivo | Papel | O que não pode tocar |
|---|---|---|
| `modem.py` | DSP puro. Os três moduladores e demoduladores. | I/O, threads, dispositivos |
| `fec.py` | Correção de erro. Bits e log-verossimilhanças entram, bytes saem. | I/O, estado |
| `xfer.py` | Pacotes: split, build, parse, CRC. Acima do modem. | dispositivos, portas |
| `scoring.py` | Geração de carga e pontuação tolerante a alinhamento. | dispositivos, portas |
| `recording.py` | Formato em disco de uma gravação: WAV float32 + JSON irmão. | dispositivos, portas |
| `serial_link.py` | Canal de controle: `Control`, `pack`/`unpack`. | áudio |
| `updater.py` | Git: fetch, reset, re-exec. | serial, áudio |
| `app.py` | Runtime: threads, filas, stream PortAudio, stdio/PTY. | — |
| `console.py` | Runtime interativo. Uma tabela de comandos para os dois papéis. | duplicar a tabela |
| `linktest.py` | Teste pontuado entre as duas máquinas. | — |
| `capture.py` | Grava a outra máquina transmitindo carga conhecida. | — |
| `recvfile.py` | Puxa um arquivo com ARQ pare-e-espere. | — |
| `selfcapture.py` | Runtime, uma máquina só. Grava esta máquina transmitindo para si mesma pelo ar. | serial |
| `bench.py` | Offline. Pontua variações de demodulação contra o acervo. | áudio, serial |
| `align.py` | Offline. Separa o erro que sincronismo conserta do que é canal. | áudio, serial |
| `study.py` | Campanha: grava, pontua e arquiva numa pasta com cabeçalho. | — |
| `channel.py` | Offline. Transforma uma varredura em mapa de frequências úteis. | áudio, serial |
| `loopback_test.py` | A suíte de testes inteira. | hardware |
| `agent.sh` | Supervisor da máquina seguidora. | — |
| `artigo/monta.py` | Montagem do artigo: confere o Python e chama o conversor. | — |
| `artigo/simeca-md/` | O conversor de markdown para docx, cópia versionada aqui. | — |
| `artigo/monta.sh`, `artigo/monta.cmd` | Invocadores do `monta.py`, Linux e Windows. Só escolhem o interpretador. | duplicar a lógica |

## Decisões de arquitetura

### DSP separado de I/O

`modem.py` não importa `sounddevice`, não cria threads e não toca em arquivo nenhum. Recebe `np.ndarray` e devolve `bytes`, e vice-versa. Consequência: o loopback test roda sem hardware, sem PortAudio, sem permissão de dispositivo — e exercita exatamente o código que roda ao vivo. `fec.py`, `scoring.py` e `recording.py` seguem a mesma regra um nível acima.

### Os moduladores e demoduladores têm estado

`FSKModulator` carrega `self.phase` entre chamadas (FSK de fase contínua — reiniciar produz cliques e energia fora da banda). `FSKDemodulator` carrega `bpf_state`, `lpf_state` e `prev_samples`, porque o áudio chega em blocos de 2048 amostras e um `lfilter` sem estado poria um transiente em cada fronteira de bloco, destruindo os bits ali.

Uma instância por stream. Use `reset()` entre sessões, nunca compartilhe entre threads.

### Discriminador delay-and-multiply, não correlação

```
bandpass -> x[n] * x[n-D] -> lowpass
```

com `D = fs / (4 * f_center)`, cerca de 90° em 1700 Hz. Depois do passa-baixas, mark é positivo e space é negativo, então a decisão de bit vira um teste de sinal. Não há recuperação de portadora envolvida.

Uma multiplicação e dois `lfilter` por bloco, tudo em C via scipy. Tolera desvio de clock muito melhor que correlação coerente. O preço é pior desempenho em SNR baixo — que não é o gargalo em acoplamento acústico curto.

### O callback de áudio faz o mínimo

`audio_callback` roda na thread de tempo real do PortAudio. Ele só move dados entre filas. Todo o DSP acontece em threads normais. Não acrescente trabalho ali.

### O squelch significa coisas diferentes em cada camada

Bell 202 gateia na amplitude absoluta de banda-base (~0,005). MFSK gateia em `contrast_min`, uma razão de 0 a 1 (~0,15 a 0,3). **Não são intercambiáveis** — 0,005 como limiar de contraste é quase nenhum gate. O comando `squelch` do console roteia para o que a camada ativa usa.

O squelch do Bell 202 é quadrático e é um piso duro de nível: `mult = x[n]·x[n-D]`, então a amplitude de banda-base vai com o *quadrado* da entrada. Com `squelch=0.005`, um sinal chegando a amplitude 0,05 cai em ~0,0025 de banda-base e é silenciado — zero bytes num canal que de resto é perfeito. "Nenhum byte, mas o `--tune` mostra energia na banda" é isso, não bug de DSP.

### Um voto sozinho decodifica uma sala vazia

Um voto é uma razão, então cinco tons de puro ruído ainda elegem um bit — observado, 485 bytes decodificados do silêncio. `MFSK_PRESENCE_MIN` é a segunda condição: o tom perdedor de cada par é uma frequência que ninguém transmitiu, então a razão mediana vencedor/perdedor separa um símbolo real de uma sala. Vale 1,3, deliberadamente baixo: 1,5 para cima começa a rejeitar símbolos legítimos sem barrar ruído adicional, porque é a margem de votos que rejeita ruído de verdade.

### O preâmbulo e a cauda não são opcionais

A recuperação de temporização é um gate early/late guiado por contraste, então precisa de *transições* — um preâmbulo que fica parado em mark não ensina nada. Na outra ponta, o demodulador mantém pouco mais de um símbolo em buffer, então uma rajada que para seca deixa o último byte preso ali. O `_feeder` do `console.py` acrescenta `idle(4)` depois de uma rajada MFSK por esse motivo; sem isso, todo `send` perdia o byte final, calado.

### Throughput medido em tom contínuo mente

Enquadrado 8N1, `0x55` é `0` `10101010` `1` — uma onda quadrada perfeitamente periódica na metade da taxa de símbolo. O detector de start bit procura uma borda de descida, e todo limite de símbolo oferece uma, então ele pode travar na borda errada e ainda produzir bytes plausíveis. Medido num link real: tom estável decodificando a 100 B/s enquanto os bytes recebidos alternavam entre `0x55` e `0x75` — um bit de diferença, a assinatura de enquadramento na borda errada. O mesmo link não recuperou nada de uma mensagem de verdade.

Avalie um link com `linktest.py` e sua carga aleatória. Trate throughput de tom como "a portadora chega", nada mais.

### A razão em banda é uma razão de somas

`level_rms / input_rms` por bloco, com média, está errado: um bloco quase silencioso tem denominador quase zero enquanto o passa-faixa ainda está tocando pelo seu próprio estado inicial, e um único bloco desses joga a janela além de 100% — observado em 9713% antes da correção. Acumule `input_rms` e `level_rms` separadamente, divida uma vez, limite em 1,0.

## Estado atual e próximos passos

**Funciona:**

- Blocos protegidos por FEC atravessam o ar. M-ária a ganho 0,5 recuperou 9 de 11 blocos a ~9,4 B/s; MFSK votado, 4 de 4 a ~1,8 B/s.
- Uma mensagem legível de 58 caracteres atravessou íntegra.
- Ruído puro decodifica 2 bytes de lixo, contra 485 antes do gate de presença.
- O fluxo de gravação-e-pontuação: uma ideia nova custa segundos, não uma ida e volta com a segunda máquina.
- **Sincronismo por varredura** (`syncsweep on`), que recupera 59 blocos de 60 na auto-captura contra 43 do gate early/late, sobre o mesmo áudio.
- **Campanha arquivada** (`study.py`): dados, gravações, figuras e cabeçalho numa pasta, com o commit que produziu os números.
- Atualização e reinício remotos pela serial, incluindo no Windows.

**Não funciona:**

- **Transferência de arquivo inteiro.** 1 pacote de 21, com pacotes de 81 bytes.
- **A camada paralela**, em 5 de 9 blocos, fica atrás tanto da votada (confiabilidade) quanto da M-ária (velocidade).

**Pistas abertas, em ordem de retorno esperado:**

1. **Comprimento do bloco na M-ária.** Blocos de 24 a 58 bytes decodificaram 9 de 11; pacotes de 81 bytes decodificaram 1 de 21. Mais símbolos entre re-sincronizações, e um escorregão de relógio desloca quatro bits e desalinha todo o resto. Medir a taxa de sucesso contra o tamanho do bloco é barato e decide o desenho da transferência.
2. **Ajuste fino do ganho** entre 0,4 e 0,6, contra o acervo.
3. **Fechar a lacuna da camada paralela.** A falha não é do decodificador — foi o sincronismo, e a correção que o levou de 1/9 para 5/9 saiu de reprocessar gravações, sem transmitir nada.
4. **Revalidar a varredura nas duas máquinas.** Todo número dela vem de auto-captura. `b syncsweep on` nos dois lados antes de medir; nada disso entra na tabela principal antes disso.
5. **Ensinar o `recvfile.py` a usar as varreduras.** Hoje ele as desliga no setup, por segurança. É o caminho que mais precisa delas, e é a transferência de arquivo que ainda não funciona.

**Coisas já tentadas e rejeitadas pela medição** (não repita sem um motivo novo):

- Equalizador por tom com média móvel nos acordes: a média absorve a cauda do símbolo anterior e passa a tratá-la como nível normal daquele tom.
- Voto ponderado treinado no preâmbulo: empate — 110 bits de treino não estimam confiabilidade.
- Janelamento Hann/Tukey das sondas: melhora o contraste em dB e não melhora a recuperação de bytes.
- Escolher os tons pelos picos medidos: o pente desliza quando algo se move na sala.
- Alargar os pares de 200 para 250 Hz: recuperação de pacotes caiu de 7/8 para 3/8. A janela após o guarda é de 8,5 ms, cerca de 118 Hz de resolução, e afastar os membros de um par aproxima os pares entre si.
- **Piloto por tom na M-ária**, para aprender o ganho do canal em cada frequência e dividir por ele: 80,9% dos bits contra 88,3% da estimativa cega que já está no código. Dividir pelo ganho é a operação errada — a decisão quer energia sobre o *ruído* daquela frequência. E um piso de ruído perfeito rende 88,4% contra os 88,3% da estimativa cega, ou seja, a estimativa cega já está no teto e não há o que ensinar a ela.
- **Silêncio entre símbolos** (`marygap`): ajuda os bits de forma monotônica — 86,7% em 0, 88,0% em 0,15, 88,9% em 0,30 — e mesmo assim não paga. São 30% do tempo no ar por dois pontos, onde os mesmos 30% em redundância rendem mais.

**Limitações que permanecem:**

- Half-duplex na prática. Não há controle de acesso ao meio; transmissão simultânea colide.
- Squelch fixo, não adaptativo ao ruído do ambiente.
- Sem cancelamento de eco: o modem escuta a própria transmissão.
- O preâmbulo aparece no RX no caminho 8N1. O modo stdio faz uma limpeza grosseira; o PTY entrega tudo cru.
- `pyserial` está no `requirements.txt` e só as ferramentas de duas máquinas o importam.
