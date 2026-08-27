"""Line-oriented serial control channel, shared by linktest.py and console.py.

This is the out-of-band wire between the two machines. It never carries
modem payload -- only control. Keeping it a separate module means the two
tools cannot drift apart on framing or timeouts.
"""

import queue
import threading

import serial


class Control:
    """Line-oriented control channel with a background reader.

    The reader thread exists so the caller can sit in a blocking audio read
    (or a blocking `input()`) and still notice a line the moment it lands.
    """

    def __init__(self, port, baud, timeout=0.1):
        self.ser = serial.Serial(port, baud, timeout=timeout)
        self.lines = queue.Queue()
        self._stop = False
        self._write_lock = threading.Lock()
        threading.Thread(target=self._reader, daemon=True).start()

    def _reader(self):
        buf = bytearray()
        while not self._stop:
            try:
                chunk = self.ser.read(64)
            except Exception:
                break
            for byte in chunk:
                if byte in (0x0A, 0x0D):
                    if buf:
                        self.lines.put(buf.decode("utf-8", "replace").strip())
                        buf = bytearray()
                else:
                    buf.append(byte)

    def send(self, line):
        # Locked because the console writes from the REPL thread while a
        # meter thread writes events from another.
        with self._write_lock:
            self.ser.write((line + "\n").encode("utf-8"))
            self.ser.flush()

    def recv(self, timeout=10.0):
        try:
            return self.lines.get(timeout=timeout)
        except queue.Empty:
            return None

    def poll(self):
        try:
            return self.lines.get_nowait()
        except queue.Empty:
            return None

    def drain(self):
        while self.poll() is not None:
            pass

    def close(self):
        self._stop = True
        try:
            self.ser.close()
        except Exception:
            pass


# A multi-line reply cannot go out as-is on a line protocol, so newlines are
# escaped on the wire and restored on arrival.

def pack(text):
    return text.replace("\\", "\\\\").replace("\n", "\\n")


def unpack(text):
    out = []
    i = 0
    while i < len(text):
        if text[i] == "\\" and i + 1 < len(text):
            nxt = text[i + 1]
            if nxt == "n":
                out.append("\n")
                i += 2
                continue
            if nxt == "\\":
                out.append("\\")
                i += 2
                continue
        out.append(text[i])
        i += 1
    return "".join(out)
