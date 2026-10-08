# Como refazer H05-ERROS-POR-TOM

Da raiz do repositório, offline (sem áudio, sem serial):

    ./venv/bin/python -u resultados/H05-ERROS-POR-TOM/erros_por_tom.py

~25 s com 10 processos (`--jobs N` muda). Lê as gravações listadas em
`CORPUS` no topo do script, demodula e grava `simbolos.json`; depois calcula
as estatísticas e escreve `por-gravacao.csv`, `por-tom.csv`,
`confusao-B2A.csv`, `confusao-A2B.csv`, `resultado.json` e
`fig-ser-por-tom.png`. A saída de texto foi guardada em `saida.txt`.

Só as estatísticas e a figura, sem demodular de novo:

    ./venv/bin/python -u resultados/H05-ERROS-POR-TOM/erros_por_tom.py --so-estatistica

As permutações usam semente fixa (20261008), então os números se repetem.

O script fixa `OMP_NUM_THREADS=1` (e equivalentes) antes de importar o numpy:
sem isso cada processo abre um BLAS multifio e a máquina fica com carga 50 sem
avançar.

Figura: barras = SER por tom transmitido; parte clara = erros em que o
detector escolheu o tom do símbolo anterior; vermelho = os 3 piores; faixa
cinza = ±1.96 desvios binomiais em torno da SER média, com o número médio de
símbolos por tom -- onde as barras cairiam se todos os tons fossem iguais.
