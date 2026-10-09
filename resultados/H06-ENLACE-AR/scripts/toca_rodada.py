import numpy as np, sounddevice as sd, sys
sys.path.insert(0,'/home/willj/audioFSK')
import enlace as E
fs=E.FS; g=0.30; z=np.zeros(int(0.7*fs)); parts=[]; marcas=[]
def add(x, rot=None):
    if rot: marcas.append((rot, sum(len(p) for p in parts)))
    parts.append(x)
for k in ('chamada','quadro','sonda'):
    for _ in range(3): add(g*E.MOLDES[k],k); add(z)
for i in (0,1):
    d=E.ABORDAGENS[i]; corpo=E.empacota(E.OLA,0x5A,b'teste',E.CTRL_N)
    add(E.modula_quadro(d,corpo),'ola%d'%i); add(z)
x=np.concatenate(parts).astype(np.float32)
np.save(sys.argv[1], x); print(marcas, len(x)/fs)
sd.play(x,fs); sd.wait()
