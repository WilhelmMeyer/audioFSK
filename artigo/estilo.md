# Estilo do autor

Extraído de dois artigos do mesmo autor, guardados em `estilo/`: o do VII SIMECA sobre a haste com roda de reação (português, controle, 2026) e o da IEEE Transactions on Industrial Electronics sobre o IVR-PFM (inglês, eletrônica de potência, 2026). Áreas e línguas diferentes, mesma forma. O que aparece nos dois é o estilo; o que aparece em um só está marcado. Serve de estrutura para o artigo do modem acústico.

## 1 O algoritmo do artigo

O artigo é um funil que desce do campo à lacuna, uma seção de mecanismo que planta ganchos, e uma seção de resultados que os colhe na mesma ordem. Quem lê só a introdução sabe o que foi feito e por quê; quem lê só os resultados encontra, a cada número, a equação que o previu.

**Introdução em cinco a sete parágrafos, um passo por parágrafo.** Do enunciado mais amplo e verdadeiro do campo até a frase "propomos". No SIMECA: rodas de reação em satélites; o limite do torque interno; a descarga e o custo de propelente; docagem e giro contínuo; bancadas terrestres; a linhagem local da mesma bancada; a lacuna; a proposta. No IEEE: demanda por conversores de alta potência; PFC e o custo de controle em três fios; comutação suave; Vienna; SC-PFM; a integração. Cada parágrafo fecha com o aglomerado de citações ou com uma frase curta que crava o ponto ("Esse torque é interno, e aí está o limite." / "Nossa haste opera nesse regime."). Nunca uma citação por frase no meio do parágrafo.

**Linhagem declarada, inclusive a própria.** Os trabalhos anteriores da mesma bancada e do mesmo autor entram nomeados, com o que fizeram, e o contraste vem em uma frase: "Em todos esses trabalhos a roda serve a um alvo de posição. Perseguimos o oposto." No IEEE: "The present work, in contrast, investigates...". A lacuna é dita como busca feita, não como ausência presumida: "não localizamos uma haste com roda de reação operada nesse regime".

**Contribuições enumeradas explicitamente**, em uma frase corrida (SIMECA: "As contribuições são o balanço..., uma cascata..., a identificação... e a validação experimental, da partida ao cruzeiro...") ou em lista numerada (IEEE: sete vantagens, depois "this work presents several developments not addressed in prior studies. These include..."). A introdução termina anunciando a verificação experimental em uma linha: "We verify the concept through practical demonstration in a 3 kW, 800 V output application."

**Princípio de funcionamento: o mecanismo em palavras antes de qualquer equação.** Primeiro o objeto e a figura (Figura 1, o diagrama), depois cada agente físico descrito qualitativamente com sua consequência (o atrito "consome momento sem cessar"; a gravidade "tem média nula sobre uma volta à velocidade constante, pois favorece o giro na metade em que o centro de massa desce e se opõe na metade em que sobe"). Só então a equação, e o leitor já sabe o que cada termo vai ser.

**Cadeia de dedução: ideal, depois a não idealidade, depois a correção, depois a aproximação simples.** No IEEE: corrente ideal (7), tanque ressonante (8) a (10), corrente de roda livre (11), tempos corrigidos (12), zona morta (16), corrente por trechos (20), THD (23) e por fim "A simple approximation THD ≈ 0.6 θ fits well". No SIMECA: dinâmica (2), balanço na volta (4), tempo de saturação (5), perfil (6), colheita (8), ondulação (9), equilíbrio (10). Cada simplificação é declarada com sua ordem ("retendo a primeira ordem em ε", "θ is considered small, allowing sin(θ) ≈ θ") e cada hipótese em lista, quando são várias ("The following assumptions are made for the analysis. 1) ... 5) ...").

**A teoria planta ganchos que os resultados colhem.** Toda equação importante fecha apontando para onde será medida: "como os resultados medem", "como os resultados mostram", "as duas assinaturas sustentam a identificação da planta nos resultados", "will be further discussed in the experimental results section". Os resultados devolvem por número: "o equilíbrio de (10)", "conforme (9)", "consistent with the analytical estimation (23)".

**Estratégia (controle, ou o que faz o papel dele): o problema como N exigências e um só recurso.** "O problema de controle tem três frentes simultâneas, ..., e um único atuador para as três." Depois a hierarquia, do mais rápido ao mais lento, em lista com nome físico em negrito e rótulo interno entre parênteses. Depois cada bloco em um parágrafo: o que mede, o que produz, por que essa estrutura e não outra ("Não tem termo proporcional, pois o filtro que extrai a média atenua a frequência da volta sem eliminá-la, e um termo proporcional devolveria esse resto ao perfil."). A separação de escalas é justificada com os números das bandas.

**Resultados na ordem da teoria, e depois na ordem da narrativa.** Abre com um parágrafo de como se mediu (sensores, taxa de amostragem, de onde saem todas as figuras) e a tabela de parâmetros com a coluna de símbolos igual à do texto. Segue a identificação, um ensaio por parâmetro, na ordem em que a teoria os introduziu (pêndulo livre, curva estática do motor, atrito da roda, razão de inércias, ganho de colheita). Só então a operação, na ordem em que acontece (partida, cruzeiro, troca de velocidade, limites, docagem). No IEEE a mesma coisa: formas de onda em três cargas, THD contra norma, comutações, degrau de carga, balanço de tensão, rendimento, térmico, comparação com a literatura.

**Cada parágrafo de resultado tem a mesma célula.** "A Figura N mostra" mais o que foi feito e em que condição; o número com incerteza; a comparação com a previsão da equação, em porcentagem; a explicação física do desvio; e o que aquele número passou a alimentar. Exemplo inteiro: "O ganho medido supera em 24% a previsão de primeira ordem de (8), mgd/2J = 48,5, porque a haste ondula cerca de 1,4 vez o comando e a gravidade atua sobre a ondulação executada. Regredindo a taxa contra essa ondulação saem a perda por atrito do pivô, 9,13 ± 0,23 rad/s² na roda, e mgd/J = 97,0 ± 1,7 s⁻², a 5% do valor obtido pelo pêndulo com a razão de inércias. São esses valores que o controle passou a usar."

**Diz o que não mediu, o que adaptou e o que ficou fora.** "though not measured in this study"; "region not exercised"; "These choices reflect implementation constraints and do not alter the control structure"; "O alinhamento de fase contra um alvo exige um segundo dispositivo e fica fora do escopo deste trabalho." O limite é explicado pela origem, não só constatado: "O limite inferior tem outra origem."

**Conclusão em três parágrafos, no passado.** O que se apresentou e o mecanismo; o que a estrutura fez e os números-chave; o passo seguinte e a fronteira do escopo. Sem afirmação nova, sem adjetivo que os resultados não sustentem. O IEEE fecha com o mesmo: mecanismo, resultado, rendimento, e antes disso disponibiliza a simulação para replicação.

## 2 A unidade é o parágrafo, e ele carrega uma ideia

Um parágrafo, uma ideia, e a ideia termina com uma consequência. Parágrafos de descrição física terminam no efeito ("e consome momento sem cessar"); parágrafos de dedução terminam na leitura da equação; parágrafos de resultado terminam no que o número alimenta. Não há parágrafo que só descreve.

Frase longa por vírgulas carregando uma cadeia causal, seguida de frase curta que crava. "Rodas de reação são o atuador padrão no controle de atitude de satélites, em que um motor acelera um volante interno e o corpo do veículo recebe o torque de reação, sem massa expelida e com boa precisão (Markley; Crassidis, 2014). Esse torque é interno, e aí está o limite." O ritmo é esse, longa e curta, e a curta é a que o leitor guarda.

Causalidade por "pois", "e é aí que", "de onde saem", "que dá", "o que confirma", nunca por "portanto" ou "assim sendo". Contraste por "não X e sim Y" ("o que não significa roda parada e sim que a excursão da roda tenderá a se igualar"). Sequência por "por sua vez", "além disso", "Subsequently", "In addition".

## 3 Equações

A oração que introduz a equação se fecha antes dela; a equação nunca parte uma frase. Em português: "a segunda lei de Newton para a rotação dá a dinâmica completa, com cada torque em função das grandezas do sistema." e então (1) e (2). Em inglês a convenção da IEEE aceita "is given as follows:" e "resulting in".

Variáveis definidas logo depois, em uma frase só, começando por "Nela," ou "Nelas," ("Here," no IEEE): "Nela, $K_t$ é a constante de torque, $K_v$ é a constante de força contraeletromotriz, $R$ é ... e $T_r$ é ...". Nunca uma lista com marcadores para definir símbolos.

Logo em seguida, a leitura física e uma consequência de projeto: "A colheita cresce com a profundidade de modulação, diminui com $\bar\omega_h$ e é máxima em φ = 90°"; "Qualquer outra forma periódica colhe apenas pelo primeiro harmônico, pois os superiores integram zero contra o $\sin\theta_h$ da gravidade, e a cossenoide entrega toda a colheita disponível com o mínimo de esforço de atuador." A equação existe para dizer algo sobre o projeto, e o texto diz o quê.

Remissão a equação por número entre parênteses no meio da frase, como substantivo: "Integrar o termo gravitacional da (2)", "recai na (4) com ε = 0", "Using (3), (4), and the equilibrium condition". Remissão a seção por nome ("a seção de resultados", "the experimental results section"), a figura e tabela por número.

Uma tabela de símbolos e componentes logo no início quando o número de variáveis é grande (IEEE, Tabela I). No SIMECA, com menos símbolos, a tabela de parâmetros nos resultados cumpre o papel, com a coluna de símbolos.

## 4 Figuras e tabelas

A figura é apresentada e o texto dialoga com ela em seguida: "A Figura 7 mostra o atrito mecânico da roda, medido por desaceleração livre com os fios do motor desconectados, necessário porque a ponte H curto-circuita o motor em razão cíclica nula e o freio elétrico mascararia o efeito do atrito." O porquê do método está na mesma frase que o método.

A legenda explica o que se vê, em que condição, e o que notar. O comprimento é decisão de espaço, não de estilo: no SIMECA a foto do protótipo tem legenda mínima e as figuras de dado têm uma ou duas frases; a conclusão física fica no corpo, e a legenda no máximo aponta para ela. "Figura 2 - Perfil de velocidade da haste, equação (6) com φ = 90° e ε = 0,3, em três voltas. (a) no ângulo. (b) no tempo. Note que os trechos lentos duram mais que os rápidos e a média temporal fica abaixo do valor central." No IEEE: "Fig. 1. (c) IVR-PFM topology: each input connection will have a set of components. ... The higher the switching period, the greater the power conversion." A legenda é um parágrafo curto, não um título.

Um painel de figura pode trocar o eixo para revelar a lei: "No painel (b) o tempo de ensaio é trocado pelo tempo que falta até a roda parar, e nesse eixo as dez desacelerações, partidas de velocidades e instantes diferentes, caem todas sobre a mesma curva." Quando um eixo colapsa ensaios diferentes numa curva, isso é o resultado, e o texto diz isso.

Gráfico de resultado sobrepõe a série prevista e a medida no mesmo eixo, e a comparação modelo contra medição é visual antes de ser textual: THD medido contra a estimativa (23) na Fig. 9(a); a desaceleração da roda contra o modelo com e sem parcela viscosa na Figura 7. A nomenclatura cunhada na teoria (θ, If w, ε, colheita) reaparece nos rótulos e legendas dos resultados.

Tabelas de dois tipos. A de parâmetros: grandeza, símbolo, valor, com os símbolos do texto. A comparativa: linhas são alternativas (topologias, referências), colunas são os critérios, e a última coluna é "Comentários" em prosa, dizendo o que cada linha propõe e onde fica aquém (IEEE, Tabelas III e V). A linha do próprio trabalho vai por último e é julgada com a mesma régua.

## 5 Números

Todo número mede algo nomeado e vem com sua incerteza quando há regressão ou repetição: "ω₀² = 1,699 ± 0,007 s⁻²", "J/I = 0,0167 ± 0,0015, o mesmo valor nos dois sentidos de rotação", "49,92 ± 1,14 rad/s".

Todo número medido é comparado com o previsto, em porcentagem, e o desvio é explicado ou declarado: "15% acima do equilíbrio de 0,1343 previsto por (10). A diferença vem da correção do feedforward de gravidade"; "8,26 rad/s², contra os 9,13 rad/s² que a planta medida no ensaio da Figura 8 prevê".

O número é traduzido para a escala que importa: "600 s, ou 24 constantes de tempo do integrador lento"; "viés de +0,0001 rad/s, menos de 0,01% do comandado"; "com sobra que garante 1 rad/s ao chegar lá". Uma duração sozinha não diz nada; em constantes de tempo, diz que o regime foi alcançado.

Ensaios repetidos são reportados em par ou em contagem, com os dois valores: "a conversão aconteceu já na primeira meia oscilação ..., com a haste cruzando o fundo a 2,779 e 2,785 rad/s contra o limiar de 2,792 rad/s". Percentual de saturação de comando, pico, sobressinal: as métricas de esforço do atuador vêm junto das de desempenho, sempre.

O que se extrapola é dito como extrapolação, com a região não exercitada marcada: "a conservative extrapolation places the 25% THD reference near Pi ≈ 0.04 Prated for this design (region not exercised); all measured points (≤ 25% load) remained below 11%."

## 6 Voz e frase

Primeira pessoa do plural para o que fizemos, medimos ou propomos: "Propomos e validamos", "Perseguimos o oposto", "Adotamos o bombeamento", "comandamos doze patamares", "we explore", "we focus", "We verify". Impessoal ou terceira pessoa para a física e a dedução: "a gravidade exerce torque", "Substituindo (6) e retendo a primeira ordem".

Tempo: presente para o mecanismo, para a dedução e para o que a figura mostra ("A Figura 9 mostra", "a colheita cresce com"); passado só para o ato de medir e para o que a bancada fez ("comandamos doze patamares", "o sistema operou em ε = 0,1353", "manteve a velocidade média por 600 s"). A conclusão mistura os dois pela mesma regra: "Apresentamos" e "A janela útil medida foi" no passado, "Ela compensa o atrito" no presente.

Sem travessão na prosa em português; vírgula, parênteses ou frase nova. Parênteses só para rótulo, sigla e citação. Dois-pontos raros. Ponto e vírgula só em citação ABNT. O IEEE usa travessão em inglês porque a revista aceita; não é o estilo, é a língua.

Nome físico antes do rótulo, sempre: "Governador de velocidade média da roda (C3)", "the switching cell with pulse-frequency modulation (SC-PFM)". Depois de apresentado, o rótulo pode andar sozinho.

Vocabulário de restrição e unicidade, porque o argumento dos dois artigos é o de um recurso só: "único atuador", "a única que toca o motor", "a roda absorve sozinha", "sem cessar", "a cada volta", "apenas", "only output voltage feedback", "without current sensing". O texto nomeia a limitação como o que estrutura o problema.

Nomear a coisa e então batizá-la: primeiro o mecanismo em palavras, depois "Essa é a colheita gravitacional", "This nonconducting interval is referred to as the zero-crossing dead zone". O nome vem depois da descrição, nunca antes.

## 7 Recursos que se repetem

- **A frase curta que crava, depois da longa.** "Descarregá-lo exige um torque externo." "É a única atuação disponível." "A pré-carga não degrada o cruzeiro." "A recuperação preserva o cruzeiro."
- **O parágrafo que abre com a tese dele.** "Trocar a velocidade média de cruzeiro é a manobra que mais exige do atuador"; "A manobra que fecha o capítulo é a de docagem".
- **O gancho para a frente.** "como os resultados medem", "que a identificação apresentada na seção de resultados explora", "which is developed throughout this article".
- **A explicação do limite pela origem.** "O limite inferior tem outra origem. Quanto mais lenta a haste, mais tempo a gravidade tem..."
- **A hipótese falsa afastada.** "o que não significa roda parada e sim que...", "Although subtle from a structural perspective, these differences result in distinct waveform behavior".
- **A honestidade sobre a prática.** O que foi adaptado na bancada e por quê, e a declaração de que isso não muda a estrutura.
- **A analogia com o campo maior, no fecho.** "É a dessaturação contínua que em órbita se faz por gradiente de gravidade, aqui em segundos em vez de dias."
- **Contribuições próprias anteriores citadas como linhagem**, com o que cada uma fez, e o presente trabalho "in contrast".

## 8 O que ele não faz

Não há meta-discurso: nada de "nesta seção apresentamos", "é importante notar", "vale ressaltar". A ordem se justifica por si. A única exceção é o parágrafo de abertura de subseção do IEEE ("In this section, we explore the operation of one of the groups"), que é convenção da revista.

Os conectores do IEEE ("As a result", "It is worth noting that", "Although..., ..." abrindo parágrafo) não atravessaram para o português: o SIMECA não tem nenhum "como resultado", "vale notar" ou "embora" de abertura. São da língua e da revista, não do autor.

Não há adjetivo de avaliação sem número ao lado. "excellent power quality" aparece na conclusão do IEEE depois de THD medido contra norma; no SIMECA não aparece adjetivo nenhum.

Não há lista de marcadores para definir variáveis, nem para resultados. Lista só para hierarquia de blocos, hipóteses de análise e vantagens enumeradas na introdução.

Não há "trabalhos futuros" como seção; o passo seguinte é uma frase na conclusão, e o que não se fará é dito como fora do escopo, com a razão.

Não há resumo de seção no fim dela. A seção termina no último resultado ou na última equação lida.

## 9 O resumo

Conceitual até a última frase, e só ela traz números. Ordem: o que o artigo apresenta e a que se compara; o problema, ou o contraste com o estado da arte ("Unlike converters in DCM, the IVR-PFM achieves..."); a solução, com o mecanismo nomeado e a lista do que ela dispensa ("eliminating the need for ... dq0 or αβ transformations, SVPWM, PLLs, and cosine generation"; "sem massa expelida"); a implementação, com o hardware; o escopo analítico quando há ("The article also analyzes..."); os resultados, com os números-chave. Sem citação, sem equação. Entre 150 e 300 palavras no SIMECA. Os números do resumo são os mesmos da conclusão, e a conclusão não traz número novo.

## 10 Lista de verificação antes de fechar uma seção

1. Cada parágrafo termina em consequência, não em descrição.
2. Cada equação foi introduzida por frase fechada, tem "Nela," e tem leitura física em seguida.
3. Cada equação de projeto aponta para o resultado que a mede.
4. Cada número de resultado tem incerteza ou repetição, comparação com previsão e explicação do desvio.
5. Cada figura é apresentada por "A Figura N mostra", com o método e o porquê do método na mesma frase, e a legenda diz o que notar.
6. Nada foi julgado com adjetivo sem número.
7. Sem travessão, sem meta-discurso, sem rótulo antes do nome físico.
8. O que não se mediu, o que se adaptou e o que ficou fora estão ditos.
