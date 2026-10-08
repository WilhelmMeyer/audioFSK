"""F-E: deriva de relogio entre a caixa (Windows, B) e o microfone (Linux, A).
Para cada gravacao de 2026-10-08 com sync_chirp, o periodo medido entre as duas
varreduras (amostras por simbolo; nominal 480) via align.probe, a mesma funcao
que o align.py usa. Cada par .wav/.json e copiado para uma pasta temporaria e
align.py roda sobre ela (saida em align-saida.txt). Figura: periodo por gravacao."""
import csv, glob, os, shutil, subprocess, sys, tempfile
import numpy as np
AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, '..', '..', '..'))
sys.path.insert(0, os.path.join(AQUI, '..')); sys.path.insert(0, RAIZ)
import recording, align  # noqa: E402
from plota import Fig, CORES, draw_text, TEXTO  # noqa: E402

CAP = os.path.join(RAIZ, 'captures')
POSICAO = {'20261008-161939': 1, '20261008-162232': 1, '20261008-162241': 1,
           '20261008-162821': 2, '20261008-162831': 2, '20261008-162926': 2,
           '20261008-162936': 2, '20261008-164832': 3, '20261008-164852': 3}
tmp = tempfile.mkdtemp(prefix='alinha-')
for j in sorted(glob.glob(os.path.join(CAP, '20261008-*.json'))):
    import json
    if json.load(open(j)).get('sync_chirp') and os.path.basename(j)[:15] in POSICAO:
        shutil.copy(j, tmp); shutil.copy(j[:-5] + '.wav', tmp)
out = subprocess.run([sys.executable, os.path.join(RAIZ, 'align.py'), tmp], capture_output=True, text=True, cwd=RAIZ)
open(os.path.join(AQUI, 'align-saida.txt'), 'w').write(out.stdout + out.stderr)
print(out.stdout[-900:])
rows = []
for samples, payload, meta in recording.load_all(tmp):
    if meta.get('kind') != 'fec' or meta.get('mode') != 'mary':
        continue
    r = align.probe(samples, payload, meta, 16)
    p_acc, p_ok, per = r[5]
    if per is None:
        rows.append([meta['recorded'], meta['label'], POSICAO[meta['recorded']], 'sim' if meta.get('ifk') else 'nao', '', '', '', '', ''])
        continue
    rows.append([meta['recorded'], meta['label'], POSICAO[meta['recorded']], 'sim' if meta.get('ifk') else 'nao',
                 '%.3f' % per, '%.1f' % (per - 480), '%.0f' % ((per - 480) / 480 * 1e6), '%.1f' % (100 * p_acc), int(bool(p_ok))])
rows.sort()
sem = [r[1] for r in rows if r[4] == '']
rows_ok = rows
rows = [r for r in rows if r[4] != '']
print('sem par de varreduras achado:', sem)
with open(os.path.join(AQUI, 'periodo-medido.csv'), 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['gravacao', 'rotulo', 'posicao', 'ifk', 'periodo_amostras_por_simbolo', 'desvio_do_nominal_amostras',
                                   'desvio_ppm', 'bits_certos_duas_varreduras_pct', 'bloco_ok']); w.writerows(rows_ok)
per = np.array([float(r[4]) for r in rows])
print('periodo medido: media %.3f, min %.3f, max %.3f, desvio %.3f; ppm medio %.0f' % (per.mean(), per.min(), per.max(), per.std(), (per.mean() - 480) / 480 * 1e6))
fig = Fig(1000, 580, (0.5, len(rows) + 0.5), (479.6, 480.4), 'gravacao (ordem cronologica; cor = posicao)', 'amostras por simbolo',
          'F-E periodo medido entre as duas varreduras (nominal 480)', xticks=range(1, len(rows) + 1), yticks=np.arange(479.6, 480.41, 0.1))
fig.line([0.5, len(rows) + 0.5], [480, 480], (120, 120, 120), 0)
for i, r in enumerate(rows):
    X = fig.px(i + 1); Y = fig.py(float(r[4]))
    c = CORES[int(r[2]) - 1]
    fig.img[Y - 5:Y + 6, X - 5:X + 6] = c
for k in (1, 2, 3):
    fig.legenda('posicao %d' % k, CORES[k - 1])
fig.salva(os.path.join(AQUI, 'fig-e-periodo-medido.png'))
shutil.rmtree(tmp)
