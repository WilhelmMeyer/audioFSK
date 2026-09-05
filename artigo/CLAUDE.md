# Instruções: artigo VII SIMECA (modem acústico)

Instruções locais para qualquer sessão que trabalhe nesta pasta. Registram as decisões de forma tomadas com o autor; não re-perguntar o que já está decidido aqui.

## O que é este trabalho

Artigo em **português** para o VII SIMECA (IFPR) sobre o modem acústico do repositório raiz. Dois autores: Winderson (primeiro autor, dados a completar por ele) e Jefferson (mesmos dados do artigo da roda de reação).

**Enquadramento, decidido em 2026-09-05: didático.** O artigo apresenta o sistema, compara brevemente com outros meios de transmissão, avalia o problema do canal acústico e propõe uma solução para este caso. Não pretende substituir outro meio nem reivindicar melhoria sobre a literatura.

**Duas camadas, decisão do autor em 2026-09-05.** O artigo apresenta a implementação da camada física e da camada de enlace. Física: as modulações (Bell 202, MFSK votado, M-ário de 16 tons), o sincronismo de símbolo e a decisão suave do demodulador. Enlace: o bloco codificado (convolucional K=7, Viterbi suave, entrelaçamento, repetição, palavra de sincronismo por correlação), o pacote com número de sequência e CRC, a subdivisão do arquivo em pacotes e o reenvio do que não chega até um limite de tentativas. Subdivisão e reenvio são enlace, ao modo de HDLC, não transporte. Acima das duas a aplicação vê uma porta serial virtual.

**O canal de controle da bancada (o cabo serial entre as máquinas) não entra no artigo, em nenhuma seção, figura ou legenda.** Decisão do autor, 2026-09-05, e a razão: ele só auxilia e automatiza o ensaio, não é recurso da comunicação em si, e apresentá-lo confundiria mais do que ajudaria a entender. O método diz que a carga conhecida é gerada dos dois lados e que só o ar carrega os bytes pontuados, e para. Não reabrir.

## Arquivos desta pasta

- `artigo_modem.md`: **fonte única da prosa.** Hoje é esqueleto: seções, comentários com o que entra em cada trecho, orçamento de palavras e a pasta de `resultados/` que sustenta cada número. Nenhum parágrafo redigido.
- `estilo.md`: o estilo do autor, extraído dos dois artigos dele (SIMECA roda de reação e IEEE TIE). **Ler antes de redigir qualquer trecho.** Tem lista de verificação no fim.
- `monta.sh`: monta docx e pdf. Aceita `--verifica`, `--sem-figuras`. Rode de qualquer pasta.
- `simeca-md/`: submódulo do conversor (`github.com/WilhelmMeyer/simeca-md`). Vazio num clone novo até `git submodule update --init`. **Correção no conversor se faz naquele repositório, nunca por cópia local**; aqui só se avança o ponteiro.
- `figuras/`: figuras do artigo, versionadas (exceção ao `.gitignore` global de `figuras/`). Vazia por enquanto.
- `artigo_modem.docx`, `artigo_modem.pdf`: saídas, ignoradas pelo git.

## Resultados

O artigo usa **só os resultados que existem em `../resultados/`**, como estão. Campanhas 01 a 15 na direção B→A; 01, 02, 03, 08, 08B, 16 e 17 na direção A→B. Cada número diz de qual direção veio. Não se planeja ensaio para o artigo nem se decide o que faltaria explicar; o texto apresenta o que foi medido.

Fonte dos números: `../CLAUDE.md` (a tabela de camadas e as entradas de "coisas que quebram") e `../resultados/<pasta>/`. Não há `fatos.md` ainda; se a redação começar a precisar de números fora do CLAUDE.md, criar um, no formato do outro repositório (número, unidade, condição, arquivo de origem).

## Regras de escrita

- Idioma: português. Termos em inglês em itálico só quando não há tradução corrente (*feedforward*).
- **Proibido travessão na prosa.** Vírgula, parênteses ou frase nova. Dois-pontos no máximo um por parágrafo, ponto e vírgula só em referência ABNT.
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
- Figura: `![](figuras/x.png "escala")` e na linha seguinte `Figura N - legenda`. Tabela: `Tabela N - legenda` na linha antes da tabela em pipes. Numeração conferida, não gerada.
- Equação de display: `$$ ... \tag{N}$$`. Precisa de pandoc (instalado).
- SVG entra como vetorial, mas exige um PNG de mesmo nome ao lado (comando de exportação no README do conversor).
- Autor com campo vazio só avisa; DOI do modelo só avisa.

## Meta de extensão

5 laudas, relaxado; piso 4. Cerca de 750 palavras por lauda, figura ou tabela vale 150 a 250. Orçamento de prosa no cabeçalho do `artigo_modem.md`: resumo 200, introdução 500, princípio 700, método 350, resultados 750, considerações 200, mais cinco figuras ou tabelas. Para cair a 4 laudas, corta-se a subseção do que não ajudou e uma figura.

## Processo de trabalho

- O autor conduz **trecho a trecho**; nenhuma seção é redigida sem pedido explícito daquele trecho. Discutir não é aprovação para escrever.
- Cada trecho redigido passa pela lista de verificação do `estilo.md` antes de ser mostrado.
- Montar com `./artigo/monta.sh --sem-figuras` para revisar texto; com figuras só no fim.
- Manter a declaração de uso de IAG atualizada: ferramenta usada e não declarada é omissão; declarada e não usada é inverdade.
- Commits em `main`, direto; sem branch.
- Estado do texto: zero parágrafos redigidos.
