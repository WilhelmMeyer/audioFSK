"""Bits errados chegam, bloco sai inteiro: a figura da camada de correcao.

Tres faixas no mesmo eixo de indice de bit codificado -- o que foi
transmitido, o que chegou (a verossimilhanca de cada bit) e onde os dois
discordam -- mais um recorte legivel e a distribuicao dos modulos, que e o
mecanismo: os bits que chegam errados sao os de baixa confianca, e a decisao
suave leva isso em conta em vez de tratar todo bit como igualmente certo.

A quarta faixa, a mensagem decodificada, NAO compartilha esse eixo e nao pode
compartilhar: `fec.encode` entrelaca depois de repetir, entao um bit da carga
nao mora numa posicao unica do bloco codificado. Ela tem eixo proprio, em
bytes da mensagem, e a figura diz isso no rotulo.

O portao e o mesmo das figuras da 07-MARY-BASE: o bloco tem de decodificar de
volta ao `payload_hex` da gravacao, byte a byte, ou o programa para. Uma
figura de correcao de erro desenhada sobre um bloco que nao decodifica nao
mostra correcao nenhuma.
"""

import argparse
import json
import os
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


def raiz():
    d = os.path.dirname(os.path.abspath(__file__))
    while d != os.path.dirname(d):
        if os.path.exists(os.path.join(d, 'modem.py')):
            return d
        d = os.path.dirname(d)
    raise SystemExit("[figura] nao achei a raiz do repositorio")


RAIZ = raiz()
sys.path.insert(0, RAIZ)

import fec                                            # noqa: E402
import recording                                      # noqa: E402
from modem import MaryDemodulator                     # noqa: E402

AQUI = os.path.dirname(os.path.abspath(__file__))
GRAVACAO = os.path.join(os.path.dirname(AQUI), 'gravacao')

# As quatro gravacoes do ponto de repeticao 1 desta campanha. Lista fechada:
# os pontos de repeticao 2 e 4 gastam outro tempo de ar e carregam outro
# numero de bits codificados, e uma delas entrar aqui por descuido daria uma
# figura correta em forma e falsa em conteudo.
STEMS = ('20260903-172504-rep1-B2A',
         '20260903-172511-rep1-B2A',
         '20260903-172519-rep1-B2A',
         '20260903-172526-rep1-B2A')
PADRAO = STEMS[0]

# O mesmo tamanho de bloco com que a campanha foi pontuada. O demodulador e
# estateful e a porta early/late anda de acordo com o que ja consumiu, entao
# alimentar tudo de uma vez daria outro alinhamento.
BLOCO = 2048

# Paleta das figuras de camada fisica deste artigo: o sinal em cinza, cor so
# para o que o receptor fez. Verde-azul quando confere com o transmitido,
# vermelho quando nao.
CERTO = '#1B7F79'
ERRADO = '#C43D2F'
SINAL = '0.45'
CLARO = '0.80'

LARGURA = 6.3           # polegadas ~ 16 cm, uma coluna

plt.rcParams.update({
    'font.size': 9,
    'axes.titlesize': 9,
    'axes.labelsize': 9.5,
    'xtick.labelsize': 8.5,
    'ytick.labelsize': 8.5,
    'legend.fontsize': 8,
    'axes.linewidth': 0.8,
    'savefig.dpi': 300,
    'figure.dpi': 300,
})


def virgula(v, casas=1):
    return f"{v:.{casas}f}".replace('.', ',')


class Bloco:
    """Uma gravacao lida, demodulada e casada com os bits transmitidos."""

    def __init__(self, stem):
        if stem not in STEMS:
            raise SystemExit(f"[figura] {stem} nao e uma das gravacoes de "
                             f"repeticao 1 desta campanha: {', '.join(STEMS)}")
        base = os.path.join(GRAVACAO, stem)
        meta = json.loads(open(base + '.json').read())
        if meta.get('mode') != 'mary' or meta.get('kind') != 'fec':
            raise SystemExit(f"[figura] {stem} nao e uma gravacao 16-FSK com FEC")
        amostras = recording.read(recording.audio_path(base))

        d = MaryDemodulator(fs=meta['fs'], baud=meta['baud'],
                            gap=meta.get('gap', 0.0), band=meta.get('band', 0.0),
                            chord=bool(meta.get('chord')))
        llr = np.concatenate([d.demodulate_soft(amostras[i:i + BLOCO])
                              for i in range(0, len(amostras), BLOCO)])

        inicio = fec.find_sync(llr)
        if inicio is None:
            raise SystemExit(f"[figura] {stem}: sincronismo nao achado")

        carga = bytes.fromhex(meta['payload_hex'])
        lido = fec.decode(llr[inicio:], meta['payload_len'],
                          repeat=meta['fec_repeat'])
        if lido != carga:
            raise SystemExit(f"[figura] {stem}: o bloco nao decodifica de volta "
                             f"a carga gravada")

        # Os bits TRANSMITIDOS, pelo mesmo caminho do transmissor:
        # convolucional, repeticao, entrelacamento. Nao sao os lidos do audio.
        self.enviado = np.asarray(fec.encode(carga, repeat=meta['fec_repeat']),
                                  dtype=np.int8)
        self.recebido = np.asarray(llr[inicio:inicio + len(self.enviado)],
                                   dtype=np.float64)
        if len(self.recebido) < len(self.enviado):
            raise SystemExit(f"[figura] {stem}: a gravacao acaba "
                             f"{len(self.enviado) - len(self.recebido)} bits "
                             f"antes do fim do quadro")

        self.stem = stem
        self.meta = meta
        self.carga = carga
        self.lido = lido
        self.duro = (self.recebido > 0).astype(np.int8)
        self.errado = self.duro != self.enviado
        self.modulo = np.abs(self.recebido)
        self.segundos = len(amostras) / meta['fs']

    @property
    def erro(self):
        return float(self.errado.mean())

    def recorte(self, largura, inicio=None):
        """Primeira janela de `largura` bits com a taxa de erro do bloco.

        Escolhida por regra, nao a olho: a janela mais a esquerda cuja
        contagem de erros e a esperada para o bloco, arredondada. Uma janela
        escolhida pela aparencia mostraria o que o desenhista quis, e o
        recorte existe justamente para dizer que o resto do bloco e assim.
        """
        if inicio is not None:
            return int(inicio)
        alvo = int(round(self.erro * largura))
        soma = np.convolve(self.errado.astype(int), np.ones(largura, int), 'valid')
        onde = np.flatnonzero(soma == alvo)
        if not len(onde):
            onde = [int(np.argmin(np.abs(soma - alvo)))]
        return int(onde[0])


def faixa_bits(ax, bits, cor_zero, cor_um):
    """Uma linha de bits como raster: cada bit uma coluna de um pixel."""
    ax.imshow(np.asarray(bits, dtype=float)[None, :], aspect='auto',
              interpolation='nearest', vmin=0, vmax=1,
              extent=(0, len(bits), 0, 1),
              cmap=matplotlib.colors.ListedColormap([cor_zero, cor_um]))
    ax.set_yticks([])
    for lado in ('left', 'right', 'top', 'bottom'):
        ax.spines[lado].set_linewidth(0.5)


def desenha(b, largura_recorte, inicio_recorte):
    n = len(b.enviado)
    fig = plt.figure(figsize=(LARGURA, 7.5))
    gs = fig.add_gridspec(6, 1,
                          height_ratios=[0.30, 1.45, 0.14, 1.15, 0.30, 1.15],
                          hspace=0.72, left=0.165, right=0.985,
                          top=0.99, bottom=0.06)

    # (a) o que foi transmitido -- sinal, portanto cinza.
    ax = fig.add_subplot(gs[0])
    faixa_bits(ax, b.enviado, '1.0', SINAL)
    ax.set_xlim(0, n)
    ax.set_xticklabels([])
    ax.set_ylabel('enviado', rotation=0, ha='right', va='center', labelpad=6)

    # (b) o que chegou: verossimilhanca com sinal e modulo, bloco inteiro.
    ax = fig.add_subplot(gs[1])
    i = np.arange(n)
    ax.axhline(0, color='0.6', lw=0.6)
    ax.vlines(i[~b.errado], 0, b.recebido[~b.errado], color=CERTO, lw=0.35)
    ax.vlines(i[b.errado], 0, b.recebido[b.errado], color=ERRADO, lw=0.9)
    ax.set_xlim(0, n)
    lim = 1.06 * np.max(b.modulo)
    ax.set_ylim(-lim, lim)
    ax.set_ylabel('verossimilhanca recebida')
    ax.set_xticklabels([])
    ax.text(0.012, 0.05, f"{virgula(100 * b.erro, 1)}% dos bits discordam do "
                         f"enviado", transform=ax.transAxes, color=ERRADO,
            fontsize=8.5, va='bottom')

    # marca o recorte da faixa seguinte
    k0 = b.recorte(largura_recorte, inicio_recorte)
    k1 = k0 + largura_recorte
    ax.axvspan(k0, k1, color='0.88', zorder=0)

    # (b2) so as posicoes onde houve erro. Presenca numa posicao e um canal
    # que nao e cor, entao esta faixa sobrevive a impressao em escala de
    # cinza, onde `CERTO` e `ERRADO` tem luminancia quase igual (96 contra
    # 100 de 255) e a faixa de cima vira uma massa unica. E tambem o lugar
    # onde a dispersao dos erros ao longo do bloco se le de relance.
    ax = fig.add_subplot(gs[2])
    ax.vlines(i[b.errado], 0, 1, color=ERRADO, lw=0.6)
    ax.set_xlim(0, n)
    ax.set_ylim(0, 1)
    ax.set_xticks([])
    ax.set_yticks([])
    for lado in ('left', 'right', 'top', 'bottom'):
        ax.spines[lado].set_linewidth(0.5)
    ax.set_ylabel('erros', rotation=0, ha='right', va='center', labelpad=6)

    # (c) o mesmo, num recorte onde cada bit e um marcador legivel.
    ax = fig.add_subplot(gs[3])
    j = np.arange(k0, k1)
    e = b.errado[k0:k1]
    v = b.recebido[k0:k1]
    ax.axhline(0, color='0.6', lw=0.6)
    ax.vlines(j, 0, v, color=CLARO, lw=0.8, zorder=1)
    ax.plot(j[~e], v[~e], 'o', ms=3.2, mfc=CERTO, mec='w', mew=0.5, ls='none',
            zorder=2, label='concorda com o bit enviado')
    ax.plot(j[e], v[e], 'D', ms=3.6, mfc=ERRADO, mec='w', mew=0.5, ls='none',
            zorder=3, label='discorda')
    ax.set_xlim(k0 - 0.5, k1 - 0.5)
    # Folga embaixo para a legenda, que nao pode cair sobre marcador nenhum.
    ax.set_ylim(-1.42 * lim, lim)
    ax.set_xlabel('indice do bit codificado')
    ax.set_ylabel('verossimilhanca recebida')
    ax.legend(loc='lower center', frameon=False, ncol=2, handletextpad=0.3,
              columnspacing=1.6, borderpad=0.1)

    # (d) a mensagem decodificada. Eixo proprio, em bytes: o entrelacamento
    # dissolve a correspondencia posicao a posicao com o bloco codificado.
    ax = fig.add_subplot(gs[4])
    bits = np.unpackbits(np.frombuffer(b.lido, dtype=np.uint8), bitorder='little')
    faixa_bits(ax, bits, '1.0', CERTO)
    ax.set_xlim(0, len(bits))
    ax.set_xticks(np.arange(0, len(bits) + 1, 64))
    ax.set_xticklabels([str(t // 8) for t in np.arange(0, len(bits) + 1, 64)])
    ax.set_xlabel(f'indice do byte da mensagem decodificada '
                  f'({len(b.lido)} B, identica a enviada)')
    ax.set_ylabel('decodificado', rotation=0, ha='right', va='center', labelpad=6)

    # (e) por que a decisao suave ganha: o erro se concentra no modulo baixo.
    ax = fig.add_subplot(gs[5])
    bins = np.linspace(0, 1.02 * np.max(b.modulo), 34)
    ax.hist(b.modulo[~b.errado], bins=bins, density=True, color=CERTO,
            alpha=0.35, label=f'bits que conferem ({int((~b.errado).sum())})')
    ax.hist(b.modulo[b.errado], bins=bins, density=True, histtype='step',
            color=ERRADO, lw=1.3, label=f'bits errados ({int(b.errado.sum())})')
    for m, c in ((b.modulo[~b.errado].mean(), CERTO),
                 (b.modulo[b.errado].mean(), ERRADO)):
        ax.axvline(m, color=c, lw=0.9, ls=':')
    ax.set_xlim(0, bins[-1])
    ax.set_xlabel('modulo da verossimilhanca (confianca do bit)')
    ax.set_ylabel('densidade')
    ax.legend(loc='upper right', frameon=False, borderpad=0.1)
    ax.text(0.40, 0.62, f"media {virgula(b.modulo[b.errado].mean(), 2)} nos "
                        f"errados, {virgula(b.modulo[~b.errado].mean(), 2)} nos "
                        f"que conferem", transform=ax.transAxes, fontsize=8.5,
            va='top')
    return fig


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stem', default=PADRAO, choices=STEMS)
    p.add_argument('--recorte', type=int, default=96,
                   help='largura, em bits codificados, da faixa ampliada')
    p.add_argument('--inicio', type=int, default=None,
                   help='primeiro bit do recorte; sem isto, escolhido por regra')
    p.add_argument('--out', action='append', default=None)
    a = p.parse_args()

    b = Bloco(a.stem)
    fig = desenha(b, a.recorte, a.inicio)
    destinos = a.out or [os.path.join(AQUI, 'fec-correcao.png'),
                         os.path.join(RAIZ, 'artigo', 'figuras', 'fec-correcao.png')]
    for d in destinos:
        os.makedirs(os.path.dirname(os.path.abspath(d)), exist_ok=True)
        fig.savefig(d)
    plt.close(fig)

    k0 = b.recorte(a.recorte, a.inicio)
    print(f"[figura] {b.stem}, {virgula(b.segundos, 2)} s gravados, "
          f"{b.meta['payload_len']} B de carga, repeticao {b.meta['fec_repeat']}")
    print(f"    {len(b.enviado)} bits codificados, "
          f"{int(b.errado.sum())} discordam ({virgula(100 * b.erro, 2)}%)")
    print(f"    modulo medio {virgula(b.modulo[b.errado].mean(), 2)} nos errados "
          f"contra {virgula(b.modulo[~b.errado].mean(), 2)} nos que conferem")
    print(f"    recorte em {k0}..{k0 + a.recorte}, "
          f"{int(b.errado[k0:k0 + a.recorte].sum())} errados")
    print(f"    bloco decodificado identico a carga: "
          f"{len(b.lido)} de {b.meta['payload_len']} bytes")
    for d in destinos:
        print(f"    {d}")


if __name__ == '__main__':
    main()
