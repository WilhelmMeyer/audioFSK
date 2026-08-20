import sys
import threading
import queue
import argparse
import os
import time
import traceback
import numpy as np
import sounddevice as sd
from modem import FSKModulator, FSKDemodulator

FS = 48000
BAUD = 1200
BLOCK_SIZE = 2048

tx_byte_queue = queue.Queue()
rx_byte_queue = queue.Queue()

tx_audio_queue = queue.Queue()

# We will modulate chunks of bytes in a background thread to keep the audio callback fast
def modulator_thread_fn(mod):
    while True:
        try:
            data = []
            # Block until we have at least one byte
            b = tx_byte_queue.get()
            data.append(b)
            # Drain the queue if more bytes are available
            while not tx_byte_queue.empty():
                data.append(tx_byte_queue.get_nowait())
                
            if data:
                # Add preamble for burst
                preamble = bytes([0x55] * 10 + [0xFF])
                payload = preamble + bytes(data)
                samples = mod.modulate(payload)
                # Split into chunks and put in audio queue
                tx_audio_queue.put(samples.astype(np.float32))
                
        except Exception as e:
            print(f"Modulator thread error: {e}", file=sys.stderr)
            time.sleep(1)

tx_buffer = np.zeros(0, dtype=np.float32)

def audio_callback(indata, outdata, frames, time_info, status):
    global tx_buffer
    if status:
        print(status, file=sys.stderr)
        
    # --- RX Processing ---
    # We pass the input directly via a queue to a demodulator thread, or do it here.
    # Demodulation uses lfilter, which is quite fast in C (numpy/scipy).
    # Let's just put input samples in a queue and process outside to guarantee no dropouts.
    rx_audio_queue.put(indata[:, 0].copy())
    
    # --- TX Processing ---
    # Fill outdata from tx_buffer
    needed = frames
    out_idx = 0
    
    while needed > 0:
        if len(tx_buffer) == 0:
            try:
                tx_buffer = tx_audio_queue.get_nowait()
            except queue.Empty:
                # Pad with silence
                outdata[out_idx:, 0] = 0
                break
                
        take = min(needed, len(tx_buffer))
        outdata[out_idx : out_idx + take, 0] = tx_buffer[:take]
        tx_buffer = tx_buffer[take:]
        out_idx += take
        needed -= take

rx_audio_queue = queue.Queue()

def demodulator_thread_fn(demod):
    while True:
        try:
            samples = rx_audio_queue.get()
            rx_bytes = demod.demodulate(samples)
            if rx_bytes:
                # Remove preamble bytes if they accidentally get decoded
                # Actually, our preamble might look like data. 
                # For a simple terminal, we can just print everything and let the user ignore garbage,
                # or we can filter it out. But 0x55 is 'U' and 0xFF is a non-printable character.
                # A proper link layer would have length and CRC. For now, it's a raw serial pipe.
                rx_byte_queue.put(rx_bytes)
        except Exception as e:
            print(f"Demodulator error: {e}", file=sys.stderr)

def pty_thread_fn(master_fd):
    while True:
        try:
            # Read from PTY
            data = os.read(master_fd, 1024)
            if data:
                for b in data:
                    tx_byte_queue.put(b)
        except OSError:
            break
            
def pty_writer_thread_fn(master_fd):
    while True:
        try:
            data = rx_byte_queue.get()
            os.write(master_fd, data)
        except OSError:
            break

def stdio_thread_fn():
    while True:
        try:
            # Read 1 character at a time from stdin
            char = sys.stdin.read(1)
            if char:
                tx_byte_queue.put(ord(char))
        except:
            break

def stdio_writer_thread_fn():
    while True:
        try:
            data = rx_byte_queue.get()
            # Clean up unprintable bytes for stdio (like our 0xFF sync byte)
            clean_data = bytes([b for b in data if b < 128 and b != 0xff])
            if clean_data:
                sys.stdout.write(clean_data.decode('ascii', errors='ignore'))
                sys.stdout.flush()
        except Exception as e:
            print(f"Stdout error: {e}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description="Acoustic FSK Modem")
    parser.add_argument('--pty', action='store_true', help="Create a PTY interface (Linux/macOS only)")
    args = parser.parse_args()

    print(f"Starting FSK Modem at {BAUD} baud (Mark: 1200Hz, Space: 2200Hz)")

    mod = FSKModulator(fs=FS, baud=BAUD)
    demod = FSKDemodulator(fs=FS, baud=BAUD, squelch=0.005)

    # Start Modem threads
    threading.Thread(target=modulator_thread_fn, args=(mod,), daemon=True).start()
    threading.Thread(target=demodulator_thread_fn, args=(demod,), daemon=True).start()

    if args.pty:
        import pty
        master, slave = pty.openpty()
        slave_name = os.ttyname(slave)
        print(f"[+] Created PTY: {slave_name}")
        print(f"    Connect to it using: picocom -b {BAUD} {slave_name}")
        
        threading.Thread(target=pty_thread_fn, args=(master,), daemon=True).start()
        threading.Thread(target=pty_writer_thread_fn, args=(master,), daemon=True).start()
    else:
        print("[+] Using standard I/O (Terminal Mode). Type and press enter (or character by character if in raw mode).")
        print("    (Note: Some terminal emulators buffer until newline.)")
        threading.Thread(target=stdio_thread_fn, daemon=True).start()
        threading.Thread(target=stdio_writer_thread_fn, daemon=True).start()

    # Start audio stream
    try:
        with sd.Stream(samplerate=FS, channels=1, callback=audio_callback, blocksize=BLOCK_SIZE):
            print("[+] Audio stream active. Press Ctrl+C to exit.")
            while True:
                time.sleep(1)
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"Failed to open audio stream: {e}", file=sys.stderr)
        traceback.print_exc()

if __name__ == "__main__":
    main()
