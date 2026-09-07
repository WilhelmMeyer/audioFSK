"""Alinhamento e ajustes comuns as tres figuras da campanha 07-MARY-BASE.

As tres figuras (`figura_tons.py`, `figura_decisao.py`,
`figura_enquadramento.py`) precisam da mesma coisa dificil: saber, em amostras
absolutas, onde cada simbolo da 16-FSK foi medido, e quais quatro bits o
transmissor pos em cada um. Nada disso e estimado a olho nem recalculado aqui.
As fronteiras vem do proprio `MaryDemodulator`, que registra em `last_window`
a amostra em que mediu cada decisao; os bits vem de `fec.frame`, o mesmo
caminho de codificacao que o transmissor usou.

O portao esta em `alinha`: o bloco tem de decodificar de volta ao
`payload_hex` da gravacao. Se nao decodificar, o alinhamento esta errado e o
programa para, porque uma figura de fronteiras desenhada sobre um bloco que
nao decodifica nao mostra o enquadramento, mostra uma suposicao.
"""

import json
import os
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


def raiz():
    """A raiz do repositorio, achada subindo ate encontrar `modem.py`.

    Nao e `dirname(dirname(...))`: isso fixaria a profundidade em que este
    arquivo mora, e quem o mover uma pasta para o lado o quebra sem aviso.
    """
    d = os.path.dirname(os.path.abspath(__file__))
    while d != os.path.dirname(d):
        if os.path.exists(os.path.join(d, 'modem.py')):
            return d
        d = os.path.dirname(d)
    raise SystemExit("[figura] nao achei a raiz do repositorio")


RAIZ = raiz()
sys.path.insert(0, RAIZ)

import fec                                                    # noqa: E402
import recording                                              # noqa: E402
from modem import MARY_BITS, MARY_TONES, MaryDemodulator, _GRAY   # noqa: E402

AQUI = os.path.dirname(os.path.abspath(__file__))
GRAVACAO = os.path.join(os.path.dirname(AQUI), 'gravacao')

# As tres gravacoes da bateria valida desta campanha, as unicas que entram em
# figura. As outras seis sao de outra condicao; uma delas entrar aqui por
# descuido produziria uma figura correta em forma e falsa em conteudo, e a
# figura nao teria como avisar. Por isso a lista e fechada e o carregador
# recusa qualquer outro nome.
STEMS = ('20260903-162209-mary-base-limpo-B2A',
         '20260903-162220-mary-base-limpo-B2A',
         '20260903-162230-mary-base-limpo-B2A')
PADRAO = STEMS[1]

# O mesmo tamanho de bloco com que `bench.py` pontuou esta campanha. Nao e
# cosmetico: o demodulador e estateful e a porta early/late anda de acordo com
# o que ja consumiu, entao alimentar tudo de uma vez daria outro alinhamento
# que o que produziu os 3 blocos de 3 do HEADER.
BLOCO = 2048

# Paleta, decidida pelo usuario para as figuras de camada fisica do artigo.
#
# A regra que a organiza: o sinal e sempre cinza, e a cor fica reservada ao
# que o receptor fez com ele. Por isso nao ha tinta colorida sobre a area de
# dados de um espectrograma -- cor sobre cinza se soma e vira uma terceira
# cor, que nao quer dizer nada. O que rotula simbolo vai em caixa propria,
# fora dos dados.
#
# Nos marcadores a forma diz o significado e a cor diz o resultado: CERTO
# quando saiu o tom que foi transmitido, ERRADO quando nao. Contorno branco
# em volta, para o marcador sobreviver tanto a fundo claro quanto a escuro.
# Nada de branco puro nem preto puro.
CERTO = '#1B7F79'
ERRADO = '#C43D2F'
CONTORNO = '#F7F7F7'
CURVA = '0.45'          # o sinal, em cinza
NEGATIVO = '#9AA7AD'    # o que ficou abaixo do proprio piso
GRADE = '0.30'          # grade de passo nominal, fina e pontilhada

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


def saidas(nome, extras=None):
    """Os dois destinos de um PNG: esta pasta e `artigo/figuras/`.

    Uma execucao grava nos dois, entao nao ha copia a sincronizar a mao: a
    pasta do artigo carrega apenas figuras, e o que as gera mora junto da
    campanha que elas medem.
    """
    if extras:
        return list(extras)
    return [os.path.join(AQUI, nome), os.path.join(RAIZ, 'artigo', 'figuras', nome)]


def grava(fig, nome, extras=None):
    destinos = saidas(nome, extras)
    for d in destinos:
        os.makedirs(os.path.dirname(os.path.abspath(d)), exist_ok=True)
        fig.savefig(d)
    plt.close(fig)
    return destinos


class _Rastreada(MaryDemodulator):
    """O demodulador do projeto, anotando o que ele ja calcula e descarta.

    Nada aqui muda uma decisao: as listas so guardam o que passou. As tres
    grandezas que uma figura precisa e o demodulador nao devolve sao a amostra
    absoluta de cada janela (`last_window`), as energias medidas nela e o piso
    corrente pelo qual elas foram divididas.

    O piso e capturado na entrada de `_update_floor`, nao no `yield`: em
    `_symbols` a ordem e medir, decidir, atualizar o piso, entregar. Ler o
    piso depois daria o divisor da proxima decisao, e a margem anotada na
    figura discordaria em silencio da que o detector usou.

    As listas nascem em `reset`, nao em `__init__`, porque `MaryDemodulator`
    chama `reset` no fim do proprio `__init__`.
    """

    def reset(self):
        super().reset()
        self.janelas = []
        self.normas = []
        self.energias = []
        self.pisos = []

    def _symbols(self, samples):
        for item in super()._symbols(samples):
            self.janelas.append(self.last_window)
            self.normas.append(item[2].copy())
            yield item

    def _update_floor(self, e):
        self.pisos.append(self.floor.copy())
        self.energias.append(np.asarray(e).copy())
        return super()._update_floor(e)


class Alinhado:
    """Uma gravacao lida, demodulada e casada com o que foi transmitido."""

    def __init__(self, stem, meta, amostras, demod, llr, inicio):
        self.stem = stem
        self.meta = meta
        self.amostras = amostras
        self.demod = demod
        self.llr = llr
        self.fs = meta['fs']
        # Bit 0 do quadro (o primeiro da palavra de sincronismo) no fluxo de
        # llr. `find_sync` devolve o primeiro bit *codificado*, 31 adiante.
        self.bit0 = inicio - len(fec.SYNC)
        self.simbolo0 = self.bit0 // MARY_BITS

    def tempo(self, k):
        """Instante, em segundos, da fronteira do simbolo `k` do quadro."""
        return self.demod.janelas[self.simbolo0 + k] / self.fs

    def janela(self, k):
        """Amostra inicial e final da janela em que o simbolo `k` foi medido.

        E a janela de decisao, ja sem o intervalo de guarda: o demodulador
        mede de `guard` ate `samples_per_tone` dentro do simbolo.
        """
        a = self.demod.janelas[self.simbolo0 + k]
        return a + self.demod.guard, a + self.demod.samples_per_tone

    def energia(self, k):
        return self.demod.energias[self.simbolo0 + k]

    def piso(self, k):
        return self.demod.pisos[self.simbolo0 + k]

    def norma(self, k):
        return self.demod.normas[self.simbolo0 + k]

    def recebido(self, k):
        return int(np.argmax(self.norma(k)))

    def cor(self, k):
        """Cor do marcador deste simbolo: o resultado, nunca o significado."""
        return CERTO if self.recebido(k) == self.tom[k] else ERRADO

    def bordas_nominais(self, k0, k1):
        """Grade de passo constante, no periodo nominal do simbolo.

        Ancorada na fronteira medida do primeiro simbolo do trecho e dai em
        diante somando o periodo nominal. E uma regua, nao uma medida: onde
        ela se afasta das fronteiras que o receptor de fato usou esta o que a
        porta early/late corrigiu.
        """
        passo = self.demod.samples_per_symbol / self.fs
        return self.tempo(k0) + passo * np.arange(k1 - k0 + 1)


    def acertos(self):
        """Fracao dos simbolos do quadro em que o tom decidido e o enviado."""
        return float(np.mean([self.recebido(k) == self.tom[k]
                              for k in range(self.simbolos)]))

    def bits_certos(self):
        duro = (np.asarray(self.llr[self.bit0:self.bit0 + len(self.quadro)]) > 0)
        return float(np.mean(duro.astype(np.int8) == self.quadro))


def faixas_dos_tons():
    """Meio caminho entre um tom e o seguinte, que delimita a faixa de cada um.

    As horizontais da grade vao aqui e nao sobre o valor do tom: uma linha em
    cima do tom tapa exatamente o que a figura mostra, e uma entre dois tons
    diz de quem e cada raia.
    """
    t = np.asarray(MARY_TONES, dtype=np.float64)
    meios = (t[:-1] + t[1:]) / 2
    passo = float(np.median(np.diff(t)))
    return np.concatenate([[t[0] - passo / 2], meios, [t[-1] + passo / 2]])


def alinha(stem=PADRAO):
    """Le a gravacao, demodula pelo caminho do projeto e casa com o enviado.

    Devolve um `Alinhado` com, por simbolo do quadro, a amostra em que ele foi
    medido, as energias dos dezesseis tons, o piso corrente e o tom que o
    transmissor pos ali. Para com `SystemExit` se qualquer elo dessa corrente
    nao fechar.
    """
    if stem not in STEMS:
        raise SystemExit(f"[figura] {stem} nao e uma das tres gravacoes da "
                         f"bateria valida desta campanha: {', '.join(STEMS)}")
    base = os.path.join(GRAVACAO, stem)
    meta = json.loads(open(base + '.json').read())
    if meta.get('mode') != 'mary' or meta.get('kind') != 'fec':
        raise SystemExit(f"[figura] {stem} nao e uma gravacao 16-FSK com FEC")
    amostras = recording.read(recording.audio_path(base))

    d = _Rastreada(fs=meta['fs'], baud=meta['baud'],
                   gap=meta.get('gap', 0.0), band=meta.get('band', 0.0),
                   chord=bool(meta.get('chord')))
    llr = np.concatenate([d.demodulate_soft(amostras[i:i + BLOCO])
                          for i in range(0, len(amostras), BLOCO)])

    inicio = fec.find_sync(llr)
    if inicio is None:
        raise SystemExit(f"[figura] {stem}: palavra de sincronismo nao achada")

    a = Alinhado(stem, meta, amostras, d, llr, inicio)
    # O preambulo tem 480 bits, 120 simbolos inteiros, entao o quadro comeca
    # numa fronteira de simbolo. Um resto aqui e trava fora do lugar, e todas
    # as fronteiras desenhadas sairiam deslocadas.
    if a.bit0 % MARY_BITS:
        raise SystemExit(f"[figura] {stem}: sincronismo em bit {a.bit0}, "
                         f"que nao e fronteira de simbolo")

    carga = bytes.fromhex(meta['payload_hex'])
    lido = fec.decode(llr[inicio:], meta['payload_len'],
                      repeat=meta['fec_repeat'])
    if lido != carga:
        raise SystemExit(f"[figura] {stem}: o bloco nao decodifica de volta a "
                         f"carga gravada; o alinhamento esta errado")

    # Os bits do quadro sao os TRANSMITIDOS, pelo mesmo caminho do
    # transmissor: convolucional, repeticao, entrelacamento, com a palavra de
    # sincronismo na frente. Nao sao os decodificados do audio. A figura
    # mostra o que foi enviado; o recebido coincidir e o resultado.
    a.quadro = fec.frame(carga, repeat=meta['fec_repeat'])
    a.simbolos = -(-len(a.quadro) // MARY_BITS)
    # O modulador enche o ultimo simbolo com zeros para fechar quatro bits.
    bits = np.concatenate([a.quadro,
                           np.zeros((-len(a.quadro)) % MARY_BITS, dtype=np.int8)])
    a.bits = bits.reshape(-1, MARY_BITS)
    # Bits em ordem de fluxo, peso crescente dentro do simbolo, como em
    # `MaryModulator.modulate_bits`.
    a.valor = [int(sum(int(b) << j for j, b in enumerate(q))) for q in a.bits]
    a.tom = [_GRAY[v] for v in a.valor]
    if a.simbolo0 + a.simbolos > len(d.janelas):
        raise SystemExit(f"[figura] {stem}: a gravacao acaba antes do quadro")
    # A janela do ultimo simbolo tem de caber inteira na gravacao. Ter a
    # amostra inicial nao basta: quem recortar `amostras[i0:i1]` no fim do
    # quadro receberia um trecho curto, e uma FFT sobre menos amostras do que
    # o detector mediu nao e a medida que o detector fez.
    fim = a.janela(a.simbolos - 1)[1]
    if fim > len(amostras):
        raise SystemExit(f"[figura] {stem}: a janela do último símbolo termina "
                         f"na amostra {fim} e a gravação tem {len(amostras)}")
    return a


def cabecalho(a):
    """As linhas de procedencia que toda figura desta campanha imprime."""
    return [f"    {a.stem}, {virgula(len(a.amostras) / a.fs, 2)} s gravados, "
            f"{a.meta['payload_len']} B de carga, repeticao "
            f"{a.meta['fec_repeat']}",
            f"    quadro de {a.simbolos} simbolos, "
            f"{virgula(a.tempo(0), 3)} a {virgula(a.tempo(a.simbolos - 1), 3)} s; "
            f"simbolo de {a.demod.samples_per_symbol} amostras, guarda "
            f"{a.demod.guard} ({virgula(100 * a.demod.guard / a.demod.samples_per_tone, 0)}%), "
            f"janela de decisao {a.demod.samples_per_tone - a.demod.guard}",
            f"    simbolos certos {virgula(100 * a.acertos())}%, "
            f"bits certos {virgula(100 * a.bits_certos())}%"]
