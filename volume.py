"""Volume do sistema: a caixa e o microfone desta máquina, na posição do
controle deslizante (0 a 1, o "%" que o usuário vê no sistema).

Runtime, como `saudacao.py`: `enlace.py` só diz qual passo quer
(`Parte.caixa_marcas`, `Estacao.pedidos_mic`), e é aqui que o passo vira
volume de verdade. Ganho digital não tira um alto-falante do limitador; o
volume do sistema tira (CLAUDE.md, 17-SPK-LEVEL-A2B; no ar em 2026-10-29 o
Linux com a caixa a 1,0 chegava ao notebook com 10-12% de bits errados,
encostado).

As duas máquinas usam a mesma escada de posições, e não uma tabela de dB
por máquina: o pedido (2026-10-29) é que as duas partam do mesmo ponto do
controle. A tabela em dB por máquina pôs o Windows a -10 dB, a posição em
que ele já estava, e lado a lado isso soou "absurdamente alto".

Linux: `wpctl`, no sink e na fonte padrão; o número dele é o % do GNOME.

Windows: um `powershell` só, vivo a sessão inteira, com a interface
IAudioEndpointVolume compilada uma vez (a de `micvol2.ps1`), lendo
`get spk|mic` e `set spk|mic <posição>` linha a linha; a posição é o
`MasterVolumeLevelScalar`, o % do controle do Windows. Abrir um powershell por
troca leva segundos lá, e a troca tem de cair num silêncio de 0,6 s.

Os volumes de partida ficam num arquivo na pasta do usuário enquanto a
sessão roda; `restaura` os devolve no fim, e quem começar e achar o arquivo
ainda lá (a sessão anterior morreu sem restaurar) restaura dele primeiro.
"""

import json
import os
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

# Passos da caixa, posição do controle, iguais nas duas máquinas, índice
# absoluto: a mesma tabela que `enlace.CAIXA_POS` (o comprimento tem de
# bater; `saudacao` confere). A chamada sobe do passo 1 (20%) até ser
# respondida, e a sondagem e o contrato andam em volta do passo travado.
# Lado a lado em 2026-10-29: Linux a 0,40 bem; Windows a 0,50 alto demais.
# Em 2026-10-29 (20:40) o B, já no alto-falante interno, chegava ao Linux a
# rms 0,010-0,013 mesmo a 70%: o topo vai a 100%, e o refino e a margem
# descem se distorcer.
# `AUDIOFSK_CAIXA="0.15,0.2,0.3,0.4,0.55,0.7,1"` troca a tabela sem mexer no código.
CAIXA = (0.15, 0.20, 0.30, 0.40, 0.55, 0.70, 1.00)
# Microfone de quem escuta, relativo ao de partida: o passo 1 é 0,6 dele.
MIC_PASSOS = (1.0, 0.6)
# Ao acertar o som, quem ouve fraco sobe o próprio microfone por estas
# posições do controle, a partir da primeira acima da de partida, até 100%.
# No B ele estava em 20% em 2026-10-29 (19:42), e quem subiu foi só a caixa
# do chamador, até 70%. O microfone fica onde parou; a volta da sondagem
# (MIC_PASSOS) passa a ser em torno dele.
# Até 100%: o microfone digital do Linux é pouco sensível, e a 75% ainda
# ouvia o B a distância a rms 0,010-0,013 (2026-10-29, 20:40).
MIC_POS = (0.20, 0.30, 0.45, 0.60, 0.75, 1.00)
ARQUIVO = Path.home() / '.audiofsk-volume-original.json'

_PS = r'''
Add-Type -TypeDefinition @"
using System; using System.Runtime.InteropServices;
[Guid("5CDF2C82-841E-4546-9722-0CF74078229A"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IAudioEndpointVolume {
 int f(); int g(); int h();
 int SetMasterVolumeLevel(float l, Guid c); int SetMasterVolumeLevelScalar(float l, Guid c);
 int GetMasterVolumeLevel(out float l); int GetMasterVolumeLevelScalar(out float l);
 int a(); int b(); int c(); int d(); int SetMute(bool m, Guid c); int GetMute(out bool m);
 int j(); int k(); int l(); int m(); int GetVolumeRange(out float mn, out float mx, out float st);
}
[Guid("D666063F-1587-4E43-81F1-B948E807363F"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IMMDevice { int Activate(ref Guid id, int ctx, IntPtr p, [MarshalAs(UnmanagedType.IUnknown)] out object o); }
[Guid("A95664D2-9614-4F35-A746-DE8DB63617E6"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IMMDeviceEnumerator { int f(); int GetDefaultAudioEndpoint(int flow, int role, out IMMDevice d); }
[ComImport, Guid("BCDE0395-E52F-467C-8E3D-C4579291692E")] class MMDeviceEnumerator {}
public class Vol {
 static IAudioEndpointVolume V(int flow) {
  var en = (IMMDeviceEnumerator)(new MMDeviceEnumerator()); IMMDevice d; en.GetDefaultAudioEndpoint(flow, 0, out d);
  var iid = typeof(IAudioEndpointVolume).GUID; object o; d.Activate(ref iid, 23, IntPtr.Zero, out o); return (IAudioEndpointVolume)o; }
 public static string Get(int flow) { var v=V(flow); float s; bool m; v.GetMasterVolumeLevelScalar(out s); v.GetMute(out m);
  return String.Format(System.Globalization.CultureInfo.InvariantCulture, "ok {0:F3} {1}", s, m ? 1 : 0); }
 public static string Set(int flow, float s) { var v=V(flow);
  v.SetMasterVolumeLevelScalar(Math.Max(0f, Math.Min(1f, s)), Guid.Empty); v.SetMute(false, Guid.Empty); return Get(flow); }
}
"@
[Console]::Out.WriteLine("pronto"); [Console]::Out.Flush()
while ($null -ne ($l = [Console]::In.ReadLine())) {
 $p = $l.Split(' '); $flow = if ($p[1] -eq 'mic') { 1 } else { 0 }
 try {
  if ($p[0] -eq 'set') { $r = [Vol]::Set($flow, [float]::Parse($p[2], [System.Globalization.CultureInfo]::InvariantCulture)) }
  else { $r = [Vol]::Get($flow) }
 } catch { $r = "erro " + $_.Exception.Message }
 [Console]::Out.WriteLine($r); [Console]::Out.Flush()
}
'''


def _tabela_caixa():
    t = os.environ.get('AUDIOFSK_CAIXA')
    if t:
        return tuple(float(x) for x in t.split(','))
    return CAIXA


class Volume:
    """`le(qual)` e `poe(qual, v)`, v a posição do controle (0 a 1), com qual 'spk' ou 'mic'; `caixa(k)` e
    `mic(k)` põem o passo k. Uma instância por processo, chamada de uma
    thread só por vez (a trava garante)."""

    def __init__(self):
        self.trava = threading.Lock()
        self.caixa_pos = _tabela_caixa()
        self._ps = None
        if sys.platform == 'win32':
            fd, nome = tempfile.mkstemp(suffix='.ps1', prefix='audiofsk-vol-')
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                f.write(_PS)
            self._ps = subprocess.Popen(
                ['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', nome],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                text=True, encoding='utf-8', errors='replace', bufsize=1,
                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            pronto = self._ps.stdout.readline().strip()
            if pronto != 'pronto':
                raise RuntimeError(f"powershell de volume não respondeu: {pronto!r}")
        self.original = None
        self.mic_base = None

    # --- baixo nível

    def _ps_cmd(self, linha):
        self._ps.stdin.write(linha + '\n')
        self._ps.stdin.flush()
        r = self._ps.stdout.readline().strip()
        if not r.startswith('ok '):
            raise RuntimeError(f"volume ({linha}): {r}")
        return float(r.split()[1])

    @staticmethod
    def _alvo(qual):
        return '@DEFAULT_AUDIO_SINK@' if qual == 'spk' else '@DEFAULT_AUDIO_SOURCE@'

    def le(self, qual):
        with self.trava:
            if self._ps is not None:
                return self._ps_cmd(f'get {qual}')
            r = subprocess.run(['wpctl', 'get-volume', self._alvo(qual)],
                               capture_output=True, text=True, timeout=5).stdout
            return float(r.split()[1])

    def poe(self, qual, v):
        """Põe o volume na posição `v` e devolve o que ficou. O microfone sai
        sempre do mudo: no Linux ele volta mudo sozinho (memória do projeto),
        no B estava mudo a -33,5 dB em 2026-10-29."""
        with self.trava:
            if self._ps is not None:
                return self._ps_cmd(f'set {qual} {v:.3f}')
            v = max(0.0, min(1.0, v))
            subprocess.run(['wpctl', 'set-volume', self._alvo(qual), f'{v:.3f}'],
                           check=True, timeout=5)
            if qual == 'mic':
                subprocess.run(['wpctl', 'set-mute', self._alvo(qual), '0'], timeout=5)
            return v

    # --- passos

    def caixa(self, k):
        return self.poe('spk', self.caixa_pos[k])

    def mic(self, k):
        return self.poe('mic', self.mic_base * MIC_PASSOS[k])

    def proximo_mic(self, direcao=1):
        """A posição de MIC_POS um passo acima (`direcao` > 0) ou abaixo do
        microfone em uso, ou None no teto/piso. Só calcula: quem move é
        `Agenda` com 'micpos'."""
        if direcao > 0:
            acima = [v for v in MIC_POS if v > self.mic_base + 0.005]
            return acima[0] if acima else None
        abaixo = [v for v in MIC_POS if v < self.mic_base - 0.005]
        return abaixo[-1] if abaixo else None

    # --- partida e fim

    def guarda_original(self, log=print):
        """Restaura o que uma sessão anterior deixou sem restaurar, lê os
        volumes de partida e os guarda em ARQUIVO."""
        if ARQUIVO.exists():
            try:
                o = json.loads(ARQUIVO.read_text())
                self.poe('spk', o['spk'])
                self.poe('mic', o['mic'])
                log(f"[volume] a sessão anterior não restaurou o volume; restaurado do arquivo: "
                    f"caixa {o['spk']:.0%}, microfone {o['mic']:.0%}")
            except Exception as e:
                log(f"[volume] arquivo de volume antigo ilegível ({e}); ignorado")
        self.original = {'spk': self.le('spk'), 'mic': self.le('mic')}
        self.mic_base = self.original['mic']
        ARQUIVO.write_text(json.dumps(dict(self.original, pid=os.getpid())))
        log(f"[volume] de partida: caixa {self.original['spk']:.0%}, microfone "
            f"{self.original['mic']:.0%}; passos da caixa "
            f"{', '.join(f'{v:.0%}' for v in self.caixa_pos)}, microfone "
            f"{', '.join(f'{self.mic_base * m:.0%}' for m in MIC_PASSOS)}")

    def restaura(self, log=print):
        if self.original is None:
            return
        try:
            self.poe('spk', self.original['spk'])
            self.poe('mic', self.original['mic'])
            ARQUIVO.unlink(missing_ok=True)
            log(f"[volume] restaurado: caixa {self.original['spk']:.0%}, "
                f"microfone {self.original['mic']:.0%}")
        except Exception as e:
            log(f"[volume] ERRO ao restaurar ({e}); o arquivo {ARQUIVO} fica para a próxima sessão")

    def fecha(self):
        if self._ps is not None:
            try:
                self._ps.stdin.close()
                self._ps.wait(timeout=3)
            except Exception:
                self._ps.kill()


class Agenda(threading.Thread):
    """Trocas de volume na hora certa do relógio de parede, numa thread à
    parte (o `wpctl` leva ~10 ms, e o laço principal não pode esperar).
    `avisos` recebe uma linha por troca, para o diário."""

    def __init__(self, vol):
        super().__init__(daemon=True)
        self.vol = vol
        self.cv = threading.Condition()
        self.fila = []                 # [(t, qual, passo)]
        self.avisos = []
        self.atual = {'spk': None, 'mic': None}
        self.parar = False

    def poe(self, t, qual, passo):
        with self.cv:
            self.fila.append((t, qual, passo))
            self.fila.sort(key=lambda x: x[0])
            self.cv.notify()

    def limpa(self, qual):
        with self.cv:
            self.fila = [x for x in self.fila if x[1] != qual]

    def fecha(self):
        with self.cv:
            self.parar = True
            self.cv.notify()
        self.join(timeout=5)

    def run(self):
        import time
        while True:
            with self.cv:
                while not self.parar and (not self.fila or self.fila[0][0] > time.time()):
                    self.cv.wait(None if not self.fila else max(0.0, self.fila[0][0] - time.time()))
                if self.parar:
                    return
                t, qual, passo = self.fila.pop(0)
            if qual == 'micpos':
                # Microfone a uma posição nova, que passa a ser a base dos
                # passos relativos (`mic_base` já foi posto por quem pediu).
                try:
                    v = self.vol.poe('mic', passo)
                    self.atual['mic'] = 0
                    self.avisos.append(f"[volume] microfone em {v:.0%} "
                                       f"({time.time() - t:+.2f}s da hora marcada)")
                except Exception as e:
                    self.avisos.append(f"[volume] ERRO ao pôr o microfone em {passo:.0%}: {e}")
                continue
            if self.atual[qual] == passo:
                continue
            try:
                v = self.vol.caixa(passo) if qual == 'spk' else self.vol.mic(passo)
                self.atual[qual] = passo
                nome = 'caixa' if qual == 'spk' else 'microfone'
                self.avisos.append(f"[volume] {nome} no passo {passo}: {v:.0%} "
                                   f"({time.time() - t:+.2f}s da hora marcada)")
            except Exception as e:
                self.avisos.append(f"[volume] ERRO ao pôr {qual} no passo {passo}: {e}")
