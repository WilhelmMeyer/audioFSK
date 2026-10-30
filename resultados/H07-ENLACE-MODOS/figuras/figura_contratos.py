"""Figura do artigo: o contrato de cada sentido do enlace negociado, sessao 2 do H07.

Para cada sentido, a margem de cada tom da grade de sondagem (562,5 a 4462,5 Hz,
passo 162,5 Hz) medida pelo receptor na ultima sondagem, e quais tons o contrato
tomou. Le so os diarios da sessao (linhas "sondagem lida" e "contrato").

    ./venv/bin/python resultados/H07-ENLACE-MODOS/figuras/figura_contratos.py
"""
import os
import re

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

AQUI = os.path.dirname(os.path.abspath(__file__))
SES = os.path.join(os.path.dirname(AQUI), 'sessoes')
RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(AQUI)))
SAIDAS = (os.path.join(AQUI, 'enlace-contratos.png'),
          os.path.join(RAIZ, 'artigo', 'figuras', 'enlace-contratos.png'))
GRADE = [562.5 + 162.5 * k for k in range(25)]
TEAL, CINZA, ERRO = '#2E7D82', '#C9D1D3', '#C0392B'
plt.rcParams.update({'font.size': 8, 'axes.labelsize': 8, 'xtick.labelsize': 7.5,
                     'ytick.labelsize': 7.5, 'axes.linewidth': 0.7, 'savefig.dpi': 300})

# (receptor que mediu, rotulo, bytes)
SENTIDOS = [('20261022-161111-enlace-ouvinte.diario.txt', 'De quem chama para quem escuta', '207 de 207 bytes'),
            ('20261022-161117-enlace-chamador.diario.txt', 'De quem escuta para quem chama', '44 de 44 bytes')]


def le(diario):
    txt = open(os.path.join(SES, diario)).read()
    margens = [int(v) for v in re.findall(r'sondagem lida:.*?margens \[([^\]]+)\]', txt)[-1].split(',')]
    c = re.findall(r'contrato para o que me chega: (\d+)-(\d+) Hz, sombras \[([^\]]*)\], par [^,]+, '
                   r'ganho ([\d.]+), (16-FSK rep\d)', txt)[-1]
    lo, hi = float(c[0]), float(c[1])
    sombras = [float(s) for s in c[2].split(',') if s.strip()]
    tons = [f for f in GRADE if lo - 1 <= f <= hi + 1 and all(abs(f - s) > 1 for s in sombras)]
    assert len(tons) == 16, (diario, len(tons))
    return margens, tons, sombras, float(c[3]), c[4]


fig, eixos = plt.subplots(2, 1, figsize=(3.4, 3.1), sharex=True)
for ax, (diario, rot, entregue) in zip(eixos, SENTIDOS):
    margens, tons, sombras, ganho, camada = le(diario)
    for f, m in zip(GRADE, margens):
        usado = any(abs(f - t) < 1 for t in tons)
        excl = any(abs(f - s) < 1 for s in sombras)
        cor = TEAL if usado else (ERRO if excl else CINZA)
        ax.bar(f, m, width=130, color=cor, hatch='////' if excl else None,
               edgecolor='white' if excl else cor, lw=0)
    rep = camada.split('rep')[1]
    ax.set_title(rot, fontsize=7.5, loc='left', pad=12)
    ax.text(0, 1.02, f'ganho {ganho:.2f} · rep {rep} · 100 baud · {entregue}'.replace('.', ','),
            transform=ax.transAxes, ha='left', va='bottom', fontsize=6.5, color='0.35')
    ax.set_ylim(0, 45)
    ax.set_yticks([0, 20, 40])
    ax.set_ylabel('Margem (dB)')
    for lado in ('top', 'right'):
        ax.spines[lado].set_visible(False)
    print(f'{rot}: tons {tons[0]:.1f}-{tons[-1]:.1f} Hz, excluidos {sombras}, ganho {ganho}, {camada}')
eixos[1].set_xlabel('Tom da sondagem (Hz)')
eixos[1].set_xticks([1000, 2000, 3000, 4000])
from matplotlib.patches import Patch
eixos[0].legend(handles=[Patch(color=TEAL, label='contratado'),
                         Patch(facecolor=ERRO, hatch='////', edgecolor='white', label='excluído'),
                         Patch(color=CINZA, label='fora da faixa')],
                frameon=False, fontsize=7, ncol=3, loc='lower left', bbox_to_anchor=(0, 1.36))
fig.tight_layout(h_pad=1.4)
for s in SAIDAS:
    fig.savefig(s, bbox_inches='tight')
print('[contratos]', ', '.join(SAIDAS))
