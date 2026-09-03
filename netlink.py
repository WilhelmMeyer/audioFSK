"""Move a capture between the two machines over the LAN instead of the cable.

The serial line is the control channel and it is the right one for commands:
it is always there, it needs no address, and it works when the network does
not. It is the wrong one for a recording. Measured on this bench, the `puxa`
path runs at 8.1 kB/s -- 94% of what 115200 baud can carry once base64's third
is paid -- so a ten-second capture costs about two minutes of cable. A campaign
of sixty recordings spends two hours moving files and ten minutes measuring.

Both machines are on the same WiFi, so the file has a much shorter way to go.
What is here is the smallest thing that does it: the stdlib's HTTP server on
one side, `urllib` on the other, no account, no daemon, no configuration.

**The receiver runs on the console side and the far machine pushes to it**,
which is the direction that matters: the far machine is the Windows one, and a
connection it opens outward meets no inbound firewall rule. The reverse -- a
server on Windows, fetched from here -- needs someone at that keyboard to allow
a listening port, and this bench exists to be driven with nobody there.

The serial cable is still what makes it work: it carries the URL. Neither side
has to know the other's address in advance, and when the network is not there
the caller falls back to `puxa` and pays the two minutes.

Deliberately not a general file server. It accepts writes only, only into the
directory it was given, only under a name it sanitises itself, and only while a
capture is in flight.
"""

import http.server
import os
import re
import socket
import threading
import urllib.error
import urllib.request
from pathlib import Path

# A capture is about 1 MB as int16 and 2 MB as float. 64 MB is far above
# anything this project records and far below anything that would fill a disk
# by accident.
MAX_BYTES = 64 * 1024 * 1024
SAFE_NAME = re.compile(r'^[A-Za-z0-9][A-Za-z0-9._-]{0,120}$')


def local_ip():
    """This machine's address on the way out, without asking the OS's tables.

    Connecting a UDP socket sends nothing -- it only makes the kernel pick the
    route and bind a source address, which is exactly the address the other
    machine has to dial. Reading it off the interface list instead means
    choosing between a docker bridge, a VPN and the WiFi, and choosing wrong
    silently.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        return s.getsockname()[0]
    except Exception:
        return '127.0.0.1'
    finally:
        s.close()


class _Handler(http.server.BaseHTTPRequestHandler):
    directory = None
    received = None

    def _reply(self, code, text):
        body = text.encode()
        self.send_response(code)
        self.send_header('Content-Type', 'text/plain')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        # The far side pings before sending: a refused connection or a silent
        # drop has to be distinguishable from a transfer that failed halfway,
        # because only the first is worth falling back to the cable for.
        self._reply(200, 'pong') if self.path.startswith('/ping') \
            else self._reply(404, 'no')

    def do_POST(self):
        name = os.path.basename(self.path.rsplit('/', 1)[-1].split('?')[0])
        if not SAFE_NAME.match(name):
            return self._reply(400, f'nome recusado: {name!r}')
        try:
            length = int(self.headers.get('Content-Length', '0'))
        except ValueError:
            return self._reply(400, 'tamanho invalido')
        if not 0 < length <= MAX_BYTES:
            return self._reply(413, f'tamanho fora de 1..{MAX_BYTES}')
        # Read to a fixed length rather than until EOF: an unbounded read is
        # how a receiver ends up holding a disk's worth of whatever arrives.
        blob, left = bytearray(), length
        while left:
            chunk = self.rfile.read(min(left, 1 << 16))
            if not chunk:
                return self._reply(400, 'conexao caiu no meio')
            blob += chunk
            left -= len(chunk)
        path = Path(self.directory) / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(bytes(blob))
        self.received.append(name)
        self._reply(200, f'ok {len(blob)}')

    def log_message(self, *args):
        pass                      # the caller's own log says what happened


class Receiver:
    """An HTTP endpoint that accepts files into one directory, briefly.

    Port 0 on purpose: the kernel picks a free one and the URL travels over
    the serial cable, so nothing has to be reserved, agreed in advance, or
    cleaned up if a previous run died holding it.
    """

    def __init__(self, directory, host=None, port=0):
        self.directory = str(directory)
        self.received = []
        handler = type('_H', (_Handler,),
                       {'directory': self.directory, 'received': self.received})
        self.server = http.server.ThreadingHTTPServer(('0.0.0.0', port), handler)
        self.host = host or local_ip()
        self.port = self.server.server_address[1]

    @property
    def url(self):
        return f'http://{self.host}:{self.port}'

    def __enter__(self):
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        return self

    def __exit__(self, *exc):
        self.server.shutdown()
        self.server.server_close()


def post_file(url, path, timeout=60.0):
    """Send one file. Returns (ok, message). Used on the machine that records."""
    path = Path(path)
    try:
        blob = path.read_bytes()
    except OSError as e:
        return False, f'nao consegui ler {path}: {e}'
    req = urllib.request.Request(f'{url.rstrip("/")}/{path.name}',
                                 data=blob, method='POST')
    req.add_header('Content-Type', 'application/octet-stream')
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return True, f'{path.name}: {resp.read().decode("utf-8", "replace")}'
    except urllib.error.URLError as e:
        return False, f'{path.name}: {e}'
    except Exception as e:
        return False, f'{path.name}: {e}'


def reachable(url, timeout=5.0):
    try:
        with urllib.request.urlopen(f'{url.rstrip("/")}/ping', timeout=timeout) as r:
            return r.read().strip() == b'pong'
    except Exception:
        return False
