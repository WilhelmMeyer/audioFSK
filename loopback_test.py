import numpy as np
from modem import FSKModulator, FSKDemodulator

def main():
    fs = 48000
    baud = 1200
    mod = FSKModulator(fs=fs, baud=baud)
    demod = FSKDemodulator(fs=fs, baud=baud)

    # Add a preamble (0x55 repeated) and a sync byte (0xFF) to help the receiver lock on
    preamble = bytes([0x55] * 10 + [0xFF])
    test_msg = preamble + b"Hello, FSK World! Testing 1 2 3."
    print(f"Original message: {test_msg}")

    # Modulate
    tx_signal = mod.modulate(test_msg)
    
    # Add some silence before and after
    silence = np.zeros(int(fs * 0.1)) # 100ms silence
    tx_signal = np.concatenate((silence, tx_signal, silence))

    # Add some noise (simulate channel)
    noise = np.random.normal(0, 0.05, len(tx_signal))
    rx_signal = tx_signal + noise

    # Demodulate
    demod = FSKDemodulator(fs=fs, baud=baud, squelch=0.005)
    rx_msg = demod.demodulate(rx_signal)
    
    print(f"Recovered message: {rx_msg}")
    
    if test_msg in rx_msg or rx_msg == test_msg:
        print("SUCCESS! The message was recovered correctly.")
    else:
        print("FAILED to recover message.")

if __name__ == "__main__":
    main()
