"""Code updates over the serial channel: the slow half of the two-layer link.

The fast half is console.py's command table -- mic, speaker, gain, squelch,
acting in milliseconds. This is the other half: the far side commits to the
remote, says `pull` over the wire, and this machine fetches it.

No serial and no audio in here, same rule modem.py follows: this module only
knows git. console.py wires it to the command table.

Restart is deliberately NOT automatic after a pull. Re-exec drops both audio
streams, so a pull landing mid-measurement would silently undo the setup the
far side just dialed in. `pull` reports that a restart is due; `restart` does
it when the far side is ready.
"""

import os
import py_compile
import subprocess
import sys
import tempfile
import time

REPO = os.path.dirname(os.path.abspath(__file__))

# Where this machine follows. NOT the branch's own tracking ref: a follower
# left on some old feature branch would take `pull` backwards onto whatever
# that branch tracks, and a hard reset onto an older commit deletes the very
# files serving the link. Measured, not hypothetical -- it deleted console.py
# and took the serial channel down with it. One fixed ref, overridable per
# call with `pull <ref>`.
DEFAULT_REF = "origin/main"

# Everything that has to import for this machine to keep answering the wire.
CRITICAL = ("console.py", "serial_link.py", "modem.py", "updater.py", "xfer.py")
# Anything console.py imports belongs here. py_compile does not execute
# imports, so a module missing or broken at import time is invisible to the
# check unless it is named -- and the agent would then die on startup with the
# serial channel gone, which is the exact failure this list exists to prevent.

# Set by request_restart(), read by the agent/console loop after the reply has
# gone out on the wire. Re-execing inside execute() would kill the process
# before the far side ever heard the answer.
pending_restart = False


def _git(*args, timeout=60):
    """Run a git command in the repo. Returns (ok, output)."""
    try:
        proc = subprocess.run(
            ("git",) + args, cwd=REPO, capture_output=True, text=True,
            timeout=timeout)
    except subprocess.TimeoutExpired:
        return False, f"timeout: git {' '.join(args)}"
    except Exception as e:
        return False, f"git {' '.join(args)}: {e}"
    out = (proc.stdout + proc.stderr).strip()
    return proc.returncode == 0, out


def _current_branch():
    ok, out = _git("rev-parse", "--abbrev-ref", "HEAD")
    return out if ok else "HEAD"


def _is_dirty():
    ok, out = _git("status", "--porcelain")
    return bool(ok and out)


def _broken():
    """Which critical files are missing or will not compile.

    Checked before re-exec, because a restart onto code that cannot import is
    unrecoverable from here: the process dies, and the serial channel that
    would let the far side fix it dies with it. Compiling is not proof the
    code is correct -- it is proof the machine will still answer.
    """
    bad = []
    with tempfile.TemporaryDirectory() as cache:
        for name in CRITICAL:
            path = os.path.join(REPO, name)
            if not os.path.exists(path):
                bad.append(f"{name}: ausente")
                continue
            try:
                py_compile.compile(path, cfile=os.path.join(cache, name + "c"),
                                   doraise=True)
            except py_compile.PyCompileError as e:
                bad.append(f"{name}: {str(e).splitlines()[-1][:120]}")
            except Exception as e:
                bad.append(f"{name}: {e}")
    return bad


def version():
    """One-line answer to 'what code is this machine actually running?'"""
    ok, desc = _git("log", "-1", "--format=%h %s")
    if not ok:
        return f"git indisponivel: {desc}"
    dirty = " (MODIFICADO)" if _is_dirty() else ""
    return f"{_current_branch()} @ {desc}{dirty}"


def pull(arg=""):
    """Fetch and hard-reset onto a remote ref. Reports what changed.

    Hard reset, not merge: this machine is the follower, its working tree is
    not where work happens, and a merge conflict on a headless side with no
    keyboard is a dead end. That makes it destructive, so a dirty tree stops
    it unless 'force' is passed.
    """
    global pending_restart

    parts = arg.split()
    force = "force" in parts or "-f" in parts
    refs = [p for p in parts if p not in ("force", "-f")]
    ref = refs[0] if refs else DEFAULT_REF

    if _is_dirty() and not force:
        ok, changed = _git("status", "--porcelain")
        return ("arvore local MODIFICADA -- pull abortado.\n"
                f"{changed}\n"
                "use 'pull force' para descartar essas mudancas")

    ok, out = _git("fetch", "--all", "--prune", timeout=120)
    if not ok:
        return f"fetch falhou: {out}"

    ok, before = _git("rev-parse", "HEAD")
    if not ok:
        return f"nao consegui ler HEAD: {before}"

    ok, target = _git("rev-parse", ref)
    if not ok:
        return f"ref desconhecida {ref!r}: {target}"

    if before == target:
        return f"ja atualizado: {ref} = {before[:7]}"

    ok, files = _git("diff", "--name-only", before, target)
    if not ok:
        files = ""

    ok, out = _git("reset", "--hard", target)
    if not ok:
        return f"reset falhou: {out}"

    # Land, then check, then keep or undo. The far side can push anything,
    # including a ref that predates these files entirely; if what arrived
    # cannot run, going back is the only move that leaves the serial channel
    # alive to be told about it.
    bad = _broken()
    if bad:
        back_ok, back_out = _git("reset", "--hard", before)
        lines = [f"codigo em {target[:7]} NAO carrega -- pull revertido:"]
        lines.extend(bad)
        lines.append(f"de volta em {before[:7]}" if back_ok
                     else f"REVERSAO TAMBEM FALHOU: {back_out}")
        return "\n".join(lines)

    names = [f for f in files.split("\n") if f]
    # Only Python changes need the process replaced; a README or a config
    # sample does not justify dropping the audio streams.
    if any(f.endswith(".py") for f in names):
        pending_restart = True

    log_ok, log = _git("log", "--oneline", f"{before}..{target}")
    lines = [f"{before[:7]} -> {target[:7]} ({ref})"]
    if log_ok and log:
        lines.append(log)
    lines.append(f"{len(names)} arquivo(s): {', '.join(names) if names else '-'}")
    lines.append("RESTART NECESSARIO -- mande 'restart'" if pending_restart
                 else "sem mudanca em .py, restart dispensavel")
    return "\n".join(lines)


def request_restart():
    """Arm the restart, unless restarting would take this machine off the air."""
    global pending_restart
    bad = _broken()
    if bad:
        return "\n".join(["restart RECUSADO -- o codigo em disco nao carrega:"]
                         + bad + ["conserte e mande de novo, ou 'pull force'"])
    pending_restart = True
    return "reiniciando..."


def restart(cleanup=None):
    """Replace this process with a fresh one, same interpreter and same argv.

    Called only after the reply is already on the wire. cleanup() must close
    the serial port and the audio streams -- exec keeps file descriptors, so a
    still-open port would make the new process fail to open it.

    orig_argv, not sys.argv: sys.argv drops the interpreter's own flags, so a
    process started as `python -u console.py ...` would come back fully
    buffered and its log would go quiet -- which reads exactly like a restart
    that never happened.
    """
    if cleanup is not None:
        try:
            cleanup()
        except Exception:
            pass
    sys.stdout.flush()
    sys.stderr.flush()
    argv = list(getattr(sys, "orig_argv", [])) or [sys.executable] + sys.argv

    if os.name == "nt":
        # execv does not mean the same thing on Windows. There is no image
        # replacement in the C runtime's exec family: it spawns a new process
        # and kills this one, and the replacement loses the console it was
        # started from. Observed twice from the Linux side -- the agent went
        # silent on `restart` and never answered again, which reads exactly
        # like code that will not import, and was not.
        #
        # Spawn deliberately instead, then leave. The pause is for the serial
        # port: cleanup() has closed it, but the handle is not necessarily
        # free the instant close() returns, and the replacement opening it too
        # early fails on the one channel that could report the failure.
        time.sleep(1.0)
        subprocess.Popen(argv, close_fds=False)
        sys.stdout.flush()
        os._exit(0)

    os.execv(argv[0], argv)
