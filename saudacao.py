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
import os
import queue
import sys
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
    args = ap.parse_args()
    if args.log:
        sys.stdout = sys.stderr = open(args.log, 'a', encoding='utf-8', buffering=1)

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
    passo_ms = 0.0

    def estado(fase):
        lag = (time.time() - t_stream - pausa_s
               - (time.time() - pausa_t if pausa_t else 0) - est.agora / FS)
        return dict(papel=args.papel, fase=fase, estado_estacao=getattr(est, 'estado', None),
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
                    ultimas=diario[-5:])

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
            pn.audio(x)
            if not pausado:
                est.ouvir(x)
            n += len(x)

    aviso.inicio("MICROFONE E ALTO-FALANTE", f"saudação acústica ({args.papel})")
    stream = sd.InputStream(samplerate=FS, channels=1, blocksize=BLOCO,
                            device=in_dev, callback=cb)
    t_stream = time.time()
    try:
        stream.start()
        while True:
            if time.time() - t0 >= args.duracao:
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
                    sd.stop()
                elif c == 'retoma' and pausado:
                    pausado, pausa_s, pausa_t = False, pausa_s + time.time() - pausa_t, None
            if finalizar and est.agora >= est.livre_em and not est.agenda:
                motivo = 'finalizada pelo painel'
                break
            if (concluido and args.fim_silencio
                    and est.agora - est.ouvido_em > args.fim_silencio * FS
                    and est.agora >= est.livre_em and not est.agenda):
                motivo = f'nada ouvido por {args.fim_silencio:.0f}s depois de concluída'
                log(f"[saudacao] {motivo}; saindo")
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
        if motivo == 'duração esgotada':
            motivo = 'interrompida'
        log(f"[saudacao] {motivo}")
    finally:
        sd.stop()
        stream.stop()
        stream.close()
        aviso.fim("saudação acústica")
        audio = np.concatenate(ouvido) if ouvido else np.zeros(0)
        meta = dict(mode='enlace', label=f'enlace-{args.papel}', papel=args.papel,
                    modo_dados=args.modo_dados,
                    saudado=est.saudado, aberto=est.aberto,
                    confirmado=getattr(est, 'confirmado', False),
                    contrato_tx=est.contrato_tx.descreve() if est.contrato_tx else None,
                    contrato_rx=est.contrato_rx.descreve() if est.contrato_rx else None,
                    recebidos=len(est.recebido), diario=diario, fim=motivo,
                    duracao_parede_s=round(time.time() - t0, 1),
                    estacao_s=round(est.agora / FS, 1),
                    nota="sessão do enlace; não é uma captura para bench/resultado")
        recording.save_as(stem, audio, dados,
                          recorded=os.path.basename(stem)[:15], **meta)
        pn.publica(dict(estado('terminada'), fim=motivo), forca=True)
        pn.fecha()
        print(f"[saudacao] sessão gravada em {stem}", flush=True)
        if args.receber_em and est.recebido:
            open(args.receber_em, 'wb').write(bytes(est.recebido))
    sys.exit(0 if est.aberto else 1)


if __name__ == '__main__':
    main()
