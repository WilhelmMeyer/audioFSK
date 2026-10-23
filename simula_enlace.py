"""Duas estações de `enlace.py` conversando por dois canais simulados.

Não é um teste do DSP -- isso é `loopback_test.py` -- e sim do protocolo: a
saudação, a sondagem, o contrato, o canal aberto e as voltas atrás. Por isso
o canal é adversário de propósito, com o que o link real já mostrou:

- dois sentidos diferentes (A->B pior que B->A);
- resposta em pente (ecos curtos) e a cauda de ~14 dB abaixo do tom;
- um limitador na saída, que faz o ganho alto perder para o baixo;
- relógios diferentes nas duas pontas (1e-4) e atraso de propagação aleatório;
- opcionalmente uma faixa morta, que derruba uma abordagem de controle e
  obriga o rodízio e as sombras;
- o próprio alto-falante entrando alto no próprio microfone, para provar que
  a cegueira durante a transmissão funciona;
- e um cenário sem parceiro, que nunca pode dizer "achei".

Imprime SUCCESS!/FAILED como `loopback_test.py`. Sem hardware.

    ./venv/bin/python simula_enlace.py            # todos os cenários
    ./venv/bin/python simula_enlace.py limpo -v   # um, com o diário das estações
    ./venv/bin/python simula_enlace.py limpo --semente=3   # outro sorteio de canal
"""

import sys
import time

import numpy as np
from scipy.signal import butter, fftconvolve, sosfilt

import enlace as E

FS = E.FS
BLOCO = 1024


class Canal:
    """Um sentido do ar: saída limitada, pente, cauda, atraso, relógio."""

    def __init__(self, rng, perda=0.3, snr_ruido=0.003, ecos=3, cauda_db=-14.0,
                 relogio=0.0, morta=None, limitador=0.35, cauda_s=0.06):
        self.rng = rng
        self.perda = perda
        self.ruido = snr_ruido
        self.relogio = relogio
        self.limitador = limitador
        self.atraso = int(rng.uniform(0.0, 0.01) * FS)
        # Ecos de 1 a 8 ms: um pente com covas fundas na banda.
        h = np.zeros(int(max(0.12, 0.01 + 5 * cauda_s) * FS))
        h[0] = 1.0
        for _ in range(ecos):
            h[int(rng.uniform(0.001, 0.008) * FS)] += rng.uniform(-0.7, 0.7)
        # A cauda: ruído decaindo, ~14 dB abaixo do direto, 60 ms (de longe,
        # mais forte e mais longa: o campo reverberante pesa mais que o direto).
        n = np.arange(len(h) - int(0.01 * FS))
        tail = rng.normal(0, 1, len(n)) * np.exp(-n / (cauda_s * FS))
        tail *= 10 ** (cauda_db / 20) / np.sqrt(np.sum(tail ** 2))
        h[int(0.01 * FS):] += tail
        self.h = h / np.sqrt(np.sum(h ** 2))
        self.sos_morta = (butter(6, morta, btype='bandstop', fs=FS, output='sos')
                          if morta else None)

    def passa(self, x):
        # Limitador do alto-falante: tanh, linear para baixo e achatando o pico.
        y = self.limitador * np.tanh(np.asarray(x) / self.limitador)
        y = fftconvolve(y, self.h)
        if self.sos_morta is not None:
            y = sosfilt(self.sos_morta, y)
        if self.relogio:
            n = len(y)
            t = np.arange(int(n * (1 + self.relogio))) / (1 + self.relogio)
            y = np.interp(t, np.arange(n), y)
        return np.concatenate([np.zeros(self.atraso), y * self.perda])


class Ar:
    """O que chega ao microfone de uma estação, indexado pelo tempo dela."""

    def __init__(self, rng, ruido, piora=None, rajadas=None, semente=0):
        self.x = np.zeros(0)
        self.rng = rng
        self.ruido = ruido
        self.piora = piora          # (instante em s, desvio do ruído, tons interferentes)
        # (por segundo, duração em s, desvio): estouros de ruído largo em
        # instantes ao acaso -- uma porta, uma cadeira, alguém falando. Um
        # sorteio à parte, para não mudar o canal dos outros cenários.
        self.rajadas = rajadas
        self._raj = []
        self._raj_rng = np.random.default_rng(semente + 200)

    def soma(self, inicio, y):
        fim = inicio + len(y)
        if fim > len(self.x):
            self.x = np.concatenate([self.x, np.zeros(fim - len(self.x))])
        self.x[inicio:fim] += y

    def le(self, a, b):
        r, tons = self.ruido, ()
        if self.piora and a >= self.piora[0] * FS:
            r, tons = self.piora[1], self.piora[2]
        out = self.rng.normal(0, r, b - a)
        n = np.arange(a, b) / FS
        for f, amp in tons:
            out += amp * np.sin(2 * np.pi * f * n)
        if self.rajadas:
            taxa, dur, desvio = self.rajadas
            while not self._raj or self._raj[-1] < b:
                t0 = (self._raj[-1] if self._raj else 0) + self._raj_rng.exponential(1 / taxa) * FS
                self._raj.append(int(t0))
            n = int(dur * FS)
            for t0 in self._raj:
                i, j = max(a, t0), min(b, t0 + n)
                if j > i:
                    out[i - a:j - a] += self._raj_rng.normal(0, desvio, j - i)
        k = min(b, len(self.x))
        if k > a:
            out[:k - a] += self.x[a:k]
        return out


def roda(cenario, verbose=False, semente=0):
    rng = np.random.default_rng(semente)
    log = print if verbose else None
    c = CENARIOS[cenario]
    modo = c.get('modo_dados', 'auto')
    a = E.Estacao('chamador', semente=semente + 1, log=log, nome='A', modo_dados=modo)
    b = None if c.get('sem_parceiro') else E.Estacao('ouvinte', semente=semente + 2,
                                                     log=log, nome='B', modo_dados=modo)
    ar_a = Ar(rng, c['ruido_a'], rajadas=c.get('rajadas'), semente=semente)
    ar_b = Ar(rng, c['ruido_b'], c.get('piora_b'), rajadas=c.get('rajadas'), semente=semente + 1)
    ab = Canal(rng, **c['ab'])
    ba = Canal(rng, **c['ba'])
    msg_a = bytes(rng.integers(0, 256, c.get('dados_a', 0)).astype(np.uint8))
    msg_b = bytes(rng.integers(0, 256, c.get('dados_b', 0)).astype(np.uint8))
    a.enviar(msg_a)
    if b:
        b.enviar(msg_b)
    t, fim = 0, int(c['segundos'] * FS)
    rng_perda = np.random.default_rng(semente + 100)   # à parte: não muda o canal
    perdidos = 0
    falas = {'A': [], 'B': []}       # (início, fim) do que cada uma tocou
    t0 = time.time()
    while t < fim:
        for est, ar_meu, ar_outro, canal in ((a, ar_a, ar_b, ab), (b, ar_b, ar_a, ba)):
            if est is None:
                continue
            bloco = ar_meu.le(t, t + BLOCO)
            if est is b and rng_perda.random() < c.get('perde_b', 0.0):
                # O bloco que a entrada de B jogou fora (transbordo do
                # PortAudio): a estação nunca o ouve, e o relógio dela -- as
                # amostras ouvidas -- fica para trás do ar.
                perdidos += 1
                if c.get('compensa', True):
                    # O que `saudacao.py` faz ao ver o buraco (pelo instante
                    # do ADC de cada bloco): silêncio do tamanho perdido, no
                    # lugar dele, e o relógio da estação continua no do ar.
                    est.ouvir(np.zeros(BLOCO))
            else:
                est.ouvir(bloco)
            x = est.passo()
            if x is not None:
                # Latência da saída que a estação não sabe (um alto-falante
                # Bluetooth declara menos do que tem): o som sai depois do
                # instante em que ela acha que tocou, para os dois ouvidos.
                oculta = c.get('latencia_oculta_b' if est is b else 'latencia_oculta',
                               c.get('latencia_oculta', 0.0))
                lat = t + BLOCO + int(oculta * FS)
                falas['A' if est is a else 'B'].append((lat, lat + len(x)))
                ar_outro.soma(lat, canal.passa(x))
                if (c.get('perde_contrato') and est is a and a.aberto and not a.confirmado
                        and len(a.ultimo_turno[0]) == a.ctrl.amostras):
                    # O turno do contrato de A com o CONTRATO na abordagem de
                    # controle: esse quadro (o primeiro segmento) chega a B
                    # debaixo de um estouro, toda vez -- a abordagem que
                    # passou na saudação deixou de passar neste sentido.
                    ar_outro.soma(lat, rng.normal(0, 2.0, a.ctrl.amostras + E.FS // 10))
                # O próprio alto-falante no próprio microfone, bem alto.
                ar_meu.soma(lat, 0.8 * np.tanh(x / 0.35))
        t += BLOCO
        if b and a.aberto and b.aberto and a.confirmado and b.confirmado \
                and a.recebido == msg_b and b.recebido == msg_a \
                and not a.fila and not b.fila and a.pendente_tx is None \
                and b.pendente_tx is None:
            break
    a.perdidos = perdidos
    a.colisao = sum(max(0, min(f1, g1) - max(f0, g0))
                    for f0, f1 in falas['A'] for g0, g1 in falas['B']) / FS
    return a, b, msg_a, msg_b, t / FS, time.time() - t0


CANAL_BOM = dict(perda=0.4, cauda_db=-16.0)
CENARIOS = {
    'limpo': dict(segundos=240, ruido_a=0.002, ruido_b=0.002,
                  ab=dict(CANAL_BOM), ba=dict(CANAL_BOM),
                  dados_a=120, dados_b=60),
    # A->B pior, relógios diferentes, uma faixa morta só em A->B que mata o
    # par 1700/2350 e um pedaço do 16-FSK: o rodízio de abordagens e as
    # sombras do contrato têm de dar conta.
    'adverso': dict(segundos=400, ruido_a=0.003, ruido_b=0.006,
                    ab=dict(perda=0.25, cauda_db=-12.0, relogio=1e-4,
                            morta=(1550, 1850), ecos=4),
                    ba=dict(perda=0.35, cauda_db=-14.0, relogio=-1e-4),
                    dados_a=90, dados_b=40),
    # O canal piora depois do contrato: em B aparecem apitos em cinco dos tons
    # contratados (um ventilador, uma fonte chiando) e mais ruído. O 16-FSK
    # rápido deixa de passar e as marcas continuam detectáveis -- é o caso
    # para que existe descer de degrau.
    'piora': dict(segundos=600, ruido_a=0.002, ruido_b=0.003,
                  piora_b=(62, 0.04, ((1050, 0.03), (1375, 0.03), (2025, 0.03),
                                      (2675, 0.03), (3000, 0.03))),
                  ab=dict(perda=0.3, cauda_db=-14.0, relogio=5e-5),
                  ba=dict(CANAL_BOM), dados_a=150, dados_b=20),
    # Como 'limpo', com 0,7 s de latência de saída que ninguém declarou. A
    # própria marca de fechamento sai da janela de cegueira se a guarda não
    # cobrir isso, e vira uma abertura fantasma.
    'latencia': dict(segundos=240, ruido_a=0.002, ruido_b=0.002,
                     ab=dict(CANAL_BOM), ba=dict(CANAL_BOM),
                     dados_a=120, dados_b=60, latencia_oculta=0.7),
    # Cada modulação fixa sozinha nos dados, sobre o canal 'limpo': mesma
    # saudação, sondagem e contrato, só os DADOS e ACK mudam. Prova que cada
    # quadro é escrito e lido de ponta a ponta pelo protocolo, não que a
    # técnica sirva para a sala -- isso é o ar que diz.
    **{f'modo_{m}': dict(segundos=600, ruido_a=0.002, ruido_b=0.002,
                         ab=dict(CANAL_BOM), ba=dict(CANAL_BOM),
                         dados_a=60, dados_b=30, modo_dados=m)
       for m in ('16fsk', '2fsk', 'votada', 'multicanal')},
    # As máquinas a alguns metros (2026-10-22): nível 26 dB abaixo do
    # 'limpo', cauda forte e longa, e o microfone de B ruidoso (no ar, o piso
    # do Windows era ~4x o do Linux). A assinatura do que se viu no ar: a
    # chamada chega a ~0,2 a ganho 0,3, as marcas de quadro rentes ao limiar,
    # os corpos a 100 baud ilegíveis e o lento lido. Antes do esforço de
    # longe, a saudação girava nas cinco abordagens de perto sem fim.
    'longe': dict(segundos=900, ruido_a=0.012, ruido_b=0.038,
                  ab=dict(perda=0.02, cauda_db=-3.0, cauda_s=0.15),
                  ba=dict(perda=0.02, cauda_db=-3.0, cauda_s=0.15),
                  dados_a=60, dados_b=30),
    # A entrada de B perdendo blocos (2026-10-22: o WAV de 900 s de B tinha
    # 873 s, atraso_s crescendo com fila_s em zero) e a saída de B com mais
    # latência escondida que a de A (eco medido +0,18-0,23 s contra
    # +0,07-0,15). O relógio de B anda atrás do ar e um quadro longo perde
    # pedaços no meio.
    'perdas': dict(segundos=400, ruido_a=0.002, ruido_b=0.004,
                   ab=dict(CANAL_BOM), ba=dict(CANAL_BOM),
                   dados_a=120, dados_b=60, perde_b=0.025,
                   latencia_oculta=0.1, latencia_oculta_b=0.2),
    # Perto num sentido e longe no outro: B ouve A forte (a chamada passa do
    # LIMIAR_LONGE) e A ouve B como de alguns metros. Só uma ponta se acha
    # longe pela chamada; a outra tem de subir o esforço pelo que lê no OLA,
    # senão responde de perto a quem só lê de longe.
    'assimetrico': dict(segundos=900, ruido_a=0.02, ruido_b=0.003,
                        ab=dict(CANAL_BOM),
                        ba=dict(perda=0.01, cauda_db=-3.0, cauda_s=0.15),
                        dados_a=60, dados_b=30),
    # O meio-aberto do ar (2026-10-22): A leu o CONTRATO de B e abriu o
    # canal; o CONTRATO de A se perde e B, que lê os DADOS que vêm atrás,
    # fica em 'aguarda_contrato' enquanto A repete o mesmo turno.
    'meio_aberto': dict(segundos=400, ruido_a=0.002, ruido_b=0.002,
                        ab=dict(CANAL_BOM), ba=dict(CANAL_BOM),
                        dados_a=120, dados_b=60, perde_contrato=True),
    # Estouros de ruído nas duas pontas, ~um a cada 12 s, de 0,4 s: perdem
    # um quadro aqui e ali em qualquer fase. É o que deixa uma ponta achar o
    # canal aberto enquanto a outra não leu o contrato (no ar, 2026-10-22,
    # A repetiu DADOS por 70 s a um B preso em 'aguarda_contrato').
    'rajadas': dict(segundos=600, ruido_a=0.002, ruido_b=0.002,
                    ab=dict(CANAL_BOM), ba=dict(CANAL_BOM),
                    dados_a=120, dados_b=60, rajadas=(1 / 12, 0.4, 0.05)),
    'sem_parceiro': dict(segundos=120, ruido_a=0.01, ruido_b=0.01,
                         ab=dict(CANAL_BOM), ba=dict(CANAL_BOM),
                         sem_parceiro=True),
}


def julga(nome, a, b, msg_a, msg_b, seg, cpu):
    if CENARIOS[nome].get('sem_parceiro'):
        ok = not a.saudado and not a.aberto
        print(f"  {nome}: {seg:.0f}s simulados ({cpu:.0f}s cpu); saudado={a.saudado} "
              f"-> {'ok' if ok else 'FALHOU: achou parceiro onde não há'}")
        return ok
    ok = (a.confirmado if a.aberto else False) and b.aberto and \
        a.recebido == msg_b and b.recebido == msg_a
    print(f"  {nome}: {seg:.0f}s simulados ({cpu:.0f}s cpu); A {a.estado}, B {b.estado}; "
          f"A recebeu {len(a.recebido)}/{len(msg_b)}, B recebeu {len(b.recebido)}/{len(msg_a)}"
          f" -> {'ok' if ok else 'FALHOU'}" + f" [modo de dados {a.modo_dados}]"
          f" [falando juntos {a.colisao:.1f}s]"
          + (f" [B perdeu {a.perdidos} blocos]" if a.perdidos else ""))
    if a.contrato_tx:
        print(f"     A->B: {a.contrato_tx.descreve()} (degrau em uso {a.degraus[a.degrau_tx]})")
    if b.contrato_tx:
        print(f"     B->A: {b.contrato_tx.descreve()} (degrau em uso {b.degraus[b.degrau_tx]})")
    return ok


def main():
    args = [x for x in sys.argv[1:] if not x.startswith('-')]
    verbose = '-v' in sys.argv
    semente = next((int(x.split('=', 1)[1]) for x in sys.argv[1:]
                    if x.startswith('--semente=')), 0)
    nomes = args or list(CENARIOS)
    ok = True
    for n in nomes:
        r = roda(n, verbose=verbose, semente=semente)
        ok &= julga(n, *r)
    print("SUCCESS!" if ok else "FAILED")
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
