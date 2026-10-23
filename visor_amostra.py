"""Serve o visor com uma sessão gravada congelada, para revisar layout sem sistema.

Não abre painel, não lê microfone, não calcula nada enquanto serve: as respostas
da API são montadas uma vez, na partida, a partir dos arquivos de uma sessão já
gravada, e depois só são devolvidas. Serve para olhar e capturar a tela enquanto
um teste de verdade roda na mesma máquina -- rode com `nice -n 19`.

    nice -n 19 ./venv/bin/python visor_amostra.py sessoes-enlace/<stem> --instante 157.2
    nice -n 19 ./venv/bin/python visor_amostra.py sessoes-enlace/<stem> --terminada

`--instante T` congela a sessão como estava T segundos depois de começar (fase,
contratos e diário até ali; o espectrograma dos segundos antes de T, do WAV).
`--terminada` mostra o estado final dela, como o visor mostra depois que a
sessão acaba e o painel não responde mais.
"""

import argparse
import json
from http.server import ThreadingHTTPServer
from pathlib import Path

import numpy as np

import recording
import visor

FS = visor.FS


def monta(stem, instante, terminada):
    stem = Path(stem)
    linhas = Path(str(stem) + '.diario.txt').read_text(encoding='utf-8').splitlines()
    fim = json.loads(Path(str(stem) + '.estado.json').read_text(encoding='utf-8'))
    if terminada:
        estado, vivo = fim, False
        x = None
    else:
        linhas = [l for l in linhas if float(l.split()[0]) <= instante]
        texto = "\n".join(linhas)
        aberto = 'CANAL ABERTO' in texto
        estado = dict(fim, fase='rodando', estado_estacao='aberto' if aberto else fim.get('estado_estacao'),
                      aberto=aberto, concluido=False, confirmado=False, finalizando=False, pausado=False,
                      estacao_s=round(instante, 2), atraso_s=0.02, fila_s=0.0, passo_ms=3.0,
                      ultimas=linhas[-5:])
        estado.pop('fim', None)
        vivo = True
        x = recording.read_wav(str(stem) + '.wav').astype(np.float32)[:int(instante * FS)]
    return dict(estado=estado, vivo=vivo, linhas=linhas, x=x, nome=stem.name)


class Congelado(visor.Visor):
    """O mesmo `Visor`, com as respostas tiradas da amostra em vez do painel e do disco."""

    def __init__(self, a):
        super().__init__('.', 'nenhum-lugar')
        self.a = a
        self._audio = None

    def estado(self):
        return dict(vivo=self.a['vivo'], estado=self.a['estado'], stem=self.a['nome'],
                    sessao=None, maquina='amostra', agora='--:--:--')

    def diario(self, desde):
        ls = self.a['linhas']
        return dict(total=len(ls), linhas=ls[desde:], fonte='painel' if self.a['vivo'] else 'disco')

    def audio(self, desde, stem_pedido, cabe=40):
        x = self.a['x']
        if x is None:
            return dict(stem=self.a['nome'], ativo=False)
        n = len(x)
        if stem_pedido == self.a['nome'] and 0 <= desde <= n and desde >= n - visor.NFFT:
            cols = []      # nada de novo: a amostra não anda
        else:
            cabe = max(1, min(int(cabe), 600))
            ini = max(0, n - visor.NFFT - cabe * visor.PASSO)
            cols = [np.clip(np.round(visor.espectro(x[k:k + visor.NFFT])), -140, 0).astype(int).tolist()
                    for k in range(ini, n - visor.NFFT + 1, visor.PASSO)]
        cauda = x[-int(0.2 * FS):]
        b = cauda[:len(cauda) // 360 * 360].reshape(360, -1)
        agora = visor.espectro(cauda)
        i = int(np.argmax(agora))
        dom = round(float(visor._ALVO[i]), 1) if agora[i] - np.median(agora) > 18 else None
        return dict(stem=self.a['nome'], ativo=True, prox=n - visor.NFFT + 1, n=n, colunas=cols,
                    forma=np.stack([b.min(1), b.max(1)], 1).round(4).tolist(),
                    rms=round(float(np.sqrt(np.mean(cauda ** 2))), 5),
                    pico=round(float(np.max(np.abs(cauda))), 4), dominante=dom,
                    f_min=visor.F_MIN, f_max=visor.F_MAX, raias=visor.N_RAIAS,
                    passo_s=visor.PASSO / FS)

    def recebido(self):
        return dict(existe=False)

    def dispositivos(self):
        return dict(entrada=[], saida=[])

    def comando(self, cmd):
        raise RuntimeError("amostra congelada: nenhuma sessão para comandar")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('stem', help="sessão gravada, sem extensão (precisa de .diario.txt, "
                                 ".estado.json e, para --instante, .wav)")
    ap.add_argument('--instante', type=float, default=None)
    ap.add_argument('--terminada', action='store_true')
    ap.add_argument('--porta', type=int, default=7130)
    args = ap.parse_args()
    if (args.instante is None) == (not args.terminada):
        ap.error("escolha --instante T ou --terminada")
    v = Congelado(monta(args.stem, args.instante, args.terminada))
    # O POST de iniciar também não pode lançar nada aqui.
    v.sessao.inicia = lambda p: (_ for _ in ()).throw(RuntimeError("amostra congelada"))
    srv = ThreadingHTTPServer(('127.0.0.1', args.porta), visor.faz_handler(v))
    print(f"[amostra] http://127.0.0.1:{args.porta}/  ({args.stem})", flush=True)
    srv.serve_forever()


if __name__ == '__main__':
    main()
