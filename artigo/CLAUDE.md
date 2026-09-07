# Instruções: artigo VII SIMECA (modem acústico)

Instruções locais para qualquer sessão que trabalhe nesta pasta. Registram as decisões de forma tomadas com o autor; não re-perguntar o que já está decidido aqui.

## O que é este trabalho

Artigo em **português** para o VII SIMECA (IFPR) sobre o modem acústico do repositório raiz. Dois autores: Winderson (primeiro autor, dados a completar por ele) e Jefferson (mesmos dados do artigo da roda de reação).

**Enquadramento, decidido em 2026-09-05: didático.** O artigo apresenta o sistema, compara brevemente com outros meios de transmissão, avalia o problema do canal acústico e propõe uma solução para este caso. Não pretende substituir outro meio nem reivindicar melhoria sobre a literatura.

**O modelo do evento manda na estrutura, mas não trava o título da seção 2.** Lido em 2026-09-05 de `Modelo de artigo - VII SIMECA.docx`. Seções numeradas obrigatórias, nesta ordem: 1 INTRODUÇÃO, 2 FUNDAMENTAÇÃO TEÓRICA, 3 METODOLOGIA, 4 RESULTADOS E DISCUSSÕES, 5 CONSIDERAÇÕES FINAIS. Só os títulos 2 e 3 podem ser trocados. Não numeradas e também obrigatórias: AGRADECIMENTOS, FINANCIAMENTO, DECLARAÇÃO DE USO DE INTELIGÊNCIA ARTIFICIAL GENERATIVA, CONFLITO DE INTERESSES, REFERÊNCIAS. Legenda de figura abaixo do elemento, de tabela acima. ORCID obrigatório para todos os autores, até seis.

**Estrutura corrente, decisão do autor em 2026-09-06, que revoga a subdivisão de 2026-09-05 abaixo:** 1 INTRODUÇÃO, 2 PRINCÍPIO DE FUNCIONAMENTO, 3 MÉTODO DE MEDIÇÃO, 4 RESULTADOS EXPERIMENTAIS, 5 CONSIDERAÇÕES FINAIS. Não há seção de fundamentação teórica. O modelo do evento sugere uma, mas isso é a forma de outro professor, não regra de conteúdo obrigatória, já que só os títulos 2 e 3 são livres e o conteúdo de cada um não é ditado. Cada mecanismo carrega a teoria mínima que o sustenta, no ponto em que é usado, em vez de um bloco de conceitos de terceiros isolado do que construímos. A introdução tem uma lauda no máximo. Objetividade antes de volume, em toda seção.

**Sumário de 2026-09-05, superado pela decisão de 2026-09-06 acima, registrado porque fixou decisões de conteúdo que sobrevivem à mudança de forma:** o mapeamento era "O meio" para 2.3 dentro de uma fundamentação teórica, "Camada física" para 3.1, "Camada de enlace" para 3.2, bancada e método para 3.3 sob o título "O MODEM ACÚSTICO E O MÉTODO DE MEDIÇÃO", resultados em 4, considerações em 5. Por trás dele estava o sumário ainda mais original, de 2026-09-05: 1 Introdução; 2 O meio; 3 Camada física; 4 Camada de enlace; 5 Bancada e resultados; 6 Considerações finais, em que o meio não é camada, fica abaixo da física, responde "com o que se está lidando" enquanto a física responde "como se transmite apesar disso", a seção 2 não adianta números medidos nesta bancada nem o protótipo e usa número só para ordem de grandeza, e os números medidos ficam nos resultados. Essa divisão entre o que é princípio e o que é número medido continua valendo dentro da seção 2 corrente, só que sem uma seção de teoria separada para abrigá-la.

**Duas camadas, decisão do autor em 2026-09-05.** O artigo apresenta a implementação da camada física e da camada de enlace. Física: as quatro formas de transmissão (2-FSK, 5×2-FSK votada, 5×2-FSK multicanal, 16-FSK), o sincronismo de símbolo e a decisão suave do demodulador. Enlace: o bloco codificado (convolucional K=7, Viterbi suave, entrelaçamento, repetição, palavra de sincronismo por correlação), o pacote com número de sequência e CRC, a subdivisão do arquivo em pacotes e o reenvio do que não chega até um limite de tentativas. Subdivisão e reenvio são enlace, ao modo de HDLC, não transporte. Acima das duas a aplicação vê uma porta serial virtual.

**O eco entra como propriedade do meio, nunca como dificuldade que enfrentamos.** O projeto antecipa reverberação, e é por isso que existe o intervalo de guarda de 35% do símbolo, mas nesta bancada não há cauda mensurável: o sinal para no piso de ruído. A seção 2.3 apresenta o fenômeno com gancho para a 4, e a 4 fecha esse gancho pela negativa, dizendo que a guarda foi projetada contra uma cauda que esta sala não tem. Se o eco entrasse na introdução como obstáculo vencido, os resultados desmentiriam o texto. As dificuldades que a bancada de fato encontrou são o pente, a saturação da cadeia analógica, o viés de amplitude da 2-FSK, os relógios independentes e o alinhamento de nibble da 16-FSK.

**O cabo serial entre as máquinas recebe uma menção muito breve na seção de bancada e resultados, como auxílio do ensaio, e só ali.** Decisão do autor, 2026-09-05, revendo a anterior de omiti-lo por completo. Ele só auxilia e automatiza o ensaio, não é recurso da comunicação, e apresentá-lo além de uma frase confundiria mais do que ajudaria. A frase diz que a carga conhecida é gerada dos dois lados e que os bytes pontuados viajaram só pelo ar.

## Nomenclatura, fixa (decisão do autor, 2026-09-05)

- **M-ária:** modulação de ordem M, em que cada símbolo é um tom escolhido entre M frequências e carrega log₂M bits. Abrange as quatro formas, inclusive a binária (M = 2). Explicar assim na primeira ocorrência.
- **FSK:** modulação por chaveamento na frequência, do inglês *frequency shift keying* (FSK). Designa a 2-FSK.
- **MFSK:** chaveamento em múltiplas frequências, do inglês *multiple frequency shift keying* (MFSK). Designa as que usam mais de duas frequências: 5×2-FSK, nas duas variantes, e 16-FSK. Cada sigla apresentada uma vez; depois só a sigla ou a notação numerada.
- **Quatro formas de transmissão, sempre por esta notação:** 2-FSK (um tom entre dois, um bit; tons do padrão Bell 202, nome do padrão dito uma vez); 5×2-FSK votada (cinco canais 2-FSK com o mesmo bit, decisão por maioria, um bit por símbolo); 5×2-FSK multicanal (cinco canais 2-FSK, um bit distinto em cada, cinco bits por símbolo); 16-FSK (um tom entre dezesseis, quatro bits por símbolo).
- **Nunca:** "20-FSK" para as de cinco pares (M conta tons dos quais um só soa); "M-ário" sem o M explicado; "MFSK" como nome de uma única forma; nomes internos do código (`mary`, `mfsk-par`, `fecrep`) na prosa.
- **Desvio em relação ao código e ao CLAUDE.md da raiz:** lá "MFSK" é a de cinco pares e "M-ary" é a de dezesseis tons. No artigo não. O código não muda; a correspondência está no CLAUDE.md da raiz, seção "Nomes no código e nomes no artigo".
- **Palavra de sincronismo:** o código e a raiz a chamam de sequência de comprimento máximo (m-sequence); medido em 2026-09-05, não é (17 uns em 31, autocorrelação cíclica entre −9 e 11). No artigo: "palavra de referência de 31 bits, localizada por correlação", sem nomear o tipo.
- **Toda sigla estrangeira:** nome em português, "do inglês", termo em itálico, sigla entre parênteses depois do termo. Exemplos: correção antecipada de erros, do inglês *forward error correction* (FEC); verificação de redundância cíclica, do inglês *cyclic redundancy check* (CRC); verossimilhança logarítmica, do inglês *log-likelihood ratio* (LLR); retransmissão automática, do inglês *automatic repeat request* (ARQ).

## Arquivos desta pasta

- `artigo_modem.md`: **fonte única da prosa.** Esqueleto com o resumo redigido; o resto são seções e comentários com o que entra em cada trecho, orçamento de palavras e a pasta de `resultados/` que sustenta cada número.
- `estilo.md`: o estilo do autor, extraído dos dois artigos dele (SIMECA roda de reação e IEEE TIE). **Ler antes de redigir qualquer trecho.** Tem lista de verificação no fim.
- `monta.py`: **a montagem, em um lugar só.** Confere a versão do Python e chama o conversor com caminhos absolutos. Não roda `cd` para dentro do conversor: as figuras já resolvem a partir da pasta do `.md`.
- `monta.sh` e `monta.cmd`: invocadores finos do `monta.py`, um para Linux e macOS, outro para Windows. Só escolhem o interpretador. **Não duplicar lógica neles**, pela mesma razão que a tabela de comandos do `console.py` é única. Aceitam `--verifica`, `--sem-figuras`. Rode de qualquer pasta.
- `MONTAGEM.md`: instruções de montagem para quem não trabalha neste repositório todo dia, inclusive no Windows. É o arquivo a apontar quando alguém pergunta como gerar o docx.
- `simeca-md/`: o conversor, **versionado dentro deste repositório** (decisão do autor, 2026-09-06, revendo a de mantê-lo como submódulo). Quem clona o audioFSK já tem tudo para montar o artigo, sem passo de submódulo e sem depender de o clone ter sido feito de um jeito específico, que era o que atrapalhava o segundo autor no Windows. A cópia veio de `github.com/WilhelmMeyer/simeca-md` em `0daa5246a85192bb50f56e03f86f679e0e396ff6`; o preço é que ela não recebe mais correção de lá nem devolve correção para lá, e a sincronia com o artigo da roda de reação, que usa o mesmo conversor, passou a ser trabalho manual. Correção no conversor se faz aqui e, se valer para os dois artigos, se leva à mão para o outro lado.
- `figuras/`: figuras do artigo, versionadas (exceção ao `.gitignore` global de `figuras/`). Três hoje, geradas por `figuras.py`, que lê os tons da 16-FSK de `modem.py` em vez de transcrevê-los: `resposta-canal.png` (Figura 1, resposta do canal com os dezesseis tons, na seção 2.1), `bancada.png` (Figura 2, o arranjo da bancada, na seção 3) e `nivel-alto-falante.png` (Figura 3, o U invertido do nível, na seção 4.2). A numeração segue a ordem em que as figuras aparecem no texto, e a da bancada entrou entre as outras duas porque a seção 3 vem antes da 4. Regenerar com `./venv/bin/python artigo/figuras.py`. Uma quarta figura foi cogitada e ficou fora, quatro painéis de espectro sintéticos para as quatro formas, porque ilustra método e não mede nada. Se entrar, vira a Figura 2 e as demais sobem um número. O artigo tem hoje quatro tabelas: 1 (meios de transmissão), 2 (tolerância a erro do código, por simulação), 3 (parâmetros do enlace), 4 (as quatro formas de transmissão).
- `artigo_modem.docx`, `artigo_modem.pdf`: saídas, ignoradas pelo git.

## Resultados

O artigo usa **só os resultados que existem em `../resultados/`**, como estão. Campanhas 01 a 15 na direção B→A; 01, 02, 03, 08, 08B, 16 e 17 na direção A→B. Cada número diz de qual direção veio. Não se planeja ensaio para o artigo nem se decide o que faltaria explicar; o texto apresenta o que foi medido.

**Fonte dos números, decisão corrigida em 2026-09-07: a pasta manda, o `../CLAUDE.md` da raiz é narrativa secundária.** As seções redigidas em 2026-09-07 foram tiradas do `HEADER.md` de cada pasta de `../resultados/`, e onde o CLAUDE.md da raiz discordava da pasta, a pasta venceu. A ordem inversa, tentada antes, produziu erros de verdade. Discrepâncias encontradas, resumidas: o nível do alto-falante A→B tem números próprios na pasta, diferentes dos citados solto na raiz; a correção do fader levou o sentido A→B a 5 blocos de 9, não a 8 de 9 como uma leitura apressada da raiz sugeria; o quadro de oito gravações de sincronismo citado na raiz é da auto-captura por Bluetooth de uma máquina só e não tem pasta em `resultados/`, então não é fonte para o artigo, que usa só o enlace de duas máquinas; a 5×2-FSK votada mede 1 bloco íntegro de 3, não o número que aparece solto alhures; a 5×2-FSK multicanal mede nenhum bloco íntegro de 6; e o resumo, com seus 11,3 bytes por segundo, vem com 4 blocos de 4, não outro denominador. Não há `fatos.md` ainda; se a redação precisar de número fora de uma pasta com `HEADER.md`, criar um, no formato do outro repositório (número, unidade, condição, arquivo de origem).

**`resultados/18-FEC-SIM`, criada em 2026-09-07, existe para que a Tabela 2 tenha fonte.** Os números de tolerância a erro do código convolucional vinham antes só do `../CLAUDE.md` da raiz, sem modelo de canal declarado. A pasta nova simula BPSK antipodal em ruído gaussiano aditivo, com o comportamento do canal acústico real (pente, limitador, deriva de relógio, sincronismo) deliberadamente fora, e diz isso na própria ressalva.

## Regras de escrita

- Idioma: português. Termos em inglês em itálico só quando não há tradução corrente (*feedforward*).
- **Proibido travessão na prosa.** Vírgula, parênteses ou frase nova. Dois-pontos no máximo um por parágrafo, ponto e vírgula só em referência ABNT.
- **Um parágrafo = uma ideia** (regra do autor, 2026-09-06). Passou de uma ideia, abre parágrafo novo. Na prática isso põe um teto de umas quatro frases e umas 80 palavras; parágrafo de sete frases e 160 palavras, que é o que a introdução e a fundamentação tinham nesta data, é sempre duas ou três ideias empilhadas. A exceção é o resumo, que o modelo do evento exige em parágrafo único, de 150 a 300 palavras; ali a regra vira corte, não quebra.
- **Direto, e curto pelo corte, não pela compressão** (regra do autor, 2026-09-06). Falar mais é dizer menos. Uma informação está bem dada quando é dada franca e direta, então some a frase que só prepara a próxima, o adjetivo que não muda o fato e a recapitulação do que o parágrafo anterior já disse. Encurtar não é espremer duas ideias numa frase longa, é tirar o que não informa.
- **Um parágrafo = uma linha.** Quebra só em fim de parágrafo, nunca para ficar bonito. Vale para comentários também.
- Voz: primeira pessoa do plural para o que fizemos, medimos ou apresentamos ("medimos", "apresentamos"). Impessoal para física e dedução.
- Tempo: presente para mecanismo e para o que a figura mostra; passado só para o ato de medir.
- Nome físico antes do rótulo interno. Nomes de arquivo, comandos e flags do repositório (`fecrep`, `syncsweep`, `capture.py`) não entram na prosa; o artigo fala de redundância, varreduras de sincronismo, gravação.
- Equações: a oração que introduz a equação se fecha antes dela; variáveis definidas logo depois com "Nela,"; leitura física em seguida; gancho para o resultado que a mede. Sem `\,` no LaTeX.
- Remissão a seção por nome, a equação e figura por número.
- Sem meta-discurso ("nesta seção", "vale ressaltar", "como resultado").
- Todo número com incerteza ou repetição, comparado com o previsto, desvio explicado. Esforço junto do desempenho. O que foi degradado de propósito, dito ao lado do número.
- Figura apresentada e o texto dialogando com ela em seguida, método e porquê do método na mesma frase. Legenda diz o que se vê, a condição e o que notar; comprimento é decisão de espaço.
- Dizer o que não se mediu, o que se adaptou e o que ficou fora, com a razão.

## O que o conversor exige

- Primeira linha não vazia depois de `## RESUMO` é o resumo. Sem ela o bloco de palavras-chave some ("Markdown sem bloco de keywords"). Há um "Resumo por redigir." de guarda.
- Figura: `![Figura N - legenda](figuras/x.png "escala")`, com a legenda dentro do texto alternativo, não numa linha separada depois. O conversor rejeita a forma antiga, `![](figuras/x.png "escala")` seguida de uma linha `Figura N - legenda`. Tabela: `Tabela N - legenda` na linha antes da tabela em pipes, sem mudança. Numeração conferida, não gerada.
- Equação de display: `$$ ... \tag{N}$$`. Precisa de pandoc (instalado).
- SVG entra como vetorial, mas exige um PNG de mesmo nome ao lado (comando de exportação no README do conversor).
- Autor com campo vazio só avisa; DOI do modelo só avisa.

## Meta de extensão

**4 a 10 laudas, pelo modelo do evento.** As 5 laudas do plano anterior eram suposição nossa, não exigência. Cerca de 750 palavras por lauda, figura ou tabela vale 150 a 250.

**O artigo como montado em 2026-09-07 tem 9 laudas com figuras e passa nas 18 verificações do conversor.** O autor decidiu, na mesma data, não cortar para 5, porque o evento aceita até 10 e nada no texto sobra por volume, é o que a estrutura sem fundamentação teórica e a seção de resultados direto das pastas de `resultados/` já pedem. O orçamento por seção do cabeçalho do `artigo_modem.md` segue como guia de proporção, não como teto rígido.

## Processo de trabalho

- O autor conduz **trecho a trecho**; nenhuma seção é redigida sem pedido explícito daquele trecho. Discutir não é aprovação para escrever.
- **Exceção pontual, aberta pelo autor em 2026-09-07:** pediu o artigo montado de trás para a frente a partir dos resultados, num dia só. Vale só para esse pedido; a regra de trecho a trecho volta a valer depois, não foi revogada.
- Cada trecho redigido passa pela lista de verificação do `estilo.md` antes de ser mostrado.
- Montar com `./artigo/monta.sh --sem-figuras` (no Windows, `artigo\monta.cmd --sem-figuras`) para revisar texto; com figuras só no fim.
- Manter a declaração de uso de IAG atualizada: ferramenta usada e não declarada é omissão; declarada e não usada é inverdade.
- Commits em `main`, direto; sem branch.
- Estado do texto, em 2026-09-07: resumo aprovado em 2026-09-05, com um número corrigido nesta data (ver "Fonte dos números" acima); seções 1 e 2 redigidas em 2026-09-06, por revisar; seções 3, 4 e 5 redigidas em 2026-09-07, por revisar.
- **Nenhuma referência foi inventada.** Onde o estilo pede aglomerado de citações há um marcador `(CITAR: ...)` no corpo dizendo que tipo de fonte entra ali, e os oito grupos necessários estão no comentário de REFERÊNCIAS. Trocar por citação real antes de submeter.
- **Os dois modelos de declaração de IAG do template não servem como estão**, pois ambos declaram uso restrito a levantamento de literatura e revisão linguística, e aqui a ferramenta entrou na concepção, na implementação e na análise. Redigir uma que diga o uso real.
