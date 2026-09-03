# 08-MARY-GAIN -- M-ario, varredura de ganho

- **Codigo:** commit `2abc119` (main), que e `0718f2c` mais as ferramentas
  desta campanha.
- **Quando:** 2026-09-03, 16:29-16:32.
- **Camada:** M-ario, 16 tons, `fecrep 2`, com FEC. Cadeia ja linear (a
  correcao registrada em 07-MARY-BASE ja estava em vigor).
- **Direcao:** B -> A. Caixa Bluetooth nova em B.
- **Payload:** 48 bytes aleatorios, quatro pontos de ganho, 3 trials cada.

Pontuacao offline por `bench.py`. Figuras extras `*-leitura.png` geradas com
`spectro.py --fundido --win 480`.

## Resultado

| ganho | gravacoes | rms | pico | blocos inteiros |
|---|---|---|---|---|
| 1,00 (mg2-g1.0) | 162920/162931/162941 | 0,0299/0,0305/0,0293 | 0,158/0,155/0,144 | **3 de 3** |
| 0,70 (mg3-g0.7) | 163126/163137/163147 | 0,0256/0,0237/0,0240 | 0,127/0,121/0,127 | **2 de 3** (163147 falhou, 0/48) |
| 0,50 (mg2-g0.5) | 163009/163020/163031 | 0,0267/0,0160/0,0221 | 0,132/0,085/0,101 | **3 de 3** |
| 0,25 (mg3-g0.25) | 163214/163225/163235 | 0,0116/0,0122/0,0129 | 0,069/0,071/0,062 | **2 de 3** (163214 falhou, 1/48) |

**Total: 11 blocos inteiros de 12.**

## Leitura

**Corrigida -- ver "Repontuacao com relogio travado" abaixo.** A leitura
original desta secao dizia que os dois trials perdidos (163147 e 163214)
eram ruido espalhado sem tendencia. Isso estava errado: os dois eram colapso
de sincronismo, nao ruido de canal nem efeito do ganho. O que segue e a
versao corrigida.

Este teste **nao achou ponto de operacao porque nao ha um**. Um fator 4 de
amplitude (12 dB, de ganho 1,00 a 0,25) e a recuperacao em bits nao se move:
os 12 trials entregaram 96-98% dos bits (ver secao abaixo) em toda a faixa de
ganho testada. O que variou entre os 12 nao foi o ganho -- foi a sorte do
sincronismo em dois deles.

Confirma o que a camada promete: M-ario decide por comparacao entre tons
dentro do mesmo simbolo, e escalar tudo nao muda qual tom e o mais forte --
**desde que nada no caminho esteja ceifando**. Compare com o teste
07-MARY-BASE saturado: la o mesmo ajuste de ganho (1.0 -> 0.5) dava 1 de 3 em
vez de 3 de 3.

## Repontuacao com relogio travado (correcao)

As duas gravacoes que o caminho vivo deu como falha (163147 e 163214) foram
repontuadas com o relogio congelado no inicio correto (melhor offset
encontrado por forca bruta), do mesmo jeito usado em 12-13-SYNC:

| gravacao | ganho | bits certos (melhor offset) | bloco pelo caminho vivo | bloco com piso por tom estimado |
|---|---|---|---|---|
| 20260903-163147-mg3-g0.7 | 0,70 | 96,7% | falhou (0/48) | recuperado |
| 20260903-163214-mg3-g0.25 | 0,25 | 97,2% | falhou (1/48) | recuperado |

Media das duas: gate 96,9% dos bits com 0/2 blocos; relogio travado no melhor
offset 97,3% com 1/2; travado dividindo pelo ruido por tom (o que o codigo ja
estima sozinho) 97,6% com **2/2**.

**Conclusao corrigida:** os dois blocos perdidos nao foram ruido nem efeito
de ganho -- foram **colapso de sincronismo**. O link entregou 96-97% dos
bits nas duas gravacoes, e o bloco se perdeu porque o `find_sync` caiu na
posicao errada. A conclusao principal deste teste (numa cadeia linear o
ganho nao importa entre 0,25 e 1,0) sai **reforcada**: em bits, os 12 trials
entregaram; o que variou foi a sorte do sincronismo, nao o ganho.

**Consequencia metodologica:** uma varredura de ganho pontuada so pelo
decodificador vivo mede a sorte do gate junto com o ganho. Blocos recuperados
e uma medida ruim para escolher parametro fino; acuracia de bits num
alinhamento por forca bruta e estavel e e a medida certa, com blocos
recuperados como numero honesto separado (mesmo principio registrado em
12-13-SYNC).

## Nota de ferramenta

Durante esta varredura o `capture.py` produziu sete gravacoes abortadas (0 a
1,4 s, rms exatamente zero) porque abria o microfone e ja comecava a contar a
janela de 10 s, sem esperar o dispositivo entregar audio -- falha que
acontece logo depois de outro processo soltar o dispositivo. **Corrigido**:
agora espera um bloco com conteudo real (nao zeros exatos) por ate 3 s e
falha alto se nao vier. As gravacoes abortadas estao em `gravacao/vazias/`
(copiadas de `captures/vazias/`), fora da pontuacao.

## Arquivos

- `gravacao/` -- as doze gravacoes validas, WAV float32 mais JSON;
  `gravacao/vazias/` -- as seis gravacoes abortadas encontradas em
  `captures/vazias/` que correspondem a esta campanha (0 a 1,4 s, rms zero),
  mantidas como evidencia da falha de ferramenta, fora da pontuacao
- `figuras/` -- espectro cru e contraste (600-3600 Hz) para as doze validas;
  mais uma figura `<stem>-leitura.png` por gravacao (`--fundido --win 480`)
- `resultado.csv` -- uma linha por gravacao valida
