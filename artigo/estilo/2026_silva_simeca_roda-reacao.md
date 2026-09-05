<!--
FONTE DO TEXTO — VII SIMECA / IFPR

Este arquivo é a fonte única da prosa. O destino é artigo_roda_reacao.docx, montado uma vez no fim (colar com Ctrl+Shift+V, texto não formatado, e aplicar os estilos do modelo: Ttulo1, Ttulo2, Corpodetexto, Legenda).

Limites do modelo:
- extensão: 4 a 10 laudas (~750 palavras/página em A4 duas colunas, 10 pt; cada figura ou tabela equivale a 150-250 palavras)
- título: no máximo 3 linhas
- resumo: 150 a 300 palavras
- palavras-chave: 3 a 5, separadas por ponto final

Convenções deste arquivo:
- equações em LaTeX, entre $...$ (inline) ou $$...$$ (destacada)
- figuras e tabelas NÃO entram aqui; são inseridas direto no docx. Aqui só se referencia no texto ("Figura 1", "Tabela 2") e se registra a legenda em comentário, para não perder o texto dela.
- comentários HTML como este não são colados no docx
- um parágrafo = uma linha; quebra de linha só em fim de parágrafo (hook tools/claude-hooks/check-line-wrap.mjs bloqueia)
- proibido travessão na prosa

Contagem: wc -w artigo/artigo_roda_reacao.md
-->

# Gestão de momento por torque gravitacional em um pêndulo com roda de reação em rotação contínua sustentada

<!--
Máximo 3 linhas. Título, autores e filiação são montados no docx a partir daqui.

Candidatos a elementos do título: roda de reação; controle de velocidade de haste giratória; colheita gravitacional / gestão de momento.
-->

**AUTORES:**

<!--
Um autor por linha, campos separados por |, nesta ordem: nome | ORCID | filiacao | e-mail. Linha com nome vazio nao entra. Maximo 6, que e o que o modelo comporta. O montador conta as linhas preenchidas, apaga as linhas de autor sobrando na tabela do modelo e as notas de filiacao correspondentes. ORCID no formato 0000-0000-0000-0000 vira link no icone; ORCID vazio remove o icone daquela linha.
-->

1. Luciano Diz da Silva | 0009-0002-5455-911X | IFPR, Campus Jacarezinho | lucianodizsilva@outlook.com
2. Jonatas Bernardino dos Santos | 0009-0005-9224-6677 | IFPR, Campus Jacarezinho | londeersbb@gmail.com
3. Ricardo Breganon | 0000-0002-8203-8699 | IFPR, Campus Jacarezinho | ricardo.breganon@ifpr.edu.br
4. Uiliam Nelson Lendzion Tomaz Alves | 0000-0002-5820-9275 | IFPR, Campus Jacarezinho | uiliam.alves@ifpr.edu.br
5. Jefferson Wilhelm Meyer Soares | 0000-0003-3372-9298 | IFPR, Campus Jacarezinho | jefferson.soares@ifpr.edu.br

**DOI:** https://doi.org/10.5281/zenodo.XXX

<!--
DOI do artigo, no rodape do bloco de titulo. Aceita a URL inteira ou so o identificador (10.5281/zenodo.123). Vazio mantem o texto do modelo.
-->

## RESUMO

Este artigo apresenta o controle de velocidade de uma haste em rotação no plano vertical atuada por roda de reação, a bancada emula o giro em velocidade constante de satélites e a docagem. O problema deste sistema é que em rotação o atrito do pivô drena momento a cada volta e satura a roda em segundos. A reposição, que no espaço vem de propulsores, bobinas magnéticas ou gradiente de gravidade, aqui vem da gravidade sobre o desbalanceamento da massa, colhida modulando o perfil de velocidade ao longo da volta sob uma malha lenta de gestão de momento. O controle é uma cascata de cinco malhas num ESP32 com dois encoders, além disso é apresentada a identificação da bancada. Resultados experimentais mostram a haste em giro completando 600 s com viés de velocidade média abaixo de 0,01% da referência, com faixa de 1,0 a 3,5 rad/s, velocidade da roda em média nula sem saturação permanente e janela de docagem de 14,1 s.

**PALAVRAS-CHAVE:** Roda de reação. Controle em cascata. Gestão de momento angular. Colheita gravitacional.

## 1 INTRODUÇÃO

Rodas de reação são o atuador padrão no controle de atitude de satélites, em que um motor acelera um volante interno e o corpo do veículo recebe o torque de reação, sem massa expelida e com boa precisão (Markley; Crassidis, 2014). Esse torque é interno, e aí está o limite. Perturbações de média não nula, como arrasto atmosférico ou pressão de radiação solar, depositam momento angular no veículo, e a roda só o retira do corpo acumulando-o em si, até saturar. Descarregá-lo exige um torque externo.

Propulsores fazem essa descarga gastando propelente, que define a vida útil da missão, e a alternativa é um torque do ambiente, o campo magnético terrestre por bobinas (Tregouet et al., 2015) ou o gradiente de gravidade sobre a distribuição de massa (Tong, 1998). Em estações orbitais a descarga é contínua, com a atitude escolhida para cancelar o acúmulo ao longo da órbita (Vadali; Oh, 1992).

O mesmo atuador governa a atitude na aproximação e na docagem, em que a janela em que a orientação se sustenta limita o tempo útil da manobra (Leomanni et al., 2022). Em satélites estabilizados por rotação o giro contínuo é o próprio regime de operação, e a atitude se sustenta pela rotação do corpo (Sidi, 1997). Nossa haste opera nesse regime.

 Em bancadas de teste, o pêndulo invertido com roda de reação é o problema clássico, com a haste estabilizada por realimentação de estado (Spong; Corke; Lozano, 2001). A velocidade da roda é levada a uma constante escolhida enquanto o pêndulo é mantido no equilíbrio (Sandoval et al., 2020).

O protótipo e o motor desta bancada são os de Souza et al. (2025), que estabilizaram o pêndulo na vertical com um controlador proporcional integral derivativo (PID) e precisaram de um proporcional integral (PI) em paralelo para regular a velocidade do motor. Ele recebeu depois controle por desigualdades matriciais lineares com restrição de saturação (Santos et al., 2026), técnica que os mesmos autores aplicaram ao pêndulo de Furuta (Alves et al., 2022). Em todos esses trabalhos a roda serve a um alvo de posição.

Perseguimos o oposto, a rotação contínua em plano vertical com velocidade média imposta pelo operador. O atrito do pivô, ausente no espaço, drena momento angular a cada volta e satura a roda em poucos segundos. O único torque externo disponível é o da gravidade sobre o desbalanceamento da haste, que integra zero na volta à velocidade constante e só rende momento líquido se a velocidade for modulada com o ângulo, como na descarga por gradiente de gravidade dos satélites. Focamos em um único eixo, com a roda como único atuador e um torque de gravidade muito maior que o de qualquer perturbação orbital, e o ciclo de saturação e descarga que em órbita leva dias aqui leva segundos. Rotação contínua de pêndulo aparece na literatura sem roda de reação, com o eixo sem atuador e o suporte oscilando (Xu; Wiercigroch; Cartmell, 2005), e não localizamos uma haste com roda de reação operada nesse regime.

Propomos e validamos um controle de velocidade para essa planta. As contribuições são o balanço de momento angular por volta, que fixa o formato e a profundidade da modulação de velocidade, uma cascata de cinco malhas que executa o perfil e governa a colheita pela velocidade média da roda, a identificação da planta em bancada e a validação experimental, da partida ao cruzeiro, à troca de velocidade média, ao envelope e a docagem.

## 2 PRINCÍPIO DE FUNCIONAMENTO

O sistema é uma haste rígida que gira em plano vertical em torno de um pivô horizontal, ver Figura 1. Em uma extremidade estão o motor de corrente contínua e a roda de reação, volante no eixo do motor, na outra um contrapeso. O lado da roda pesa mais, o centro de massa fica a $d$ do pivô e a gravidade exerce torque sobre esse desbalanceamento.

![](figuras/fig_diagrama_sistema.svg "0.85")
Figura 1 - Diagrama do conjunto haste e roda de reação.

Sobre a haste agem os torques da gravidade, do atrito do pivô e da reação da roda. A roda tem como única conexão mecânica com a haste o eixo do próprio motor, e o torque que a acelera reage sobre a haste com módulo igual e sinal trocado, par interno que redistribui momento angular entre roda e haste sem injetar momento no conjunto. É a única atuação disponível, e o máximo físico da velocidade da roda impede sustentar esse torque indefinidamente. O atrito do pivô, com parcelas seca e viscosa, opõe-se ao movimento em qualquer sentido e velocidade e consome momento sem cessar. O torque da gravidade, por sua vez, tem média nula sobre uma volta à velocidade constante, pois favorece o giro na metade em que o centro de massa desce e se opõe na metade em que sobe.

Denotando por $\omega_h$ a velocidade da haste e por $I$ o momento de inércia do conjunto em torno do pivô, a segunda lei de Newton para a rotação dá a dinâmica completa, com cada torque em função das grandezas do sistema.

$$I\frac{d\omega_h}{dt} = \tau_g + \tau_p + \tau_r \tag{1}$$
$$I\dot{\omega}_h = -mgd\sin\theta_h - T_p - J\dot{\omega}_r \tag{2}$$

Nelas, $\theta_h$ é a posição angular da haste medida do ponto mais baixo do centro de massa, $mgd$ é o torque máximo da gravidade, $T_p$ é o módulo do atrito do pivô, contrário ao giro e dependente da velocidade da haste, $J$ é o momento de inércia da roda e $\omega_r$ é a velocidade da roda em relação à haste, a grandeza que o encoder mede.

Com o motor desligado, a equação (2) descreve um pêndulo físico, e a linearização de $\sin\theta_h$ em pequena amplitude no ponto baixo dá a frequência natural $\omega_0$.

$$\omega_0^2 = \frac{mgd}{I} \tag{3}$$

Ela amarra o desbalanceamento à inércia do conjunto e se mede pelo período da oscilação livre. Em amplitude maior o período cresce pela não linearidade, e as duas assinaturas sustentam a identificação da planta nos resultados.

A grandeza controlada é a velocidade média de uma volta inteira. Nessa média, à velocidade constante, a aceleração da haste e o torque da gravidade se anulam, e, com $\langle x\rangle$ denotando a média na volta, (2) se reduz ao balanço de momento angular da volta.

$$J\langle\dot{\omega}_r\rangle = -\langle T_p\rangle \tag{4}$$

A roda acumula momento à taxa fixada pelo atrito do pivô na velocidade média da haste. Com a velocidade da roda limitada a $\omega_{r,max}$ pela tensão de alimentação, o cruzeiro partindo da roda parada tem duração máxima $t_{sat}$, da ordem de dez segundos, como os resultados medem.

$$t_{sat} = \frac{J\omega_{r,max}}{\langle T_p\rangle} \tag{5}$$

As equações (4) e (5) valem para a volta à velocidade constante, regime que uma docagem exige, com a haste mantendo a referência imperturbada enquanto a roda absorve sozinha o momento angular drenado pelo pivô, e (5) dando o tempo disponível para a manobra.

### 2.1 Colheita gravitacional

O atrito do pivô drena momento angular a cada volta e a roda apenas o redistribui. Repor exige torque externo, e a estratégia aqui é usar o torque que a gravidade impõe sobre o desbalanceamento da haste. Fazendo a haste mais lenta na descida do centro de massa e mais rápida na subida, a gravidade favorece o giro por mais tempo do que se opõe, e a volta fecha com momento líquido. Essa é a colheita gravitacional, obtida modulando a referência de velocidade pelo ângulo da haste.

![](figuras/fig_perfil_velocidade.png "1.0")
Figura 2 - Perfil de velocidade da haste, equação (6) com φ = 90° e ε = 0,3, em três voltas. (a) no ângulo. (b) no tempo. Note que os trechos lentos duram mais que os rápidos e a média temporal fica abaixo do valor central.

$$\omega_{h,ref}(\theta_h) = \bar\omega_h\left[1 + \varepsilon\cos(\theta_h - \varphi)\right] \tag{6}$$

Nela, $\bar\omega_h$ é o valor central do perfil, $\varepsilon$ é a profundidade de modulação e $\varphi$ é a fase em relação ao ponto mais baixo do centro de massa. O perfil é uma cossenoide no ângulo, como mostra a Figura 2, e não no tempo, em que se distorce com os trechos lentos durando mais que os rápidos. Por isso a média da volta, $\bar\omega_h\sqrt{1-\varepsilon^2}$, fica abaixo do valor central, diferença de segunda ordem em $\varepsilon$ que a dedução seguinte, de primeira ordem, trata como nula.

O momento que a gravidade entrega por volta é a integral do torque no tempo, escrita no ângulo com $dt = d\theta_h/\omega_h$.

$$\Delta H_g = -mgd\int_0^{2\pi}\frac{\sin\theta_h}{\omega_h(\theta_h)}d\theta_h \tag{7}$$

Substituindo (6) e retendo a primeira ordem em $\varepsilon$, a integral resulta na colheita por volta.

$$\Delta H_g = \frac{\pi mgd\varepsilon\sin\varphi}{\bar\omega_h} \tag{8}$$

A colheita cresce com a profundidade de modulação, diminui com $\bar\omega_h$ e é máxima em $\varphi = 90°$, com a haste mais lenta na metade em que o centro de massa desce. Qualquer outra forma periódica colhe apenas pelo primeiro harmônico, pois os superiores integram zero contra o $\sin\theta_h$ da gravidade, e a cossenoide entrega toda a colheita disponível com o mínimo de esforço de atuador.

Dentro de cada volta o torque da gravidade alterna de sinal, e é a roda que o absorve para a haste manter o perfil. Integrar o termo gravitacional da (2) mostra que a velocidade da roda ondula com amplitude de primeiro harmônico, sobreposta à taxa de variação média de (4).

$$\Delta\omega_r = \frac{mgd}{J\bar\omega_h} \tag{9}$$

A ondulação cresce quando a velocidade média da haste cai, e é ela, contra o limite de velocidade da roda, que fixa o piso da faixa de operação, como os resultados mostram.

A operação se sustenta quando a colheita (8) repõe, volta a volta, o que o atrito retira. O atrito consome $2\pi\langle T_p\rangle/\bar\omega_h$ por volta, e igualar as duas parcelas dá a profundidade de modulação de equilíbrio, razão direta entre o atrito em $\bar\omega_h$ e o torque máximo do desbalanceamento.

$$\varepsilon_{eq} = \frac{2\langle T_p\rangle}{mgd\sin\varphi} \tag{10}$$

### 2.2 Modelo do atuador

O atuador é um motor de corrente contínua acionado por ponte H com modulação por largura de pulso. O comando $u$ tem módulo igual à razão cíclica e sinal igual ao do sentido de rotação, e a armadura recebe a tensão média $uV_s$, o que dá a dinâmica da roda em torno do próprio eixo.

$$J\dot{\omega}_r = \frac{K_t}{R}\left(uV_s - K_v\omega_r\right) - T_r \tag{11}$$

Nela, $K_t$ é a constante de torque, $K_v$ é a constante de força contraeletromotriz, $R$ é a resistência do circuito de armadura e $T_r$ é o torque de atrito da roda, com parcelas seca e viscosa como o atrito do pivô. A parcela seca cresce em velocidade baixa e impõe uma zona morta no comando $u$, que o controle vence a cada passagem da roda por zero.

De (11) saem as duas assinaturas que a identificação apresentada na seção de resultados explora, a reta de regime, em que a velocidade cresce com $u$ com inclinação próxima de $V_s/K_v$, e a resposta de primeira ordem ao degrau, com constante de tempo $\tau_m = JR/(K_tK_v)$.

![](figuras/fig_diagrama_cascata.svg "1.00")
Figura 3 - Diagrama de blocos da cascata. No destaque, a hierarquia, dos governadores lentos (C3, C4) ao gerador de perfil (C2), à malha da haste (C1) e à da roda (C0).

As equações (2), (6) e (11) descrevem a planta completa, do comando $u$ à velocidade da haste, com todas as grandezas acessíveis pelos dois encoders.

## 3 ESTRATÉGIA DE CONTROLE

O problema de controle tem três frentes simultâneas, percorrer o perfil (6) dentro de cada volta, manter a colheita no equilíbrio (10) de volta a volta e conservar as velocidades médias de roda e haste ao longo de minutos, e um único atuador para as três, o motor da roda.

Por (2), o torque disponível sobre a haste é a reação $-J\dot{\omega}_r$, e comandar torque na haste equivale a comandar aceleração na roda. Organizamos o controle em uma cascata de cinco controladores, mostrada na Figura 3. O operador fixa apenas a velocidade média de cruzeiro da haste. Do mais rápido ao mais lento:

- **Malha de velocidade da roda (C0)**: a única que comanda o motor.
- **Malha de velocidade da haste (C1)**: segue a referência instantânea de velocidade e impõe aceleração à roda.
- **Gerador de perfil (C2)**: dá a referência instantânea de (6) a partir do ângulo medido.
- **Governador de velocidade média da roda (C3)**: ajusta a profundidade de modulação $\varepsilon$.
- **Governador de velocidade média da haste (C4)**: desloca o valor central do perfil.

A malha da roda é calculada a 1 kHz e as demais a 100 Hz. A separação de escalas está nas bandas, as malhas da roda e da haste respondem dentro de cada volta, enquanto os ganhos e os filtros confinam os governadores a 0,01 Hz e 0,003 Hz, bem abaixo da frequência de uma volta, de modo que eles enxergam apenas as médias, sem reagir ao perfil que eles mesmos comandam.

### 3.1 Execução do perfil

Executar o perfil (6) sobre a haste é tarefa das duas malhas mais internas, ambas proporcional integral e operando sobre velocidades medidas pelos encoders.

A malha de velocidade da roda (C0) é a única que toca o motor. Compara a velocidade-alvo com a medida no encoder do motor e produz o comando (12) limitado a $|u| \le 1$.

$$u = K_{p,r}e_r + K_{i,r}\int e_r dt, \qquad e_r = \omega_{r,ref} - \omega_r \tag{12}$$

A malha de velocidade da haste (C1) segue a referência instantânea $\omega_{h,ref}(\theta_h)$ produzida pelo gerador de perfil (C2). Isolar $\dot{\omega}_r$ em (2) mostra o que o atuador entrega a cada instante, e as duas parcelas conhecidas entram como *feedforward*.

$$\begin{array}{l} \dot{\omega}_{r,ref} = -\frac{mgd}{J}\sin\theta_h - \frac{I}{J}\frac{d\omega_{h,ref}}{dt} \\ \qquad - K_{p,h}e_h - K_{i,h}\int e_h dt, \\ e_h = \omega_{h,ref} - \omega_h \end{array} \tag{13}$$

O primeiro termo antecipa o torque da gravidade sobre o desbalanceamento. O segundo é a aceleração exigida pela própria modulação do perfil. A derivada do perfil é analítica, $d\omega_{h,ref}/dt = -\bar\omega_h\varepsilon\sin(\theta_h - \varphi)\omega_{h,ref}$, obtida de (6) com $d\theta_h/dt$ tomado como a própria referência. A saída de (13) é integrada no tempo para formar a velocidade-alvo que a C0 recebe.

### 3.2 Gestão do equilíbrio

O gerador de perfil (C2) converte o ângulo medido da haste na referência instantânea de (6). É uma fórmula pura no ângulo, sem estado próprio. O perfil é espelhado pelo sentido de rotação, como a medida do C3, pois a fase ótima põe a haste mais lenta onde o centro de massa desce nos dois sentidos.

O C2 também corrige a diferença entre o valor central do perfil e a média que a haste de fato executa. A média no tempo fica abaixo do valor central na razão $\sqrt{1-\varepsilon^2}$, como a 2.1 mostrou.

$$\bar\omega_{h,ef} = \frac{\bar\omega_h}{\sqrt{1-\varepsilon^2}} \tag{14}$$

Em que $\bar\omega_h$ é a média imposta, somando a referência do operador com o deslocamento corrigido pelo C4. O ajuste é determinístico, sem ganho a sintonizar.

O governador de velocidade média da roda (C3) fecha o balanço de (10) durante a operação. Ele compara a velocidade média da roda, extraída por um filtro de corte abaixo da frequência de rotação, com uma referência de média. Este controlador ajusta a profundidade de modulação que o C2 utiliza. A planta que ele enxerga é um integrador de ganho conhecido, pois dividir a colheita por volta (8) e o consumo do atrito pela duração da volta $2\pi/\bar\omega_h$ generaliza (4) para incluir a colheita.

$$J\langle\dot{\omega}_r\rangle = \frac{mgd\varepsilon\sin\varphi}{2} - \langle T_p\rangle \tag{15}$$

Ela recai na (4) com $\varepsilon = 0$ e se anula na profundidade de equilíbrio de (10). O controlador é proporcional integral, com integração condicional e saída saturada no intervalo $[0, \varepsilon_{max}]$, em que o teto limita a ondulação imposta à haste e o piso em zero basta porque reduzir a colheita e deixar o atrito agir já devolve momento. Em cruzeiro o valor médio da referência de velocidade da roda é zero, o que não significa roda parada e sim que a excursão da roda tenderá a se igualar nas duas direções em regime permanente. Já para a pré-docagem é um valor não nulo, a fim de ter maior excursão da roda antes de alcançar a saturação.

O governador de velocidade média da haste (C4) cobre o que a correção determinística da média não alcança, a parcela da ondulação executada que não é a senoide comandada. Ele integra o erro entre a média pedida e a medida e devolve um deslocamento do valor central do perfil. Não tem termo proporcional, pois o filtro que extrai a média atenua a frequência da volta sem eliminá-la, e um termo proporcional devolveria esse resto ao perfil.

![](figuras/fig_prototipo.png "0.75")
Figura 4 - Protótipo em bancada.

### 3.3 Partida por bombeamento

O cruzeiro pressupõe a haste já girando, e a partida do repouso é um modo próprio. Adotamos o bombeamento de energia do pêndulo, com a reação da roda empurrando sempre no sentido do movimento, de modo que cada meia oscilação acrescenta energia. A grandeza realimentada é a energia mecânica por unidade de inércia da haste, com $\omega_0$ de (3) e $\theta_h$ medido a partir do ponto baixo, escrita sem a linearização de pequena amplitude porque o bombeamento percorre toda a faixa de ângulo.

$$E = \frac{1}{2}\omega_h^2 + \omega_0^2\left(1 - \cos\theta_h\right) \tag{16}$$

Um pulso curto de comando máximo tira a haste do repouso e dá à lei o sinal de velocidade de que ela precisa. O bombeamento substitui apenas a malha da haste.

A mesma energia decide a transição ao cruzeiro. Quando $E$ supera a barreira do ponto alto, que vale $2\omega_0^2$ na unidade de (16), com sobra que garante 1 rad/s ao chegar lá, a gravidade fecha a volta sozinha e o controle converte sem esperar a passagem pelo topo. Em cruzeiro, se a velocidade da haste permanecer abaixo de um piso pelo equivalente a meia volta o movimento voltou a ser oscilação, e o controle retorna à partida.

## 4 RESULTADOS EXPERIMENTAIS

A Figura 4 mostra o protótipo em operação. Um anel deslizante acopla o eixo da haste aos circuitos de

Tabela 1 - Parâmetros do protótipo.

| Grandeza | Símbolo | Valor |
|---|---|---|
| Motor CC com redutor | | CHP-36GP-555 |
| Alimentação | $V_s$ | 12 V |
| Microcontrolador | | ESP32 |
| Inércia do conjunto | $I$ | 4,6×10⁻² kg·m² |
| Inércia da roda | $J$ | 7,7×10⁻⁴ kg·m² |
| Desbalanceamento | $mgd$ | 0,078 N·m |
| Frequência natural | $\omega_0^2$ | 1,699 s⁻² |
| Constantes do motor | $K_t = K_v$ | 0,0991 N·m/A |
| Atrito seco da roda | $T_{r,s}$ | 14,8 mN·m |
| Atrito visc. da roda | $b_r$ | 95,5 µN·m·s/rad |
| Atrito seco do pivô | $T_{p,s}$ | 2,7 mN·m |
| Atrito visc. do pivô | $b_p$ | 3,5 mN·m·s/rad |
| Encoder da haste | | 2400 cont./volta |
| Encoder da roda | | 350 cont./volta |

![](figuras/fig_pendulo.png "1.00")
Figura 5 - Pêndulo livre da haste com o motor desligado, de onde saem a frequência natural e o atrito do pivô. Dois ensaios com a haste liberada à mão, cobrindo amplitudes de 12° a 123°.

potência e de sinal, permitindo a rotação contínua sem o arrasto do cabeamento. Toda a medição vem dos dois encoders, a velocidade da haste obtida por período entre bordas em velocidade baixa e por janela de contagem em velocidade alta, e a da roda por janela deslizante de 8 ms. A telemetria grava todos os sinais da cascata em CSV a 100 Hz, e dessas séries saem todas as figuras e métricas desta seção. A Tabela 1 reúne os parâmetros do protótipo, com os símbolos das seções anteriores.

A Figura 5 mostra o pêndulo livre da haste com o motor desligado, em dois ensaios com a haste liberada à mão, cobrindo amplitudes de 12° a 123°. Com o ângulo em função do tempo. Com o período de cada ciclo contra a amplitude. E com a perda de amplitude por ciclo.

O período de pequena amplitude é 4,82 s, que por (3) dá ω₀² = 1,699 ± 0,007 s⁻², e os 48 ciclos extraídos seguem o período do pêndulo simples com desvio

eficaz de 1,5%, o que confirma a dependência ω₀²(1−cosθ) usada na lei de energia da partida (16). A perda de amplitude por ciclo separa o atrito do pivô em uma parcela seca e uma viscosa, ΔA = 0,1359 + 0,1843·A, de onde saem $T_{p,s}$ e $b_p$ da Tabela 1.

A Figura 6 mostra a resposta em regime do motor em malha aberta, levantada com uma escada de degraus de comando nos dois sentidos e uma rampa fina na região central. A inclinação da reta é 121,0 rad/s por unidade de comando, que a 12 V dá $K_v$ = 0,0991 V·s/rad no eixo da roda por (11). A rampa central expõe a zona morta do atuador, com arranque em comando 0,106 e morte em 0,098. O atrito da roda cresce quando a velocidade cai, e é esse degrau que o integrador da malha de velocidade da roda vence toda vez que a roda cruza velocidade baixa.

A Figura 7 mostra o atrito mecânico da roda, medido por desaceleração livre com os fios do motor desconectados, necessário porque a ponte H curto-circuita o motor em razão cíclica nula e o freio elétrico mascararia o efeito do atrito. No painel (b) o tempo de ensaio é trocado pelo tempo que falta até a roda parar, e nesse eixo as dez desacelerações, partidas de velocidades e instantes diferentes, caem todas sobre a mesma curva, a trajetória de parada da roda. É sobre ela que as duas parcelas do atrito se separam, a seca, constante, que sozinha daria a reta tracejada, e a viscosa, sombreada entre a reta e a trajetória medida. O modelo resultante é desaceleração = 19,20 + 0,1241·ω rad/s², dominado pela parcela seca, e com a inércia da Tabela 1 saem $T_{r,s}$ = 14,8 mN·m e $b_r$ = 95,5 µN·m/(rad/s).

A razão de inércias sai dos mesmos degraus de comando, pelo ajuste do balanço de momento angular em torno do pivô com os parâmetros do pêndulo travados e um único parâmetro livre, J/I = 0,0167 ± 0,0015, o mesmo valor nos dois sentidos de rotação.

A Figura 8 mostra o ensaio em que medimos a perda por atrito do pivô e o ganho de colheita com a haste em rotação. Com o governador de velocidade média da roda desligado, comandamos doze patamares de ondulação ε fixa, em 0, 0,10, 0,20 e 0,35, com a haste em cruzeiro a 2,5 rad/s. Sem o governador, a velocidade média da roda sobe ou desce conforme a colheita supere a perda ou fique aquém dela. A reta

![](figuras/fig_curva_estatica.png "1.00")
Figura 6 - Resposta da roda à escada de comando em malha aberta, que dá a curva estática do atuador. Degraus nos dois sentidos e rampa fina na região central, onde aparece a zona morta de atuação do motor.

![](figuras/fig_atrito_roda.png "1.00")
Figura 7 - Desaceleração livre da roda para medir o atrito mecânico, com os fios do motor desconectados. Desacelerações sucessivas, comparadas ao modelo com e sem parcela viscosa.

![](figuras/fig_dreno_colheita.png "1.00")
Figura 8 - Resposta da velocidade média da roda a patamares de ondulação comandada, que dá a perda por atrito do pivô e o ganho de colheita. Haste em cruzeiro a 2,5 rad/s com o governador de velocidade média da roda desligado.

ajustada, taxa = 60,3·ε − 8,1, dá o ganho de colheita de 60,3 ± 1,6 rad/s² por unidade de ε e cruza zero em ε = 0,1343, o equilíbrio de (10) em que a colheita iguala a perda por atrito. Com o governador ligado, em ensaio independente, o sistema operou em ε = 0,1353.

O ganho medido supera em 24% a previsão de primeira ordem de (8), mgd/2J = 48,5, porque a haste ondula cerca de 1,4 vez o comando e a gravidade atua sobre a ondulação executada. Regredindo a taxa contra essa ondulação saem a perda por atrito do

![](figuras/fig_cruzeiro.png "1.00")
Figura 9 - Cruzeiro contínuo da haste por 600 s a 2,5 rad/s, com a velocidade média da roda mantida em torno de zero. Um trecho do regime ampliado à direita.

pivô, 9,13 ± 0,23 rad/s² na roda, e mgd/J = 97,0 ± 1,7 s⁻², a 5% do valor obtido pelo pêndulo com a razão de inércias. São esses valores que o controle passou a usar, mgd/J no *feedforward* de gravidade e o ganho de colheita na sintonia do governador.

A partida converte a oscilação da haste em rotação contínua quando a energia cruza o limiar de (16). Em duas partidas com o limiar calculado a partir do ω₀² medido no pêndulo livre, a conversão aconteceu já na primeira meia oscilação do bombeamento, com a haste cruzando o fundo a 2,779 e 2,785 rad/s contra o limiar de 2,792 rad/s, margem de energia de 0,4 e 0,9%. Da partida ao cruzeiro estabelecido decorreram 2,85 e 2,84 s.

O cruzeiro de 600 s, ou 24 constantes de tempo do integrador lento, manteve a velocidade média com viés de +0,0001 rad/s, menos de 0,01% do comandado, flutuação eficaz de 0,0017 rad/s e erro máximo de 0,0062 rad/s, dentro da banda de 0,03 rad/s. A velocidade média da roda cresceu à taxa de +0,0002 rad/s², isto é, a colheita compensou a perda por atrito do pivô sem que a roda caminhasse para nenhum dos limites de grampeamento, e o comando não saturou em amostra nenhuma, com pico de 0,681.

A ondulação de regime se estabeleceu em ε = 0,1542, 15% acima do equilíbrio de 0,1343 previsto por (10). A diferença vem da correção do *feedforward* de gravidade, que com o ganho medido deixa de empurrar a haste em excesso, e a ondulação comandada passa a sustentar a colheita inteira. A razão entre a ondulação executada e a comandada é 1,154, com defasagem de +2,2°.

![](figuras/fig_degrau_rampa.png "1.00")
Figura 10 - Resposta do controle à troca de velocidade média comandada, em degrau e em rampa de 0,05 rad/s². Mesmas trocas de 2,5 para 3,5 rad/s e de 3,5 para 2,0 rad/s, ampliadas abaixo.

![](figuras/fig_limites.png "1.00")
Figura 11 - Resposta do controle ao degrau de velocidade comandada, apresentando os limites de operação da velocidade média. Um ensaio subindo até 5,5 rad/s e outro descendo até 1,0 rad/s.

Trocar a velocidade média de cruzeiro é a manobra que mais exige do atuador, durante a transição a roda absorve o momento angular da aceleração da haste e ainda precisa continuar com a compensação do atrito no pivô, e é aí que ela pode saturar. O ensaio mostra que limitar a taxa da referência evita essa saturação. A Figura 10 compara uma transição em degrau na referência de velocidade média com uma rampa de 0,05 rad/s², nas mesmas trocas de 2,5 para 3,5 rad/s e de 3,5 para 2,0 rad/s.

Um sinal ao degrau leva a haste ao novo valor com sobressinal de 11,1% na subida, e o pico instantâneo da roda chega a 103,0 rad/s na subida e a 104,6 rad/s na descida, com o comando do motor saturado em 4,37% das amostras do minuto seguinte à troca. A rampa, por outro lado, leva o pico a 78,5 e 69,2 rad/s, reduz a saturação do comando a 1,03% na subida e a zero na descida, e o sobressinal a 2,7%.

O ensaio seguinte procura os limites da velocidade média, na Figura 11, um ensaio subindo até 5,5 rad/s e outro descendo até 1,0 rad/s.

![](figuras/fig_dock.png "1.00")
Figura 12 - Manobra de docagem, com a pré-carga da roda, a janela de velocidade instantânea constante e a recuperação do cruzeiro. Janela de docagem ampliada à direita.

Acima dessa faixa a folga do comando acaba, com 6,1% das amostras no máximo em 4,5 rad/s e metade do tempo em 5,5 rad/s, velocidade em que a haste assenta 8% abaixo da comandada. O limite inferior tem outra origem. Quanto mais lenta a haste, mais tempo a gravidade tem para acelerar e frear a roda dentro de cada volta, e a excursão da roda cresce com o inverso da velocidade média, conforme (9). Em 1,0 rad/s a roda chega a 109,6 rad/s contra os 105 rad/s do grampeamento da referência, e é aí que aparece a primeira saturação do ensaio que desce.

A manobra que fecha o capítulo é a de docagem, na Figura 12. Ela eleva a velocidade média da roda a +50 rad/s, reserva de momento angular disponível para a manobra, zera a ondulação do perfil e desliga o governador de velocidade média da roda. A haste passa a girar sem colheita, e a roda absorve sozinha o momento angular drenado pelo atrito do pivô, como em (4), até atingir o limite de grampeamento de 105 rad/s.

A pré-carga não degrada o cruzeiro. Em ensaio próprio de 200 s a velocidade média da roda se sustentou em 49,92 ± 1,14 rad/s, com a velocidade média da haste na referência e flutuação de 0,0015 rad/s, e o pico instantâneo da roda ficou em 96,5 rad/s, abaixo do limite de 105 rad/s e dentro da margem prevista pela soma da ondulação de gravidade de (9) com a do perfil comandado. O esforço de controle sobe, com comando eficaz 61% maior que no mesmo cruzeiro sem pré-carga, e na entrada por degrau, que produz sobressinal de 42% na velocidade média por volta e pico instantâneo de 110 rad/s.

A janela de docagem durou 14,1 s. Com o perfil plano e o integrador lento congelado, a referência instantânea da haste ficou fixa em 2,5204 rad/s e a velocidade média da roda caiu a uma taxa de 8,26 rad/s², contra os 9,13 rad/s² que a planta medida no ensaio da Figura 8 prevê. Nessa mesma taxa, levar a roda do repouso ao limite de 105 rad/s tomaria cerca de 12 s, que é o prazo de saturação de (5) para esta bancada.

A recuperação preserva o cruzeiro. Ao atingir o limite a colheita é religada, a velocidade média da roda volta a zero 7,0 s depois e a velocidade média da haste cai a 2,20 rad/s antes de retornar a 2,52 rad/s.

## 5 CONSIDERAÇÕES FINAIS

Apresentamos o controle de velocidade de uma haste giratória em plano vertical atuada apenas por roda de reação, em rotação contínua sustentada. A colheita de momento angular vem da excursão mais lenta ou mais rápida da haste conforme o ângulo, comandada pelo controle, e possível pelo desbalanceamento do conjunto. Ela compensa o atrito do pivô, que drena momento angular sem cessar. O balanço médio por volta previu a profundidade de equilíbrio e a ondulação da roda dentro da volta.

A cascata de cinco malhas executa esse programa com dois encoders e um único atuador, separando as malhas rápidas, que impõem o perfil dentro da volta, das lentas, que governam apenas as médias. A haste manteve a velocidade média por 600 s com viés abaixo de 0,01% da referência, na faixa de 1,0 a 3,5 rad/s, com velocidade média da roda nula e sem saturação permanente. É a dessaturação contínua que em órbita se faz por gradiente de gravidade, aqui em segundos em vez de dias.

Por fim, uma malha adicional emula a docagem, em que a velocidade instantânea da haste precisa se manter constante e a roda absorve sozinha o momento angular drenado pelo atrito, sem colheita. A janela útil medida foi de 14,1 s e decorre do modelo levantado em malha aberta, assim como em órbita a janela de aproximação é limitada pelo momento que a roda ainda pode absorver. O passo seguinte é a trajetória de referência na pré-carga da roda, que hoje entra por degrau. O alinhamento de fase contra um alvo exige um segundo dispositivo e fica fora do escopo deste trabalho.

## FINANCIAMENTO

Este estudo contou com apoio financeiro do Conselho Nacional de Desenvolvimento Científico e Tecnológico (CNPq), Brasil – Bolsa nº 190401/2025-7.

## DECLARAÇÃO DE USO DE INTELIGÊNCIA ARTIFICIAL GENERATIVA

Em conformidade com a Portaria CNPq nº 2.664/2026, os autores declaram o uso de Claude-Code (Anthropic) e Codex (OpenAI) na concepção, para discussão da abordagem e levantamento de referências, na implementação e na análise, para redação e depuração do firmware e dos scripts de ensaio, e na redação do texto, para clareza e correção de linguagem. Todo o conteúdo gerado foi verificado e editado pelos autores, que assumem responsabilidade integral pelo trabalho.


## CONFLITO DE INTERESSES

Os autores declaram não haver conflito de interesses no desenvolvimento e na publicação deste trabalho.

## REFERÊNCIAS

ALVES, U. N. L. T.; BREGANON, R.; PIVOVAR, L. E.; ALMEIDA, J. P. L. S.; BARBARA, G. V.; MENDONÇA, M.; PALÁCIOS, R. H. C. Discrete-time H∞ integral control via LMIs applied to a Furuta pendulum. Journal of Control, Automation and Electrical Systems, v. 33, n. 3, p. 1-12, 2022. DOI: 10.1007/s40313-021-00867-x.



LEOMANNI, M.; QUARTULLO, R.; BIANCHINI, G.; GARULLI, A.; GIANNITRAPANI, A. Variable-horizon guidance for autonomous rendezvous and docking to a tumbling target. Journal of Guidance, Control, and Dynamics, v. 45, n. 5, p. 846-858, 2022. DOI: 10.2514/1.G006340.

MARKLEY, F. L.; CRASSIDIS, J. L. Fundamentals of Spacecraft Attitude Determination and Control. New York: Springer, 2014. DOI: 10.1007/978-1-4939-0802-8.

SANDOVAL, J.; KELLY, R.; SANTIBÁÑEZ, V.; MORENO-VALENZUELA, J. A speed regulator for a torque-driven inertia wheel pendulum. IFAC-PapersOnLine, v. 53, n. 2, p. 6293-6298, 2020. DOI: 10.1016/j.ifacol.2020.12.1749.

SANTOS, J. B.; SILVA, L. D.; SOUZA, R. H. S.; RIBEIRO, F. S. F.; BREGANON, R.; ALVES, U. N. L. T. Controle via LMIs de um protótipo de pêndulo invertido com roda de reação. Revista Mundi Engenharia, Tecnologia e Gestão, Paranaguá, v. 11, n. 2, p. 1-14, 2026. DOI: 10.21575/25254782rmetg2026vol11n22573.

SIDI, M. J. Spacecraft Dynamics and Control: A Practical Engineering Approach. Cambridge: Cambridge University Press, 1997. DOI: 10.1017/CBO9780511815652.

SOUZA, R. H. S.; SILVA, L. D.; RIBEIRO, F. S. F.; BREGANON, R.; ALVES, U. N. L. T. Projeto, implementação e controle de um protótipo pêndulo invertido com roda de reação. In: SIMPÓSIO DE ENGENHARIA DE CONTROLE E AUTOMAÇÃO, 6., 2025, Jacarezinho. Anais [...]. Jacarezinho: IFPR, 2025. p. 40-49. DOI: 10.29327/1780404.6-4.

SPONG, M. W.; CORKE, P.; LOZANO, R. Nonlinear control of the Reaction Wheel Pendulum. Automatica, v. 37, n. 11, p. 1845-1851, 2001. DOI: 10.1016/S0005-1098(01)00145-5.

TONG, D. Spacecraft momentum dumping using gravity gradient. Journal of Spacecraft and Rockets, v. 35, n. 5, p. 714-717, 1998. DOI: 10.2514/2.3389.

TREGOUET, J.-F.; ARZELIER, D.; PEAUCELLE, D.; PITTET, C.; ZACCARIAN, L. Reaction wheels desaturation using magnetorquers and static input allocation. IEEE Transactions on Control Systems Technology, v. 23, n. 2, p. 525-539, 2015. DOI: 10.1109/TCST.2014.2326037.


VADALI, S. R.; OH, H.-S. Space station attitude control and momentum management: a nonlinear look. Journal of Guidance, Control, and Dynamics, v. 15, n. 3, p. 577-586, 1992. DOI: 10.2514/3.20878.

XU, X.; WIERCIGROCH, M.; CARTMELL, M. P. Rotating orbits of a parametrically-excited pendulum. Chaos, Solitons & Fractals, v. 23, n. 5, p. 1537-1548, 2005. DOI: 10.1016/j.chaos.2004.06.053.

<!-- Formatação ABNT autor-data conforme o modelo do SIMECA; ordem alfabética. Todas verificadas em 2026-08-24 (DOI/handle resolvendo em página do editor, Crossref ou repositório). -->
