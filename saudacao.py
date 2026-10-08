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
relida offline em vez de repetida na sala.

Nada disto foi medido no ar ainda.
"""

import argparse
import queue
import sys
import time

import numpy as np
import sounddevice as sd

import aviso
import enlace
import recording
from selfcapture import resolve, wait_ready, _fan_out

FS = enlace.FS
BLOCO = 2048


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
    ap.add_argument('--latencia', type=float, default=None,
                    help="latência da saída em s (padrão: a que o PortAudio declara)")
    ap.add_argument('--out', default='sessoes-enlace')
    ap.add_argument('--semente', type=int, default=None)
    args = ap.parse_args()

    dados = args.enviar.encode()
    if args.enviar_arquivo:
        dados += open(args.enviar_arquivo, 'rb').read()

    t0 = time.time()
    diario = []

    def log(s):
        diario.append(s)
        print(s, flush=True)

    est = enlace.Estacao(args.papel, semente=args.semente, log=log)
    est.enviar(dados)

    wait_ready(args.out_device)
    in_dev, out_dev = resolve(args.in_device), resolve(args.out_device)
    if args.latencia is not None:
        lat = int(args.latencia * FS)
    else:
        try:
            lat = int(sd.query_devices(out_dev, 'output')['default_low_output_latency'] * FS)
        except Exception:
            lat = int(0.1 * FS)
    log(f"[saudacao] papel {args.papel}, entrada {sd.query_devices(in_dev, 'input')['name']!r}, "
        f"saída {sd.query_devices(out_dev, 'output')['name']!r}, latência {lat / FS:.3f}s, "
        f"{len(dados)} bytes a enviar")

    q = queue.Queue()
    ouvido = []

    def cb(indata, frames, time_info, status):
        q.put(indata[:, 0].copy())

    def alimenta():
        n = 0
        while True:
            try:
                x = q.get_nowait()
            except queue.Empty:
                return n
            ouvido.append(x)
            est.ouvir(x)
            n += len(x)

    aviso.inicio("MICROFONE E ALTO-FALANTE", f"saudação acústica ({args.papel})")
    stream = sd.InputStream(samplerate=FS, channels=1, blocksize=BLOCO,
                            device=in_dev, callback=cb)
    try:
        stream.start()
        concluido = False
        while time.time() - t0 < args.duracao:
            try:
                x = q.get(timeout=0.5)
            except queue.Empty:
                continue
            ouvido.append(x)
            est.ouvir(x)
            alimenta()
            burst = est.passo()
            if burst is not None:
                # Quanto de entrada chegou enquanto `passo` decidia: o áudio
                # vai soar depois disso, mais a latência da saída.
                atraso = sum(len(c) for c in list(q.queue)) + lat
                est.desloca_saida(atraso)
                sd.play(_fan_out(np.clip(burst, -1, 1).astype(np.float32), out_dev),
                        FS, device=out_dev)
            if (not concluido and est.aberto and est.confirmado and not est.fila
                    and est.pendente_tx is None):
                concluido = True
                log(f"[saudacao] tudo enviado e confirmado em {time.time() - t0:.1f}s; "
                    f"recebidos {len(est.recebido)} bytes")
                if args.receber_em:
                    open(args.receber_em, 'wb').write(bytes(est.recebido))
    except KeyboardInterrupt:
        log("[saudacao] interrompido")
    finally:
        sd.stop()
        stream.stop()
        stream.close()
        aviso.fim("saudação acústica")
        audio = np.concatenate(ouvido) if ouvido else np.zeros(0)
        meta = dict(mode='enlace', label=f'enlace-{args.papel}', papel=args.papel,
                    saudado=est.saudado, aberto=est.aberto,
                    confirmado=getattr(est, 'confirmado', False),
                    contrato_tx=est.contrato_tx.descreve() if est.contrato_tx else None,
                    contrato_rx=est.contrato_rx.descreve() if est.contrato_rx else None,
                    recebidos=len(est.recebido), diario=diario,
                    nota="sessão do enlace; não é uma captura para bench/resultado")
        stem = recording.save(args.out, audio, dados, **meta)
        print(f"[saudacao] sessão gravada em {stem}", flush=True)
        if args.receber_em and est.recebido:
            open(args.receber_em, 'wb').write(bytes(est.recebido))
    sys.exit(0 if est.aberto else 1)


if __name__ == '__main__':
    main()
