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
from modem import (MaryModulator, MaryDemodulator, MARY_TONES, chirp,
                   MFSKModulator, MFSKDemodulator, MFSK_PAIRS)
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
    # A dos quadros de longe (ver ABORDAGENS). Cinco vezes mais longa: a
    # correlação esperada da marca verdadeira é a mesma, mas a dos falsos cai.
    # Medido em 2026-10-22 sobre 677 s de sessões reais (dados 16-FSK a 2 m,
    # silêncio e quadros de longe): pico falso por segundo p99 0,15, p99,9
    # 0,16, contra até 0,21 do molde de 80 ms -- o que deixa o limiar descer.
    'quadro_longo': (700.0, 3400.0, 0.40),
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
# Um limiar por marca, e não um só. Medido no ar em 2026-10-08, Linux->Windows
# a ~2 m (o sentido ruim): chamada 0,20-0,33 contra o pior falso em dados
# reais 0,18; quadro 0,30-0,36 contra 0,16-0,21 nos dados desse sentido e até
# 0,31 nos dados 16-FSK do outro (H04). O 0,36 único do simulador deixava a
# chamada de fora em todas as 56 tentativas de uma sessão de 5 minutos. Os
# erros não custam o mesmo: uma chamada falsa custa uma troca (o CRC do OLA
# recusa), uma chamada perdida custa a sessão -- por isso a chamada fica
# rente ao falso. Uma marca de quadro falsa vira um segmento ilegível.
LIMIARES = {'chamada': 0.17, 'resposta': 0.17, 'quadro': 0.21, 'sonda': 0.26,
            'quadro_longo': 0.18}
QUADROS = ('quadro', 'quadro_longo')
LIMIAR = min(LIMIARES.values())
_BANDA = butter(4, (500.0, 3700.0), btype='bandpass', fs=FS, output='sos')

# --- Quadros ----------------------------------------------------------------

PRE_SYM = 48                          # preâmbulo curto: o relógio vem das marcas
IDLE_SYM = 6

# As duas camadas 5x2-FSK, com o nome que `fec`/`console.py` dão às suas.
# O quadro é o do `console.py` (`_fec_frame` em mfsk), não um encurtado:
# preâmbulo alternado de 80 símbolos e cauda de 4, que o CLAUDE.md dá como
# não opcionais nessa camada. Aqui o relógio vem das marcas, então o
# preâmbulo é folga -- mas um quadro igual ao que já foi medido no ar é
# comparável com aquelas medidas, e um encurtado não seria.
CAMADAS_5X2 = {'votada': 'mfsk', 'multicanal': 'mfsk-par'}
IDLE_5X2 = 4


@dataclass(frozen=True)
class Descritor:
    """Tudo que o receptor precisa para ler um quadro: alfabeto e tamanho."""
    tons: tuple
    bits: int
    rep: int
    nbytes: int
    ganho: float
    nome: str = ''
    baud: int = BAUD
    guarda: float = 0.15
    pre: int = PRE_SYM
    camada: str = 'tons'        # 'tons' (16-FSK, 2-FSK), 'votada' ou 'multicanal' (5x2)
    marca: str = 'quadro'       # ou 'quadro_longo', a dos quadros de longe

    @property
    def lm(self):
        return len(MOLDES[self.marca])

    @property
    def sps(self):
        return FS // self.baud

    @property
    def nsym(self):
        if self.camada in CAMADAS_5X2:
            # Contado pela mesma função que o `console.py` e os leitores
            # offline usam: preâmbulo alternado de 80, corpo, cauda de 4.
            return fec.layer_frame_symbols(CAMADAS_5X2[self.camada], self.nbytes,
                                           self.rep, npairs=len(MFSK_PAIRS))
        nb = _frame_len(self.nbytes, self.rep)
        return self.pre + -(-nb // self.bits) + IDLE_SYM

    @property
    def amostras(self):
        """Duração no ar, marcas inclusas."""
        return 2 * self.lm + 2 * HUSH + self.nsym * self.sps

    @property
    def segundos(self):
        return self.amostras / FS


_FRAME_LEN = {}


def _frame_len(nbytes, rep):
    k = (nbytes, rep)
    if k not in _FRAME_LEN:
        _FRAME_LEN[k] = len(fec.frame(bytes(nbytes), repeat=rep))
    return _FRAME_LEN[k]


def _preambulo(bits, n=PRE_SYM):
    """Valores do preâmbulo. Percorre todos os tons, não só os extremos: o
    preâmbulo aqui não ensina o relógio (as marcas ensinam), ele assenta o
    piso de cada tom, e um tom que nunca soa nunca fica fora da atualização do
    piso -- o que faz cada tom convergir no mesmo ritmo."""
    m = 1 << bits
    return [(i * 7) % m if m > 2 else i % 2 for i in range(n)]


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
    if desc.camada in CAMADAS_5X2:
        # Os tons são os MFSK_PAIRS fixos, não os da sondagem: a camada vota
        # entre os dois membros de um par, e um par escolhido pela sondagem
        # mudaria o que foi medido sobre ela.
        par = desc.camada == 'multicanal'
        k = len(MFSK_PAIRS)
        mod = MFSKModulator(fs=FS, baud=desc.baud, parallel=par)
        corpo_bits = (fec.frame_parallel(corpo, k, repeat=desc.rep) if par
                      else fec.frame(corpo, repeat=desc.rep))
        s = np.concatenate([
            mod.modulate_bits(fec.preamble_bits('mfsk', npairs=k, parallel=par)),
            mod.modulate_bits(list(corpo_bits)),
            mod.idle(IDLE_5X2)])
    else:
        mod = MaryModulator(fs=FS, baud=desc.baud, tones=desc.tons, bits=desc.bits)
        s = np.concatenate([
            mod.modulate_bits(_valores_em_bits(_preambulo(desc.bits, desc.pre), desc.bits)),
            mod.modulate_bits(list(fec.frame(corpo, repeat=desc.rep))),
            mod.idle(IDLE_SYM)])
    assert len(s) == desc.nsym * desc.sps, (len(s), desc.nsym * desc.sps)
    m = MOLDES[desc.marca]
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
    sps = desc.sps
    LQ = desc.lm
    nominal = LQ + 2 * HUSH + desc.nsym * sps
    r = 1.0 if p2 is None else (p2 - p1) / nominal
    if not 0.995 <= r <= 1.005:
        return None, None
    fim = p1 + int((LQ + 2 * HUSH + (desc.nsym + 1) * sps) * r)
    seg = np.asarray(audio[p1:fim], dtype=np.float64)
    if len(seg) < (LQ + HUSH + desc.nsym * sps) * r:
        return None, None
    if desc.camada in CAMADAS_5X2:
        # Relógio congelado nas marcas, como no 16-FSK; palavra de
        # sincronismo e Viterbi por `fec.decode_block`, que é o caminho do
        # `fecrx` e do `recvfile.py` (votação da palavra no multicanal,
        # cópias recolhidas de cada par por `pair_map`).
        par = desc.camada == 'multicanal'
        k = len(MFSK_PAIRS)
        d = MFSKDemodulator(fs=FS, baud=desc.baud, guard=desc.guarda, parallel=par,
                            steer=False, skip=int(round((LQ + HUSH) * r)), period=sps * r)
        partes = [d.demodulate_soft(seg[i:i + 2048]) for i in range(0, len(seg), 2048)]
        partes = [q for q in partes if len(q)]
        if not partes:
            return None, None
        llr = np.concatenate(partes)
        corpo, ini = fec.decode_block(llr, desc.nbytes, desc.rep, npairs=k if par else None)
        if corpo is None:
            return None, None
        return (corpo if confere(corpo) else None), llr[ini:]
    d = _Demod(fs=FS, baud=desc.baud, tones=desc.tons, bits=desc.bits,
               guard=desc.guarda, steer=False, skip=int(round((LQ + HUSH) * r)),
               period=sps * r)
    partes = [d.demodulate_soft(seg[i:i + 2048]) for i in range(0, len(seg), 2048)]
    partes = [q for q in partes if len(q)]
    if not partes:
        return None, None
    llr = np.concatenate(partes)
    # Onde a palavra de sincronismo deve terminar, procurada só a dois
    # símbolos de distância: as marcas já disseram onde o quadro está, e uma
    # busca larga só daria ao ruído do preâmbulo a chance de ganhar.
    alvo = desc.pre * desc.bits + len(fec.SYNC)
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

OLA, OLA_OK, CONTRATO, SONDA_G, DADOS, ACK, FIM = 1, 2, 3, 4, 5, 6, 7
NOMES = {OLA: 'OLA', OLA_OK: 'OLA_OK', CONTRATO: 'CONTRATO', SONDA_G: 'SONDA_G',
         DADOS: 'DADOS', ACK: 'ACK', FIM: 'FIM'}
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

# O lento: 16-FSK a 20 baud (50 ms por símbolo), guarda de 30%, repetição 2.
# Feito para o Linux->Windows medido em 2026-10-08 a ~2 m, onde o 2-FSK a 100
# baud chegava com 25-35% dos bits errados: num par, o tom alto quase nunca
# vencia (2350 Hz chegava *mais fraco* quando enviado), e a cauda de um tom
# ficava a poucos dB do seguinte por dezenas de ms. Dezesseis tons espalham o
# risco de um tom comido por todo o bloco, onde o FEC o conserta; o símbolo
# longo põe cinco vezes mais energia em cada decisão; a guarda pula o começo,
# onde o tom anterior ainda soa. Preâmbulo curto: o relógio vem das marcas.
LENTO_BAUD = 20
LENTO_GUARDA = 0.30
LENTO_PRE = 8
ABORDAGENS = (
    Descritor((1700, 2350), 1, 1, CTRL_N, 0.30, 'fsk2 1700/2350 g0.30'),
    Descritor(tuple(MARY_TONES), 4, 2, CTRL_N, 0.30, '16-FSK lento rep2 g0.30',
              LENTO_BAUD, LENTO_GUARDA, LENTO_PRE),
    Descritor((1212, 1862), 1, 1, CTRL_N, 0.30, 'fsk2 1212/1862 g0.30'),
    Descritor(tuple(MARY_TONES), 4, 2, CTRL_N, 0.30, '16-FSK rep2 g0.30'),
    Descritor((1700, 2350), 1, 1, CTRL_N, 0.12, 'fsk2 1700/2350 g0.12'),
    # De longe (índices 5 e 6). Medido em 2026-10-22 com as máquinas a alguns
    # metros: a chamada caiu de 0,45-0,50 (a 2 m) para 0,18-0,27; as marcas de
    # quadro chegavam rentes ao limiar (0,19-0,21 no Linux->Windows, cujo
    # microfone tem piso ~4x o do Linux; 0,27-0,31 no outro sentido); os
    # corpos a 100 baud saíam ilegíveis nos dois sentidos e só o lento passou,
    # e só às vezes. Longe falta símbolo longo e marca que se ache, não mais
    # rodízio. Volume ajuda pouco: as chamadas do Linux a 0,15, 0,30 e 0,50
    # chegaram com correlação parecida (o alto-falante já comprime), e no
    # simulador 0,90 pelo limitador deixou o 16-FSK *pior*. Então ganho só
    # moderado (o 0,50 que a chamada já usava no ar) e a marca longa.
    Descritor(tuple(MARY_TONES), 4, 2, CTRL_N, 0.50, '16-FSK lento rep2 g0.50 marca longa',
              LENTO_BAUD, LENTO_GUARDA, LENTO_PRE, marca='quadro_longo'),
    Descritor(tuple(MARY_TONES), 4, 2, CTRL_N, 0.50, '16-FSK muito lento rep2 g0.50 marca longa',
              10, LENTO_GUARDA, LENTO_PRE, marca='quadro_longo'),
)
# Esforço: 0 é o de sempre, que a 2 m funciona e não deve mudar (lá o ganho
# menor vence, porque o alto-falante comprime); 1 é o de longe. Sobe quando a
# chamada ou a resposta chegam fracas, ou quando todas as abordagens de
# perto passaram sem resposta, e não desce mais na mesma execução.
ORDEM_ABORDAGENS = ((0, 1, 2, 3, 4), (5, 6))
GANHOS_CHAMADA = ((0.30, 0.15, 0.50), (0.50,))
LIMIAR_LONGE = 0.42          # chamada/resposta abaixo disto: longe (2 m dá 0,45-0,50; alguns metros 0,30-0,36)
SONDA_GANHO_LONGE = 0.50

# --- Sondagem e contrato -----------------------------------------------------

GRADE = tuple(562.5 + 162.5 * k for k in range(25))     # 562,5 .. 4462,5 Hz
# Quatro, porque o contrato guarda o índice em 2 bits. Até 2026-10-22 iam a
# 0,45; de longe é o degrau alto que pode ser o único lido.
GANHOS = (0.12, 0.25, 0.45, 0.80)
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
# De longe a escada de ganho vai no 16-FSK lento, na mesma forma do degrau
# LENTO (20 baud, guarda 0,3, marca longa): a 100 baud ela nunca era lida de
# longe (2026-10-22), e o contrato saía com ganho e degrau no chute. Assim o
# receptor mede o lento de fato -- a velocidade passa a ser negociada como o
# ganho. Só os três ganhos de cima; o primeiro fica sem sonda (0,5).
SONDA_G_LONGE = tuple(None if i == 0 else
                      Descritor(tuple(MARY_TONES), 4, 1, SONDA_N, g, f'sonda lenta g{g}',
                                LENTO_BAUD, LENTO_GUARDA, LENTO_PRE, marca='quadro_longo')
                      for i, g in enumerate(GANHOS))
# E uma a 100 baud depois delas, fora da escada de ganho (`res[len(GANHOS)]`):
# "longe" é decidido pela chamada e vale para a sessão, mas os dois sentidos
# não precisam estar igualmente longe. Sem esta sonda o receptor nunca via se
# o sentido dele segura 100 baud, e contratava o lento num sentido que media
# 0-1% de bits errados (simulador, cenário 'assimetrico', 2026-10-23).
SONDA_RAPIDA_GANHO = 2                      # índice em GANHOS: 0,45
SONDA_G_LONGE += (Descritor(tuple(MARY_TONES), 4, 1, SONDA_N, GANHOS[SONDA_RAPIDA_GANHO],
                            f'sonda rápida g{GANHOS[SONDA_RAPIDA_GANHO]}'),)


def sonda_g(longe):
    return SONDA_G_LONGE if longe else SONDA_G_DESC

# Degraus de taxa, do mais rápido ao mais lento. Limiares de erro de bit
# (antes do FEC) a partir de CLAUDE.md: taxa 1/3 suave inteira até ~13%,
# repetida duas vezes até ~25%. Aqui com folga, porque três sondas por
# sentido são poucas e o contrato pode ser renegociado para baixo, nunca o
# contrário sem nova sondagem.
DEGRAUS = ('16-FSK rep1', '16-FSK rep2', '16-FSK rep4', '2-FSK rep1', '16-FSK lento',
           '16-FSK muito lento')
LENTO = 4
# O de longe (2026-10-22, alguns metros): no Linux->Windows o lento a rep2
# não passou nem em quadro de controle, e o muito lento (10 baud) passou.
MUITO_LENTO = 5
LIMIARES_BER = (0.07, 0.15, 0.25, 0.35, 0.40)
# Só nestes estados uma marca de sonda pode ser de verdade. Fora deles ela é
# um falso no meio de outra coisa, e lida como sondagem tirava de cena tudo o
# que viesse nos ~40 s seguintes (a duração de uma sondagem de longe): em
# 2026-10-23, em tempo real, uma no meio dos DADOS de A fez B perder os
# quadros seguintes e pedir degrau atrás de degrau até o 2-FSK.
ESPERA_SONDA = ('sondando', 'aguarda_sonda', 'aguarda_contrato')
MARGEM_FORA = -3.0           # dB, mediana das margens da sondagem: abaixo disto ela foi lida fora do lugar
LIMIAR_LENTO = 0.10          # erro de bit na sonda lenta abaixo disto: o lento serve

# Modulação dos dados (DADOS e ACK do canal aberto). 'auto' é a escada acima,
# que desce do 16-FSK para o 2-FSK e o lento conforme as falhas. Os outros
# fixam uma técnica só, para medir cada uma sozinha no mesmo link: a escada
# passa a mudar só a repetição, nunca a técnica, e uma técnica que não serve
# para a sala aparece como falha em vez de ser escondida pela troca. Saudação,
# sondagem e contrato são os mesmos em todos os modos -- só os dados mudam,
# para que a comparação seja justa. As duas pontas precisam do mesmo modo; o
# código dele vai num byte livre do CONTRATO (0 em 'auto', o mesmo byte de
# preenchimento de antes) e uma divergência fica escrita no diário.
MODOS_DADOS = ('auto', '16fsk', '2fsk', 'votada', 'multicanal')
DEGRAUS_MODO = {
    'auto': DEGRAUS,
    '16fsk': ('16-FSK rep1', '16-FSK rep2', '16-FSK rep4'),
    '2fsk': ('2-FSK rep1', '2-FSK rep2'),
    # 40 bytes a rep1 já são 11 s de 5x2 votada; rep2 passa de 20 s.
    'votada': ('5x2 votada rep1', '5x2 votada rep2'),
    'multicanal': ('5x2 multicanal rep1', '5x2 multicanal rep2', '5x2 multicanal rep4'),
}
_REPS_MODO = {'16fsk': (1, 2, 4), '2fsk': (1, 2), 'votada': (1, 2),
              'multicanal': (1, 2, 4)}


def _ordem_sonda(sessao):
    rng = np.random.RandomState(1000 + sessao)
    ordem = [k for k in range(len(GRADE)) for _ in range(SONDA_REPS)]
    rng.shuffle(ordem)
    return ordem


def carga_sonda_g(sessao, i):
    rng = np.random.RandomState(7919 * (sessao + 1) + i)
    return bytes([i]) + bytes(rng.randint(0, 256, SONDA_N - 6).astype(np.uint8))


def _tons_sonda(sessao, ganho=SONDA_GANHO_TOM):
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
    return np.concatenate(partes) * ganho


def _sonda_tons_nominal():
    return int(SONDA_SIL * FS) + len(GRADE) * SONDA_REPS * int(SONDA_PASSO * FS)


def modula_sonda(sessao, ganho_tons=SONDA_GANHO_TOM, longe=False):
    """`ganho_tons` só muda o nível dos tons, não o que se mede com eles: a
    margem de cada tom é contra o piso e contra os outros tons, todos no
    mesmo ganho. As sondas de ganho, depois, ficam nos ganhos da escada."""
    m = MOLDES['sonda']
    z = np.zeros(HUSH)
    partes = [m, z, _tons_sonda(sessao, ganho_tons), z, m, np.zeros(GAP)]
    for i, d in enumerate(sonda_g(longe)):
        if d is None:
            continue
        partes += [modula_quadro(d, empacota(SONDA_G, sessao, carga_sonda_g(sessao, i), SONDA_N)),
                   np.zeros(GAP)]
    return np.concatenate(partes)


def sonda_amostras(longe=False):
    return (2 * LQ + 2 * HUSH + _sonda_tons_nominal() + GAP
            + sum(d.amostras + GAP for d in sonda_g(longe) if d is not None))


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
        return cls(tons, ((v >> 25) & 31, (v >> 30) & 31), (v >> 35) & 3, (v >> 37) & 7)

    def descritor(self, degrau=None, nbytes=DADOS_N, modo='auto'):
        d = self.degrau if degrau is None else degrau
        g = GANHOS[self.ganho]
        if modo != 'auto':
            # Degrau é índice em DEGRAUS_MODO[modo]: só a repetição muda. O
            # ganho é o do contrato em todos; os tons são os do contrato no
            # 16-FSK e no 2-FSK e os MFSK_PAIRS fixos no 5x2.
            rep = _REPS_MODO[modo][d]
            nome = f'contrato {DEGRAUS_MODO[modo][d]} {nbytes}B'
            if modo == '16fsk':
                return Descritor(tuple(GRADE[k] for k in self.tons), 4, rep, nbytes, g, nome)
            if modo == '2fsk':
                return Descritor(tuple(GRADE[k] for k in self.par), 1, rep, nbytes, g, nome)
            k = len(MFSK_PAIRS)
            return Descritor(tuple(t for p in MFSK_PAIRS for t in p),
                             k if modo == 'multicanal' else 1, rep, nbytes, g, nome,
                             camada=modo)
        if d == 3:
            return Descritor(tuple(GRADE[k] for k in self.par), 1, 1, nbytes, g,
                             f'contrato 2-FSK {nbytes}B')
        if d == MUITO_LENTO:
            return Descritor(tuple(GRADE[k] for k in self.tons), 4, 2, nbytes, g,
                             f'contrato 16-FSK muito lento {nbytes}B',
                             10, LENTO_GUARDA, LENTO_PRE, marca='quadro_longo')
        if d == LENTO:
            # Marca longa: o lento é o degrau de longe, e lá a de 80 ms
            # fica rente ao limiar.
            return Descritor(tuple(GRADE[k] for k in self.tons), 4, 1, nbytes, g,
                             f'contrato 16-FSK lento {nbytes}B',
                             LENTO_BAUD, LENTO_GUARDA, LENTO_PRE, marca='quadro_longo')
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
    if top < 1 - LIMIARES_BER[-1]:
        # Nenhuma sonda lida (todas a 0,5 quando nem a marca foi achada): o
        # "menor ganho que acerta tanto quanto o melhor" seria o mais baixo,
        # o oposto do que um canal assim pede. De longe é o caso comum.
        gi = len(GANHOS) - 1
    ber, inteiro = sondas_g[gi]
    if ber < LIMIARES_BER[0] and inteiro:
        degrau = 0
    elif ber < LIMIARES_BER[1]:
        degrau = 1
    elif ber < LIMIARES_BER[2]:
        degrau = 2
    elif ber < LIMIARES_BER[3]:
        degrau = 3
    elif ber < LIMIARES_BER[4]:
        # Nem o 16-FSK a 100 baud foi lido com menos de 35% de erro: o canal
        # não segura símbolo de 10 ms. Começa no lento.
        degrau = LENTO
    else:
        degrau = MUITO_LENTO
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

    def varre(self, fixas=frozenset()):
        """Avança a varredura até onde o áudio permite; devolve as marcas novas.
        `fixas`: posições de marcas já usadas, que nenhuma outra substitui."""
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
                for i in np.flatnonzero(s >= LIMIARES[tipo]):
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
                # A curta e a longa de quadro são a mesma varredura em 80 e
                # 400 ms: uma correlaciona com a outra, e a curta apagava a
                # longa do OLA de longe (teste 12, 2026-10-22) -- o ouvinte
                # tentava lê-lo como quadro de perto. As duas ficam; quem
                # escolhe é a estação, pelo que o estado dela espera.
                rivais = [m for m in novas + self.marcas[-8:]
                          if m[0] >= r0 - L and abs(pos - m[0]) < int(0.15 * FS)
                          and {m[1], tipo} != set(QUADROS)]
                # Uma marca fraca guardada no pedaço anterior não pode calar
                # uma forte que só aparece neste: no H06 (sessão 3, 191,48 s)
                # um falso de 0,25 no fim de um ACK apagou a marca de
                # fechamento verdadeira, de 0,65, 123 ms depois, e o ACK nunca
                # foi lido. A forte substitui a fraca -- só se a fraca for de
                # quadro ou sonda (a chamada e a resposta já agiram em
                # `_marca`) e ainda não tiver sido usada por um segmento.
                fracas = [m for m in rivais if m in self.marcas and m[2] < sc
                          and m[1] in QUADROS + ('sonda',) and m[0] not in fixas]
                if len(fracas) != len(rivais):
                    continue
                for m in fracas:
                    self.marcas.remove(m)
                novas.append((pos, tipo, sc))
            self.varrido = r1
        novas.sort()
        self.marcas += novas
        return novas


# --- Estação ------------------------------------------------------------------

RESP = int(0.8 * FS)           # pausa antes de responder
# A vez de cada um. Só o chamador abre um turno; o ouvinte responde numa vez
# que as duas pontas calculam igual, contada do fim do turno do chamador:
# começa RESP_VEZ depois (mais o que leva ler um turno longo, e mais de
# longe), e se o ouvinte não estiver pronto até TOL_VEZ depois disso, cala e
# espera o próximo turno do chamador. O chamador, que sabe quando a vez do
# ouvinte começa e quanto ela pode durar, nunca fala dentro dela -- nem para
# repetir. Antes o ouvinte respondia quando acabava de ler, a qualquer hora,
# e o chamador repetia depois de um prazo com sorteio: no ar (2026-10-27) os
# dois falaram juntos.
RESP_VEZ = int(2.5 * FS)
TOL_VEZ = int(1.5 * FS)
LAT_OUTRO = int(1.5 * FS)      # latência de saída do outro lado, que daqui não se mede
FIM_TENTATIVAS = 3


def atraso_vez(n, esforco):
    """Do fim de um turno de `n` amostras do chamador ao começo da vez do
    ouvinte. Cresce com o turno porque a leitura cresce com ele (em
    2026-10-22, de longe, um turno de 75 s foi respondido ~6 s depois)."""
    return RESP_VEZ + n // 8 + 4 * FS * esforco
GUARDA = int(0.5 * FS)         # cegueira depois de tocar
ESPERA = int(3.0 * FS)         # quanto esperar o começo de uma resposta
# Quanto esperar outro segmento num turno. Tem de cobrir o atraso da
# varredura (PASSO + 2 moldes), senão o segmento seguinte -- que começa 0,1 s
# depois -- ainda não foi achado quando a folga vence. Era 1 s fixo; com a
# marca longa a varredura passou a andar ~1,3 s atrás, e em 2026-10-22 o
# chamador deu o turno por encerrado no meio da sondagem do outro lado e
# repetiu por cima dela.
FOLGA = Ouvido.PASSO + 2 * max(len(m) for m in MOLDES.values()) + int(0.5 * FS)
import os as _os
_DEPURA = bool(_os.environ.get('ENLACE_DEPURA'))
# Com o canal aberto, uma chamada só derruba a sessão se for forte: os dados
# 16-FSK chegam a 0,18 no molde da chamada, rente ao limiar dela (0,17), e um
# falso desses no meio de uma transferência reiniciava tudo.
# Era 0,30, acima da chamada de longe (0,18-0,27 em 2026-10-22): um canal que
# morria longe nunca era recomeçado pela chamada do outro lado. O silêncio
# exigido abaixo (SILENCIO_MORTO sem nada legível) já afasta os dados.
# Era 0,20, e no ar (2026-10-27, notebook da Giselle) as chamadas do chamador
# que recomeçou chegavam a ~0,18 de longe: o ouvinte, de canal aberto, não
# voltou nunca. O falso que motivou o limiar alto -- a varredura casando com
# um quadro de dados -- hoje cai antes, em "chamada dentro de outro som", e o
# silêncio exigido continua valendo; basta a chamada passar do limiar dela.
LIMIAR_RECOMECO = LIMIARES['chamada']
SILENCIO_MORTO = 90 * FS       # canal aberto sem nada legível: dado por morto (o muito lento leva 52 s por quadro de dados)


class Estacao:
    """Uma ponta do enlace. `papel` é 'chamador' ou 'ouvinte'.

    Uso: a cada pedaço de áudio, `ouvir(pedaço)` e depois `passo()`; se
    `passo` devolver amostras, tocá-las já. O relógio é o número de amostras
    ouvidas, e o que for tocado é tido como começando no instante atual.
    """

    def __init__(self, papel, semente=None, log=None, nome=None, modo_dados='auto'):
        assert papel in ('chamador', 'ouvinte')
        if modo_dados not in MODOS_DADOS:
            raise ValueError(f"modo de dados {modo_dados!r}; um de {MODOS_DADOS}")
        self.papel = papel
        self.modo_dados = modo_dados
        self.degraus = DEGRAUS_MODO[modo_dados]
        self.ultimo_degrau = len(self.degraus) - 1
        self.nome = nome or papel
        self.rng = np.random.default_rng(semente)
        self.ouvido = Ouvido()
        self._log = log or (lambda s: None)
        self.eventos = []          # (t, texto)
        self.recebido = bytearray()
        self.fila = bytearray()
        self.pendente_tx = None
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
        self.ouve_ate = 0          # o turno do outro lado não acaba antes disto
        self._terminal = False     # o último segmento lido fecha o turno
        self.outro_tem_mais = False  # o outro lado mandou DADOS: pode haver mais
        self.sondar_em = None      # chamador ocioso: próxima consulta ao outro lado
        self.turno_ultimo = 0      # fim do último segmento lido
        self._cursor = 0           # marcas antes disto já foram tratadas
        self._eco_janela = (0, 0)  # quando tocou a minha última varredura de saudação
        self.ultimo_turno = None   # o que eu toquei por último, para repetir
        self.espera_ate = None     # prazo para o começo de uma resposta
        self.tentativas = 0
        self.ab = 0                # abordagem de controle em uso
        self.esforco = 0           # índice em ORDEM_ABORDAGENS / GANHOS_CHAMADA
        self._chamou_fim = None    # fim da minha última chamada; resposta antes disso é falsa
        self.k_chamada = 0
        self.livre_em = 0          # fim do que estou tocando
        self.ouvido_em = -10 * FS  # última marca ouvida
        self._chamada_em = None    # a última chamada que respondi
        self._resp_len = 0         # duração prevista da resposta ao meu último turno
        self._usadas = set()       # marcas já lidas como parte de um segmento
        self.lat_extra = 0         # latência de saída não declarada, medida no próprio eco
        self._eco = None           # (tipo, início) da última varredura de saudação tocada
        self._niveis = []          # (instante, rms) de 0,25 s fora da cegueira, para o piso
        self._turno_ini = 0        # abertura do turno que está chegando
        self._lido_ini = 0         # abertura do último segmento lido
        self.encerrada = False     # despediu-se: tudo entregue nos dois sentidos
        self.fim_tentativas = 0    # FIMs mandados sem resposta
        self._piso = None
        self._nivel_em = 0
        self.reinicia()
        self.anota("tempos no ar: " + "; ".join(
            f"{d.nome} {d.segundos:.1f}s" for d in ABORDAGENS)
            + f"; sondagem {sonda_amostras() / FS:.1f}s")
        self.anota(f"modo de dados: {modo_dados} (degraus: {', '.join(self.degraus)}); "
                   "a outra ponta precisa do mesmo")

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
        self.encerrada = False
        self.fim_tentativas = 0

    def _toca(self, partes, depois=0, espera=True, guarda_turno=True, apos=None, eco=None):
        """Agenda um turno: segmentos separados por GAP, `depois` amostras
        após o fim do que chegou por último (ou a partir de `apos`)."""
        if self.encerrada:
            return
        s = []
        for p in partes:
            s += [p, np.zeros(GAP)]
        x = np.concatenate(s[:-1])
        quando = max(self.agora, (self.turno_ultimo if apos is None else apos) + depois)
        # Um turno novo substitui o que ainda espera a vez, nunca se soma a
        # ele: a decisão mais recente é a que vale, e dois turnos na fila
        # saem colados, o segundo por cima da resposta do outro lado (sessão
        # 3 do H06, A mandou o mesmo pedaço duas vezes seguidas). O que já
        # está tocando saiu da agenda em `passo` e não é tocado aqui.
        self.agenda = [(quando, x, eco)]
        if guarda_turno:
            self.ultimo_turno = partes
        # A resposta só começa depois que o outro lado varreu e decodificou o
        # que eu disse, e isso cresce com o tamanho do turno: em 2026-10-22, de
        # longe, um turno de 75 s no muito lento foi respondido ~6 s depois do
        # fim, e com a espera fixa de 3 s eu já repetia por cima da resposta.
        # De longe, mais 4 s: a varredura com a marca longa anda ~1,3 s atrás,
        # e no ar (2026-10-22) o Windows levou mais que os 5 s para começar a
        # responder a uma sondagem -- o chamador repetiu e embolou as duas.
        # E a resposta inteira, não só o começo dela: se a marca de abertura
        # se perder, é o comprimento previsto que impede falar por cima.
        self._resp_len = self._vez_do_outro()
        self.espera_ate = self._fim_da_vez(quando, len(x)) if espera else None

    def _fim_da_vez(self, a, n):
        """Até quando a resposta a um turno de `n` amostras tocado em `a` pode
        chegar: a vez do outro lado inteira, com a tolerância dele, a
        latência das duas saídas e a resposta mais longa que o estado admite.
        Antes disto, repetir seria falar por cima de uma resposta."""
        return (a + self.lat_extra + n + atraso_vez(n, self.esforco) + TOL_VEZ
                + LAT_OUTRO + self._resp_len + 2 * Ouvido.PASSO)

    def _minha_vez(self, partes, espera=True):
        """O ouvinte fala só na vez dele: a partir de RESP_VEZ (mais a leitura)
        depois do fim do turno do chamador, e nunca mais tarde que TOL_VEZ
        disso. Atrasado, cala -- o chamador repete o turno, e a vez volta."""
        if not self._terminal:
            # O fim do turno do chamador só se sabe ao certo pelo último
            # segmento dele, lido: um ilegível no fim deixa o instante em
            # aberto, e uma vez contada de um fim errado cairia em cima da
            # repetição dele. Calo; ele repete, e desce o degrau se preciso.
            self.anota("turno do chamador não lido até o fim; calo e espero a repetição")
            return False
        # O tamanho que conta para a leitura é o do último segmento lido, não
        # desde a primeira marca do turno: uma marca falsa (eco) antes dele
        # inflava a conta, a vez saía depois do prazo do chamador e ele
        # repetia por cima ('latencia', 2026-10-27). Menor nunca é perigoso:
        # a vez continua começando depois do fim de verdade do turno.
        n = max(0, self.turno_ultimo - max(self._turno_ini, self._lido_ini))
        quando = self.turno_ultimo + atraso_vez(n, self.esforco)
        if self.agora > quando + TOL_VEZ:
            self.anota(f"perdi a minha vez ({(self.agora - quando) / FS:.1f}s tarde); "
                       "calo e espero o chamador repetir")
            return False
        self._toca(partes, apos=quando, espera=espera)
        return True

    def _quadro(self, desc, tipo, carga, mais=False):
        return modula_quadro(desc, empacota(tipo, self.sessao, carga, desc.nbytes, mais))

    def _ganho_chamada(self):
        g = GANHOS_CHAMADA[self.esforco]
        self.k_chamada += 1
        return g[(self.k_chamada - 1) % len(g)]

    def _sobe_esforco(self, porque):
        if self.esforco + 1 < len(ORDEM_ABORDAGENS):
            self.esforco += 1
            self.anota(f"{porque}; esforço de longe: abordagens "
                       f"{', '.join(ABORDAGENS[i].nome for i in ORDEM_ABORDAGENS[self.esforco])}, "
                       f"chamada e tons da sondagem em {GANHOS_CHAMADA[self.esforco][0]}")
            return True
        return False

    def _sonda(self):
        return modula_sonda(self.sessao, SONDA_GANHO_LONGE if self.esforco else SONDA_GANHO_TOM,
                            longe=bool(self.esforco))

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
        if self._eco_janela[1] > self.agora:
            self._eco_janela = (self._eco_janela[0] + n, self._eco_janela[1] + n)
        a, b = self.ouvido.cegos[-1]
        self.ouvido.cegos[-1] = (a + n, b + n)
        self.livre_em += n
        if self.espera_ate is not None:
            self.espera_ate += n
        if self._chamou_fim is not None and self._chamou_fim > self.agora:
            self._chamou_fim += n          # a chamada que acabou de sair

    def ouvir(self, x):
        self.ouvido.acrescenta(x)

    def _mede_piso(self):
        """Piso de ruído: percentil 10 do rms de 0,25 s dos últimos 120 s
        (mais longo que um quadro muito lento, que tem 52 s)."""
        if self.agora - self._nivel_em < FS // 4:
            return
        self._nivel_em = self.agora
        r = self._rms_valido(self.agora - FS // 4, self.agora)
        if r is None:
            return
        self._niveis = [(t, v) for t, v in self._niveis if t > self.agora - 120 * FS]
        self._niveis.append((self.agora, r))
        if len(self._niveis) >= 8:
            self._piso = float(np.percentile([v for _, v in self._niveis], 10))

    def _ocupado(self):
        """Escutar antes de falar: o outro lado ainda está tocando? Não diz
        o quê nem se dá para ler -- só que há som acima do piso. Em 2026-10-22,
        de longe, três vezes uma ponta deu o turno do outro por encerrado
        (quadro ilegível, marca seguinte abaixo do limiar) e repetiu por cima
        dele. Longe o sinal chega só ~4-6 dB acima do piso, daí 1,5x."""
        if not self._piso:
            return False
        r = self._rms_valido(self.agora - FS // 2, self.agora)
        return r is not None and r > 1.5 * self._piso

    def passo(self):
        self._mede_piso()
        fixas = set(self._usadas)
        if self.pendente is not None:
            fixas.add(self.pendente['pos'])
        for pos, tipo, sc in self.ouvido.varre(fixas):
            self._marca(pos, tipo, sc)
        self._le_segmentos()
        if (self.turno_fim is not None and self.agora >= self.turno_fim
                and not self._terminal and self.ouvido.varrido < self.ouve_ate + FOLGA):
            pass                          # pela máquina de estados, o outro lado ainda fala
        elif (self.turno_fim is not None and self.agora >= self.turno_fim
                and self._ocupado() and self.agora < self.turno_fim + 60 * FS):
            pass                          # ainda chega som: o turno não acabou
        elif self.turno_fim is not None and self.agora >= self.turno_fim:
            if _DEPURA:
                self.anota(f"  fim de turno: terminal={self._terminal}, varrido "
                           f"{self.ouvido.varrido / FS:.2f}s, ouve_ate {self.ouve_ate / FS:.2f}s")
            turno, self.turno, self.turno_fim = self.turno, [], None
            self._turno(turno)
            self._terminal = False         # vale para o turno que acabou de ser tratado
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
                # A varredura não é apagada, e alta no próprio microfone ela
                # dá marca de quadro falsa (teste 11, 2026-10-22: o ouvinte
                # passava 10 s lendo um quadro que não existia e perdia o OLA).
                self._eco_janela = (a, a + self.lat_extra + len(x) + GUARDA)
                if eco == 'chamada':
                    self._chamou_fim = a + len(x)
            else:
                # Desde o instante em que toca, não desde a latência medida:
                # a de um alto-falante Bluetooth varia (0,5 a 0,7 s medidos
                # em 2026-10-27), e quando saía mais cedo que a medida a
                # marca de abertura escapava da cegueira e a estação abria
                # "o turno do outro" sobre o próprio quadro (no ar, sessão 6,
                # três esperas de 40-55 s). Com as vezes, o outro lado não
                # fala enquanto eu toco, então começar cedo não custa nada.
                self.ouvido.cego(a, a + self.lat_extra + len(x) + GUARDA)
            if self.espera_ate is not None:
                self.espera_ate = max(self.espera_ate, self._fim_da_vez(a, len(x)))
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
        if tipo == 'chamada' and self.papel == 'ouvinte' and self._piso:
            r = self._rms_valido(pos - FS // 2, pos)
            if r is not None and r > 1.5 * self._piso:
                # Uma chamada de verdade começa no silêncio: o chamador só chama
                # depois de esperar. Achada no meio de outro som, é a varredura
                # casando com um pedaço do quadro do chamador, e responder a ela
                # seria falar por cima dele ('assimetrico', semente 2: 0,20
                # dentro de um quadro de dados, duas vezes).
                if _DEPURA:
                    self.anota(f"  chamada dentro de outro som ignorada ({sc:.2f})")
                return
        if tipo == 'chamada':
            if self.papel == 'ouvinte' and self.aberto and sc >= LIMIAR_RECOMECO and \
                    self.agora - self.progresso_em > SILENCIO_MORTO:
                # Recomeça, mas não responde a esta: se for mesmo o chamador
                # recomeçando, ele chama de novo em seguida.
                self.anota("chamada nova com o canal mudo há tempo; o outro lado "
                           "recomeçou -- recomeço também")
                self.reinicia()
                return
            if self.papel == 'ouvinte' and not self.aberto and self.saudado:
                # No meio da negociação. Com o limiar da chamada rente ao
                # falso (0,17), os tons da sondagem chegam a 0,20 nela; se o
                # outro lado de fato recomeçou, os prazos de 'aguarda_*'
                # devolvem esta ponta à escuta e a chamada seguinte é ouvida.
                return
            if (self.papel == 'ouvinte' and not self.aberto and self._chamada_em is not None
                    and pos - self._chamada_em < 2 * len(MOLDES['chamada']) + RESP + ESPERA):
                # O chamador só chama de novo depois de esperar a minha
                # resposta inteira; antes disso não é chamada, é o eco da
                # minha própria resposta. Em 2026-10-22 (teste 8) uma dessas,
                # a 0,17, foi respondida, e a segunda resposta caiu em cima
                # do OLA.
                if _DEPURA:
                    self.anota(f"  chamada cedo demais ignorada ({sc:.2f})")
                return
            if self.papel == 'ouvinte' and not self.aberto:
                self._chamada_em = pos
                self.anota(f"chamada ouvida (correlação {sc:.2f})")
                if sc < LIMIAR_LONGE and self.esforco == 0:
                    self._sobe_esforco(f"chamada fraca ({sc:.2f} < {LIMIAR_LONGE})")
                g = self._ganho_chamada()
                self.turno_ultimo = pos + len(MOLDES['chamada'])
                self._toca([MOLDES['resposta'] * g], depois=RESP, espera=False,
                           guarda_turno=False, eco='resposta')
                self.estado = 'aguarda_ola'
                self.espera_ate = self.agora + 20 * FS
        elif tipo == 'resposta':
            if self.estado == 'chamando' and self.papel == 'chamador':
                if self._chamou_fim is None or pos < self._chamou_fim:
                    # Resposta a uma chamada que ainda não terminou -- ou que
                    # nem saiu. Em 2026-10-22 um estalo no início da gravação
                    # deu 0,20 no molde da resposta antes da primeira
                    # chamada, e o chamador passou 100 s mandando OLA a
                    # quem nunca o tinha ouvido.
                    if _DEPURA:
                        self.anota(f"  resposta fora de hora ignorada ({sc:.2f} em {pos / FS:.2f}s)")
                    return
                if sc < LIMIAR_LONGE and self.esforco == 0:
                    self._sobe_esforco(f"resposta fraca ({sc:.2f} < {LIMIAR_LONGE})")
                self.ab = ORDEM_ABORDAGENS[self.esforco][0]
                self.anota(f"resposta ouvida (correlação {sc:.2f}); enviando OLA "
                           f"em {ABORDAGENS[self.ab].nome}")
                self.sessao = int(self.rng.integers(1, 256))
                self.turno_ultimo = pos + len(MOLDES['resposta'])
                self.estado = 'ola'
                self.tentativas = 0
                self._envia_ola()
        # quadro e sonda viram segmentos, lidos quando o áudio deles chegar

    def _candidatos(self, marca=None):
        """Descritores que podem estar no ar agora, por ordem de chance; só
        os abertos pela `marca` dada, se houver -- a marca de abertura já diz
        se o quadro é de perto ou de longe."""
        c = list(ABORDAGENS)
        if self.contrato_rx is not None:
            # Só a escada do meu modo: as duas pontas rodam o mesmo, e um
            # comprimento de 5x2 que caísse perto de um de 16-FSK só custaria
            # leituras a mais, nunca uma leitura errada (o CRC decide).
            for d in range(self.ultimo_degrau + 1):
                for n in (DADOS_N, CTRL_N):
                    c.append(self.contrato_rx.descritor(d, n, self.modo_dados))
        return [d for d in c if marca is None or d.marca == marca]

    def _le_segmentos(self):
        while True:
            if self.pendente is None:
                prox = [m for m in self.ouvido.marcas
                        if (m[1] in QUADROS or (m[1] == 'sonda' and self.estado in ESPERA_SONDA))
                        and m[0] >= max(self._cursor, self.turno_ultimo if not self.turno else 0)
                        and not self._eco_janela[0] <= m[0] < self._eco_janela[1]
                        and m[0] not in self._usadas]
                quero = 'quadro_longo' if self.esforco else 'quadro'
                # Só entre as duas de quadro: a de sondagem não tem par, e
                # apagá-la por uma de quadro falsa ao lado fazia a sondagem
                # inteira ser lida como quadros ilegíveis ('limpo', 2026-10-23).
                prox = [m for m in prox if m[1] == quero or m[1] not in QUADROS or not any(
                    o[1] == quero and abs(o[0] - m[0]) < FS // 2 for o in prox)]
                if not prox:
                    return
                if self.turno and self._terminal:
                    # O turno já acabou: o segmento que o fecha foi lido. Uma
                    # marca logo depois é de outro turno -- ou falsa -- e não
                    # entra neste; antes ela virava um ilegível no fim dele e
                    # o ouvinte calava ("não lido até o fim"), a cada
                    # repetição: no ar (2026-10-27, notebook da Giselle), a
                    # sala dava 12 ilegíveis por turno e a sessão não fechou.
                    return
                pos, tipo, _ = prox[0]
                if tipo in QUADROS and tipo != quero and self.ouvido.varrido < pos + FS // 2:
                    return                 # a marca que o estado espera pode estar logo atrás
                if tipo in QUADROS:
                    dur = max(d.amostras for d in self._candidatos(tipo))
                else:
                    dur = sonda_amostras(bool(self.esforco))
                self.pendente = dict(pos=pos, tipo=tipo, tentou=set(),
                                     prazo=pos + int(dur * 1.006) + SPS)
                if not self.turno:
                    # Abertura de um turno novo: ele dura o que a máquina de
                    # estados diz, leia-se o meio dele ou não (ver também
                    # `_segmento`, que corrige isto se a abertura era falsa).
                    self._turno_ini = pos
                    self.ouve_ate = pos + int(self._vez_do_outro() * 1.006)
                    if _DEPURA:
                        self.anota(f"  turno do outro aberto em {pos / FS:.2f}s ({tipo}), estado "
                                   f"{self.estado}: ouço até {self.ouve_ate / FS:.2f}s")
                self.turno_fim = None              # outro segmento do mesmo turno
            p = self.pendente
            if p['tipo'] in QUADROS:
                # O prazo vale sobre o áudio já varrido, não sobre o presente: a
                # varredura anda ~0,9 s atrás, e um prazo contado do presente
                # lia pela abertura antes de a marca de fechamento -- que cai
                # justo no fim do candidato mais longo -- ter sido procurada.
                if not self._tenta_quadro(p, final=self.ouvido.varrido >= p['prazo']):
                    return
            else:
                if self.agora < p['prazo']:
                    return
                self._le_sonda(p['pos'])
            self._usadas.add(p['pos'])
            self.pendente = None

    def _fechamento(self, p1, dur, marca='quadro'):
        """A marca de quadro que fecha um quadro aberto em p1 com duração
        nominal `dur`, se houver uma onde deve estar (±0,4%)."""
        alvo = p1 + dur - len(MOLDES[marca])
        tol = int(0.004 * dur)
        for pos, tipo, _ in self.ouvido.marcas:
            if tipo == marca and pos != p1 and abs(pos - alvo) <= tol:
                return pos
        return None

    def _tenta_quadro(self, p, final):
        """Tenta ler o quadro pendente. Cada candidato é lido assim que a sua
        marca de fechamento chega -- um quadro de controle de 4 s não espera
        o prazo do quadro mais lento possível (10 s). No prazo, os que não
        tiveram fechamento são lidos só pela abertura, com relógio nominal.
        Devolve True quando o segmento está resolvido, lido ou não."""
        p1 = p['pos']
        if self._le_candidatos(p, nominal=final):
            return True
        # Uma marca de fechamento caiu exatamente onde um dos comprimentos
        # previstos termina e a leitura falhou: o quadro tem esse comprimento
        # e está ilegível. Esperar o prazo do candidato mais lento (10 s)
        # para tentar os outros só pela abertura atrasava o veredito tanto
        # que as repetições do outro lado se empilhavam na fila.
        lidos_com_fecho = [q2 for (_, q2) in p['tentou'] if q2 is not None]
        if not final and not lidos_com_fecho:
            if not self._calou(p1, p['tipo']):
                return False
            # Calou antes do prazo: o quadro acabou, e cabe no que já chegou.
            # Ler pela abertura, com relógio nominal, como no prazo -- sem
            # isto o veredito saía sem leitura nenhuma (`tentou=[]`): no H06,
            # sessão 2, um OLA 2-FSK cuja marca de fechamento chegou 29 ms
            # fora da tolerância nunca foi lido.
            if self._le_candidatos(p, nominal=True):
                return True
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

    def _le_candidatos(self, p, nominal):
        """Lê o quadro pendente em cada candidato: pela marca de fechamento
        quando ela chegou, e só pela abertura (relógio nominal) se `nominal`.
        Cada (candidato, fechamento) é tentado uma vez. True se um passou no
        CRC; nesse caso o segmento já foi registrado.

        Primeiro todos os que têm fechamento, depois os nominais, do mais
        longo ao mais curto. A ordem importa porque um quadro pode conter
        outro mais curto que passa no CRC: no 5x2 multicanal, `pair_map` põe
        a cópia 0 inteira nos primeiros símbolos, então a cabeça de um rep4 é
        um rep1 válido. Lido como rep1, o quadro "acaba" 6 s antes do fim de
        verdade e a resposta sai por cima de quem ainda está tocando --
        observado no simulador, a troca virou um laço de repetições e a sessão
        recomeçou, entregando um pedaço duas vezes. A marca de fechamento é a
        prova do comprimento; sem ela, errar para o mais longo só atrasa a
        resposta, errar para o mais curto colide."""
        p1 = p['pos']
        cands = self._candidatos(p['tipo'])
        lq = len(MOLDES[p['tipo']])
        tentativas = []
        for d in cands:
            p2 = self._fechamento(p1, d.amostras, p['tipo'])
            if p2 is not None and self.agora >= p2 + lq + SPS:
                tentativas.append((d, p2))
        if nominal:
            for d in sorted(cands, key=lambda d: -d.amostras):
                if self.agora >= p1 + d.amostras + SPS:
                    tentativas.append((d, None))
        for d, q2 in tentativas:
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
                               (q2 + lq) if q2 is not None else p1 + d.amostras, inicio=p1)
                return True
        return False

    def _calou(self, p1, marca='quadro'):
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
        curto = min(d.amostras for d in self._candidatos(marca))
        if ate < p1 + int(0.99 * curto):
            return False
        # E só sobre o que não é cegueira: o que a própria estação tocou é
        # zerado na entrada, e zero lido como silêncio declarava "calou" com
        # o outro lado tocando. No H06, sessão 3, isto fez 5 vereditos sem
        # leitura nenhuma, três com a janela 100% cega, e cada um virou uma
        # resposta por cima do quadro do outro lado. Janela quase toda cega:
        # não se sabe, e "não sei" não é silêncio.
        ini = p1 + len(MOLDES[marca]) + HUSH
        ref = self._rms_valido(ini, ini + FS // 2)
        rec = self._rms_valido(ate - int(0.4 * FS), ate)
        if ref is None or rec is None:
            return False
        return rec < 0.3 * ref

    def _rms_valido(self, a, b):
        """rms das amostras fora da cegueira em [a, b), ou None se mais da
        metade do trecho for cega."""
        inv = self.ouvido._invalido(a, b)
        if inv.mean() > 0.5:
            return None
        x = self.ouvido.trecho(a, b)[~inv]
        return float(np.sqrt(np.mean(x ** 2)))

    def _le_sonda(self, p1):
        dur_tons = 2 * LQ + 2 * HUSH + _sonda_tons_nominal()
        alvo = p1 + dur_tons - LQ
        p2 = None
        for pos, tipo, _ in self.ouvido.marcas:
            if tipo == 'sonda' and pos != p1 and abs(pos - alvo) <= int(0.004 * dur_tons):
                p2 = pos
                self._usadas.add(pos)
        longe = bool(self.esforco)
        if _DEPURA:
            sm = [(round(pos / FS, 2), round(sc, 2)) for pos, tipo, sc in self.ouvido.marcas
                  if tipo == 'sonda' and abs(pos - p1) < 60 * FS]
            self.anota(f"  sonda em {p1 / FS:.2f}s, fechamento "
                       f"{'não achado' if p2 is None else f'em {p2 / FS:.2f}s'}; marcas de sonda {sm}")
        audio = self.ouvido.trecho(p1, p1 + sonda_amostras(longe) + FS)
        margem = mede_tons(audio, 0, None if p2 is None else p2 - p1, self.sessao)
        r = 1.0 if p2 is None else (p2 - p1) / (dur_tons - LQ)
        # As sondas de ganho, em posições conhecidas depois da marca final.
        res = []
        q = int(round(dur_tons * r)) + int(GAP * r)
        for i, d in enumerate(sonda_g(longe)):
            if d is None:
                res.append((0.5, False))
                continue
            perto = [pos - p1 for pos, tipo, _ in self.ouvido.marcas
                     if tipo == d.marca and abs(pos - p1 - q) <= int(0.03 * FS)]
            ber, inteiro = 0.5, False
            if perto:
                s1 = perto[0]
                self._usadas.add(p1 + s1)
                fecho = [pos - p1 for pos, tipo, _ in self.ouvido.marcas
                         if tipo == d.marca
                         and abs(pos - p1 - s1 - (d.amostras - d.lm)) <= int(0.004 * d.amostras)]
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
        fim = p1 + sonda_amostras(longe)
        if np.median(margem) < MARGEM_FORA and not any(ok for _, ok in res):
            # Os tons enviados chegaram mais fracos que os não enviados, e
            # nenhuma sonda de ganho foi achada: não é um canal ruim (num
            # canal ruim as margens caem para perto de zero, não abaixo), é
            # a sondagem lida a partir da marca errada. Contratar com isso
            # deu ganho 0,8 e muito lento num canal limpo (2026-10-23, a
            # regressão de ebda203). Conta como ilegível e espera a repetição.
            self.anota(f"sondagem fora do lugar (margem mediana {np.median(margem):.0f} dB, "
                       f"nenhuma sonda de ganho achada); tratada como ilegível")
            self._segmento(('ilegivel', p1), fim)
            return fim
        self._segmento(('sonda', margem, res, longe), fim, inicio=p1)
        return fim

    def _segmento(self, ev, fim, inicio=None):
        if ev[0] != 'ilegivel' and inicio is not None:
            self._lido_ini = inicio        # abertura do último segmento lido
        if (inicio is not None and ev[0] != 'ilegivel'
                and all(e[0] == 'ilegivel' for e in self.turno)):
            # O primeiro segmento lido do turno é a abertura de verdade; as
            # ilegíveis antes dele podem ter sido marcas falsas. O prazo do
            # turno conta daqui, e só cresce. Em 2026-10-23 (simulador,
            # 'assimetrico', semente 1) o eco curto da marca longa que fecha o
            # OLA_OK, 80 ms depois do fim dele, abriu "o turno de B" 30 s antes
            # de B falar, e A encerrou o turno de verdade com o CONTRATO lido e
            # a sondagem atrás dele não. Só no lido: re-ancorar a cada
            # ilegível alongava a espera a cada marca falsa ('longe', 350 s
            # para 514 s).
            self.ouve_ate = max(self.ouve_ate, inicio + int(self._vez_do_outro() * 1.006))
        self.turno.append(ev)
        self.turno_ultimo = max(self.turno_ultimo, fim)
        # Lido, o quadro ocupa até o fim; ilegível, não se sabe o
        # comprimento, e as marcas que chegaram enquanto se tentava lê-lo
        # continuam valendo. Antes o cursor ia para "agora" e pulava a marca
        # do OLA verdadeiro que começara durante a leitura de um falso.
        self._cursor = ev[1] + 1 if ev[0] == 'ilegivel' else max(self._cursor, fim)
        if ev[0] == 'ilegivel' and self.turno and self._terminal:
            return                         # o turno já fechou no lido; ver `_le_segmentos`
        ultimo = (ev[0] == 'sonda'
                  or (ev[0] == 'quadro' and not abre(ev[1])[1]))
        self._terminal = ultimo
        self.turno_fim = self.agora if ultimo else self.agora + FOLGA

    def _vez_do_outro(self):
        """Quanto dura o turno que o outro lado manda em seguida, pelo estado
        em que estou. As duas pontas rodam a mesma máquina de estados, então
        isso se sabe sem ouvir nada -- e é o que separa as vezes de falar.
        Antes, um turno acabava por evento (FOLGA depois do último segmento
        lido) e uma marca perdida no meio dele o encerrava cedo: em
        2026-10-22, de longe, o CONTRATO de B chegou ilegível, a marca da
        sondagem que vinha atrás não foi achada, e A repetiu a própria
        sondagem por cima da de B (testes 5, 6 e 7). Na dúvida, o mais longo
        possível: esperar demais só atrasa, falar cedo colide."""
        e = self.estado
        if e == 'ola':
            # O OLA_OK vem na abordagem de longe se o outro lado se achar
            # longe, o que ele pode decidir sozinho.
            return max(ABORDAGENS[j].amostras for j in ORDEM_ABORDAGENS[-1] + (self.ab,))
        if e == 'sondando':
            return self.ctrl.amostras + GAP + sonda_amostras(bool(self.esforco))
        if e == 'aguarda_sonda':
            return sonda_amostras(bool(self.esforco))
        if e == 'aguarda_contrato':
            d = self.contrato_rx.descritor(self._degrau_inicial(self.contrato_rx),
                                           DADOS_N, self.modo_dados)
            return self.ctrl.amostras + GAP + d.amostras
        if self.aberto and self.contrato_rx is not None:
            # Um quadro só; o outro lado pode ter descido um degrau desde o
            # último que li (por silêncio, ou acompanhando o meu pedido).
            k = min(self.degrau_rx + 1, self.ultimo_degrau)
            return self.contrato_rx.descritor(k, DADOS_N, self.modo_dados).amostras
        return 0

    # --- prazos

    def _prazos(self):
        if self.encerrada:
            return
        if self.aberto and self.agora - self.progresso_em > 3 * SILENCIO_MORTO:
            # Nem a chamada de quem recomeçou foi ouvida com força (ver
            # LIMIAR_RECOMECO): sem nada legível por tanto tempo, recomeço
            # sozinho em vez de esperar para sempre num canal morto.
            self.anota("canal aberto sem nada legível há muito tempo; recomeçando")
            self.reinicia()
            return
        if (self.aberto and self.confirmado and self.papel == 'chamador'
                and self.pendente_tx is None and self.ocioso()
                and self.agora - self.ouvido_em > 2 * FS
                and (self.fila or self.outro_tem_mais
                     or (self.sondar_em is not None and self.agora >= self.sondar_em))):
            # Só o chamador abre uma troca no canal aberto; o ouvinte só
            # responde, e manda o que tem dentro da resposta. Com os dois
            # podendo começar, os dois começavam juntos. Ocioso, o chamador
            # ainda consulta de tempos em tempos, para o ouvinte poder falar.
            self.sondar_em = None
            self._toca(self._turno_dados(), apos=self.agora)
            return
        if self.estado == 'chamando':
            if self.espera_ate is None and self.agora >= self.proxima_chamada and not self.agenda:
                g = self._ganho_chamada()
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
        if self._ocupado():
            # Algo ainda soa: não repito por cima. O piso se adapta em ~2 min,
            # então um ruído novo e constante não trava isto para sempre.
            return
        # Prazo vencido sem resposta.
        self.espera_ate = None
        if self.estado == 'ola':
            self.tentativas += 1
            ordem = ORDEM_ABORDAGENS[self.esforco]
            if self.tentativas >= len(ordem):
                # Repetir o mesmo rodízio no mesmo volume não leva a nada
                # que a primeira volta não tenha levado: sobe o esforço.
                if self._sobe_esforco("OLA sem resposta em todas as abordagens"):
                    self.tentativas = 0
                    self.ab = ORDEM_ABORDAGENS[self.esforco][0]
                    self._envia_ola()
                    return
                self.anota("OLA sem resposta em todas as abordagens; voltando a chamar")
                self.reinicia()
                return
            self.ab = ordem[self.tentativas % len(ordem)]
            self.anota(f"sem OLA_OK; tentando {ABORDAGENS[self.ab].nome}")
            self._envia_ola()
        elif self.fim_tentativas and self.aberto and self.papel == 'chamador':
            if self.fim_tentativas >= FIM_TENTATIVAS:
                # Tudo já tinha sido entregue e confirmado antes do FIM; o
                # que se perdeu foi só a despedida. Não há o que esperar.
                self.anota(f"{self.fim_tentativas} FIM sem resposta; tudo já estava "
                           "entregue -- encerro")
                self.encerrada = True
                return
            self.fim_tentativas += 1
            self.anota(f"FIM sem resposta; repito ({self.fim_tentativas}/{FIM_TENTATIVAS})")
            self._toca(self._turno_fim(), apos=self.agora)
        elif self.estado == 'sondando' or (self.aberto and self.papel == 'chamador'):
            self._sem_resposta()
        elif self.estado in ('aguarda_sonda', 'aguarda_contrato') and self.tentativas < 3:
            # O turno do outro lado chegou ilegível (ou não chegou): ele vai
            # repeti-lo, que é o que faz quem fala ao não ouvir resposta.
            # Desistir aqui jogava fora a saudação inteira -- observado no ar
            # em 2026-10-08, um CONTRATO lento perdido uma vez e a sessão
            # voltou à estaca zero enquanto o outro lado ainda repetia.
            self.tentativas += 1
            self.anota(f"nada legível em '{self.estado}'; esperando a repetição "
                       f"({self.tentativas}/3)")
            self.espera_ate = self.agora + 2 * max(d.amostras for d in self._candidatos()) + ESPERA
        elif self.estado in ('aguarda_ola', 'aguarda_sonda', 'aguarda_contrato'):
            self.anota(f"nada mais em '{self.estado}'; voltando a escutar")
            self.reinicia()

    def _sem_resposta(self):
        """O turno ficou sem resposta lida: conta, desce o degrau se for
        o caso e repete. Um caminho só, venha do prazo vencido ou de um
        turno ilegível que chegou depois dele -- antes o segundo repetia
        sem descer, e com o ouvinte calado (ele não fala sobre o que não
        leu) a escada nunca descia ('assimetrico', semente 1)."""
        self.tentativas += 1
        self.sem_progresso += 1
        if self.tentativas > 8 or self.sem_progresso > 10:
            self.anota(f"sem resposta em '{self.estado}'; voltando ao começo")
            self.reinicia()
            return
        if self.aberto and self.confirmado and self.tentativas % 2 == 0 \
                and self.degrau_tx < self.ultimo_degrau:
            # Silêncio não é falha que o receptor possa contar: se nem a
            # marca foi achada, ele não sabe que falei. Quem desce o
            # degrau, então, sou eu; o receptor tenta todos os degraus
            # pelo comprimento do quadro, sem precisar ser avisado.
            self.degrau_tx += 1
            self.anota(f"duas repetições sem resposta; desço para {self.degraus[self.degrau_tx]}")
            if self.degrau_rx < self.ultimo_degrau:
                # O silêncio pode ser eu que não ouço o outro lado: o
                # ouvinte não repete por conta própria, então o pedido
                # para ele descer também tem de partir daqui.
                self.degrau_rx += 1
                self.anota(f"e peço {self.degraus[self.degrau_rx]} ao outro lado")
        self.anota(f"sem resposta em '{self.estado}'; repetindo o turno")
        # Já depois da vez inteira do ouvinte (o prazo é o fim dela), e
        # sem sorteio: só o chamador abre turnos, não há com quem
        # desempatar.
        self._toca(self._retransmite(), apos=self.agora)

    def _retransmite(self):
        if self.aberto and self.confirmado:
            # Reconstruído, não repetido: o ack e o pedido de degrau podem ter
            # mudado desde a última vez.
            return self._turno_dados(forcar=True)
        if self.aberto and self.contrato_tx is not None:
            # O turno do contrato ficou sem resposta. O CONTRATO foi na
            # abordagem de controle, e o outro lado pode tê-lo perdido mesmo
            # lendo os DADOS que vinham atrás -- no ar, em 2026-10-22, A
            # repetiu o mesmo turno por 70 s a um B preso em
            # 'aguarda_contrato' que logava "turno: ['DADOS']" a cada vez.
            # Repetido, ele vai no formato do contrato que o outro lado mediu
            # para este sentido e já procura (`_candidatos`, CTRL_N), que é o
            # que provou passar.
            d = self.contrato_tx.descritor(self.degrau_tx, CTRL_N, self.modo_dados)
            return ([self._quadro(d, CONTRATO, self.contrato_rx.empacota() + self._byte_modo(),
                                  mais=True)]
                    + self._turno_dados(forcar=True, so_partes=True))
        return self.ultimo_turno

    # --- fases

    def _envia_ola(self):
        d = ABORDAGENS[self.ab]
        self._toca([self._quadro(d, OLA, bytes([self.ab, self.esforco]))], depois=RESP)

    def _turno(self, eventos):
        if self.encerrada:
            # Despediu-se: não responde a mais nada. No ar (sessão 6) o
            # chamador encerrado leu ilegíveis, "pediu degrau" e voltou a
            # tocar; o ouvinte respondeu a um ACK depois do próprio FIM.
            return
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
                # A abordagem vem pelo índice que o OLA carrega, e com ela o
                # esforço de quem chamou. Se qualquer uma das pontas se acha
                # longe, as duas passam a falar de longe daqui em diante: a
                # distância vale para os dois sentidos, e uma ponta que
                # respondesse de perto a quem fala de longe não seria ouvida.
                i = carga[0] if carga[0] < len(ABORDAGENS) else ABORDAGENS.index(d)
                if self.esforco == 0 and (i in ORDEM_ABORDAGENS[1] or carga[1]):
                    self._sobe_esforco("o OLA veio de quem está longe")
                if self.esforco and i not in ORDEM_ABORDAGENS[1]:
                    i = ORDEM_ABORDAGENS[1][0]
                self.ctrl = ABORDAGENS[i]
                self.saudado = True
                self.estado = 'aguarda_sonda'
                self.anota(f"OLA lido em {d.nome}; saudação concluída, respondendo OLA_OK "
                           f"em {self.ctrl.nome}")
                self._minha_vez([self._quadro(self.ctrl, OLA_OK, bytes([i, self.esforco]))])
                return
        quadros = [(q, d) for q, d in quadros if q[2] == self.sessao]
        tipos = {q[0]: (q, d) for q, d in quadros}

        if self.estado == 'ola':
            if OLA_OK in tipos:
                i, esf = tipos[OLA_OK][0][3][:2]
                if esf and self.esforco == 0:
                    self._sobe_esforco("o OLA_OK veio de quem está longe")
                # A abordagem em que o outro lado respondeu, que é a de longe
                # se qualquer um dos dois estiver longe.
                self.ctrl = ABORDAGENS[i] if i < len(ABORDAGENS) else tipos[OLA_OK][1]
                self.saudado = True
                self.tentativas = 0
                self.anota(f"OLA_OK lido em {self.ctrl.nome}; saudação concluída, sondando")
                self.estado = 'sondando'
                self._toca([self._sonda()], depois=RESP)
            return

        if self.estado == 'aguarda_sonda' or (self.estado == 'aguarda_contrato'
                                               and sondas and CONTRATO not in tipos):
            if sondas:
                self.contrato_rx = self._contrato_de(sondas[0], "chega")
                self.estado = 'aguarda_contrato'
                self.tentativas = 0
                self._minha_vez([self._quadro(self.ctrl, CONTRATO,
                                              self.contrato_rx.empacota() + self._byte_modo(),
                                              mais=True),
                                 self._sonda()])
            return

        if self.estado == 'sondando':
            if CONTRATO in tipos and sondas:
                self.contrato_tx = Contrato.abre(tipos[CONTRATO][0][3])
                self._confere_modo(tipos[CONTRATO][0][3])
                self.anota(f"contrato para o que EU envio: {self.contrato_tx.descreve()}")
                self.contrato_rx = self._contrato_de(sondas[0], "chega")
                self.estado = 'contratando'
                self.tentativas = 0
                self._abre_canal()
                self._toca([self._quadro(self.ctrl, CONTRATO, self.contrato_rx.empacota() + self._byte_modo(), mais=True)]
                           + self._turno_dados(forcar=True, so_partes=True), depois=RESP)
            return

        if self.estado == 'aguarda_contrato':
            if CONTRATO in tipos:
                self.contrato_tx = Contrato.abre(tipos[CONTRATO][0][3])
                self._confere_modo(tipos[CONTRATO][0][3])
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
        _, margem, res, longe = sonda
        rapida = res[len(GANHOS)] if len(res) > len(GANHOS) else None
        res = res[:len(GANHOS)]
        c = decide(margem, res)
        if longe:
            # A escada veio no próprio lento: o que ela mediu é o degrau
            # LENTO, não uma extrapolação dos 100 baud. Inteiro ou quase
            # (a taxa 1/3 suave segura ~13%), fica no lento; senão, muito lento.
            ber, inteiro = res[c.ganho]
            c = Contrato(c.tons, c.par, c.ganho,
                         LENTO if inteiro or ber < LIMIAR_LENTO else MUITO_LENTO)
            if rapida is not None and rapida[1] and rapida[0] < LIMIARES_BER[0]:
                # A sonda a 100 baud deste sentido chegou inteira e limpa:
                # ele não está tão longe quanto a sessão. Rep2, não rep1 --
                # uma sonda só é pouca prova --, e a escada desce sozinha.
                c = Contrato(c.tons, c.par, SONDA_RAPIDA_GANHO, 1)
        elif self.esforco and c.degrau < LENTO:
            # De longe, os degraus a 100 baud e o 2-FSK falharam no ar mesmo
            # com a sondagem a 32% (2026-10-22): começa no lento, e a escada
            # desce ao muito lento se preciso.
            c = Contrato(c.tons, c.par, c.ganho, LENTO)
        bers = ", ".join(f"g{GANHOS[i]}:{b * 100:.0f}%{'*' if ok else ''}"
                         for i, (b, ok) in enumerate(res))
        if rapida is not None:
            bers += f"; 100 baud g{GANHOS[SONDA_RAPIDA_GANHO]}:{rapida[0] * 100:.0f}%" \
                    f"{'*' if rapida[1] else ''}"
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

    # --- modo de dados

    def _byte_modo(self):
        """O código do meu modo de dados, no byte que sobra do CONTRATO.
        Em 'auto' é 0 -- o mesmo preenchimento de antes --, e o quadro sai
        idêntico ao de sempre."""
        return bytes([MODOS_DADOS.index(self.modo_dados)])

    def _confere_modo(self, carga):
        """Escreve no diário se o outro lado roda outro modo de dados. Não
        negocia: o modo é escolhido por quem mede, nas duas pontas, e uma
        divergência tem de aparecer como divergência -- os dados de um lado
        não vão ser lidos pelo outro, e sem esta linha isso pareceria um
        canal ruim."""
        k = carga[5] if len(carga) > 5 else 0
        outro = MODOS_DADOS[k] if k < len(MODOS_DADOS) else f'desconhecido ({k})'
        if outro != self.modo_dados:
            self.anota(f"AVISO: o outro lado usa modo de dados {outro}, eu {self.modo_dados}; "
                       "os quadros de dados não vão se entender -- rodar as duas pontas "
                       "com o mesmo --modo-dados")
        else:
            self.anota(f"modo de dados confirmado nas duas pontas: {outro}")

    def _degrau_inicial(self, contrato):
        """Onde a escada do meu modo começa. Em 'auto' é o degrau do
        contrato. No 16-FSK fixo, o do contrato limitado ao rep4 (a sondagem
        mede justamente o 16-FSK). Nos outros, o primeiro: a sondagem não
        mediu essas técnicas, e começar com a menor redundância mostra cada
        uma como ela é -- se não servir, desce pela repetição."""
        if self.modo_dados == 'auto':
            return contrato.degrau
        if self.modo_dados == '16fsk':
            return min(contrato.degrau, self.ultimo_degrau)
        return 0

    # --- canal aberto: pare-e-espere

    def _abre_canal(self):
        self.aberto = True
        self.confirmado = False
        self.outro_tem_mais = False
        self.sondar_em = None
        self.seq_tx = 0
        if self.pendente_tx is not None:
            # Um pedaço que a sessão anterior mandou e nunca viu confirmado
            # volta para a frente da fila. Sem isto, recomeçar a sessão o
            # jogava fora -- no ar, em 2026-10-08, o outro lado recebeu o fim
            # da mensagem e nunca o começo. O preço é que um pedaço entregue
            # cujo ACK se perdeu chega duas vezes; perder é pior.
            self.fila[0:0] = self.pendente_tx[1]
        self.pendente_tx = None
        self.ultimo_rx = 255
        self.degrau_tx = self._degrau_inicial(self.contrato_tx)
        self.degrau_rx = self._degrau_inicial(self.contrato_rx)
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
            d = self.contrato_tx.descritor(self.degrau_tx, DADOS_N, self.modo_dados)
            carga = bytes([seq, self.ultimo_rx, self.degrau_rx, len(pedaco)]) + pedaco
            q = self._quadro(d, DADOS, carga)
        else:
            d = self.contrato_tx.descritor(self.degrau_tx, CTRL_N, self.modo_dados)
            q = self._quadro(d, ACK, bytes([self.ultimo_rx, self.degrau_rx]))
        return [q]

    def _turno_fim(self):
        d = self.contrato_tx.descritor(self.degrau_tx, CTRL_N, self.modo_dados)
        return [self._quadro(d, FIM, bytes([self.ultimo_rx]))]

    def _dados(self, quadros, ruins):
        if any(q[0][0] == FIM for q in quadros):
            if self.papel == 'ouvinte':
                # Responde a todo FIM, também a um repetido (o meu se perdeu),
                # e não fala mais nada: não tem relógio próprio para isso.
                # Responde uma vez e não fala mais nada. Se a vez passou, cala
                # sem encerrar: o chamador repete o FIM.
                if self._minha_vez(self._turno_fim(), espera=False):
                    self.anota("FIM do chamador: respondo FIM e calo")
                    self.encerrada = True
            else:
                self.anota("FIM respondido: sessão encerrada")
                self.espera_ate = None
                self.encerrada = True
            return
        if self.papel == 'chamador' and self.fim_tentativas:
            # Já me despedi: só o FIM do outro lado interessa. Antes um turno
            # ilegível aqui caía no caminho dos dados e eu mandava um ACK em
            # vez de repetir o FIM, e o ouvinte respondia com um pedido de
            # degrau que reabria tudo (sessão 6: dois FIMs, 70 s).
            return
        responder = not self.confirmado
        progresso = False
        for (tipo, mais, sess, carga), d in quadros:
            if tipo == DADOS:
                seq, ack, pede, n = carga[0], carga[1], carga[2], carga[3]
                pedaco = bytes(carga[4:4 + n])
                # O degrau em que este quadro chegou é o piso do que peço:
                # se o outro lado já desceu, pedir mais rápido seria inútil.
                for k in range(self.ultimo_degrau + 1):
                    if d == self.contrato_rx.descritor(k, d.nbytes, self.modo_dados):
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
            if pede <= self.ultimo_degrau and pede > self.degrau_tx:
                # Um piso, não uma ordem: quem recebe só sabe das falhas que
                # chegou a ver, e quem transmite pode ter descido sozinho por
                # silêncio. Tomar o pedido ao pé da letra fazia os dois
                # oscilarem, um descendo e o outro mandando subir. Subir de
                # novo pede nova sondagem.
                self.anota(f"o outro lado pede o degrau {self.degraus[pede]} para o que envio")
                self.degrau_tx = pede
        if progresso:
            if self.papel == 'chamador':
                # Um turno lido do ouvinte é a resposta, com dados ou só o ACK.
                # Antes o ACK sozinho não desarmava o prazo, e o chamador
                # "repetia o turno" a cada ~13 s depois de tudo entregue (no
                # ar, 2026-10-27), até as duas pontas falarem juntas.
                self.espera_ate = None
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
            if self.falhas_rx >= 2 and self.degrau_rx < self.ultimo_degrau:
                self.degrau_rx += 1
                self.falhas_rx = 0
                self.anota(f"quadros ilegíveis; pedindo {self.degraus[self.degrau_rx]}")
                if self.degrau_tx < self.degrau_rx:
                    # O pedido vai dentro dos meus quadros, e se eu não leio
                    # os do outro lado é provável que ele também não leia os
                    # meus -- então nunca chega. Em 2026-10-22, de longe, os
                    # dois pediram o muito lento um ao outro e ficaram no
                    # lento para sempre. Desço junto; quem recebe tenta todos
                    # os degraus pelo comprimento, sem precisar ser avisado.
                    self.degrau_tx = self.degrau_rx
                    self.anota(f"desço também o que envio para {self.degraus[self.degrau_tx]}")
            if self.sem_progresso > 8:
                self.anota("canal perdido; voltando ao começo")
                self.reinicia()
                return
        recebeu = any(q[0][0] == DADOS for q in quadros)
        if self.papel == 'ouvinte':
            # O ouvinte responde a todo turno do chamador, na vez dele, e
            # nunca fala sem ser chamado: o prazo, e com ele a repetição, é
            # só do chamador.
            self._minha_vez(self._turno_dados(), espera=False)
            return
        if not progresso and self.espera_ate is not None and self.agora < self.espera_ate:
            # Nada lido, e a vez do ouvinte ainda não acabou: o que soou pode
            # ser o começo da resposta dele. Responder agora seria falar por
            # cima dela ('piora', 2026-10-27: 3,9 s juntos). Quando a vez
            # acabar sem resposta lida, o prazo repete o turno.
            return
        self.outro_tem_mais = recebeu
        if self.pendente_tx is not None or self.fila or recebeu:
            responder = True
        if not progresso and ruins:
            # Nada lido e o prazo já passou: é um turno sem resposta, como o
            # do prazo vencido -- conta e desce o degrau do mesmo jeito.
            self.espera_ate = None
            self._sem_resposta()
            return
        if responder:
            # Sem confirmação o outro lado pode não ter o CONTRATO: a resposta
            # é a repetição, que o leva no formato medido ('meio_aberto': com
            # DADOS sozinhos o ouvinte ficou 140 s preso em 'aguarda_contrato').
            self._toca(self._turno_dados() if self.confirmado else self._retransmite(),
                       depois=RESP)
        elif progresso:
            # O ouvinte respondeu só com ACK: não tem mais nada, e o que ele
            # mandou antes eu já confirmei (senão ele repetiria os DADOS). Do
            # meu lado também acabou. Despedida explícita, em vez de consultar
            # o outro lado para sempre.
            self.anota("tudo entregue nos dois sentidos; mando FIM")
            self.fim_tentativas = 1
            self._toca(self._turno_fim(), depois=RESP)

    # A fila de dados de quem está ocioso: se o canal está aberto, o outro
    # lado calado e há o que mandar, mandar sem ser chamado.
    def ocioso(self):
        return (self.aberto and not self.agenda and self.espera_ate is None
                and self.pendente is None and not self.turno and self.agora >= self.livre_em)
