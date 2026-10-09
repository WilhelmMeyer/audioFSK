import sys, numpy as np, sounddevice as sd
seg=float(sys.argv[1]); fs=48000; dev=int(sys.argv[3]) if len(sys.argv)>3 else None
x=sd.rec(int(seg*fs),samplerate=fs,channels=1,dtype='float32',device=dev); sd.wait()
np.save(sys.argv[2], x[:,0]); print('gravado', sd.query_devices(dev, 'input')['name'], 'pico', abs(x).max())
