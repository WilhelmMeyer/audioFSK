"""Figuras do artigo: a modulação de cinco pares votados, vista no ar.

Três figuras tiradas da mesma gravação e do mesmo alinhamento, por isso um
programa só:

  a  alternância dos acordes -- os dois acordes se revezando símbolo a
     símbolo, no trecho alternado que abre a transmissão
  b  espectro dos acordes -- um painel para um símbolo que levava bit 0 e
     outro para um que levava bit 1, na janela exata em que o detector
     decide, com o voto de cada par
  c  votação nos dados -- o mesmo mecanismo sobre a carga codificada, onde os
     bits não se alternam mais

    ./venv/bin/python resultados/05-MFSK-VOTE/figuras/figura_voto.py

Em (a) e (c) o espectrograma e a leitura do receptor vão na mesma figura, uma
por cima da outra: o fundo é o STFT, que é o sinal como um analisador o
mostraria, e por cima vão as fronteiras de símbolo, o bit e um marcador em
cada tom que ganhou o seu par naquele símbolo. Separar os dois em painéis
obrigaria o leitor a casar duas imagens no olho; sobrepostos, a decisão fica
em cima da evidência que a produziu.

Nada do alinhamento é estimado a olho, e nada é contado em múltiplos de 480
amostras. Os símbolos saem do próprio `MFSKDemodulator`: cada iteração de
`_symbols` deixa em `last_window` o índice absoluto da janela que produziu
aquela decisão, que é onde o receptor de fato mediu, com a porta early/late já
tendo corrigido o passo. O início do bloco sai de `fec.find_sync` sobre os
mesmos valores suaves, como em `bench.py`. A conferência é o próprio
decodificador: esta gravação devolve os 48 bytes sem erro, então as fronteiras
desenhadas são as que decodificaram.

Os bits anotados na figura (c) são os *transmitidos*: a carga do sidecar
passada por `fec.frame`, o mesmo caminho do transmissor. O recebido coincidir
é o resultado, não o rótulo.
"""

import argparse
import json
import os
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.ticker import FuncFormatter, MultipleLocator
import numpy as np


def raiz():
    d = os.path.dirname(os.path.abspath(__file__))
    while d != os.path.dirname(d):
        if os.path.exists(os.path.join(d, 'modem.py')):
            return d
        d = os.path.dirname(d)
    raise SystemExit("[voto] nao achei a raiz do repositorio")


RAIZ = raiz()
sys.path.insert(0, RAIZ)

import fec
import recording
from modem import MFSKDemodulator, MFSK_PAIRS

AQUI = os.path.dirname(os.path.abspath(__file__))
GRAVACAO = os.path.join(RAIZ, 'resultados', '05-MFSK-VOTE', 'gravacao',
                        '20260903-155727-mfsk-vote-B2A.wav')

LARGURA = 6.3
BLOCO = 2048              # o mesmo bloco em que o caminho vivo entrega áudio

# (a) o preâmbulo: os últimos símbolos antes da palavra de sincronismo, onde a
# porta já convergiu e a alternância está limpa.
PRE_SIMBOLOS = 12
# (c) a carga: 30 símbolos, 0,30 s, o suficiente para caber um dígito por
# símbolo na largura de uma coluna.
CARGA_SIMBOLOS = 30

# Espectrograma: janela de um símbolo, que é a mais longa que se pode usar sem
# atravessar fronteiras e misturar os dois acordes. 480 amostras dão 100 Hz por
# bin, e os tons estão a 200 Hz dentro do par e a 220 Hz entre pares vizinhos:
# isto é o limite do que qualquer janela resolve a 100 baud, e é por isso que a
# leitura do detector vai sobreposta em vez de o leitor ter de achar dez raias.
NJANELA = 480
SALTO = 48
NFFT = 8192               # só enche a imagem de pontos; a resolução é a janela
FAIXA = (600.0, 2750.0)   # os dez tons vão de 700 a 2580 Hz
DINAMICA = 30.0           # dB abaixo do máximo, onde a escala satura
MAPA = 'Greys'            # cinza: claro onde nao ha energia, escuro no tom

# Cores das linhas da figura (b), a mesma paleta das figuras das campanhas
# 01, 02 e 03. Nada é codificado só por cor: no espectrograma o marcador tem
# forma própria e o bit vai escrito, e em (b) o tom vencedor é o marcador
# cheio contra o vazado do perdedor.
TEAL = '#0F5257'
TEAL_MED = '#2E7D82'
GELO = '#BFDDE4'
# O quadrinho do bit acima de cada simbolo. O trecho escolhido e um em que
# todo bit saiu certo, entao nao ha estado de erro para codificar: o numero e
# o bit, e ele e ao mesmo tempo o que foi transmitido e o que o receptor leu.
CAIXA = '#ECEDEE'      # cinza claro para a caixa do bit, fora do quadro
TRACO = '0.30'         # cinza escuro em vez de preto puro
# Com o espectro em cinza, a cor fica reservada ao que o receptor fez, e nao
# ao sinal. Duas para os marcadores -- o par que votou o bit transmitido e o
# que votou contra -- e duas faixas de fundo, muito claras, dizendo qual bit
# estava sendo transmitido em cada instante.
ACERTO = '#1B7F79'     # verde-azulado
ERRO = '#C43D2F'       # vermelho tijolo
CONTORNO = 'white'     # separa o marcador tanto do preto quanto do branco
FAIXA_0 = '#3C6FB0'   # azul
FAIXA_1 = '#2E8B74'   # verde: amarelo sobre cinza vira marrom e briga com o mapa
TINTA = 0.09           # a faixa tinge, nao pinta
MARCA_ALPHA = 0.85

# Prefixo com o nome da camada no artigo, 5x2-FSK votada, para as tres
# ficarem juntas na pasta e ao lado das da 16-FSK, que seguem a mesma regra.
SAIDAS = {
    'a': '5x2fsk-alternancia.png',
    'b': '5x2fsk-espectro-dos-acordes.png',
    'c': '5x2fsk-votacao-nos-dados.png',
}

plt.rcParams.update({
    'font.size': 9,
    'axes.labelsize': 9.5,
    'xtick.labelsize': 8.5,
    'ytick.labelsize': 8.5,
    'legend.fontsize': 8,
    'axes.linewidth': 0.8,
    'savefig.dpi': 300,
    'figure.dpi': 300,
})

TONS_0 = np.array(MFSK_PAIRS, dtype=float)[:, 0]
TONS_1 = np.array(MFSK_PAIRS, dtype=float)[:, 1]
# As dez frequências em ordem de banda e o bit que cada uma significa. Nada
# digitado: a polaridade alterna ao longo da banda e sai de MFSK_PAIRS.
ORDEM = np.argsort(np.concatenate([TONS_0, TONS_1]))
TONS = np.concatenate([TONS_0, TONS_1])[ORDEM]
BITS = np.concatenate([np.zeros(len(TONS_0), int),
                       np.ones(len(TONS_1), int)])[ORDEM]


def virgula(v, casas=1):
    return f"{v:.{casas}f}".replace('.', ',')


class Leitura:
    """A gravação, os símbolos que o demodulador decidiu e onde ele mediu."""

    def __init__(self, wav):
        self.meta = json.load(open(os.path.splitext(wav)[0] + '.json'))
        self.samples = recording.read(wav)
        self.fs = self.meta['fs']
        self.demod = MFSKDemodulator(fs=self.fs, baud=self.meta['baud'])
        janela, bit, contraste, llr = [], [], [], []
        for i in range(0, len(self.samples), BLOCO):
            for b, c, l in self.demod._symbols(self.samples[i:i + BLOCO]):
                janela.append(self.demod.last_window)
                bit.append(b)
                contraste.append(c)
                llr.append(l)
        self.janela = np.array(janela, dtype=int)
        self.bit = np.array(bit, dtype=int)
        self.contraste = np.array(contraste)
        self.llr = np.array(llr)

        self.payload = bytes.fromhex(self.meta['payload_hex'])
        self.repeat = self.meta.get('fec_repeat', 1)
        # Onde o bloco começa, pelo mesmo mecanismo do receptor: correlação da
        # palavra de 31 bits sobre os valores suaves, nunca contagem de
        # símbolos.
        self.inicio = fec.find_sync(self.llr)
        if self.inicio is None:
            raise SystemExit("[voto] find_sync nao achou o bloco")
        self.sync = self.inicio - len(fec.SYNC)
        self.recebido = fec.decode(self.llr[self.inicio:], len(self.payload),
                                   repeat=self.repeat)
        # Os bits que foram ao ar, do payload pelo caminho do transmissor.
        self.quadro = np.asarray(fec.frame(self.payload, repeat=self.repeat),
                                 dtype=int)
        self.corpo = self.quadro[len(fec.SYNC):]
        n = min(len(self.corpo), len(self.llr) - self.inicio)
        self.n_corpo = n
        self.decidido = (self.llr[self.inicio:self.inicio + n] > 0).astype(int)
        self.erro = self.decidido != self.corpo[:n]

    @property
    def guard(self):
        return self.demod.guard

    @property
    def passo(self):
        return self.demod.samples_per_symbol

    def transmitido(self, k):
        """O bit que foi transmitido no símbolo k, ou None fora do quadro."""
        i = k - self.sync
        return int(self.quadro[i]) if 0 <= i < len(self.quadro) else None

    def energias(self, k):
        """As energias `e0`/`e1` do símbolo k, na janela do detector."""
        seg = self.samples[self.janela[k] + self.guard:self.janela[k] + self.passo]
        return (np.abs(self.demod.probe_0 @ seg) ** 2,
                np.abs(self.demod.probe_1 @ seg) ** 2)

    def vencedores(self, k):
        """As cinco frequências que ganharam o seu par no símbolo k."""
        e0, e1 = self.energias(k)
        return np.where(e1 > e0, TONS_1, TONS_0), (e1 > e0).astype(int)


def espectrograma(ax, L, k0, k1):
    """STFT com janela de um símbolo: o sinal como um analisador o mostraria."""
    i0 = L.janela[k0]
    i1 = L.janela[k1 - 1] + L.passo
    jan = np.hanning(NJANELA)
    cen = np.arange(max(0, i0 - NJANELA // 2),
                    min(len(L.samples), i1 + NJANELA // 2) - NJANELA, SALTO)
    S = np.array([np.abs(np.fft.rfft(L.samples[c:c + NJANELA] * jan, NFFT))
                  for c in cen]).T
    f = np.fft.rfftfreq(NFFT, 1 / L.fs)
    db = 20 * np.log10(np.maximum(S, 1e-12))
    db -= db.max()
    faixa = (f >= FAIXA[0]) & (f <= FAIXA[1])
    ms = (cen + NJANELA / 2 - i0) * 1000.0 / L.fs
    im = ax.pcolormesh(ms, f[faixa], db[faixa], cmap=MAPA, vmin=-DINAMICA,
                       vmax=0.0, shading='nearest', rasterized=True)
    ax.set_ylim(*FAIXA)
    ax.set_xlim(ms.min(), ms.max())
    return im


def sobrepoe(ax, L, k0, k1, rotulo, marcar=None):
    """A leitura do receptor por cima do espectrograma.

    Três coisas, e nenhuma delas depende de cor: a fronteira de cada símbolo,
    onde a porta early/late a colocou; o bit daquele símbolo, escrito acima do
    quadro; e um marcador em cada um dos cinco tons que ganhou o seu par --
    que é a votação, desenhada onde ela acontece.
    """
    i0 = L.janela[k0]
    ms = lambda i: (i - i0) * 1000.0 / L.fs
    # A grade separa, nao decora: fina, clara e translucida, para ler por cima
    # do mapa sem competir com ele.
    #
    # Dois lados por simbolo, comeco e fim da janela de decisao, e nao uma
    # linha so no comeco. Uma linha so daria simbolos de larguras diferentes e
    # sugeriria que o simbolo dura mais ou menos, o que nao acontece: o passo
    # do relogio varia 15 amostras, 3%. O que salta e *qual sonda venceu* --
    # cedo, em cima ou tarde, a 60 amostras uma da outra -- e isso desloca a
    # janela em ate um quarto de simbolo sem mudar a duracao dele. Com os dois
    # lados desenhados a largura fica constante e o que se ve entre uma janela
    # e a seguinte, folga ou sobreposicao, e a correcao da porta.
    # Sem faixa tingida sobre o espectrograma: qualquer cor por cima do cinza
    # se soma a ele e vira outra cor, e o que a figura mostra e o nivel. O bit
    # do simbolo fica na caixa acima do quadro, fora dos dados, e la a cor nao
    # se mistura com nada.
    passo_ms = L.passo * 1000.0 / L.fs

    # Grade de espacamento constante, um traco por simbolo no periodo nominal
    # de 480 amostras. As janelas de decisao caem alguns milissegundos para um
    # lado ou para o outro, porque a porta early/late escolhe entre tres
    # sondas, mas isso e informacao do receptor e nao a regua do tempo: uma
    # grade de passo irregular so faz o leitor duvidar do eixo.
    for j in range(k1 - k0 + 1):
        ax.axvline(j * passo_ms, color='0.30', linewidth=0.5,
                   linestyle=(0, (1, 2)), zorder=5)
    # E as horizontais vao *entre* os tons, no meio do caminho de um para o
    # seguinte, delimitando a faixa de cada um. Em cima do valor do tom elas
    # cortariam justamente o que a figura quer que se leia.
    for a, b in zip(TONS[:-1], TONS[1:]):
        ax.axhline((a + b) / 2, color='0.30', linewidth=0.5,
                   linestyle=(0, (1, 2)), zorder=5)
    for k in range(k0, k1):
        centro = ms(L.janela[k] + (L.guard + L.passo) / 2)
        vence, _ = L.vencedores(k)
        # O tom vencedor de cada par, com a forma dizendo o que ele significa:
        # circulo cheio para o tom que quer dizer 0, losango para o que quer
        # dizer 1. Assim da para ler o simbolo pelos marcadores, sem subir ate
        # o numero em cima nem depender de cor.
        # A forma diz o que o tom significa, a cor diz se aquele par votou o
        # bit que foi transmitido. Contorno branco para o marcador nao sumir
        # nem no fundo preto nem no branco.
        vale = np.array([0 if t in set(TONS_0) else 1 for t in vence])
        bit = rotulo(k)
        for forma, qual in (('o', 0), ('D', 1)):
            for cor, certo in ((ACERTO, True), (ERRO, False)):
                alvo = vence[(vale == qual) & ((vale == bit) == certo)]
                if len(alvo):
                    ax.plot([centro] * len(alvo), alvo, forma, markersize=5.4,
                            markerfacecolor=cor, markeredgecolor=CONTORNO,
                            markeredgewidth=0.8, alpha=MARCA_ALPHA,
                            linestyle='none', zorder=6)
        # O bit vai no centro da celula da grade, e nao sobre a janela
        # medida: a fileira de cima e a leitura do simbolo, e uma fileira de
        # espacamento irregular so parece desalinhada. Os marcadores, esses,
        # ficam onde o receptor mediu.
        fonte = 8.5 if k1 - k0 <= 12 else 6.0
        ax.annotate(str(rotulo(k)), xy=((k - k0 + 0.5) * passo_ms, FAIXA[1]),
                    xytext=(0, 6), textcoords='offset points',
                    ha='center', va='bottom', fontsize=fonte, color=TRACO,
                    zorder=8,
                    bbox=dict(boxstyle='square,pad=0.22' if k1 - k0 <= 12
                              else 'square,pad=0.15',
                              facecolor=FAIXA_1 if rotulo(k) else FAIXA_0,
                              alpha=0.22, edgecolor='0.65',
                              linewidth=0.4))
    ax.set_yticks(TONS)
    ax.set_yticklabels([virgula(t, 0) for t in TONS], fontsize=7.5)
    ax.set_ylabel('Frequência dos dez tons (Hz)')
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: virgula(v, 0)))
    gemeo = ax.twinx()
    gemeo.set_ylim(*FAIXA)
    gemeo.set_yticks(TONS)
    gemeo.set_yticklabels([str(b) for b in BITS], fontsize=7.5)
    gemeo.tick_params(length=2)
    gemeo.set_ylabel('Bit que o tom significa', fontsize=8.5)


def legenda_sobreposta(ax):
    """Duas entradas, e nada mais.

    A grade e a caixa do bit se explicam pelos eixos e nao precisam de linha
    na legenda. E o marcador nao fala em vencedor: ele aponta o tom que o
    detector leu naquele simbolo, um por par.
    """
    def amostra(forma, cor, texto):
        return Line2D([], [], color=CONTORNO, linestyle='none', marker=forma,
                      markersize=5.4, markerfacecolor=cor, markeredgewidth=0.8,
                      label=texto)

    ax.legend(handles=[
        amostra('o', ACERTO, 'Tom detectado, significa 0'),
        amostra('D', ACERTO, 'Tom detectado, significa 1'),
        amostra('o', ERRO, 'Par que votou contra o bit transmitido'),
    ], loc='upper center', bbox_to_anchor=(0.5, -0.14), ncol=2,
        frameon=False, handletextpad=0.5, columnspacing=2.0, fontsize=8)


def barra(fig, ax, im):
    b = fig.colorbar(im, ax=ax, pad=0.09, fraction=0.05)
    b.set_label('Nível relativo ao máximo do trecho (dB)', fontsize=8)
    b.ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: virgula(v, 0)))


def figura_a(L, args):
    """O preâmbulo alternado: os dois acordes se revezando símbolo a símbolo."""
    k1 = L.sync                       # o preâmbulo termina onde o sync começa
    k0 = k1 - PRE_SIMBOLOS

    # O bit ideal do preâmbulo não é o que o receptor leu: é o que o
    # transmissor mandou, `fec.preamble_bits`, alinhado pela palavra de
    # sincronismo que o vem logo depois. Assim o indicador de (a) compara as
    # mesmas duas coisas que o de (c) -- ideal contra medido.
    pre = fec.preamble_bits(L.meta['mode'], npairs=len(MFSK_PAIRS))
    base = L.sync - len(pre)

    def rotulo(k):
        i = k - base
        return int(pre[i]) if 0 <= i < len(pre) else int(L.bit[k])

    fig, ax = plt.subplots(figsize=(LARGURA, 3.9), layout='constrained')
    im = espectrograma(ax, L, k0, k1)
    sobrepoe(ax, L, k0, k1, rotulo)
    ax.set_xlabel('Tempo dentro do preâmbulo (ms)')
    ax.xaxis.set_major_locator(MultipleLocator(20))
    legenda_sobreposta(ax)
    erra = [k for k in range(k0, k1)
            if 0 <= k - base < len(pre) and int(pre[k - base]) != int(L.bit[k])]
    print(f"        {PRE_SIMBOLOS - len(erra)} dos {PRE_SIMBOLOS} símbolos "
          f"lidos como transmitidos" + (f"; erra em {erra}" if erra else ""))
    barra(fig, ax, im)
    salvar(fig, args, 'a')

    print(f"    (a) {PRE_SIMBOLOS} símbolos do preâmbulo, símbolos {k0} a "
          f"{k1 - 1}, terminando na palavra de sincronismo")
    print(f"        bits decididos: {''.join(str(b) for b in L.bit[k0:k1])}")
    print(f"        espectrograma: Hann de {NJANELA} amostras "
          f"({virgula(1000 * NJANELA / L.fs)} ms, {virgula(L.fs / NJANELA, 0)} Hz "
          f"por bin), salto {SALTO}; marcadores e fronteiras vêm do detector, "
          f"cuja janela é de {L.passo - L.guard} amostras depois de {L.guard} "
          f"de guarda")
    acordo = [k for k in range(k0, k1)
              if list(L.vencedores(k)[1]).count(L.bit[k]) >= 3]
    print(f"        em {len(acordo)} dos {PRE_SIMBOLOS} símbolos a maioria dos "
          f"cinco pares aponta o bit decidido")


def figura_b(L, args):
    """A FFT da janela de decisão de um símbolo, um painel para cada bit.

    Dois painéis e não duas curvas no mesmo eixo: são instantes diferentes, e
    a comparação que o receptor faz é dentro de um instante, entre os dois
    tons de um par.

    Os dez marcadores não são leitura da curva: são as energias `e0`/`e1` que
    o detector compara, medidas com `probe_0`/`probe_1` na mesma janela
    retangular de 408 amostras de que a FFT foi tirada. A forma diz o que o
    tom significa e a cor diz se o par concordou com o bit transmitido.
    """
    k1 = L.sync - 2
    k0 = k1 - 1
    if L.bit[k0] != 0 or L.bit[k1] != 1:
        k0, k1 = k1, k0
    nwin = L.passo - L.guard

    def espectro(k):
        seg = L.samples[L.janela[k] + L.guard:L.janela[k] + L.passo]
        X = np.abs(np.fft.rfft(seg, NFFT)) * 2 / nwin
        return np.fft.rfftfreq(NFFT, 1 / L.fs), 20 * np.log10(np.maximum(X, 1e-12))

    def db(e):
        return 20 * np.log10(np.maximum(np.sqrt(np.asarray(e)) * 2 / nwin, 1e-12))

    f, S0 = espectro(k0)
    _, S1 = espectro(k1)
    faixa = (f >= FAIXA[0]) & (f <= FAIXA[1])
    alto = max(S0[faixa].max(), S1[faixa].max()) + 8
    baixo = min(S0[faixa].min(), S1[faixa].min()) - 3

    fig, eixos = plt.subplots(2, 1, figsize=(LARGURA, 5.6),
                              layout='constrained', sharex=True, sharey=True)
    resumo = []
    for ax, k, S, bit in ((eixos[0], k0, S0, 0), (eixos[1], k1, S1, 1)):
        e0, e1 = L.energias(k)
        vence = (e1 > e0).astype(int)
        resumo.append((k, bit, db(e0), db(e1), vence))
        # Barra fina em cada tom, atras da curva, com a altura que o detector
        # mediu ali. A curva diz o que chegou em toda a banda; a barra diz os
        # dez numeros que a decisao usa, e so eles.
        for i in range(len(MFSK_PAIRS)):
            for tons, e, significa in ((TONS_0, e0[i], 0), (TONS_1, e1[i], 1)):
                venceu = int(vence[i]) == significa
                ax.bar(tons[i], db(e) - baixo, 26.0, bottom=baixo,
                       color=((ACERTO if significa == bit else ERRO) if venceu
                              else '0.80'),
                       edgecolor='none', alpha=0.75, zorder=2)
        ax.plot(f[faixa], S[faixa], color='0.35', linewidth=0.9, zorder=3)
        for i in range(len(MFSK_PAIRS)):
            significa = int(vence[i])
            tom = (TONS_1 if significa else TONS_0)[i]
            nivel = db(e1[i] if significa else e0[i])
            ax.plot([tom], [nivel], 'D' if significa else 'o', markersize=6.5,
                    markerfacecolor=ACERTO if significa == bit else ERRO,
                    markeredgecolor=CONTORNO, markeredgewidth=0.8, zorder=6)

        maioria = 1 if vence.sum() * 2 > len(vence) else 0
        ax.annotate(f"Bit {bit} transmitido.  Os cinco pares votaram "
                    f"{''.join(str(int(v)) for v in vence)}, maioria {maioria}.",
                    xy=(0.5, 0.97), xycoords='axes fraction', ha='center',
                    va='top', fontsize=8.5, color=TRACO)
        ax.set_ylim(baixo, alto)
        ax.set_xlim(*FAIXA)
        ax.set_ylabel('Nível na janela\nde decisão (dBFS)')
        ax.yaxis.set_major_locator(MultipleLocator(10))
        ax.grid(True, axis='y', color='0.93', linewidth=0.5)
        ax.set_axisbelow(True)
        for eixo in (ax.xaxis, ax.yaxis):
            eixo.set_major_formatter(FuncFormatter(lambda v, _: virgula(v, 0)))
    eixos[1].set_xticks(TONS)
    eixos[1].set_xticklabels([virgula(t, 0) for t in TONS], fontsize=7.5,
                             rotation=90)
    eixos[1].set_xlabel('Frequência dos dez tons (Hz)')
    eixos[0].legend(handles=[
        Line2D([], [], color=CONTORNO, linestyle='none', marker='o',
               markersize=6.5, markerfacecolor=ACERTO, markeredgewidth=0.8,
               label='Tom detectado, significa 0'),
        Line2D([], [], color=CONTORNO, linestyle='none', marker='D',
               markersize=6.5, markerfacecolor=ACERTO, markeredgewidth=0.8,
               label='Tom detectado, significa 1'),
        Line2D([], [], color=CONTORNO, linestyle='none', marker='o',
               markersize=6.5, markerfacecolor=ERRO, markeredgewidth=0.8,
               label='Par que votou contra o bit transmitido'),
        Patch(facecolor='0.80', edgecolor='none',
              label='Barra: energia medida em cada um dos dez tons'),
    ], loc='upper center', bbox_to_anchor=(0.5, -0.02), ncol=2, frameon=False,
        fontsize=7.5, handletextpad=0.4)
    salvar(fig, args, 'b')

    print(f"    (b) FFT da janela de decisão: símbolo {k0} (bit 0) em cima, "
          f"símbolo {k1} (bit 1) embaixo; janela de {nwin} amostras "
          f"({virgula(1000 * nwin / L.fs)} ms, {virgula(L.fs / nwin)} Hz por "
          f"bin), retangular, guarda de {L.guard} de {L.passo} descartada")
    for k, bit, d0, d1, vence in resumo:
        maioria = 1 if vence.sum() * 2 > len(vence) else 0
        print(f"        símbolo {k}, bit {bit}: votos "
              f"{list(map(int, vence))} -> maioria {maioria}")
        for i, (t0, t1) in enumerate(MFSK_PAIRS):
            print(f"          par {i}  {virgula(t0, 0):>5} Hz (0) "
                  f"{virgula(d0[i]):>7} dBFS   {virgula(t1, 0):>5} Hz (1) "
                  f"{virgula(d1[i]):>7} dBFS   diferença "
                  f"{virgula(abs(d0[i] - d1[i])):>5} dB")


def melhor_trecho(L, n):
    """Um trecho de n símbolos em que todo bit saiu certo.

    A figura mostra onde o mecanismo funciona, então o trecho não pode ter bit
    errado: 36 das 77 janelas de 30 símbolos do bloco não erram nenhum. Entre
    essas, escolhe-se a que mais tem símbolos com par discordante -- um par
    votando contra os outros quatro e o bit final ainda saindo certo, que é a
    votação trabalhando à vista.

    Isto não contradiz o bloco ter saído inteiro: inteiro é depois da
    correção, e antes dela 12% dos símbolos do bloco são decididos errado. A
    distribuição desses erros é bimodal -- a maior parte das janelas não erra
    nada e uma cauda erra um quarto dos bits -- e é por isso que existe janela
    limpa deste tamanho para escolher.
    """
    melhor, quantos = None, -1
    for k0 in range(L.inicio, L.inicio + L.n_corpo - n):
        if L.erro[k0 - L.inicio:k0 - L.inicio + n].any():
            continue
        divide = sum(1 for k in range(k0, k0 + n)
                     if 0 < int(L.vencedores(k)[1].sum()) < len(MFSK_PAIRS))
        if divide > quantos:
            melhor, quantos = k0, divide
    if melhor is None:
        raise SystemExit("[voto] nenhum trecho sem erro deste tamanho")
    return melhor, quantos


def figura_c(L, args):
    """A carga codificada: fronteiras de símbolo e bits transmitidos.

    A mesma figura de (a), agora sobre dados de verdade, onde os bits não se
    alternam. O que muda é só a sequência; o mecanismo é o mesmo.
    """
    k0, divididos = melhor_trecho(L, CARGA_SIMBOLOS)
    k1 = k0 + CARGA_SIMBOLOS

    fig, ax = plt.subplots(figsize=(LARGURA, 4.0), layout='constrained')
    im = espectrograma(ax, L, k0, k1)
    erradas = []

    def rotulo(k):
        # Transmitido e lido são o mesmo número em todo o trecho, que é a
        # condição para ele ter sido escolhido. Um número só, portanto.
        medido = int(L.decidido[k - L.inicio])
        ideal = L.transmitido(k)
        if ideal != medido:
            erradas.append(k)
        return ideal

    sobrepoe(ax, L, k0, k1, rotulo)
    ax.set_xlabel('Tempo dentro do trecho (ms)')
    ax.xaxis.set_major_locator(MultipleLocator(50))
    legenda_sobreposta(ax)
    barra(fig, ax, im)
    salvar(fig, args, 'c')

    t_bloco = (L.janela[k0] - L.janela[L.inicio]) / L.fs
    print(f"    (c) {CARGA_SIMBOLOS} símbolos da carga, símbolos {k0} a "
          f"{k1 - 1}, {virgula(CARGA_SIMBOLOS / L.meta['baud'], 2)} s de ar")
    print(f"        começa {virgula(t_bloco, 2)} s depois do primeiro bit "
          f"codificado do bloco (o bloco todo dura "
          f"{virgula(L.n_corpo / L.meta['baud'], 2)} s)")
    print(f"        bits transmitidos: "
          f"{''.join(str(L.transmitido(k)) for k in range(k0, k1))}")
    print(f"        bits decididos:    "
          f"{''.join(str(int(L.decidido[k - L.inicio])) for k in range(k0, k1))}")
    print(f"        todo bit do trecho saiu certo: {len(erradas)} de "
          f"{CARGA_SIMBOLOS} símbolos discordam")
    print(f"        e em {divididos} dos {CARGA_SIMBOLOS} símbolos ao menos um "
          f"par votou contra os outros, com o bit final ainda saindo certo")
    passos = np.diff(L.janela[k0:k1])
    print(f"        distância entre janelas vizinhas no trecho: "
          f"{int(passos.min())} a {int(passos.max())} amostras, contra "
          f"{L.passo} de largura de janela -- daí a folga e a sobreposição "
          f"entre elas na figura")
    print(f"        e isso é quase todo escolha de sonda, não relógio: a porta "
          f"corrige o passo em {L.demod.step} amostras por símbolo "
          f"({virgula(100 * L.demod.step / L.passo)}%), enquanto as três "
          f"sondas ficam a {L.demod.delta} amostras uma da outra, o que "
          f"desloca a janela em até {2 * L.demod.delta}")


def salvar(fig, args, qual):
    # Dois destinos e uma geração só: `artigo/figuras/` carrega apenas
    # figuras, e o que as gera mora junto da campanha que elas medem.
    destinos = args.out or [os.path.join(AQUI, SAIDAS[qual]),
                            os.path.join(RAIZ, 'artigo', 'figuras', SAIDAS[qual])]
    for destino in destinos:
        os.makedirs(os.path.dirname(os.path.abspath(destino)), exist_ok=True)
        fig.savefig(destino)
    plt.close(fig)
    print("[voto] " + ", ".join(destinos))


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--wav', default=GRAVACAO)
    ap.add_argument('--figura', choices=('a', 'b', 'c'), action='append',
                    help="qual figura gerar; repetível. Sem ela, as três")
    ap.add_argument('--out', action='append', metavar='PNG',
                    help="onde gravar; só com uma figura por vez")
    args = ap.parse_args()
    quais = args.figura or ['a', 'b', 'c']
    if args.out and len(quais) != 1:
        raise SystemExit("[voto] --out exige uma figura só")

    L = Leitura(args.wav)
    inteiro = L.recebido == L.payload
    falhos = sum(a != b for a, b in
                 zip(L.recebido.ljust(len(L.payload), b'\0'), L.payload))
    print(f"[voto] {os.path.basename(args.wav)}: {len(L.samples)} amostras a "
          f"{L.meta['fs']} Hz, {len(L.janela)} símbolos a {L.meta['baud']} baud")
    print(f"    bloco: {len(L.payload)} bytes, repetição {L.repeat}, "
          f"{falhos} bytes falhos, bloco {'INTEIRO' if inteiro else 'FALHOU'}")
    print(f"    palavra de sincronismo no símbolo {L.sync} "
          f"(amostra {L.janela[L.sync]}, {virgula(L.janela[L.sync] / L.fs, 3)} s "
          f"da gravação); corpo codificado a partir do símbolo {L.inicio}")
    print(f"    bits do corpo: {L.n_corpo} comparados contra o transmitido, "
          f"{virgula(100 * float(np.mean(~L.erro)))}% certos antes da correção")
    votos = np.array([L.vencedores(k)[1]
                      for k in range(L.inicio, L.inicio + L.n_corpo)])
    print("    acerto de voto por par, no corpo:")
    for i, (t0, t1) in enumerate(MFSK_PAIRS):
        print(f"      par {i}  {virgula(t0, 0):>5} Hz (bit 0) / "
              f"{virgula(t1, 0):>5} Hz (bit 1): "
              f"{virgula(100 * float(np.mean(votos[:, i] == L.corpo[:L.n_corpo])))}%")
    jan = np.array([int(L.erro[i:i + CARGA_SIMBOLOS].sum())
                    for i in range(0, L.n_corpo - CARGA_SIMBOLOS, CARGA_SIMBOLOS)])
    print(f"    erros em janelas de {CARGA_SIMBOLOS} símbolos: "
          f"{int((jan == 0).sum())} janelas sem erro nenhum, "
          f"{int((jan >= CARGA_SIMBOLOS // 4).sum())} com um quarto ou mais, "
          f"de {len(jan)} -- a distribuição é bimodal e não há trecho típico")

    for qual in quais:
        {'a': figura_a, 'b': figura_b, 'c': figura_c}[qual](L, args)


if __name__ == '__main__':
    main()
