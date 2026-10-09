import numpy as np, sys
sys.path.insert(0,'/home/willj/audioFSK'); import enlace as E, fec
from scipy.signal import sosfiltfilt, fftconvolve
S='/tmp/claude-1000/-home-willj-audioFSK/0605c850-c58c-4c68-a96a-b8b620ad16f4/scratchpad'
x=np.load(sys.argv[1]).astype(float); tx=np.load(S+'/tocado_lento.npy').astype(float); fs=E.FS
c=np.abs(fftconvolve(sosfiltfilt(E._BANDA,x),tx[::-1],'full'))[len(tx)-1:]; t0=int(np.argmax(c[:15*fs])); print('início %.3f'%(t0/fs))
sc={k:np.abs(fftconvolve(sosfiltfilt(E._BANDA,x),E.MOLDES[k][::-1],'valid')) for k in E.MOLDES}
def norm(k,p):
    m=E.MOLDES[k]; y=sosfiltfilt(E._BANDA,x[p:p+len(m)]); return np.dot(y,m)/np.linalg.norm(y)/np.linalg.norm(m)
off=2*(len(E.MOLDES['chamada'])+int(0.8*fs)); z=int(0.8*fs)
for i,a in enumerate([1,1,0,3]):
    d=E.ABORDAGENS[a]; p1=t0+off; p2=p1+d.amostras-E.LQ
    corpo,llr=E.le_quadro(x,p1,d,p2)
    r=np.array(list(fec.frame(E.empacota(E.OLA,0x40+i,bytes([a]),E.CTRL_N),repeat=d.rep)))[len(fec.SYNC):]
    l=np.asarray(llr)[:len(r)] if llr is not None else None
    ber=None if l is None else min(np.mean((l>0)!=(r[:len(l)]==1)),np.mean((l<0)!=(r[:len(l)]==1)))
    print(f"{d.nome}: CRC {'OK' if corpo is not None else 'falhou'}, bits errados {ber if ber is None else round(ber,3)}")
    off+=d.amostras+z
