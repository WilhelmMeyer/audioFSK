# G20-SUBTRAI-CAUDA: subtração da cauda dos símbolos anteriores, offline

Data 2026-10-08. **Só leitura de `captures/`: nada foi transmitido nem gravado.** Código no `c57fc74` (o `modem.py` real foi usado só para conferir as decisões: idênticas, 1,000, nas 13 gravações). Resultado completo em `RESULTADO.md`; tabela por gravação e variante em `tabela.txt`; oráculos em `oraculo_cru.txt` e `ganho.txt`.

## O que é

Subtrai, na energia de cada tom, a cauda estimada dos 1 a 3 símbolos anteriores (coeficiente cego e online, razão de duas EMAs), antes da decisão. Muda só o receptor, não o fio. Comparada com o receptor atual (a), com o IFK e com um oráculo que conhece os tons anteriores verdadeiros.

## Resumo

Bits antes do FEC, média por regime (sem IFK): eco (6 gravações) 85,8 % -> 89,0 % (k=1..3) -> 90,4 % (k=1..3 ×4); moderado (2) 89,2 -> 91,4 -> 92,3; limpo (2) 99,9 -> 100,0 -> 100,0. Contagem k=1..3 contra o atual: 9 melhores, 1 igual, 0 piores. Blocos: eco 3/6 -> 5/6; moderado 1/2 -> 1/2; limpo 2/2.

## Ressalvas (leia antes de citar)

- **Variante escolhida nos mesmos dados em que foi medida** (k, piso cru, ganho ×4 foram comparados nas 13 gravações). Precisa de validação em gravações novas, em especial nas rodadas r1 a r4 (posição 2, não usadas aqui), antes de entrar no `modem.py`.
- O regime "limpo" são as três gravações a 10 cm da passada A, em que não há cauda a subtrair; ali o resultado é nulo, como deveria.
- Os regimes "eco" e "moderado" vêm da bancada anterior (caixa em posições piores), não da bancada final.
- "Oráculo" usa o tom anterior verdadeiro e escolhe o fator na própria gravação: é um teto otimista, não um receptor.
- Os pares f04/f06 foram gravados segundos um do outro; parte da diferença IFK contra subtração é gravação, não método.

## Refazer

A raiz do repositório é o diretório de trabalho (`captures/` com os wav):

    ./venv/bin/python resultados/G20-SUBTRAI-CAUDA/subtrai.py 20261008-161939-f04-16fsk 20261008-162926-f04-16fsk-v4 ...   > out-<stem>.json   # grava cache-<stem>.pkl nesta pasta, imprime json
    ./venv/bin/python resultados/G20-SUBTRAI-CAUDA/tabela.py          # lê out-*.json, escreve tabela.txt
    ./venv/bin/python resultados/G20-SUBTRAI-CAUDA/oraculo_cru.py <stem>
    ./venv/bin/python resultados/G20-SUBTRAI-CAUDA/ganho.py <stem>

Os `out-*.json`/`cache-*.pkl` (pickles) não foram copiados para cá; `subtrai.py` os recria. `subtrai.py` já ajusta o `sys.path` para a raiz (dois níveis acima da pasta). Não testei a reexecução completa.

## Validação fora da amostra

26 gravações novas, variante congelada (detalhes em `validacao/VALIDACAO.md`, números em `validacao/resumo.txt`).

- Sem IFK: bits 97.18 -> 98.56 %, melhor em 16 de 16; oráculo 98.82 %. Erros de bit -49 %. Blocos 26/26 em todas as variantes.
- Com IFK: efeito neutro (+0.1 a +0.2 pt).
- Subtração simples + subtração empata com IFK (98.44 vs 98.49 %): equivale ao IFK sem mudar o fio; somar os dois não acrescenta.
- As conclusões do G20 original de que a subtração supera o IFK NÃO se repetiram neste canal moderado.
