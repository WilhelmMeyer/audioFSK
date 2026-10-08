"""Saudação, contrato e canal: a camada de enlace que fala só pelo áudio.

Hoje os dois lados do link combinam tudo pelo cabo serial (ou pelo túnel SSH):
quem transmite, em que modo, com que ganho, com que `fecrep`. Este módulo tira
essa combinação do cabo e a põe no ar, em três fases:

1. **Saudação.** Quem chama toca uma varredura subindo ("estou aqui") e escuta;
   quem ouve responde com uma varredura descendo. A varredura é o sinal mais
   detectável que este projeto tem -- larga, nenhuma cova do pente a apaga, e o
   filtro casado a comprime num pico -- e não precisa de um único bit certo
   para ser reconhecida. Depois disso um quadro de controle com CRC (`OLA` /
   `OLA_OK`) confirma que não foi ruído. O quadro de controle é tentado em
   várias *abordagens* (par de tons, ganho, camada) em rodízio, para que uma
   característica local que derrube uma abordagem não derrube todas; quem
   ouve tenta todas as abordagens sobre o mesmo áudio e o CRC escolhe.

2. **Contrato.** Cada lado toca uma sondagem: tons em degraus numa grade de
   162,5 Hz (em ordem embaralhada, porque a cauda do tom anterior chega ~6 dB
   acima do piso e inflaria o seguinte; mediana de três) e uma escada de
   ganhos com um bloco 16-FSK de conteúdo conhecido em cada degrau. Quem
   *recebe* mede, e por isso quem recebe decide o contrato daquele sentido:
   os 16 tons (janela deslizante sobre a grade, pulando até seis "sombras"),
   o par para 2-FSK, o ganho (o menor dentro de um ponto do melhor -- se um
   ganho menor acerta mais, a cadeia está comprimindo) e o degrau de taxa.
   O contrato é por sentido: os dois sentidos deste link já mediram SNR
   diferentes.

3. **Canal.** Quadros de dados com CRC no contrato de cada sentido, pare-e-
   espere, half-duplex. A primeira troca de dados é a confirmação do contrato.
   Falhas repetidas fazem o receptor pedir um degrau mais lento (o pedido vai
   no cabeçalho de cada quadro de volta); falhas demais devolvem à saudação.

Mesma regra de camadas do `modem.py`: nada de dispositivo, thread, arquivo ou
relógio de parede. `Estacao` recebe amostras (`ouvir`) e devolve o que tocar
(`passo`); o tempo é o número de amostras ouvidas. Por isso o mesmo código
roda sob `saudacao.py` (áudio de verdade) e sob `simula_enlace.py` (dois
canais simulados), e o simulador exercita exatamente o que vai ao ar.

Nada disto foi medido no ar ainda.
"""

from dataclasses import dataclass

import numpy as np
from scipy.signal import butter, fftconvolve, sosfiltfilt

import fec
from modem import MaryModulator, MaryDemodulator, MARY_TONES, chirp
from xfer import crc16

FS = 48000
BAUD = 100
SPS = FS // BAUD                      # 480 amostras por símbolo, nominal

# --- Marcas -----------------------------------------------------------------
#
# Quatro varreduras, distintas por sentido e por inclinação. A chamada e a
# resposta são longas (0,2 s) porque são o primeiro contato e precisam do maior
# ganho de processamento; as de quadro e de sondagem são as de 80 ms que o
# link já usa, de inclinação mais que o dobro, o que mantém baixa a correlação
# cruzada entre as duas famílias.
MARCAS = {
    'chamada': (600.0, 3600.0, 0.20),
    'resposta': (3600.0, 600.0, 0.20),
    'quadro': (700.0, 3400.0, 0.08),
    'sonda': (3400.0, 700.0, 0.08),
}
MOLDES = {k: chirp(FS, *v) for k, v in MARCAS.items()}
LQ = len(MOLDES['quadro'])            # 3840
HUSH = int(0.05 * FS)                 # silêncio entre a marca e o quadro
GAP = int(0.10 * FS)                  # entre segmentos de um mesmo turno

# Correlação normalizada (0 a 1) entre o molde e o trecho que ele cobre. Não
# pico sobre a mediana da região, como `modem.find_chirp`: aquilo funciona
# sobre uma gravação que contém a varredura, e aqui a região varrida pode ser
# meio segundo de silêncio colado num quadro -- a mediana do silêncio fica
# minúscula e qualquer tom do quadro passa do limiar. A normalizada não
# depende do volume nem da vizinhança e é comparável entre moldes, o que
# resolve também qual família de varredura venceu num mesmo lugar. Medido no
# canal adverso do simulador: marcas verdadeiras 0,48-0,51; o maior falso
# (dados, ruído, molde da outra família) 0,29.
#
# E sempre sobre o sinal filtrado na banda das varreduras: a correlação
# normalizada divide pela energia do trecho, e ruído fora da banda só
# aumenta o divisor. Sem o filtro, com ruído branco forte, as marcas caíam
# para 0,19 enquanto o quadro entre elas ainda decodificava -- a marca era o
# elo mais fraco, o contrário do que precisa ser. Com o filtro, no mesmo
# ruído, 0,46 contra 0,22 do maior falso. Ida e volta (sosfiltfilt) para não
# atrasar o pico: a posição da marca é o relógio do quadro.
LIMIAR = 0.36
_BANDA = butter(4, (500.0, 3700.0), btype='bandpass', fs=FS, output='sos')

# --- Quadros ----------------------------------------------------------------

PRE_SYM = 48                          # preâmbulo curto: o relógio vem das marcas
IDLE_SYM = 6


@dataclass(frozen=True)
class Descritor:
    """Tudo que o receptor precisa para ler um quadro: alfabeto e tamanho."""
    tons: tuple
    bits: int
    rep: int
    nbytes: int
    ganho: float
    nome: str = ''

    @property
    def nsym(self):
        nb = _frame_len(self.nbytes, self.rep)
        return PRE_SYM + -(-nb // self.bits) + IDLE_SYM

    @property
    def amostras(self):
        """Duração no ar, marcas inclusas."""
        return 2 * LQ + 2 * HUSH + self.nsym * SPS

    @property
    def segundos(self):
        return self.amostras / FS


_FRAME_LEN = {}


def _frame_len(nbytes, rep):
    k = (nbytes, rep)
    if k not in _FRAME_LEN:
        _FRAME_LEN[k] = len(fec.frame(bytes(nbytes), repeat=rep))
    return _FRAME_LEN[k]


def _preambulo(bits):
    """Valores do preâmbulo. Percorre todos os tons, não só os extremos: o
    preâmbulo aqui não ensina o relógio (as marcas ensinam), ele assenta o
    piso de cada tom, e um tom que nunca soa nunca fica fora da atualização do
    piso -- o que faz cada tom convergir no mesmo ritmo."""
    m = 1 << bits
    return [(i * 7) % m if m > 2 else i % 2 for i in range(PRE_SYM)]


def _valores_em_bits(vals, bits):
    out = []
    for v in vals:
        out += [(v >> j) & 1 for j in range(bits)]
    return out


def modula_quadro(desc, corpo):
    """Marca, silêncio, preâmbulo, palavra de sincronismo e bloco codificado,
    cauda, silêncio, marca. Duas marcas: a primeira dá o início, o intervalo
    entre elas dá o período do símbolo medido, como em `syncsweep`."""
    if len(corpo) != desc.nbytes:
        raise ValueError(f"corpo de {len(corpo)} bytes num quadro de {desc.nbytes}")
    mod = MaryModulator(fs=FS, baud=BAUD, tones=desc.tons, bits=desc.bits)
    s = np.concatenate([
        mod.modulate_bits(_valores_em_bits(_preambulo(desc.bits), desc.bits)),
        mod.modulate_bits(list(fec.frame(corpo, repeat=desc.rep))),
        mod.idle(IDLE_SYM)])
    assert len(s) == desc.nsym * SPS, (len(s), desc.nsym * SPS)
    m = MOLDES['quadro']
    z = np.zeros(HUSH)
    return np.concatenate([m, z, s, z, m]) * desc.ganho


class _Demod(MaryDemodulator):
    """O mesmo receptor, com as energias calculadas por partes real e
    imaginária. Valores idênticos (a amostra é real, então |Ps|² =
    (Re P·s)² + (Im P·s)²); o motivo é tempo: no numpy 2.5.2 desta máquina,
    matriz complexa 16x408 vezes vetor real leva 8,9 ms e as duas reais
    0,013 ms -- o 16-FSK lia um quadro de 3,3 s em 5,7 s de CPU, mais lento
    que o ar. `modem.MaryDemodulator._energies` tem o mesmo custo no caminho
    ao vivo; a correção lá é uma linha, e fica para quando `modem.py` não
    tiver trabalho alheio por commitar."""

    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self._partes = [(np.ascontiguousarray(p.real), np.ascontiguousarray(p.imag))
                        for p in self.probes]

    def _energies(self, start):
        key = (self.consumed, len(self.buf), start)
        if self._e_key == key:
            return self._e_val
        seg = self.buf[start + self.guard:start + self.samples_per_tone]
        e = sum((re @ seg) ** 2 + (im @ seg) ** 2 for re, im in self._partes)
        self._e_key, self._e_val = key, e
        return e


def le_quadro(audio, p1, desc, p2=None):
    """Lê um quadro de `audio` cuja marca de abertura começa em `p1`.

    Com a marca de fechamento (`p2`) o período é medido; sem ela, nominal.
    Devolve (corpo ou None, llr do bloco codificado ou None). O CRC decide se
    o corpo vale; o llr volta mesmo quando não vale, porque a sondagem conta
    bits errados sobre um conteúdo que já conhece.
    """
    nominal = LQ + 2 * HUSH + desc.nsym * SPS
    r = 1.0 if p2 is None else (p2 - p1) / nominal
    if not 0.995 <= r <= 1.005:
        return None, None
    fim = p1 + int((LQ + 2 * HUSH + (desc.nsym + 1) * SPS) * r)
    seg = np.asarray(audio[p1:fim], dtype=np.float64)
    if len(seg) < (LQ + HUSH + desc.nsym * SPS) * r:
        return None, None
    d = _Demod(fs=FS, baud=BAUD, tones=desc.tons, bits=desc.bits,
               steer=False, skip=int(round((LQ + HUSH) * r)),
                        period=SPS * r)
    partes = [d.demodulate_soft(seg[i:i + 2048]) for i in range(0, len(seg), 2048)]
    partes = [q for q in partes if len(q)]
    if not partes:
        return None, None
    llr = np.concatenate(partes)
    # Onde a palavra de sincronismo deve terminar, procurada só a dois
    # símbolos de distância: as marcas já disseram onde o quadro está, e uma
    # busca larga só daria ao ruído do preâmbulo a chance de ganhar.
    alvo = PRE_SYM * desc.bits + len(fec.SYNC)
    want = 2.0 * fec.SYNC - 1.0
    melhor, onde = -2.0, None
    for e in range(alvo - 2 * desc.bits, alvo + 2 * desc.bits + 1):
        if e - len(fec.SYNC) < 0 or e > len(llr):
            continue
        sc = float(np.dot(np.sign(llr[e - len(fec.SYNC):e]), want)) / len(fec.SYNC)
        if sc > melhor:
            melhor, onde = sc, e
    if onde is None:
        return None, None
    ncod = _frame_len(desc.nbytes, desc.rep) - len(fec.SYNC)
    bloco = llr[onde:onde + ncod]
    if len(bloco) < ncod:
        return None, bloco
    corpo = fec.decode(bloco, desc.nbytes, repeat=desc.rep)
    return (corpo if confere(corpo) else None), bloco


# --- Corpos -----------------------------------------------------------------
#
# tipo, flags, sessão, carga, CRC-16. Tamanho fixo por espécie de quadro: o
# receptor precisa do tamanho para saber onde o quadro termina, e um tamanho
# que viajasse dentro do quadro só seria lido depois de o quadro ter sido lido.

OLA, OLA_OK, CONTRATO, SONDA_G, DADOS, ACK = 1, 2, 3, 4, 5, 6
NOMES = {OLA: 'OLA', OLA_OK: 'OLA_OK', CONTRATO: 'CONTRATO', SONDA_G: 'SONDA_G',
         DADOS: 'DADOS', ACK: 'ACK'}
CTRL_N = 12
SONDA_N = 16
DADOS_N = 40
DADOS_CARGA = DADOS_N - 5 - 4          # seq, ack, pede, len


def empacota(tipo, sessao, carga, n, mais=False):
    carga = bytes(carga)
    if len(carga) > n - 5:
        raise ValueError("carga grande demais")
    c = bytes([tipo, 1 if mais else 0, sessao & 0xFF]) + carga.ljust(n - 5, b'\0')
    k = crc16(c)
    return c + bytes([k >> 8, k & 0xFF])


def confere(corpo):
    if corpo is None or len(corpo) < 5:
        return False
    k = crc16(corpo[:-2])
    return corpo[-2:] == bytes([k >> 8, k & 0xFF])


def abre(corpo):
    """(tipo, mais, sessão, carga) de um corpo que já passou no CRC."""
    return corpo[0], bool(corpo[1] & 1), corpo[2], corpo[3:-2]


# --- Abordagens de controle --------------------------------------------------
#
# O quadro de controle é lento de propósito (2-FSK, 1 bit por símbolo, ~4 s
# para 12 bytes) e é tentado em rodízio. Mudam o par de tons, o ganho e por
# fim a camada inteira, para que um lugar que derrube uma não derrube todas.
# Os tons 1700/2350 são o `fsk2` (medidos a 10 cm em G01-TONS); 1212/1862 é um
# par alternativo de mesma separação, *não medido*; a última é o 16-FSK com
# repetição, a camada de melhor resultado no ar, para um lugar em que as duas
# frequências de um par caiam ambas em covas.

ABORDAGENS = (
    Descritor((1700, 2350), 1, 1, CTRL_N, 0.30, 'fsk2 1700/2350 g0.30'),
    Descritor((1212, 1862), 1, 1, CTRL_N, 0.30, 'fsk2 1212/1862 g0.30'),
    Descritor(tuple(MARY_TONES), 4, 2, CTRL_N, 0.30, '16-FSK rep2 g0.30'),
    Descritor((1700, 2350), 1, 1, CTRL_N, 0.12, 'fsk2 1700/2350 g0.12'),
)
GANHOS_CHAMADA = (0.30, 0.15, 0.50)

# --- Sondagem e contrato -----------------------------------------------------

GRADE = tuple(562.5 + 162.5 * k for k in range(25))     # 562,5 .. 4462,5 Hz
GANHOS = (0.12, 0.20, 0.30, 0.45)
SONDA_TOM = 0.05
SONDA_PASSO = 0.06
SONDA_SIL = 0.30
SONDA_REPS = 3
SONDA_GANHO_TOM = 0.30
SOMBRAS_MAX = 6
# Tons 16-FSK das sondas de ganho: os de sempre, por ora. O contrato escolhe
# os tons depois, e a confirmação no contrato é o que mede a escolha.
SONDA_G_DESC = tuple(Descritor(tuple(MARY_TONES), 4, 1, SONDA_N, g, f'sonda g{g}')
                     for g in GANHOS)

# Degraus de taxa, do mais rápido ao mais lento. Limiares de erro de bit
# (antes do FEC) a partir de CLAUDE.md: taxa 1/3 suave inteira até ~13%,
# repetida duas vezes até ~25%. Aqui com folga, porque três sondas por
# sentido são poucas e o contrato pode ser renegociado para baixo, nunca o
# contrário sem nova sondagem.
DEGRAUS = ('16-FSK rep1', '16-FSK rep2', '16-FSK rep4', '2-FSK rep1')
LIMIARES_BER = (0.07, 0.15, 0.25)


def _ordem_sonda(sessao):
    rng = np.random.RandomState(1000 + sessao)
    ordem = [k for k in range(len(GRADE)) for _ in range(SONDA_REPS)]
    rng.shuffle(ordem)
    return ordem


def carga_sonda_g(sessao, i):
    rng = np.random.RandomState(7919 * (sessao + 1) + i)
    return bytes([i]) + bytes(rng.randint(0, 256, SONDA_N - 6).astype(np.uint8))


def _tons_sonda(sessao):
    """A parte de tons da sondagem, entre as duas marcas de sonda."""
    passo, ntom = int(SONDA_PASSO * FS), int(SONDA_TOM * FS)
    rampa = int(0.004 * FS)
    env = np.ones(ntom)
    r = 0.5 * (1 - np.cos(np.pi * np.arange(rampa) / rampa))
    env[:rampa], env[-rampa:] = r, r[::-1]
    t = np.arange(ntom) / FS
    partes = [np.zeros(int(SONDA_SIL * FS))]
    for k in _ordem_sonda(sessao):
        p = np.zeros(passo)
        p[:ntom] = np.sin(2 * np.pi * GRADE[k] * t) * env
        partes.append(p)
    return np.concatenate(partes) * SONDA_GANHO_TOM


def _sonda_tons_nominal():
    return int(SONDA_SIL * FS) + len(GRADE) * SONDA_REPS * int(SONDA_PASSO * FS)


def modula_sonda(sessao):
    m = MOLDES['sonda']
    z = np.zeros(HUSH)
    partes = [m, z, _tons_sonda(sessao), z, m, np.zeros(GAP)]
    for i, d in enumerate(SONDA_G_DESC):
        partes += [modula_quadro(d, empacota(SONDA_G, sessao, carga_sonda_g(sessao, i), SONDA_N)),
                   np.zeros(GAP)]
    return np.concatenate(partes)


def sonda_amostras():
    return (2 * LQ + 2 * HUSH + _sonda_tons_nominal() + GAP
            + sum(d.amostras + GAP for d in SONDA_G_DESC))


def mede_tons(audio, p1, p2, sessao):
    """Margem de cada tom da grade, em dB, sobre o pior entre o piso em
    silêncio e o que chega naquela frequência enquanto soam tons distantes
    (cauda e intermodulação incluídas -- é contra isso que o 16-FSK decide).
    Mediana de três passos por tom."""
    nominal = LQ + 2 * HUSH + _sonda_tons_nominal()
    r = 1.0 if p2 is None else (p2 - p1) / nominal
    if not 0.995 <= r <= 1.005:
        r = 1.0
    base = p1 + (LQ + HUSH) * r
    a0, w = int(0.008 * FS), int(0.038 * FS)
    n = np.arange(w)
    sondas = np.exp(-2j * np.pi * np.outer(GRADE, n) / FS)

    def energia(ini):
        i = int(round(base + ini * r))
        seg = np.asarray(audio[i:i + w], dtype=np.float64)
        if len(seg) < w:
            return np.zeros(len(GRADE))
        return np.abs(sondas @ seg) ** 2

    sil = [energia(s) for s in range(int(0.02 * FS), int((SONDA_SIL - 0.02) * FS) - w, w)]
    piso = np.median(np.array(sil), axis=0)
    ordem = _ordem_sonda(sessao)
    passo = int(SONDA_PASSO * FS)
    E = np.array([energia(int(SONDA_SIL * FS) + j * passo + a0) for j in range(len(ordem))])
    ordem = np.array(ordem)
    margem = np.zeros(len(GRADE))
    for k in range(len(GRADE)):
        on = np.median(E[ordem == k, k])
        longe = np.abs(ordem - k) >= 3
        interf = np.median(E[longe, k])
        margem[k] = 10 * np.log10(max(on, 1e-30) / max(piso[k], interf, 1e-30))
    return margem


# Acima disto mais margem não muda decisão nenhuma, e perseguir o último dB
# só empurra os tons para fora da banda já medida no ar.
MARGEM_BASTA = 30.0
CUSTO_SOMBRA = 2.0       # dB por tom pulado
CUSTO_PASSO = 1.0        # dB por passo de grade longe da banda de sempre
PADRAO_16 = 2            # GRADE[2] = 887,5 Hz, o primeiro dos MARY_TONES
PADRAO_PAR = (7, 11)     # 1700/2350, o fsk2


def escolhe_16(margem, sombras_max=SOMBRAS_MAX):
    """Índices na grade dos 16 tons do contrato.

    Faixa deslizante com sombras: uma janela de 16+s tons consecutivos da
    grade, da qual saem os s piores. Vale o pior tom que fica, até
    MARGEM_BASTA; cada sombra custa CUSTO_SOMBRA e cada passo de grade longe
    da banda de sempre custa CUSTO_PASSO. Num canal limpo, portanto, saem os
    tons de sempre sem sombra nenhuma; as sombras só aparecem quando um tom
    está de fato numa cova."""
    m = np.minimum(np.asarray(margem, dtype=float), MARGEM_BASTA)
    melhor = None
    for s in range(sombras_max + 1):
        for a in range(len(GRADE) - 16 - s + 1):
            jan = list(range(a, a + 16 + s))
            fica = sorted(sorted(jan, key=lambda k: m[k])[s:])
            nota = (min(m[k] for k in fica) - CUSTO_SOMBRA * s
                    - CUSTO_PASSO * abs(a - PADRAO_16))
            if melhor is None or nota > melhor[0]:
                melhor = (nota, fica)
    return melhor[1]


def escolhe_par(margem):
    """Dois índices da grade a pelo menos quatro passos (650 Hz), como o fsk2,
    com o mesmo teto de margem e a mesma atração pelo par de sempre."""
    m = np.minimum(np.asarray(margem, dtype=float), MARGEM_BASTA)
    melhor = None
    for a in range(len(GRADE)):
        for b in range(a + 4, len(GRADE)):
            nota = (min(m[a], m[b]) - CUSTO_PASSO * (abs(a - PADRAO_PAR[0])
                                                     + abs(b - PADRAO_PAR[1])))
            if melhor is None or nota > melhor[0]:
                melhor = (nota, (a, b))
    return melhor[1]


@dataclass
class Contrato:
    tons: tuple          # 16 índices na grade
    par: tuple           # 2 índices na grade
    ganho: int           # índice em GANHOS
    degrau: int          # índice em DEGRAUS

    def empacota(self):
        mapa = sum(1 << k for k in self.tons)
        v = mapa | (self.par[0] << 25) | (self.par[1] << 30) | (self.ganho << 35) | (self.degrau << 37)
        return v.to_bytes(5, 'little')

    @classmethod
    def abre(cls, b):
        v = int.from_bytes(bytes(b[:5]), 'little')
        tons = tuple(k for k in range(25) if v >> k & 1)
        if len(tons) != 16:
            raise ValueError("contrato sem 16 tons")
        return cls(tons, ((v >> 25) & 31, (v >> 30) & 31), (v >> 35) & 3, (v >> 37) & 3)

    def descritor(self, degrau=None, nbytes=DADOS_N):
        d = self.degrau if degrau is None else degrau
        g = GANHOS[self.ganho]
        if d == 3:
            return Descritor(tuple(GRADE[k] for k in self.par), 1, 1, nbytes, g,
                             f'contrato 2-FSK {nbytes}B')
        return Descritor(tuple(GRADE[k] for k in self.tons), 4, (1, 2, 4)[d], nbytes, g,
                         f'contrato {DEGRAUS[d]} {nbytes}B')

    def descreve(self):
        f = [GRADE[k] for k in self.tons]
        falta = [GRADE[k] for k in range(min(self.tons), max(self.tons) + 1) if k not in self.tons]
        return (f"{f[0]:.0f}-{f[-1]:.0f} Hz, sombras {[round(x) for x in falta]}, "
                f"par {GRADE[self.par[0]]:.0f}/{GRADE[self.par[1]]:.0f}, "
                f"ganho {GANHOS[self.ganho]}, {DEGRAUS[self.degrau]}")


def decide(margem, sondas_g):
    """O contrato de um sentido, a partir do que o receptor mediu.

    `sondas_g`: (ber, inteiro) por degrau de ganho, ber 0,5 quando a sonda nem
    foi achada. Ganho: o menor dentro de um ponto do melhor -- um ganho menor
    que acerta tanto quanto o maior é a cadeia saindo da compressão, e a folga
    sobra para o dia em que a sala mudar."""
    acerto = [1 - b for b, _ in sondas_g]
    top = max(acerto)
    gi = min(i for i, a in enumerate(acerto) if a >= top - 0.01)
    ber, inteiro = sondas_g[gi]
    if ber < LIMIARES_BER[0] and inteiro:
        degrau = 0
    elif ber < LIMIARES_BER[1]:
        degrau = 1
    elif ber < LIMIARES_BER[2]:
        degrau = 2
    else:
        degrau = 3
    return Contrato(tuple(escolhe_16(margem)), escolhe_par(margem), gi, degrau)


# --- Ouvido: varredura contínua do que chega ---------------------------------

class Ouvido:
    """Guarda o áudio que chega e acha as marcas nele, continuamente.

    Nunca "toca e depois grava uma janela": uma chamada que caísse na borda
    de uma janela seria cortada ao meio e nunca achada, o que pareceria uma
    sala ruim. O áudio entra em pedaços de qualquer tamanho e a varredura
    anda sobre ele com sobreposição. O que a própria estação tocou (mais uma
    guarda) é zerado ao entrar e excluído da busca: o microfone ouve o
    próprio alto-falante muito mais alto que o outro lado.
    """

    PASSO = FS // 2
    GUARDA_MAX = 90 * FS

    def __init__(self):
        self.buf = np.zeros(0, dtype=np.float32)
        self.base = 0
        self.fim = 0
        self.cegos = []
        self.varrido = 0
        self.marcas = []          # (pos, tipo, score), pos = início da marca
        self.lmax = max(len(m) for m in MOLDES.values())

    def cego(self, a, b):
        self.cegos.append((a, b))
        self.cegos = [(x, y) for x, y in self.cegos if y > self.base]

    def _invalido(self, a, b):
        inv = np.zeros(b - a, dtype=bool)
        if a < self.base:
            inv[:self.base - a] = True
        for x, y in self.cegos:
            lo, hi = max(x, a), min(y, b)
            if lo < hi:
                inv[lo - a:hi - a] = True
        return inv

    def acrescenta(self, x):
        x = np.asarray(x, dtype=np.float32).copy()
        a = self.fim
        x[self._invalido(a, a + len(x))] = 0.0
        self.buf = np.concatenate([self.buf, x])
        self.fim += len(x)
        if len(self.buf) > self.GUARDA_MAX:
            corta = len(self.buf) - self.GUARDA_MAX
            self.buf = self.buf[corta:]
            self.base += corta

    def trecho(self, a, b):
        a2, b2 = max(a, self.base), min(b, self.fim)
        out = np.zeros(max(0, b - a), dtype=np.float64)
        if a2 < b2:
            out[a2 - a:b2 - a] = self.buf[a2 - self.base:b2 - self.base]
        return out

    def varre(self):
        """Avança a varredura até onde o áudio permite; devolve as marcas novas."""
        novas = []
        L = self.lmax
        while self.fim - self.varrido >= self.PASSO + 2 * L:
            r0, r1 = self.varrido, self.varrido + self.PASSO
            a = r0 - L
            x = sosfiltfilt(_BANDA, self.trecho(a, r1 + 2 * L))
            inv = np.concatenate([[0], np.cumsum(self._invalido(a, r1 + 2 * L))])
            achadas = []
            e = np.concatenate([[0.0], np.cumsum(x * x)])
            for tipo, m in MOLDES.items():
                lt = len(m)
                c = np.abs(fftconvolve(x, m[::-1], mode='valid'))
                q = np.arange(len(c))
                ruim = (inv[q + lt] - inv[q]) > 0
                en = np.sqrt(np.maximum(e[q + lt] - e[q], 0.0)) * np.linalg.norm(m)
                s = np.where(ruim | (en <= 0), 0.0, c / np.maximum(en, 1e-12))
                h = lt // 2
                for i in np.flatnonzero(s >= LIMIAR):
                    pos = a + i
                    if not r0 <= pos < r1:
                        continue
                    if s[i] < s[max(0, i - h):i + h + 1].max():
                        continue
                    achadas.append((pos, tipo, float(s[i])))
            # Uma varredura também correlaciona, mais fraco, com o molde da
            # outra família. No mesmo lugar, fica a mais forte.
            achadas.sort(key=lambda t: -t[2])
            for pos, tipo, sc in achadas:
                if any(abs(pos - p) < int(0.15 * FS) for p, _, _ in novas + self.marcas[-8:]
                       if p >= r0 - L):
                    continue
                novas.append((pos, tipo, sc))
            self.varrido = r1
        novas.sort()
        self.marcas += novas
        return novas


# --- Estação ------------------------------------------------------------------

RESP = int(0.8 * FS)           # pausa antes de responder
GUARDA = int(0.5 * FS)         # cegueira depois de tocar
ESPERA = int(3.0 * FS)         # quanto esperar o começo de uma resposta
FOLGA = int(1.0 * FS)          # quanto esperar outro segmento num turno
import os as _os
_DEPURA = bool(_os.environ.get('ENLACE_DEPURA'))
SILENCIO_MORTO = 20 * FS       # canal aberto sem nada legível: dado por morto


class Estacao:
    """Uma ponta do enlace. `papel` é 'chamador' ou 'ouvinte'.

    Uso: a cada pedaço de áudio, `ouvir(pedaço)` e depois `passo()`; se
    `passo` devolver amostras, tocá-las já. O relógio é o número de amostras
    ouvidas, e o que for tocado é tido como começando no instante atual.
    """

    def __init__(self, papel, semente=None, log=None, nome=None):
        assert papel in ('chamador', 'ouvinte')
        self.papel = papel
        self.nome = nome or papel
        self.rng = np.random.default_rng(semente)
        self.ouvido = Ouvido()
        self._log = log or (lambda s: None)
        self.eventos = []          # (t, texto)
        self.recebido = bytearray()
        self.fila = bytearray()
        self.saudado = False
        self.aberto = False
        self.contrato_tx = None    # o contrato do sentido em que eu transmito
        self.contrato_rx = None
        self.ctrl = None
        self.sessao = 0
        self.agenda = []           # [(instante, amostras)]
        self.pendente = None       # segmento em leitura: (pos, tipo, prazo)
        self.turno = []            # eventos do turno que está chegando
        self.turno_fim = None      # instante em que o turno se dá por encerrado
        self.turno_ultimo = 0      # fim do último segmento lido
        self.ultimo_turno = None   # o que eu toquei por último, para repetir
        self.espera_ate = None     # prazo para o começo de uma resposta
        self.tentativas = 0
        self.ab = 0                # abordagem de controle em uso
        self.k_chamada = 0
        self.livre_em = 0          # fim do que estou tocando
        self.ouvido_em = -10 * FS  # última marca ouvida
        self._usadas = set()       # marcas já lidas como parte de um segmento
        self.lat_extra = 0         # latência de saída não declarada, medida no próprio eco
        self._eco = None           # (tipo, início) da última varredura de saudação tocada
        self.reinicia()
        self.anota("tempos no ar: " + "; ".join(
            f"{d.nome} {d.segundos:.1f}s" for d in ABORDAGENS)
            + f"; sondagem {sonda_amostras() / FS:.1f}s")

    # --- utilidades

    @property
    def agora(self):
        return self.ouvido.fim

    def anota(self, s):
        t = self.agora / FS
        self.eventos.append((t, s))
        self._log(f"[{self.nome} {t:7.2f}s] {s}")

    def enviar(self, dados):
        self.fila += bytes(dados)

    def reinicia(self):
        self.estado = 'chamando' if self.papel == 'chamador' else 'escutando'
        self.proxima_chamada = self.agora + int(self.rng.uniform(0.2, 1.0) * FS)
        self.saudado = self.aberto = False
        self.contrato_tx = self.contrato_rx = self.ctrl = None
        self.ultimo_turno = None
        self.espera_ate = None
        self.tentativas = 0
        self.sem_progresso = 0

    def _toca(self, partes, depois=0, espera=True, guarda_turno=True, apos=None, eco=None):
        """Agenda um turno: segmentos separados por GAP, `depois` amostras
        após o fim do que chegou por último (ou a partir de `apos`)."""
        s = []
        for p in partes:
            s += [p, np.zeros(GAP)]
        x = np.concatenate(s[:-1])
        quando = max(self.agora, (self.turno_ultimo if apos is None else apos) + depois)
        self.agenda.append((quando, x, eco))
        if guarda_turno:
            self.ultimo_turno = partes
        self.espera_ate = (quando + len(x) + RESP + ESPERA) if espera else None

    def _quadro(self, desc, tipo, carga, mais=False):
        return modula_quadro(desc, empacota(tipo, self.sessao, carga, desc.nbytes, mais))

    # --- laço

    def desloca_saida(self, n):
        """O que `passo` acabou de devolver só começa a soar `n` amostras
        depois do instante atual da estação: áudio de entrada ainda na fila
        do runtime, mais a latência da saída (num alto-falante Bluetooth, uma
        fração apreciável de segundo). Sem isto a cegueira cobriria o
        intervalo errado e a estação se ouviria."""
        if n <= 0:
            return
        if self._eco is not None:
            self._eco = (self._eco[0], self._eco[1] + n)
        a, b = self.ouvido.cegos[-1]
        self.ouvido.cegos[-1] = (a + n, b + n)
        self.livre_em += n
        if self.espera_ate is not None:
            self.espera_ate += n

    def ouvir(self, x):
        self.ouvido.acrescenta(x)

    def passo(self):
        for pos, tipo, sc in self.ouvido.varre():
            self._marca(pos, tipo, sc)
        self._le_segmentos()
        if self.turno_fim is not None and self.agora >= self.turno_fim:
            turno, self.turno, self.turno_fim = self.turno, [], None
            self._turno(turno)
        self._prazos()
        if self.agenda and self.agenda[0][0] <= self.agora and self.agora >= self.livre_em:
            _, x, eco = self.agenda.pop(0)
            a = self.agora
            self.livre_em = a + len(x) + self.lat_extra
            if eco:
                # A varredura de saudação não é apagada da entrada: nenhuma
                # estação age sobre a do próprio tipo, e ouvir o próprio eco
                # é como se mede quanto o som demora de fato a sair.
                self.ouvido.cego(a, a)
                self._eco = (eco, a)
            else:
                self.ouvido.cego(a + self.lat_extra, a + self.lat_extra + len(x) + GUARDA)
            if self.espera_ate is not None:
                self.espera_ate = max(self.espera_ate,
                                      a + self.lat_extra + len(x) + RESP + ESPERA)
            return x
        return None

    # --- recepção

    def _marca(self, pos, tipo, sc):
        if self._eco is not None and tipo == self._eco[0]:
            d = pos - self._eco[1]
            if -SPS <= d < 2 * FS:
                # O meu próprio eco. A latência que o runtime declarou já está
                # descontada em `_eco`; o que sobra é a que ninguém declarou
                # (um alto-falante Bluetooth declara menos do que tem). Sem
                # isto, com 0,7 s a mais, a minha marca de fechamento saía da
                # janela de cegueira e virava a abertura de um quadro fantasma.
                novo = max(0, d)
                if abs(novo - self.lat_extra) > SPS:
                    self.anota(f"latência de saída medida no eco: +{novo / FS:.3f}s "
                               "além da declarada")
                self.lat_extra = novo
                self._eco = None
                return
        if (self.papel == 'chamador') == (tipo == 'chamada') and tipo in ('chamada', 'resposta'):
            return                      # a do meu tipo, de um eco que já não espero
        self.ouvido_em = pos
        if tipo == 'chamada':
            if self.papel == 'ouvinte' and self.aberto and \
                    self.agora - self.progresso_em > SILENCIO_MORTO:
                self.anota("chamada nova com o canal mudo há tempo; o outro lado "
                           "recomeçou -- recomeço também")
                self.reinicia()
            if self.papel == 'ouvinte' and not self.aberto:
                self.anota(f"chamada ouvida (correlação {sc:.2f})")
                g = GANHOS_CHAMADA[self.k_chamada % len(GANHOS_CHAMADA)]
                self.k_chamada += 1
                self.turno_ultimo = pos + len(MOLDES['chamada'])
                self._toca([MOLDES['resposta'] * g], depois=RESP, espera=False,
                           guarda_turno=False, eco='resposta')
                self.estado = 'aguarda_ola'
                self.espera_ate = self.agora + 20 * FS
        elif tipo == 'resposta':
            if self.estado == 'chamando' and self.papel == 'chamador':
                self.anota(f"resposta ouvida (correlação {sc:.2f}); enviando OLA "
                           f"em {ABORDAGENS[self.ab].nome}")
                self.sessao = int(self.rng.integers(1, 256))
                self.turno_ultimo = pos + len(MOLDES['resposta'])
                self.estado = 'ola'
                self.tentativas = 0
                self._envia_ola()
        # quadro e sonda viram segmentos, lidos quando o áudio deles chegar

    def _candidatos(self):
        """Descritores que podem estar no ar agora, por ordem de chance."""
        c = list(ABORDAGENS)
        if self.contrato_rx is not None:
            for d in range(4):
                for n in (DADOS_N, CTRL_N):
                    c.append(self.contrato_rx.descritor(d, n))
        return c

    def _le_segmentos(self):
        while True:
            if self.pendente is None:
                prox = [m for m in self.ouvido.marcas
                        if m[1] in ('quadro', 'sonda') and m[0] >= self.turno_ultimo
                        and m[0] not in self._usadas]
                if not prox:
                    return
                pos, tipo, _ = prox[0]
                if tipo == 'quadro':
                    dur = max(d.amostras for d in self._candidatos())
                else:
                    dur = sonda_amostras()
                self.pendente = dict(pos=pos, tipo=tipo, tentou=set(),
                                     prazo=pos + int(dur * 1.006) + SPS)
                self.turno_fim = None              # outro segmento do mesmo turno
            p = self.pendente
            if p['tipo'] == 'quadro':
                if not self._tenta_quadro(p, final=self.agora >= p['prazo']):
                    return
            else:
                if self.agora < p['prazo']:
                    return
                self._le_sonda(p['pos'])
            self._usadas.add(p['pos'])
            self.pendente = None

    def _fechamento(self, p1, dur):
        """A marca de quadro que fecha um quadro aberto em p1 com duração
        nominal `dur`, se houver uma onde deve estar (±0,4%)."""
        alvo = p1 + dur - LQ
        tol = int(0.004 * dur)
        for pos, tipo, _ in self.ouvido.marcas:
            if tipo == 'quadro' and pos != p1 and abs(pos - alvo) <= tol:
                return pos
        return None

    def _tenta_quadro(self, p, final):
        """Tenta ler o quadro pendente. Cada candidato é lido assim que a sua
        marca de fechamento chega -- um quadro de controle de 4 s não espera
        o prazo do quadro mais lento possível (10 s). No prazo, os que não
        tiveram fechamento são lidos só pela abertura, com relógio nominal.
        Devolve True quando o segmento está resolvido, lido ou não."""
        p1 = p['pos']
        for d in self._candidatos():
            p2 = self._fechamento(p1, d.amostras)
            tentativas = []
            if p2 is not None and self.agora >= p2 + LQ + SPS:
                tentativas.append(p2)
            if final and self.agora >= p1 + d.amostras + SPS:
                tentativas.append(None)
            for q2 in tentativas:
                if (d, q2) in p['tentou']:
                    continue
                p['tentou'].add((d, q2))
                fim = p1 + int(d.amostras * 1.006) + SPS
                audio = self.ouvido.trecho(p1, fim)
                corpo, _ = le_quadro(audio, 0, d, None if q2 is None else q2 - p1)
                if corpo is not None:
                    if q2 is not None:
                        self._usadas.add(q2)
                    self._segmento(('quadro', corpo, d, None),
                                   (q2 + LQ) if q2 is not None else p1 + d.amostras)
                    return True
        # Uma marca de fechamento caiu exatamente onde um dos comprimentos
        # previstos termina e a leitura falhou: o quadro tem esse comprimento
        # e está ilegível. Esperar o prazo do candidato mais lento (10 s)
        # para tentar os outros só pela abertura atrasava o veredito tanto
        # que as repetições do outro lado se empilhavam na fila.
        lidos_com_fecho = [q2 for (_, q2) in p['tentou'] if q2 is not None]
        if not final and not lidos_com_fecho and not self._calou(p1):
            return False
        # Nada passou no CRC. Conta como segmento ilegível -- quem fala sabe
        # que alguém falou -- e o turno espera um pouco por mais. O fim é
        # agora, não a marca de abertura: uma resposta contada da abertura
        # sairia por cima da repetição do outro lado, que não me ouve
        # enquanto toca.
        if _DEPURA:
            self.anota(f"  ilegível em {p1 / FS:.2f}s: final={final}, "
                       f"tentou={[(d.nome, None if q2 is None else round((q2 - p1) / FS, 3)) for d, q2 in p['tentou']]}")
        self._segmento(('ilegivel', p1), self.agora)
        return True

    def _calou(self, p1):
        """O outro lado parou de tocar? Sem a marca de fechamento não se sabe
        o comprimento do quadro, e esperar o do candidato mais lento atrasa o
        veredito em até sete segundos -- tempo em que quem falou já desistiu
        de esperar e repete. A energia volta ao piso quando o quadro acaba,
        e isso não depende de bit nenhum."""
        # Só sobre o áudio que a varredura já cobriu: ela anda até ~0,9 s
        # atrás do presente, e um silêncio visto antes dela pode ser o que
        # vem logo depois de uma marca de fechamento ainda não achada --
        # medido, isso declarava ilegíveis quadros perfeitos.
        ate = self.ouvido.varrido
        curto = min(d.amostras for d in self._candidatos())
        if ate < p1 + int(0.99 * curto):
            return False
        ini = p1 + LQ + HUSH
        ref = np.sqrt(np.mean(self.ouvido.trecho(ini, ini + FS // 2) ** 2))
        rec = np.sqrt(np.mean(self.ouvido.trecho(ate - int(0.4 * FS), ate) ** 2))
        return rec < 0.3 * ref

    def _le_sonda(self, p1):
        dur_tons = 2 * LQ + 2 * HUSH + _sonda_tons_nominal()
        alvo = p1 + dur_tons - LQ
        p2 = None
        for pos, tipo, _ in self.ouvido.marcas:
            if tipo == 'sonda' and pos != p1 and abs(pos - alvo) <= int(0.004 * dur_tons):
                p2 = pos
                self._usadas.add(pos)
        audio = self.ouvido.trecho(p1, p1 + sonda_amostras() + FS)
        margem = mede_tons(audio, 0, None if p2 is None else p2 - p1, self.sessao)
        r = 1.0 if p2 is None else (p2 - p1) / (dur_tons - LQ)
        # As sondas de ganho, em posições conhecidas depois da marca final.
        res = []
        q = int(round(dur_tons * r)) + int(GAP * r)
        for i, d in enumerate(SONDA_G_DESC):
            perto = [pos - p1 for pos, tipo, _ in self.ouvido.marcas
                     if tipo == 'quadro' and abs(pos - p1 - q) <= int(0.03 * FS)]
            ber, inteiro = 0.5, False
            if perto:
                s1 = perto[0]
                self._usadas.add(p1 + s1)
                fecho = [pos - p1 for pos, tipo, _ in self.ouvido.marcas
                         if tipo == 'quadro'
                         and abs(pos - p1 - s1 - (d.amostras - LQ)) <= int(0.004 * d.amostras)]
                p2q = fecho[0] if fecho else None
                if p2q is not None:
                    self._usadas.add(p1 + p2q)
                corpo, llr = le_quadro(audio, s1, d, p2q)
                if llr is not None:
                    conhecido = empacota(SONDA_G, self.sessao, carga_sonda_g(self.sessao, i), SONDA_N)
                    ref = fec.encode(conhecido, repeat=1)
                    k = min(len(ref), len(llr))
                    ber = float(np.mean((llr[:k] > 0) != (ref[:k] > 0))) if k else 0.5
                    inteiro = corpo == conhecido
                q = s1
            q += int((d.amostras + GAP) * r)
            res.append((ber, inteiro))
        fim = p1 + sonda_amostras()
        self._segmento(('sonda', margem, res), fim)
        return fim

    def _segmento(self, ev, fim):
        self.turno.append(ev)
        self.turno_ultimo = max(self.turno_ultimo, fim)
        ultimo = (ev[0] == 'sonda'
                  or (ev[0] == 'quadro' and not abre(ev[1])[1]))
        self.turno_fim = self.agora if ultimo else self.agora + FOLGA

    # --- prazos

    def _prazos(self):
        if (self.aberto and self.confirmado and self.fila and self.pendente_tx is None
                and self.ocioso() and self.agora - self.ouvido_em > 2 * FS):
            self._toca(self._turno_dados(), apos=self.agora)
            return
        if self.estado == 'chamando':
            if self.espera_ate is None and self.agora >= self.proxima_chamada and not self.agenda:
                g = GANHOS_CHAMADA[self.k_chamada % len(GANHOS_CHAMADA)]
                self.k_chamada += 1
                self.anota(f"chamando (ganho {g})")
                self.turno_ultimo = self.agora
                self._toca([MOLDES['chamada'] * g], espera=True, guarda_turno=False,
                           eco='chamada')
            elif (self.espera_ate is not None and self.agora > self.espera_ate
                  and not self.agenda):
                self.espera_ate = None
                self.proxima_chamada = self.agora + int(self.rng.uniform(0.5, 2.0) * FS)
            return
        if (self.espera_ate is None or self.agora <= self.espera_ate or self.agenda
                or self.pendente is not None or self.turno or self.agora < self.livre_em):
            return
        # Prazo vencido sem resposta.
        self.espera_ate = None
        if self.estado == 'ola':
            self.tentativas += 1
            if self.tentativas >= 2 * len(ABORDAGENS):
                self.anota("OLA sem resposta em todas as abordagens; voltando a chamar")
                self.reinicia()
                return
            self.ab = (self.ab + 1) % len(ABORDAGENS)
            self.anota(f"sem OLA_OK; tentando {ABORDAGENS[self.ab].nome}")
            self._envia_ola()
        elif self.estado == 'sondando' or (
                self.aberto and (self.pendente_tx is not None or not self.confirmado)):
            self.tentativas += 1
            self.sem_progresso += 1
            if self.tentativas > 8 or self.sem_progresso > 10:
                self.anota(f"sem resposta em '{self.estado}'; voltando ao começo")
                self.reinicia()
                return
            if self.aberto and self.confirmado and self.tentativas % 2 == 0 \
                    and self.degrau_tx < 3:
                # Silêncio não é falha que o receptor possa contar: se nem a
                # marca foi achada, ele não sabe que falei. Quem desce o
                # degrau, então, sou eu; o receptor tenta todos os degraus
                # pelo comprimento do quadro, sem precisar ser avisado.
                self.degrau_tx += 1
                self.anota(f"duas repetições sem resposta; desço para {DEGRAUS[self.degrau_tx]}")
            self.anota(f"sem resposta em '{self.estado}'; repetindo o turno")
            self._toca(self._retransmite(),
                       apos=self.agora + int(self.rng.uniform(0, 1.0) * FS))
        elif self.estado in ('aguarda_ola', 'aguarda_sonda', 'aguarda_contrato'):
            self.anota(f"nada mais em '{self.estado}'; voltando a escutar")
            self.reinicia()

    def _retransmite(self):
        if self.aberto and self.confirmado:
            # Reconstruído, não repetido: o ack e o pedido de degrau podem ter
            # mudado desde a última vez.
            return self._turno_dados(forcar=True)
        return self.ultimo_turno

    # --- fases

    def _envia_ola(self):
        d = ABORDAGENS[self.ab]
        self._toca([self._quadro(d, OLA, bytes([self.ab]))], depois=RESP)

    def _turno(self, eventos):
        quadros = [(abre(e[1]), e[2]) for e in eventos if e[0] == 'quadro'
                   and abre(e[1])[0] in NOMES]
        sondas = [e for e in eventos if e[0] == 'sonda']
        ruins = sum(1 for e in eventos if e[0] == 'ilegivel')
        tipos = [NOMES[q[0][0]] for q in quadros] + ['SONDA'] * len(sondas)
        self.anota(f"turno: {tipos or '-'}" + (f", {ruins} ilegível(is)" if ruins else ""))
        # Uma sessão nova do outro lado (OLA) é ouvida em qualquer estado,
        # menos com o canal aberto -- aí só se o OLA vier de outra sessão.
        for (tipo, mais, sess, carga), d in quadros:
            if tipo == OLA and self.papel == 'ouvinte' and (not self.aberto or sess != self.sessao):
                if self.aberto:
                    self.reinicia()
                self.sessao = sess
                self.ctrl = d
                self.saudado = True
                self.estado = 'aguarda_sonda'
                self.anota(f"OLA lido em {d.nome}; saudação concluída, respondendo OLA_OK")
                self._toca([self._quadro(d, OLA_OK, bytes([carga[0]]))], depois=RESP)
                return
        quadros = [(q, d) for q, d in quadros if q[2] == self.sessao]
        tipos = {q[0]: (q, d) for q, d in quadros}

        if self.estado == 'ola':
            if OLA_OK in tipos:
                self.ctrl = tipos[OLA_OK][1]
                self.saudado = True
                self.tentativas = 0
                self.anota(f"OLA_OK lido em {self.ctrl.nome}; saudação concluída, sondando")
                self.estado = 'sondando'
                self._toca([modula_sonda(self.sessao)], depois=RESP)
            return

        if self.estado == 'aguarda_sonda' or (self.estado == 'aguarda_contrato'
                                               and sondas and CONTRATO not in tipos):
            if sondas:
                self.contrato_rx = self._contrato_de(sondas[0], "chega")
                self.estado = 'aguarda_contrato'
                self._toca([self._quadro(self.ctrl, CONTRATO, self.contrato_rx.empacota(), mais=True),
                            modula_sonda(self.sessao)], depois=RESP)
            return

        if self.estado == 'sondando':
            if CONTRATO in tipos and sondas:
                self.contrato_tx = Contrato.abre(tipos[CONTRATO][0][3])
                self.anota(f"contrato para o que EU envio: {self.contrato_tx.descreve()}")
                self.contrato_rx = self._contrato_de(sondas[0], "chega")
                self.estado = 'contratando'
                self.tentativas = 0
                self._abre_canal()
                self._toca([self._quadro(self.ctrl, CONTRATO, self.contrato_rx.empacota(), mais=True)]
                           + self._turno_dados(forcar=True, so_partes=True), depois=RESP)
            return

        if self.estado == 'aguarda_contrato':
            if CONTRATO in tipos:
                self.contrato_tx = Contrato.abre(tipos[CONTRATO][0][3])
                self.anota(f"contrato para o que EU envio: {self.contrato_tx.descreve()}")
                self._abre_canal()
                self._dados(quadros, ruins + (0 if DADOS in tipos or ACK in tipos else 1))
            return

        if self.aberto:
            if CONTRATO in tipos and self.papel == 'ouvinte':
                # O chamador repetiu o turno do contrato: a primeira resposta
                # se perdeu. Responder de novo.
                pass
            self._dados(quadros, ruins)

    def _contrato_de(self, sonda, sentido):
        _, margem, res = sonda
        c = decide(margem, res)
        bers = ", ".join(f"g{GANHOS[i]}:{b * 100:.0f}%{'*' if ok else ''}"
                         for i, (b, ok) in enumerate(res))
        self.anota(f"sondagem lida: bits errados {bers}; margens "
                   f"{np.round(margem).astype(int).tolist()} dB")
        self.anota(f"contrato para o que me {sentido}: {c.descreve()}")
        if c.ganho == 0:
            # A borda da escada, não um ótimo cercado. Num link real com o
            # volume do sistema alto é a assinatura de compressão de CLAUDE.md
            # (o ganho menor sempre vence), e o remédio é o fader analógico,
            # que esta escada não alcança.
            self.anota("AVISO: venceu o menor ganho da escada; se o volume do "
                       "outro lado estiver alto, baixá-lo e saudar de novo")
        return c

    # --- canal aberto: pare-e-espere

    def _abre_canal(self):
        self.aberto = True
        self.confirmado = False
        self.seq_tx = 0
        self.pendente_tx = None
        self.ultimo_rx = 255
        self.degrau_tx = self.contrato_tx.degrau
        self.degrau_rx = self.contrato_rx.degrau
        self.falhas_rx = 0
        self.sem_progresso = 0
        self.tentativas = 0
        self.progresso_em = self.agora
        self.estado = 'aberto'

    def _turno_dados(self, forcar=False, so_partes=False):
        if self.pendente_tx is None and self.fila:
            pedaco = bytes(self.fila[:DADOS_CARGA])
            del self.fila[:DADOS_CARGA]
            self.pendente_tx = (self.seq_tx, pedaco)
            self.seq_tx = (self.seq_tx + 1) % 255
        if self.pendente_tx is not None:
            seq, pedaco = self.pendente_tx
            d = self.contrato_tx.descritor(self.degrau_tx, DADOS_N)
            carga = bytes([seq, self.ultimo_rx, self.degrau_rx, len(pedaco)]) + pedaco
            q = self._quadro(d, DADOS, carga)
        else:
            d = self.contrato_tx.descritor(self.degrau_tx, CTRL_N)
            q = self._quadro(d, ACK, bytes([self.ultimo_rx, self.degrau_rx]))
        return [q]

    def _dados(self, quadros, ruins):
        responder = not self.confirmado
        progresso = False
        for (tipo, mais, sess, carga), d in quadros:
            if tipo == DADOS:
                seq, ack, pede, n = carga[0], carga[1], carga[2], carga[3]
                pedaco = bytes(carga[4:4 + n])
                # O degrau em que este quadro chegou é o piso do que peço:
                # se o outro lado já desceu, pedir mais rápido seria inútil.
                for k in range(4):
                    if d == self.contrato_rx.descritor(k, d.nbytes):
                        self.degrau_rx = max(self.degrau_rx, k)
                if seq == (self.ultimo_rx + 1) % 255 or (self.ultimo_rx == 255 and seq == 0):
                    self.recebido += pedaco
                    self.ultimo_rx = seq
                    self.anota(f"dados seq {seq}: {n} bytes ({d.nome})")
                responder = True
            elif tipo == ACK:
                ack, pede = carga[0], carga[1]
            else:
                continue
            progresso = True
            if self.pendente_tx is not None and ack == self.pendente_tx[0]:
                self.pendente_tx = None
            if pede < 4 and pede > self.degrau_tx:
                # Um piso, não uma ordem: quem recebe só sabe das falhas que
                # chegou a ver, e quem transmite pode ter descido sozinho por
                # silêncio. Tomar o pedido ao pé da letra fazia os dois
                # oscilarem, um descendo e o outro mandando subir. Subir de
                # novo pede nova sondagem.
                self.anota(f"o outro lado pede o degrau {DEGRAUS[pede]} para o que envio")
                self.degrau_tx = pede
        if progresso:
            self.progresso_em = self.agora
            self.falhas_rx = 0
            self.sem_progresso = 0
            self.tentativas = 0
            if not self.confirmado:
                self.confirmado = True
                self.anota("CANAL ABERTO: contrato confirmado pelos dois lados")
        elif ruins:
            self.falhas_rx += 1
            self.sem_progresso += 1
            responder = True
            if self.falhas_rx >= 2 and self.degrau_rx < 3:
                self.degrau_rx += 1
                self.falhas_rx = 0
                self.anota(f"quadros ilegíveis; pedindo {DEGRAUS[self.degrau_rx]}")
            if self.sem_progresso > 8:
                self.anota("canal perdido; voltando ao começo")
                self.reinicia()
                return
        if self.pendente_tx is not None or self.fila:
            responder = True
        if responder:
            self._toca(self._turno_dados(), depois=RESP,
                       espera=self.pendente_tx is not None or bool(self.fila) or not self.confirmado)

    # A fila de dados de quem está ocioso: se o canal está aberto, o outro
    # lado calado e há o que mandar, mandar sem ser chamado.
    def ocioso(self):
        return (self.aberto and not self.agenda and self.espera_ate is None
                and self.pendente is None and not self.turno and self.agora >= self.livre_em)
