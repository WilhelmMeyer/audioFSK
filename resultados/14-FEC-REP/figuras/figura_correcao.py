"""Figura do artigo (capítulo 4): a correção agindo num bloco real.

Uma gravação 16-FSK com correção de erros, repetição 1, lida offline como o
receptor lê (demodulação suave em blocos de 2048 amostras, palavra de
referência por correlação, Viterbi). Em cima, os bits codificados na ordem em
que foram transmitidos, com um traço em cada posição onde a decisão dura da
verossimilhança discorda do bit enviado (o enviado é refeito por fec.encode a
partir da carga gravada, não lido do áudio). Embaixo, os bits da mensagem
depois do Viterbi, conferidos contra a carga. Os dois eixos têm escalas
próprias: o entrelaçamento desfaz a correspondência posição a posição. Por
último, a confiança |LLR| dos bits que chegaram certos e dos trocados.

    ./venv/bin/python resultados/14-FEC-REP/figuras/figura_correcao.py
"""
import json
import os
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(AQUI)))
sys.path.insert(0, RAIZ)
import fec                                            # noqa: E402
import modem                                          # noqa: E402
import recording                                      # noqa: E402

STEM = '20260903-172519-rep1-B2A'   # a de mais bits trocados entre as quatro de repetição 1
BLOCO = 2048                        # o mesmo fatiamento com que a campanha foi pontuada
SAIDAS = (os.path.join(AQUI, 'correcao-bloco.png'),
          os.path.join(RAIZ, 'artigo', 'figuras', 'correcao-bloco.png'))
TEAL, TEAL_MED, CINZA = '#0F5257', '#2E7D82', '#9AA5A8'
ERRADO = '#C43D2F'
plt.rcParams.update({'font.size': 8.5, 'axes.labelsize': 8.5, 'xtick.labelsize': 7.5,
                     'ytick.labelsize': 8, 'axes.linewidth': 0.7, 'savefig.dpi': 300,
                     'figure.dpi': 300})


def virgula(v, casas=1):
    return f'{v:.{casas}f}'.replace('.', ',')


def le():
    base = os.path.join(os.path.dirname(AQUI), 'gravacao', STEM)
    meta = json.load(open(base + '.json'))
    x = recording.read(recording.audio_path(base))
    d = modem.MaryDemodulator(fs=meta['fs'], baud=meta['baud'], gap=meta.get('gap', 0.0),
                              band=meta.get('band', 0.0), chord=bool(meta.get('chord')),
                              gray=modem.gray_gravado(meta))
    llr = np.concatenate([d.demodulate_soft(x[i:i + BLOCO]) for i in range(0, len(x), BLOCO)])
    ini = fec.find_sync(llr)
    if ini is None:
        raise SystemExit(f'[correcao] {STEM}: palavra de referência não achada')
    carga = bytes.fromhex(meta['payload_hex'])
    lido = fec.decode(llr[ini:], meta['payload_len'], repeat=meta['fec_repeat'])
    if lido != carga:
        raise SystemExit(f'[correcao] {STEM}: o bloco não decodifica de volta à carga')
    env = np.asarray(fec.encode(carga, repeat=meta['fec_repeat']), dtype=np.int8)
    rec = np.asarray(llr[ini:ini + len(env)], dtype=float)
    return env, rec, carga, lido


def bordas(ax, n, nome):
    ax.set_xticks([0, n])
    ax.set_xticklabels(['0', str(n)])
    for r, ha in zip(ax.get_xticklabels(), ('left', 'right')):
        r.set_ha(ha)
    ax.text(0.5, -0.32, nome, transform=ax.transAxes, ha='center', va='top',
            fontsize=7, color='0.35')


def main():
    env, rec, carga, lido = le()
    err = (rec > 0).astype(np.int8) != env
    mod = np.abs(rec)
    msg_err = np.unpackbits(np.frombuffer(lido, np.uint8)) != np.unpackbits(np.frombuffer(carga, np.uint8))
    n, nm = len(env), 8 * len(carga)

    fig = plt.figure(figsize=(3.4, 2.55))
    gs = fig.add_gridspec(3, 1, height_ratios=[0.5, 0.5, 1.25], hspace=1.25,
                          left=0.03, right=0.97, top=0.9, bottom=0.15)

    ax = fig.add_subplot(gs[0])
    ax.axhspan(0, 1, color='#E3EEEF', lw=0)
    ax.vlines(np.flatnonzero(err) + 0.5, 0, 1, color=ERRADO, lw=0.55)
    ax.set_xlim(0, n); ax.set_ylim(0, 1); ax.set_yticks([])
    bordas(ax, n, 'ordem de transmissão')
    ax.set_title(f'Recebidos: {err.sum()} de {n} bits codificados trocados '
                 f'({virgula(100 * err.mean())}%)', fontsize=7.5, loc='left', pad=3)
    ax.tick_params(length=2, pad=1.5)

    ax = fig.add_subplot(gs[1])
    ax.axhspan(0, 1, color=TEAL_MED, alpha=0.45, lw=0)
    ax.vlines(np.flatnonzero(msg_err) + 0.5, 0, 1, color=ERRADO, lw=0.55)
    ax.set_xlim(0, nm); ax.set_ylim(0, 1); ax.set_yticks([])
    bordas(ax, nm, 'ordem da mensagem')
    ax.set_title(f'Decodificados: {int(msg_err.sum())} de {nm} bits da mensagem trocados',
                 fontsize=7.5, loc='left', pad=3)
    ax.tick_params(length=2, pad=1.5)

    ax = fig.add_subplot(gs[2])
    bins = np.linspace(0, 1.02 * mod.max(), 30)
    ax.hist(mod[~err], bins=bins, density=True, color=TEAL_MED, alpha=0.45, lw=0,
            label=f'certos (média {virgula(mod[~err].mean(), 2)})')
    ax.hist(mod[err], bins=bins, density=True, histtype='step', color=ERRADO, lw=1.1,
            label=f'trocados (média {virgula(mod[err].mean(), 2)})')
    ax.set_xlim(0, bins[-1]); ax.set_yticks([])
    ax.set_xlabel('Confiança do bit codificado, |LLR|', labelpad=1.5)
    ax.legend(frameon=False, fontsize=7, loc='upper right', handlelength=1.2)
    for lado in ('top', 'right', 'left'):
        ax.spines[lado].set_visible(False)
    ax.tick_params(length=2, pad=1.5)

    for s in SAIDAS:
        fig.savefig(s)
    print(f'[correcao] {STEM}: {err.sum()} de {n} bits codificados trocados '
          f'({virgula(100 * err.mean(), 2)}%), mensagem {int(msg_err.sum())} de {nm} trocados')
    print(f'    |LLR| médio {virgula(mod[err].mean(), 2)} nos trocados, {virgula(mod[~err].mean(), 2)} nos certos')
    for s in SAIDAS:
        print('   ', s)


if __name__ == '__main__':
    main()
