"""Rastreia um bit da mensagem ate as posicoes onde ele aparece no bloco.

A figura anterior mostrava "erra bits e acerta a mensagem" e nao deixava ver o
esquema: cada bit da mensagem entra no codificador e faz sair tres bits, e o
entrelacamento espalha esses tres pelo bloco. Aqui os tres sao seguidos ate a
posicao em que foram transmitidos e ate a verossimilhanca com que chegaram.

Dois casos, escolhidos por regra e nao a mao: o bit limpo cuja pior das tres
confiancas e a maior do bloco, e o primeiro bit com uma das tres trocadas. O
caso de duas trocadas foi tirado a pedido do autor: existe no bloco (tres bits
o tem) mas confunde mais do que mostra, porque o leitor ja entendeu o desempate
no caso anterior.

A faixa de cima existe para nao se perder a mensagem de vista: os 48 bytes
transmitidos, com os dois bytes de onde saem os bits seguidos marcados.

Cada bit da mensagem aparece em QUINZE posicoes transmitidas, nao tres: ele
fica na janela por sete passos e, em cada passo, um subconjunto diferente das
tres saidas depende dele (3, 2, 3, 2, 1, 1 e 3 saidas, somando quinze). A
versao anterior desta figura mostrava so as tres do passo em que o bit entra,
o que sugeria que a evidencia sobre ele eram tres bits. Nao sao.

CUIDADO com o que a figura afirma. No passo em que o bit entra, o codificador
emite tres bits, e os tres dependem dele e dos seis anteriores. O bit continua
influenciando os passos seguintes enquanto anda pelo registrador, e o Viterbi
nao decide um bit olhando so essas tres posicoes: ele escolhe o caminho inteiro.
A legenda diz "os tres bits emitidos quando este bit entrou".

    ./venv/bin/python resultados/14-FEC-REP/figuras/figura_fec_rastro.py
"""

import json
import pathlib
import sys

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

RAIZ = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ))
import fec  # noqa: E402

STEM = 'resultados/14-FEC-REP/gravacao/20260903-172504-rep1-B2A'
LLR = 'resultados/14-FEC-REP/llr/20260903-172504-rep1-B2A.csv'
AQUI = pathlib.Path(__file__).resolve().parent
SAIDAS = [AQUI / 'fec-rastro.png', RAIZ / 'artigo' / 'figuras' / 'fec-rastro.png']

CONFERE = '#1B7F79'
DISCORDA = '#C43D2F'


def carrega():
    meta = json.load(open(RAIZ / (STEM + '.json')))
    payload = bytes.fromhex(meta['payload_hex'])
    csv = np.genfromtxt(RAIZ / LLR, delimiter=',', skip_header=1)
    llr = csv[:, 1:].ravel()
    inicio = fec.find_sync(llr)
    if inicio is None:
        sys.exit('sincronismo nao encontrado')
    tx = fec.encode(payload, repeat=1)
    rx = llr[inicio:inicio + len(tx)]
    if fec.decode(rx, len(payload)) != payload:
        sys.exit('a decodificacao nao reproduz o payload; nao desenhar')
    return payload, tx, rx


# Quais das tres saidas dependem da posicao j+1 da janela. Vem dos proprios
# polinomios: a saida usa a posicao se o bit correspondente estiver ligado.
def _saidas_por_posicao():
    tabela = []
    for j in range(fec.K):
        quais = [i for i, poly in enumerate(fec.POLYS_R13)
                 if (poly >> (fec.K - 1 - j)) & 1]
        tabela.append(quais)
    return tabela


def rastro(payload, tx, rx):
    """Para cada bit da mensagem, TODAS as posicoes que dependem dele.

    Um bit fica na janela por sete passos. Em cada passo saem tres bits, e
    quais deles dependem dele muda conforme a posicao que ele ocupa. Somando,
    sao quinze posicoes, e nao as tres do passo em que ele entrou.
    """
    n = len(tx)
    idx = fec.interleave_index(n, 16)      # transmitido[p] = codificado[idx[p]]
    pos = np.zeros(n, dtype=int)
    pos[idx] = np.arange(n)                # pos[c] = posicao transmitida
    errado = (rx > 0).astype(np.int8) != tx
    por_posicao = _saidas_por_posicao()
    passos = n // len(fec.POLYS_R13)
    linhas = []
    for k in range(len(payload) * 8):
        ps = []
        for j, quais in enumerate(por_posicao):
            passo = k + j
            if passo >= passos:
                continue
            ps += [int(pos[3 * passo + i]) for i in quais]
        linhas.append((k, ps, [float(rx[p]) for p in ps],
                       [bool(errado[p]) for p in ps]))
    return linhas, errado


def escolhe(linhas):
    limpos = [r for r in linhas if not any(r[3])]
    um = [r for r in linhas if sum(r[3]) == 1]
    dois = [r for r in linhas if sum(r[3]) == 2]
    casos = [max(limpos, key=lambda r: min(abs(v) for v in r[2]))]
    if um:
        casos.append(um[0])
    return casos


def faixa_mensagem(eixo, payload, casos):
    """Os 48 bytes como texto, com os bytes dos bits seguidos em destaque."""
    texto = payload.decode('ascii', 'replace')
    destaque = {k // 8 for k, _, _, _ in casos}
    for i, ch in enumerate(texto):
        marcado = i in destaque
        eixo.text(i + 0.5, 0.42, ch, ha='center', va='center',
                  fontsize=8.5 if not marcado else 9.5,
                  color='0.35' if not marcado else CONFERE,
                  fontweight='normal' if not marcado else 'bold',
                  family='monospace')
        if marcado:
            eixo.add_patch(plt.Rectangle((i + 0.06, 0.08), 0.88, 0.68,
                                         fill=False, ec=CONFERE, lw=1.2))
    for k, _, _, _ in casos:
        eixo.annotate(f'bit {k}', (k // 8 + 0.5, 0.05), ha='center', va='top',
                      fontsize=8, color=CONFERE)
    eixo.set_xlim(0, len(texto))
    eixo.set_ylim(-0.5, 1.0)
    eixo.axis('off')
    eixo.set_title('mensagem transmitida, 48 bytes', fontsize=9.5, loc='left', pad=2)


def companheiros(rx, tx, errado, n):
    """Para cada bit trocado, a confianca dele e a dos dois companheiros.

    Companheiros sao os outros dois bits emitidos no mesmo passo do
    codificador, isto e, pelo mesmo bit da mensagem.
    """
    idx = fec.interleave_index(n, 16)
    pos = np.zeros(n, dtype=int)
    pos[idx] = np.arange(n)
    mag = np.abs(rx)
    saida = []
    for p in np.where(errado)[0]:
        c = idx[p]
        k = c // 3
        outros = [pos[3 * k + i] for i in range(3) if 3 * k + i != c]
        saida.append((float(mag[p]),
                      [(float(mag[q]), bool(errado[q])) for q in outros]))
    return sorted(saida, key=lambda r: r[0])


def desenha(casos, rx, tx, errado, n, payload):
    fig = plt.figure(figsize=(6.3, 8.0), layout='constrained')
    grade = fig.add_gridspec(len(casos) + 3, 1,
                             height_ratios=[0.7] + [1] * len(casos) + [1.5, 1.5])
    eixos = [fig.add_subplot(grade[0, :])]
    for i in range(len(casos)):
        eixos.append(fig.add_subplot(grade[i + 1, :]))
    eixos.append(fig.add_subplot(grade[-2, :]))
    eixo_disp = fig.add_subplot(grade[-1, :])
    faixa_mensagem(eixos[0], payload, casos)
    for eixo, (k, ps, vs, es) in zip(eixos[1:], casos):
        eixo.axhline(0, color='0.55', lw=0.8, zorder=1)
        for p, v, e in zip(ps, vs, es):
            cor = DISCORDA if e else CONFERE
            eixo.plot([p, p], [0, v], color=cor, lw=1.6, zorder=2)
            eixo.plot([p], [v], marker='D' if e else 'o',
                      color=cor if e else 'none',
                      mec=DISCORDA if e else CONFERE,
                      ms=6.5 if e else 5.5, mew=1.3, zorder=3)
            if e:
                texto = f'confiança {abs(v):.2f}'.replace('.', ',')
                eixo.annotate(texto, (p, v), textcoords='offset points',
                              xytext=(0, -16), ha='center', va='top',
                              fontsize=8.5, color=DISCORDA)
        erros = sum(es)
        rotulo = ('as quinze posições conferem' if erros == 0
                  else 'uma das quinze chegou trocada, as outras catorze não'
                  if erros == 1
                  else f'{erros} das quinze chegaram trocadas')
        eixo.set_title(f'bit {k} da mensagem: {rotulo}', fontsize=9.5,
                       loc='left', pad=3)
        eixo.set_xlim(-20, n + 20)
        eixo.set_ylim(-6.2, 6.2)
        eixo.set_yticks([-4, 0, 4])
        eixo.set_ylabel('confiança,\ncom o sinal do bit', fontsize=8.5)
        eixo.tick_params(labelsize=8.5)
        eixo.grid(axis='x', color='0.85', lw=0.5, ls=':')
    eixos[len(casos)].set_xlabel('posição no bloco transmitido (1170 bits)', fontsize=9.5)

    eixo = eixos[-1]
    mag = np.abs(rx)
    faixas = np.linspace(0, float(mag.max()) + 0.01, 26)
    n_ok, _ = np.histogram(mag[~errado], bins=faixas)
    n_err, _ = np.histogram(mag[errado], bins=faixas)
    centros = (faixas[:-1] + faixas[1:]) / 2
    largura = (faixas[1] - faixas[0]) * 0.92
    eixo.bar(centros, n_err, width=largura, color=DISCORDA,
             label=f'chegaram trocados ({errado.sum()})')
    eixo.bar(centros, n_ok, width=largura, bottom=n_err, color=CONFERE,
             alpha=0.35, label=f'chegaram certos ({(~errado).sum()})')
    eixo.set_xlabel('confiança com que o bit chegou', fontsize=9.5)
    eixo.set_ylabel('bits', fontsize=9.5)
    eixo.tick_params(labelsize=8.5)
    eixo.legend(frameon=False, fontsize=8.5, loc='upper right')
    eixo.spines['top'].set_visible(False)
    eixo.spines['right'].set_visible(False)
    eixo.set_title('os trocados chegaram com pouca confiança',
                   fontsize=9.5, loc='left', pad=3)

    pares = companheiros(rx, tx, errado, n)
    for i, (conf, outros) in enumerate(pares):
        alturas = [conf] + [c for c, _ in outros]
        eixo_disp.plot([i, i], [min(alturas), max(alturas)], color='0.8',
                       lw=0.8, zorder=1)
        for c, e in outros:
            eixo_disp.plot([i], [c], marker='o' if not e else 'D',
                           color=CONFERE if not e else DISCORDA, ms=4,
                           mec='white', mew=0.5, zorder=2)
        eixo_disp.plot([i], [conf], marker='D', color=DISCORDA, ms=4.5,
                       mec='white', mew=0.5, zorder=3)
    eixo_disp.set_xlim(-1.5, len(pares) + 0.5)
    eixo_disp.set_xticks([])
    eixo_disp.set_xlabel('os 69 bits que chegaram trocados, '
                         'em ordem de confiança', fontsize=9.5)
    eixo_disp.set_ylabel('confiança', fontsize=9.5)
    eixo_disp.tick_params(labelsize=8.5)
    eixo_disp.spines['top'].set_visible(False)
    eixo_disp.spines['right'].set_visible(False)
    eixo_disp.spines['bottom'].set_visible(False)
    eixo_disp.set_title('cada bit trocado e os outros dois emitidos no mesmo '
                        'passo do codificador', fontsize=9.5, loc='left', pad=3)

    for saida in SAIDAS:
        fig.savefig(saida, dpi=300)
        print('escrito', saida)


def main():
    payload, tx, rx = carrega()
    linhas, errado = rastro(payload, tx, rx)
    casos = escolhe(linhas)
    for k, ps, vs, es in casos:
        print(f'bit {k}: posições {ps} módulos '
              f'{[round(abs(v), 2) for v in vs]} trocados {es}')
    print(f'{errado.sum()} de {len(tx)} bits trocados '
          f'({100 * errado.mean():.2f}%)')
    desenha(casos, rx, tx, errado, len(tx), payload)


if __name__ == '__main__':
    main()
