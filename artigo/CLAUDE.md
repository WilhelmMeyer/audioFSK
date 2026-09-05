# Instruções: artigo VII SIMECA (modem acústico)

Instruções locais para qualquer sessão que trabalhe nesta pasta. Registram as decisões de forma tomadas com o autor; não re-perguntar o que já está decidido aqui.

## O que é este trabalho

Artigo em **português** para o VII SIMECA (IFPR) sobre o modem acústico do repositório raiz. Dois autores: Winderson (primeiro autor, dados a completar por ele) e Jefferson (mesmos dados do artigo da roda de reação).

**Enquadramento, decidido em 2026-09-05: didático.** O artigo apresenta o sistema, compara brevemente com outros meios de transmissão, avalia o problema do canal acústico e propõe uma solução para este caso. Não pretende substituir outro meio nem reivindicar melhoria sobre a literatura. Nada de "supera", "melhor que", "novo". O valor está em mostrar o problema sendo medido, cada camada falhando de um jeito nomeável, e a correção que cada falha pediu.

**O canal de controle da bancada (o cabo serial entre as máquinas) não entra no artigo.** Decisão de 2026-09-05. O método diz que a carga conhecida é gerada dos dois lados e que só o ar carrega os bytes pontuados, e para.

## Arquivos desta pasta

- `artigo_modem.md`: **fonte única da prosa.** Hoje é esqueleto: seções, comentários com o que entra em cada trecho, orçamento de palavras e a pasta de `resultados/` que sustenta cada número. Nenhum parágrafo redigido.
- `estilo.md`: o estilo do autor, extraído dos dois artigos dele (SIMECA roda de reação e IEEE TIE). **Ler antes de redigir qualquer trecho.** Tem lista de verificação no fim.
- `monta.sh`: monta docx e pdf. Aceita `--verifica`, `--sem-figuras`. Rode de qualquer pasta.
- `simeca-md/`: submódulo do conversor (`github.com/WilhelmMeyer/simeca-md`). Vazio num clone novo até `git submodule update --init`. **Correção no conversor se faz naquele repositório, nunca por cópia local**; aqui só se avança o ponteiro.
- `figuras/`: figuras do artigo, versionadas (exceção ao `.gitignore` global de `figuras/`). Vazia por enquanto.
- `artigo_modem.docx`, `artigo_modem.pdf`: saídas, ignoradas pelo git.

## Estado dos resultados (2026-09-05)

Campanhas em `../resultados/`, cada uma com `HEADER.md` (commit, condições, caveats) e `resultado.csv`. A direção **B→A está completa**: 01 a 15, uma pasta por campanha. A direção **A→B tem parte**: 01, 02, 03, 08 (e 08B), 16 e 17 têm a variante `-A2B`; **faltam A→B de 04 a 07 (camadas físicas) e de 09 a 15 (gap, banda, acorde, sincronismo, redundância, arquivo).** Cada número no artigo diz de qual direção veio, e o que só foi medido em uma direção é dito assim. A assimetria em si é conteúdo: A→B tem menos SNR por tom (10,3 dB contra 13,2) e foi onde a saturação do alto-falante se mediu (16, 17).

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

## Pendências

- Winderson: sobrenome, ORCID, campus, e-mail (linha 1 de autores).
- Título: três candidatos em comentário no `.md`; escolha do autor.
- Levantamento de referências: seis clusters listados no fim do `.md` (meios de transmissão, Bell 202/AFSK, canal acústico em ambiente fechado, OFDM/chirp/MFSK acústicos, códigos convolucionais e Viterbi suave, m-sequências). Nada levantado ainda.
- Figuras: nenhuma feita. Candidatas no `.md`: diagrama do enlace; resposta em frequência medida com os 16 tons sobre o pente; bancada; bits e blocos contra nível do alto-falante. Fontes em `../resultados/*/figuras/` e `../channel.py`.
- Financiamento: preencher ou remover a seção.
- Decidir se o "cabo" fica na comparação de meios da introdução (hoje fica, como meio, não como recurso da bancada).
- Ensaios A→B faltantes: 04 a 07 e 09 a 15. Decidir quais o artigo precisa nas duas direções (no mínimo 14-FEC-REP e 15-PKT-ARQ, que dão os números do resumo) e quais ficam declarados como medidos só em B→A.
- Estado do texto: zero parágrafos redigidos. Próximo passo natural é o resumo ou a introdução, a pedido.
