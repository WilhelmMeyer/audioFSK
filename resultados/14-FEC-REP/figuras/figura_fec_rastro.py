"""Rastreia um bit da mensagem ate as posicoes onde ele aparece no bloco.

A figura anterior mostrava "erra bits e acerta a mensagem" e nao deixava ver o
esquema: cada bit da mensagem entra no codificador e faz sair tres bits, e o
entrelacamento espalha esses tres pelo bloco. Aqui os tres sao seguidos ate a
posicao em que foram transmitidos e ate a verossimilhanca com que chegaram.

Tres casos, escolhidos por regra e nao a mao: o bit limpo cuja pior das tres
confiancas e a maior do bloco, o primeiro bit com uma das tres trocadas, e o
primeiro com duas trocadas (so tres bits do bloco tem duas).

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


def rastro(payload, tx, rx):
    """Para cada bit da mensagem, as tres posicoes transmitidas e o que chegou."""
    n = len(tx)
    idx = fec.interleave_index(n, 16)      # transmitido[p] = codificado[idx[p]]
    pos = np.zeros(n, dtype=int)
    pos[idx] = np.arange(n)                # pos[c] = posicao transmitida
    errado = (rx > 0).astype(np.int8) != tx
    linhas = []
    for k in range(len(payload) * 8):
        ps = [int(pos[3 * k + i]) for i in range(3)]
        linhas.append((k, ps, [float(rx[p]) for p in ps], [bool(errado[p]) for p in ps]))
    return linhas, errado


def escolhe(linhas):
    limpos = [r for r in linhas if not any(r[3])]
    um = [r for r in linhas if sum(r[3]) == 1]
    dois = [r for r in linhas if sum(r[3]) == 2]
    casos = [max(limpos, key=lambda r: min(abs(v) for v in r[2]))]
    if um:
        casos.append(um[0])
    if dois:
        casos.append(dois[0])
    return casos


def desenha(casos, rx, tx, errado, n):
    fig, eixos = plt.subplots(len(casos) + 1, 1, figsize=(6.3, 6.4),
                              gridspec_kw={'height_ratios': [1] * len(casos) + [1.5]})
    for eixo, (k, ps, vs, es) in zip(eixos, casos):
        eixo.axhline(0, color='0.55', lw=0.8, zorder=1)
        for p, v, e in zip(ps, vs, es):
            cor = DISCORDA if e else CONFERE
            eixo.plot([p, p], [0, v], color=cor, lw=1.6, zorder=2)
            eixo.plot([p], [v], marker='D' if e else 'o', color=cor, ms=7,
                      mec='white', mew=1.0, zorder=3)
            eixo.annotate(f'{abs(v):.2f}', (p, v), textcoords='offset points',
                          xytext=(0, 9 if v > 0 else -16), ha='center', fontsize=8.5)
        erros = sum(es)
        rotulo = {0: 'as tres posicoes conferem',
                  1: 'uma das tres chegou trocada',
                  2: 'duas das tres chegaram trocadas'}[erros]
        eixo.set_title(f'bit {k} da mensagem: {rotulo}', fontsize=9.5, loc='left', pad=3)
        eixo.set_xlim(-20, n + 20)
        eixo.set_ylim(-5.6, 5.6)
        eixo.set_yticks([-4, 0, 4])
        eixo.set_ylabel('verossim.', fontsize=8.5)
        eixo.tick_params(labelsize=8.5)
        eixo.grid(axis='x', color='0.85', lw=0.5, ls=':')
    eixos[len(casos) - 1].set_xlabel('posição no bloco transmitido (1170 bits)', fontsize=9.5)

    eixo = eixos[-1]
    mag_err = np.abs(rx[errado])
    mag_ok = np.abs(rx[~errado])
    faixas = np.linspace(0, max(mag_ok.max(), mag_err.max()), 28)
    eixo.hist(mag_ok, bins=faixas, density=True, color=CONFERE, alpha=0.35,
              label=f'bits que conferem ({(~errado).sum()})')
    eixo.hist(mag_err, bins=faixas, density=True, histtype='step', lw=1.6,
              color=DISCORDA, label=f'bits trocados ({errado.sum()})')
    eixo.axvline(mag_err.mean(), color=DISCORDA, ls=':', lw=1.2)
    eixo.axvline(mag_ok.mean(), color=CONFERE, ls=':', lw=1.2)
    eixo.set_xlabel('módulo da verossimilhança (confiança do bit)', fontsize=9.5)
    eixo.set_ylabel('densidade', fontsize=9.5)
    eixo.tick_params(labelsize=8.5)
    eixo.legend(frameon=False, fontsize=8.5)
    eixo.annotate(f'média {mag_err.mean():.2f} nos trocados,'
                  f' {mag_ok.mean():.2f} nos que conferem',
                  (0.97, 0.72), xycoords='axes fraction', ha='right', fontsize=8.5)
    fig.tight_layout(h_pad=1.1)
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
    desenha(casos, rx, tx, errado, len(tx))


if __name__ == '__main__':
    main()
