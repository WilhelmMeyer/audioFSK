import numpy as np, sounddevice as sd, sys
sys.path.insert(0,'/home/willj/audioFSK')
import enlace as E
fs=E.FS; z=np.zeros(int(0.8*fs)); parts=[]
for k in range(2): parts += [0.3*E.MOLDES['chamada'], z]
seq=[1,1,0,3]   # lento, lento, fsk2, 16-FSK rep2
for i,a in enumerate(seq):
    d=E.ABORDAGENS[a]; parts += [E.modula_quadro(d, E.empacota(E.OLA,0x40+i,bytes([a]),E.CTRL_N)), z]
x=np.concatenate(parts).astype(np.float32); np.save(sys.argv[1],x); print(len(x)/fs,'s')
sd.play(x,fs); sd.wait()
