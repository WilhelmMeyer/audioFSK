"""Saudação, contrato e canal pelo áudio, numa máquina de verdade.

O protocolo está em `enlace.py` (sem I/O); este arquivo só liga uma
`Estacao` ao microfone e ao alto-falante. Roda nas duas pontas, uma como
`chamador` e outra como `ouvinte`, e nenhuma das duas usa o cabo serial nem
o túnel: tudo o que elas combinam passa pelo ar. O cabo/túnel pode continuar
ligado para *observar* (ler os diários), nunca para combinar.

    # na máquina que escuta (começa primeiro, mas não precisa)
    ./venv/bin/python -u saudacao.py --papel ouvinte --enviar "oi do B"
    # na outra
    ./venv/bin/python -u saudacao.py --papel chamador --enviar-arquivo testcard.bmp

A entrada fica aberta o tempo todo e a estação procura as marcas num fluxo
contínuo -- nunca "toca e depois grava uma janela", que cortaria ao meio uma
chamada caída na borda da janela. O que a própria máquina toca é zerado na
entrada (com a latência da saída descontada, `desloca_saida`).

Tudo o que o microfone ouviu na sessão é salvo em `--out` (WAV float32 +
JSON com o diário e os contratos), para que uma sessão que falhou possa ser
relida offline em vez de repetida na sala. O áudio e o diário vão para o disco
*durante* a sessão, não só no fim, e ela pode ser acompanhada e parada de fora
(`painel.py estado|log|segue|pausa|retoma|finaliza|para`): ver `painel.py`.

Sai sozinha quando termina o que tinha a mandar e não ouve marca nenhuma por
`--fim-silencio` segundos: a outra ponta acabou ou sumiu, e esperar
`--duracao` inteira não mede mais nada.

Na máquina B, para sobreviver à queda do SSH, lance o processo fora da
sessão SSH (um processo filho do sshd morre com ela):

    powershell -Command "Invoke-CimMethod -ClassName Win32_Process -MethodName Create
        -Arguments @{CommandLine='<python> -u saudacao.py ... --log sessao.log';
                     CurrentDirectory='<pasta>'}"
"""

import argparse
import collections
import os
import queue
import sys
import threading
import time

import numpy as np
import sounddevice as sd

import aviso
import enlace
import painel
import recording
from selfcapture import resolve, wait_ready, _fan_out

FS = enlace.FS
BLOCO = 2048


class AudioReal:
    """O microfone e o alto-falante desta máquina, pelo PortAudio."""

    simulado = None

    def __init__(self, args):
        wait_ready(args.out_device)
        self.in_dev, self.out_dev = resolve(args.in_device), resolve(args.out_device)
        if args.latencia is not None:
            self.lat = int(args.latencia * FS)
        else:
            try:
                self.lat = int(sd.query_devices(self.out_dev, 'output')
                               ['default_low_output_latency'] * FS)
            except Exception:
                self.lat = int(0.1 * FS)
        self.nome_entrada = sd.query_devices(self.in_dev, 'input')['name']
        self.nome_saida = sd.query_devices(self.out_dev, 'output')['name']
        self.stream = None

    def abre(self, cb):
        # Latência alta: o callback é Python e precisa do GIL, e uma volta
        # longa do laço principal o atrasa; com o buffer curto o PortAudio
        # transborda e joga a entrada fora (ver `Lacunas`).
        self.stream = sd.InputStream(samplerate=FS, channels=1, blocksize=BLOCO,
                                     device=self.in_dev, latency='high',
                                     callback=lambda d, f, t, st: cb(
                                         d[:, 0].copy(), t.inputBufferAdcTime,
                                         bool(st.input_overflow)))
        self.stream.start()

    def toca(self, x):
        sd.play(_fan_out(np.clip(x, -1, 1).astype(np.float32), self.out_dev),
                FS, device=self.out_dev)

    def cala(self):
        sd.stop()

    def encerrado(self):
        return False

    def fecha(self):
        sd.stop()
        if self.stream is not None:
            self.stream.stop()
            self.stream.close()


class Lacunas:
    """Acha a entrada que o PortAudio jogou fora e devolve o silêncio que a repõe.

    O relógio da estação é o número de amostras que ela ouviu. Um bloco
    perdido não é um buraco para ela, é o tempo andando para trás: tudo o que
    vem depois chega adiantado, e um quadro que perde um bloco no meio
    escorrega meio símbolo e fica ilegível. Medido na máquina B em
    2026-10-22: 873 s de áudio numa sessão de 900 s, `atraso_s` crescendo
    com `fila_s` em zero. No simulador, 2,5% dos blocos perdidos assim não
    deixam ler um único OLA em 400 s; repostos como silêncio no lugar certo,
    a sessão fecha como num canal limpo.

    O tamanho do buraco vem do instante do ADC de cada bloco, quando o
    dispositivo o informa. Sem ele, do relógio de parede -- mas só depois de
    um transbordo avisado: um relógio de placa que anda devagar também faz a
    parede adiantar, e aí inserir silêncio cortaria quadros ao meio em vez
    de consertá-los. Qual dos dois acontece em B ainda não se sabe; os
    contadores (`buracos` com `transbordos`, ou sem) é que vão dizer.

    O instante do ADC é comparado no acumulado, nunca bloco a bloco: pelo
    PulseAudio ele anda em degraus (medido aqui em 2026-10-27: parado por
    ~80 ms de blocos, depois um salto de ~80 ms), e cada salto lido sozinho
    parecia um buraco -- 420 s de silêncio inseridos numa sessão de 900 s
    que não perdeu nada, e nenhum quadro legível. `d` é quanto o ADC andou
    além das amostras entregues; o degrau faz `d` oscilar sem crescer, um
    relógio lento faz `d` subir aos poucos, e só um bloco perdido faz `d`
    saltar acima do maior valor recente. Só esse salto é reposto.
    """

    FOLGA_PAREDE = 0.25        # s; abaixo disto é jitter do callback, não perda
    JANELA_ADC = 3.0           # s; o maior `d` recente é a referência do salto
    APRENDE_ADC = 1.0          # s; antes disto só se aprende a oscilação

    def __init__(self):
        self.adc0 = None
        self.recentes = collections.deque()    # (amostra, d) para o máximo recente
        self.t0 = None
        self.n = 0
        self.perdidas = 0          # amostras repostas
        self.buracos = 0
        self.transbordos = 0
        self.com_adc = None        # o dispositivo informa o instante do ADC?

    def antes_de(self, n, adc, transbordo):
        """Amostras perdidas antes deste bloco de `n` amostras."""
        agora = time.time()
        if transbordo:
            self.transbordos += 1
        falta = 0
        if self.t0 is None:
            self.t0 = agora - n / FS
            self.com_adc = bool(adc)
            if adc:
                self.adc0 = adc
        elif adc and self.adc0 is not None:
            d = (adc - self.adc0) * FS - self.n
            while self.recentes and self.recentes[0][0] < self.n - self.JANELA_ADC * FS:
                self.recentes.popleft()
            ref = max(r[1] for r in self.recentes) if self.recentes else d
            if d < ref - FS:
                # O instante do ADC voltou atrás (dispositivo reaberto):
                # recomeça a referência em vez de ler um buraco negativo.
                self.adc0 = adc - self.n / FS
                self.recentes.clear()
                d = 0.0
            elif self.n > self.APRENDE_ADC * FS and d - ref > n // 2:
                falta = int(round(d - ref))
            self.recentes.append((self.n + falta, d - falta))
        elif transbordo:
            # O bloco logo depois do transbordo: o que falta na parede é o
            # que se perdeu, em blocos inteiros (o PortAudio perde buffers).
            f = int((agora - self.t0) * FS) - self.n - n
            if f > n // 2:
                falta = int(round(f / n)) * n
        elif self.transbordos:
            f = int((agora - self.t0) * FS) - self.n - n
            if f > self.FOLGA_PAREDE * FS:
                falta = f - int(0.05 * FS)
        if falta:
            self.perdidas += falta
            self.buracos += 1
        self.n += falta + n
        return falta


class Mundo:
    """O ar entre duas estações, simulado e em tempo real.

    Os canais, o ruído e a latência oculta são os de um cenário de
    `simula_enlace.py`; o que muda é o relógio: aqui ele é o de parede, um
    bloco a cada BLOCO/FS segundos, entregue a cada ponta pelo mesmo tipo de
    callback que o PortAudio chama. Assim cada ponta roda o laço de
    `sessao` inteiro -- painel, pausa, fila, atraso -- e pode ficar para trás
    do relógio como no ar. O que uma ponta toca entra no ar bloco a bloco,
    para que `cala` (pausa) corte o resto como `sd.stop()` corta.
    """

    DEGRAU_ADC = 0.08          # s

    def __init__(self, cenario, semente=0):
        import simula_enlace as S
        c = S.CENARIOS[cenario]
        if c.get('sem_parceiro'):
            raise ValueError("cenário sem parceiro não tem segunda ponta para simular")
        rng = np.random.default_rng(semente)
        self.cenario = cenario
        self.oculta = {'chamador': int(c.get('latencia_oculta', 0.0) * FS),
                       'ouvinte': int(c.get('latencia_oculta_b',
                                            c.get('latencia_oculta', 0.0)) * FS)}
        self.perde = {'ouvinte': c.get('perde_b', 0.0)}
        self.rng_perda = np.random.default_rng(semente + 100)
        # Mesma ordem de sorteio de `simula_enlace.roda`: o canal do cenário
        # é o mesmo para a mesma semente.
        self.ar = {'chamador': S.Ar(rng, c['ruido_a'], rajadas=c.get('rajadas'), semente=semente),
                   'ouvinte': S.Ar(rng, c['ruido_b'], c.get('piora_b'),
                                   rajadas=c.get('rajadas'), semente=semente + 1)}
        self.canal = {'chamador': S.Canal(rng, **c['ab']),
                      'ouvinte': S.Canal(rng, **c['ba'])}
        self.cb = {}
        self.saidas = {'chamador': [], 'ouvinte': []}   # [início, no outro, no meu]
        self.t = 0
        self.trava = threading.Lock()
        self.fim = threading.Event()
        self.rapido = bool(os.environ.get('AUDIOFSK_SIM_RAPIDO'))
        self.pendentes = {}         # papel -> função: blocos ainda na fila dessa ponta
        threading.Thread(target=self._relogio, daemon=True).start()

    def _relogio(self):
        prox = time.time()
        while not self.fim.is_set():
            a, b = self.t, self.t + BLOCO
            blocos = {}
            with self.trava:
                for lado in self.ar:
                    # O ar guarda só o ruído; o que foi tocado soma aqui.
                    blocos[lado] = self.ar[lado].le(a, b)
                for lado, saidas in self.saidas.items():
                    outro = 'ouvinte' if lado == 'chamador' else 'chamador'
                    for s in saidas:
                        for dest, y in ((outro, s[1]), (lado, s[2])):
                            i, j = max(a, s[0]), min(b, s[0] + len(y))
                            if j > i:
                                blocos[dest][i - a:j - a] += y[i - s[0]:j - s[0]]
                    saidas[:] = [s for s in saidas if s[0] + max(len(s[1]), len(s[2])) > b]
                self.t = b
                cbs = dict(self.cb)
            for lado, cb in cbs.items():
                if self.rng_perda.random() < self.perde.get(lado, 0.0):
                    continue             # transbordo: o bloco some, o próximo avisa
                # Instante do ADC, como o PortAudio o dá pelo PulseAudio: o
                # do relógio do ar, mas em degraus de DEGRAU_ADC (medido em
                # 2026-10-27). Um carimbo exato escondeu que `Lacunas` lia
                # cada degrau como um buraco.
                adc = 1.0 + np.floor(a / FS / self.DEGRAU_ADC) * self.DEGRAU_ADC
                cb(blocos[lado].astype(np.float32), adc, False)
            if self.rapido:
                # Sem relógio de parede: cada bloco só sai quando as duas
                # pontas já consumiram o anterior. Para separar o que é do
                # ritmo de tempo real do que é do modelo do ar.
                while any(f() > 0 for f in self.pendentes.values()) and not self.fim.is_set():
                    time.sleep(0.001)
                continue
            prox += BLOCO / FS
            espera = prox - time.time()
            if espera > 0:
                time.sleep(espera)
            elif espera < -1.0:
                prox = time.time()      # a CPU não deu conta: perde o atraso, não acelera

    def toca(self, lado, x, lat):
        y = self.canal[lado].passa(x)
        eco = 0.8 * np.tanh(np.asarray(x) / 0.35)
        with self.trava:
            self.saidas[lado].append([self.t + lat + self.oculta[lado], y, eco])

    def cala(self, lado):
        with self.trava:
            for s in self.saidas[lado]:
                k = max(0, self.t - s[0])
                s[1], s[2] = s[1][:k], s[2][:k]


class AudioSim:
    """Uma ponta do `Mundo`, com a mesma cara de `AudioReal`."""

    def __init__(self, mundo, papel, latencia=None):
        self.mundo, self.papel = mundo, papel
        self.simulado = mundo.cenario
        self.lat = int((0.1 if latencia is None else latencia) * FS)
        self.nome_entrada = self.nome_saida = f"simulado:{mundo.cenario}"

    def abre(self, cb, pendentes=None):
        with self.mundo.trava:
            self.mundo.cb[self.papel] = cb
            if pendentes is not None:
                self.mundo.pendentes[self.papel] = pendentes

    def toca(self, x):
        self.mundo.toca(self.papel, np.clip(x, -1, 1), self.lat)

    def cala(self):
        self.mundo.cala(self.papel)

    def encerrado(self):
        return self.mundo.fim.is_set()

    def fecha(self):
        self.mundo.cala(self.papel)
        with self.mundo.trava:
            self.mundo.cb.pop(self.papel, None)
            self.mundo.pendentes.pop(self.papel, None)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--papel', choices=('chamador', 'ouvinte'), required=True)
    ap.add_argument('--in-device', default=None, help="nome (ou parte) do microfone")
    ap.add_argument('--out-device', default=None, help="nome (ou parte) do alto-falante")
    ap.add_argument('--enviar', default='', help="texto a mandar quando o canal abrir")
    ap.add_argument('--enviar-arquivo', default=None)
    ap.add_argument('--receber-em', default=None, help="grava aqui o que chegar")
    ap.add_argument('--duracao', type=float, default=600.0, help="segundos, no máximo")
    ap.add_argument('--modo-dados', choices=enlace.MODOS_DADOS, default='auto',
                    help="modulação dos dados: auto (escada de hoje) ou uma técnica fixa; "
                         "as duas pontas precisam do mesmo")
    ap.add_argument('--latencia', type=float, default=None,
                    help="latência da saída em s (padrão: a que o PortAudio declara)")
    ap.add_argument('--out', default='sessoes-enlace')
    ap.add_argument('--semente', type=int, default=None)
    ap.add_argument('--fim-silencio', type=float, default=120.0,
                    help="s sem marca ouvida, depois de tudo enviado e confirmado, "
                         "para sair sozinho (0 desliga)")
    ap.add_argument('--painel-porta', type=int, default=painel.PORTA,
                    help="porta TCP do painel em 127.0.0.1 (0 desliga)")
    ap.add_argument('--log', default=None,
                    help="arquivo para a saída (para quem roda sem console)")
    ap.add_argument('--simulado', default=None, metavar='CENARIO',
                    help="sem microfone nem alto-falante: as duas pontas rodam neste "
                         "processo, sobre um cenário de simula_enlace.py, em tempo real")
    ap.add_argument('--parceiro-enviar', default='resposta da outra ponta, simulada',
                    help="com --simulado: o que a outra ponta manda")
    ap.add_argument('--parceiro-out', default=None,
                    help="com --simulado: pasta da outra ponta (padrão: <out>-parceiro)")
    args = ap.parse_args()
    if args.log:
        sys.stdout = sys.stderr = open(args.log, 'a', encoding='utf-8', buffering=1)
    if not args.simulado:
        sys.exit(sessao(args, AudioReal(args)))

    # As duas pontas no mesmo processo: esta com o painel e a pasta pedidos,
    # a outra no papel oposto, painel na porta seguinte e pasta própria, para
    # que um segundo visor a mostre (`visor.py --painel-porta P+1 --out ...`).
    os.environ['AUDIOFSK_AVISO'] = '0'        # ninguém está ocupando a sala
    semente = 0 if args.semente is None else args.semente
    mundo = Mundo(args.simulado, semente)
    par = argparse.Namespace(**vars(args))
    par.papel = 'ouvinte' if args.papel == 'chamador' else 'chamador'
    par.enviar, par.enviar_arquivo, par.receber_em = args.parceiro_enviar, None, None
    par.painel_porta = args.painel_porta + 1 if args.painel_porta else 0
    par.out = args.parceiro_out or args.out.rstrip('/\\') + '-parceiro'
    par.semente = semente + 2 if args.papel == 'chamador' else semente + 1
    args.semente = semente + 1 if args.papel == 'chamador' else semente + 2
    th = threading.Thread(target=sessao, args=(par, AudioSim(mundo, par.papel, par.latencia)),
                          daemon=True)
    th.start()
    try:
        r = sessao(args, AudioSim(mundo, args.papel, args.latencia))
    except KeyboardInterrupt:
        r = 1
    # A ponta com o painel acabou (parada, finalizada, duração): a outra acaba
    # junto. Esperá-la deixava o processo vivo e sem painel, e o visor travado.
    mundo.fim.set()
    th.join(timeout=10)
    sys.exit(r)


def sessao(args, audio):
    """Uma estação ligada a `audio` até acabar; devolve o código de saída."""
    dados = args.enviar.encode()
    if args.enviar_arquivo:
        dados += open(args.enviar_arquivo, 'rb').read()

    t0 = time.time()
    diario = []
    stem = os.path.join(args.out, time.strftime("%Y%m%d-%H%M%S") + f"-enlace-{args.papel}")
    pn = painel.Painel(stem, porta=args.painel_porta, fs=FS)

    def log(s):
        s = pn.linha(s)
        diario.append(s)
        print(s, flush=True)

    est = enlace.Estacao(args.papel, semente=args.semente, log=log,
                         modo_dados=args.modo_dados)
    est.enviar(dados)

    lat = audio.lat
    log(f"[saudacao] papel {args.papel}, entrada {audio.nome_entrada!r}, "
        f"saída {audio.nome_saida!r}, latência {lat / FS:.3f}s, "
        f"{len(dados)} bytes a enviar")

    log(f"[saudacao] pid {os.getpid()}, painel em 127.0.0.1:{pn.porta}, "
        f"gravando em {stem}.*")
    q = queue.Queue()
    ouvido = []
    pausado = False
    pausa_s = 0.0          # quanto tempo de parede a estação ficou congelada
    pausa_t = None
    finalizar = False
    concluido = False
    motivo = 'duração esgotada'
    anotado = False        # o motivo do fim já está no diário
    passo_ms = 0.0

    def estado(fase):
        lag = (time.time() - t_stream - pausa_s
               - (time.time() - pausa_t if pausa_t else 0) - est.agora / FS)
        return dict(papel=args.papel, simulado=audio.simulado, fase=fase, estado_estacao=getattr(est, 'estado', None),
                    saudado=est.saudado, aberto=est.aberto,
                    confirmado=getattr(est, 'confirmado', False),
                    contrato_tx=est.contrato_tx.descreve() if est.contrato_tx else None,
                    contrato_rx=est.contrato_rx.descreve() if est.contrato_rx else None,
                    a_enviar=len(est.fila), pendente_tx=est.pendente_tx is not None,
                    enviados_total=len(dados), recebidos=len(est.recebido),
                    estacao_s=round(est.agora / FS, 2), atraso_s=round(lag, 2),
                    fila_s=round(q.qsize() * BLOCO / FS, 2), passo_ms=round(passo_ms, 1),
                    ultima_marca_ha_s=round((est.agora - est.ouvido_em) / FS, 1),
                    rms_entrada=round(float(np.sqrt(np.mean(ouvido[-1] ** 2))), 4)
                    if ouvido else None,
                    pausado=pausado, concluido=concluido, finalizando=finalizar,
                    entrada_perdida_s=round(lacunas.perdidas / FS, 2),
                    buracos_entrada=lacunas.buracos, transbordos=lacunas.transbordos,
                    ultimas=diario[-5:])

    lacunas = Lacunas()

    def cb(x, adc=None, transbordo=False):
        falta = lacunas.antes_de(len(x), adc, transbordo)
        if falta:
            q.put(np.zeros(falta, dtype=np.float32))
        q.put(x)

    def alimenta():
        n = 0
        while True:
            try:
                x = q.get_nowait()
            except queue.Empty:
                return n
            ouvido.append(x)
            pn.audio(x)
            if not pausado:
                est.ouvir(x)
            n += len(x)

    if not audio.simulado:
        aviso.inicio("MICROFONE E ALTO-FALANTE", f"saudação acústica ({args.papel})")
    t_stream = time.time()
    try:
        if audio.simulado:
            audio.abre(cb, pendentes=q.qsize)
        else:
            audio.abre(cb)
        while True:
            if time.time() - t0 >= args.duracao:
                break
            if audio.encerrado():
                motivo = 'simulação encerrada'
                break
            while not pn.comandos.empty():
                c = pn.comandos.get()
                log(f"[saudacao] comando do painel: {c}")
                if c == 'para':
                    motivo = 'parada pelo painel'
                    raise KeyboardInterrupt
                if c == 'finaliza':
                    finalizar = True
                elif c == 'pausa' and not pausado:
                    pausado, pausa_t = True, time.time()
                    audio.cala()
                    pn.corta(lat)
                elif c == 'retoma' and pausado:
                    pausado, pausa_s, pausa_t = False, pausa_s + time.time() - pausa_t, None
            if finalizar and est.agora >= est.livre_em and not est.agenda:
                motivo = 'finalizada pelo painel'
                break
            if (getattr(est, 'encerrada', False) and not est.agenda
                    and est.agora > est.livre_em + 3 * FS):
                # Despediu-se (FIM) e o último som já saiu. Não espera silêncio
                # na sala: um ruído acima do piso adiava a saída para sempre.
                motivo = 'encerrada pelo FIM'
                log(f"[saudacao] {motivo}; saindo")
                anotado = True
                break
            if (concluido and args.fim_silencio
                    and est.agora - est.ouvido_em > args.fim_silencio * FS
                    and est.agora >= est.livre_em and not est.agenda):
                motivo = f'nada ouvido por {args.fim_silencio:.0f}s depois de concluída'
                log(f"[saudacao] {motivo}; saindo")
                anotado = True
                break
            pn.publica(estado('pausada' if pausado else 'rodando'))
            try:
                x = q.get(timeout=0.5)
            except queue.Empty:
                continue
            ouvido.append(x)
            pn.audio(x)
            if pausado:
                alimenta()
                continue
            est.ouvir(x)
            alimenta()
            tp = time.time()
            burst = est.passo()
            passo_ms = 1000 * (time.time() - tp)
            if burst is not None:
                # Quanto de entrada chegou enquanto `passo` decidia: o áudio
                # vai soar depois disso, mais a latência da saída.
                atraso = sum(len(c) for c in list(q.queue)) + lat
                est.desloca_saida(atraso)
                audio.toca(burst)
                pn.saida(burst, atraso + est.lat_extra)
            if (not concluido and est.aberto and est.confirmado and not est.fila
                    and est.pendente_tx is None):
                concluido = True
                log(f"[saudacao] tudo enviado e confirmado em {time.time() - t0:.1f}s; "
                    f"recebidos {len(est.recebido)} bytes")
                if args.receber_em:
                    open(args.receber_em, 'wb').write(bytes(est.recebido))
    except KeyboardInterrupt:
        if motivo == 'duração esgotada':
            motivo = 'interrompida'
        log(f"[saudacao] {motivo}")
        anotado = True
    finally:
        if not anotado:
            log(f"[saudacao] {motivo}")
        log(f"[saudacao] entrada: instante do ADC {'informado' if lacunas.com_adc else 'ausente'}, "
            f"{lacunas.transbordos} transbordo(s) avisado(s)")
        if lacunas.buracos:
            log(f"[saudacao] a entrada perdeu {lacunas.perdidas / FS:.2f}s em {lacunas.buracos} "
                f"buraco(s) ({lacunas.transbordos} transbordo(s) avisados); repostos como silêncio")
        audio.fecha()
        if not audio.simulado:
            aviso.fim("saudação acústica")
        gravado = np.concatenate(ouvido) if ouvido else np.zeros(0)
        meta = dict(mode='enlace', label=f'enlace-{args.papel}', papel=args.papel,
                    modo_dados=args.modo_dados,
                    saudado=est.saudado, aberto=est.aberto,
                    confirmado=getattr(est, 'confirmado', False),
                    contrato_tx=est.contrato_tx.descreve() if est.contrato_tx else None,
                    contrato_rx=est.contrato_rx.descreve() if est.contrato_rx else None,
                    recebidos=len(est.recebido), diario=diario, fim=motivo,
                    duracao_parede_s=round(time.time() - t0, 1),
                    estacao_s=round(est.agora / FS, 1),
                    simulado=audio.simulado,
                    nota="sessão do enlace; não é uma captura para bench/resultado"
                         + ("; SIMULADA, sem ar nenhum" if audio.simulado else ""))
        recording.save_as(stem, gravado, dados,
                          recorded=os.path.basename(stem)[:15], **meta)
        pn.publica(dict(estado('terminada'), fim=motivo), forca=True)
        pn.fecha()
        print(f"[saudacao] sessão gravada em {stem}", flush=True)
        if args.receber_em and est.recebido:
            open(args.receber_em, 'wb').write(bytes(est.recebido))
    return 0 if est.aberto else 1


if __name__ == '__main__':
    main()
