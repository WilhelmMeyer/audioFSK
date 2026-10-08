"""On-screen notice while a test is using the microphone or the loudspeaker.

Whoever sits at the machine cannot tell when a capture starts or ends -- the
tools run unattended, often launched by someone else, and a room that must
stay quiet for a recording gives no sign that it is being recorded. This puts
a notice on screen for exactly the interval the audio device is in use, and
replaces it with a short "liberado" when it is released.

Two backends, one interface:

- Linux with a desktop: `notify-send`, one bubble replaced in place.
- Windows (and Linux without `notify-send`): a small always-on-top banner,
  drawn by this same file run as a child process with tkinter. It closes when
  told to, and also when its parent dies -- it watches its own stdin, which is
  a pipe from the parent -- so a crashed test cannot leave it on screen.

Runtime only, like `app.py`: no DSP, and nothing here may fail or slow a
test. `inicio`/`fim` only post the wanted state to a worker thread, so they
return at once (spawning PowerShell or Python on Windows takes most of a
second, which would otherwise land inside a capture's timing). Do not call
them from a PortAudio callback all the same. With no display at all every
call is a no-op.

The notice is silent on purpose: a notification chime during a capture would
land in the recording it announces.

    with aviso.em_uso("microfone + alto-falante", "selfcapture, teste 3/8"):
        ...
"""

import atexit
import contextlib
import os
import queue
import shutil
import subprocess
import sys
import threading

_WIN = sys.platform == 'win32'
_NOTIFY = None if _WIN else shutil.which('notify-send')
_DESKTOP = _WIN or bool(os.environ.get('DISPLAY') or os.environ.get('WAYLAND_DISPLAY'))
_ATIVO = _DESKTOP and os.environ.get('AUDIOFSK_AVISO', '1') != '0'

_q = queue.Queue()
_worker = None
_lock = threading.Lock()


# --- backends: run only on the worker thread

class _NotifySend:
    def __init__(self):
        self.id = None

    def show(self, titulo, corpo, ativo):
        cmd = [_NOTIFY, '-a', 'audioFSK', '-p', '-h', 'boolean:suppress-sound:true',
               '-i', 'audio-input-microphone',
               '-u', 'critical' if ativo else 'normal']
        if not ativo:
            cmd.append('-e')
        if self.id is not None:
            cmd += ['-r', str(self.id)]
        out = subprocess.run(cmd + [titulo, corpo], capture_output=True,
                             text=True, timeout=3).stdout.strip()
        if out.isdigit():
            self.id = int(out)

    def close(self):
        pass


class _Banner:
    def __init__(self):
        self.proc = None

    def _kill(self):
        if self.proc and self.proc.poll() is None:
            try:
                self.proc.stdin.close()      # an 'on' banner closes on EOF
                self.proc.wait(timeout=0.5)
            except Exception:                # noqa: BLE001
                self.proc.kill()
        self.proc = None

    def show(self, titulo, corpo, ativo):
        self._kill()
        flags = 0x08000000 if _WIN else 0    # CREATE_NO_WINDOW: no console flash
        exe = sys.executable
        if _WIN and exe.lower().endswith('python.exe'):
            alt = exe[:-len('python.exe')] + 'pythonw.exe'
            exe = alt if os.path.exists(alt) else exe
        self.proc = subprocess.Popen(
            [exe, os.path.abspath(__file__), '--banner',
             'on' if ativo else 'off', titulo, corpo],
            stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL, creationflags=flags)

    def close(self):
        self._kill()


def _run():
    backend = _NotifySend() if _NOTIFY else _Banner()
    while True:
        items = [_q.get()]
        while True:                          # coalesce: the latest state wins
            try:
                items.append(_q.get_nowait())
            except queue.Empty:
                break
        try:
            if None in items:
                backend.close()
            else:
                backend.show(*items[-1])
        except Exception:                    # noqa: BLE001 - never fail a test
            pass
        for _ in items:
            _q.task_done()
        if None in items:
            return


def _post(item):
    global _worker
    if not _ATIVO:
        return
    with _lock:
        if _worker is None:
            _worker = threading.Thread(target=_run, name='aviso', daemon=True)
            _worker.start()
            atexit.register(_flush)
    _q.put(item)


def _flush():
    """At exit, let the last notice reach the screen, then take a banner down
    once it has been read."""
    try:
        if _NOTIFY:
            _q.put(None)
            _q.join()
        else:
            # The 'off' banner times itself out; just let it be spawned.
            import time
            t0 = time.time()
            while _q.unfinished_tasks and time.time() - t0 < 3:
                time.sleep(0.05)
    except Exception:                        # noqa: BLE001
        pass


def inicio(o_que, detalhe=''):
    _post((f"🔴 {o_que} EM USO", detalhe or "teste de áudio em andamento", True))


def fim(detalhe=''):
    _post(("✅ áudio liberado", detalhe or "teste terminou", False))


@contextlib.contextmanager
def em_uso(o_que, detalhe=''):
    inicio(o_que, detalhe)
    try:
        yield
    finally:
        fim(detalhe)


# --- the banner itself, when this file runs as a child process

def _banner(estado, titulo, corpo):
    import tkinter as tk
    ativo = estado == 'on'
    bg = '#c62828' if ativo else '#2e7d32'
    root = tk.Tk()
    root.overrideredirect(True)
    root.attributes('-topmost', True)
    if _WIN:
        try:
            root.attributes('-toolwindow', True)
        except tk.TclError:
            pass
    frame = tk.Frame(root, bg=bg, padx=16, pady=10)
    frame.pack()
    tk.Label(frame, text=titulo, bg=bg, fg='white',
             font=('Segoe UI' if _WIN else 'Sans', 14, 'bold')).pack(anchor='w')
    tk.Label(frame, text=corpo, bg=bg, fg='white',
             font=('Segoe UI' if _WIN else 'Sans', 10)).pack(anchor='w')
    root.update_idletasks()
    w, h = root.winfo_reqwidth(), root.winfo_reqheight()
    root.geometry(f"+{root.winfo_screenwidth() - w - 24}+{24}")

    # Parent gone or told us to go: stdin reaches EOF.
    done = threading.Event()

    def watch():
        try:
            sys.stdin.buffer.read()
        except Exception:                    # noqa: BLE001
            pass
        done.set()

    # Only the 'on' banner follows its parent; 'liberado' outlives it so the
    # last notice of a run is still read after the process has exited.
    if ativo and sys.stdin is not None:
        threading.Thread(target=watch, daemon=True).start()

    def poll():
        if done.is_set():
            root.destroy()
            return
        root.after(100, poll)

    root.after(100, poll)
    if not ativo:
        root.after(3000, root.destroy)       # "liberado" reads, then goes
    frame.bind('<Button-1>', lambda e: root.destroy())
    root.mainloop()


if __name__ == '__main__' and len(sys.argv) == 5 and sys.argv[1] == '--banner':
    _banner(*sys.argv[2:])
