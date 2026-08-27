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
import subprocess
import sys

REPO = os.path.dirname(os.path.abspath(__file__))

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


def _upstream():
    """Tracking ref for the current branch, or origin/main as the fallback."""
    ok, out = _git("rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")
    return out if ok and out else "origin/main"


def _is_dirty():
    ok, out = _git("status", "--porcelain")
    return bool(ok and out)


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
    ref = refs[0] if refs else _upstream()

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
    global pending_restart
    pending_restart = True
    return "reiniciando..."


def restart(cleanup=None):
    """Replace this process with a fresh one, same interpreter and same argv.

    Called only after the reply is already on the wire. cleanup() must close
    the serial port and the audio streams -- exec keeps file descriptors, so a
    still-open port would make the new process fail to open it.
    """
    if cleanup is not None:
        try:
            cleanup()
        except Exception:
            pass
    sys.stdout.flush()
    sys.stderr.flush()
    os.execv(sys.executable, [sys.executable] + sys.argv)
