import numpy as np, sys
sys.path.insert(0,'/home/willj/audioFSK')
import enlace as E
from scipy.signal import sosfiltfilt, fftconvolve, hilbert
FS=E.FS
def _cs(x): return np.concatenate([[0.0],np.cumsum(x)])
def real(x,m):
    x=sosfiltfilt(E._BANDA,x); c=np.abs(fftconvolve(x,m[::-1],'valid'))
    e=_cs(x*x); L=len(m); q=np.arange(len(c))
    return c/(np.sqrt(np.maximum(e[q+L]-e[q],0))*np.linalg.norm(m)+1e-12)
def seg(x,m,K):
    """mean over K segments of |complex corr| / energies of that segment"""
    x=sosfiltfilt(E._BANDA,x); xa=hilbert(x); ma=hilbert(m)
    L=len(m); n=len(x)-L+1; e=_cs(np.abs(xa)**2); out=np.zeros(n)
    b=np.linspace(0,L,K+1).astype(int)
    for k in range(K):
        s0,s1=b[k],b[k+1]; mk=ma[s0:s1]
        c=np.abs(fftconvolve(xa,np.conj(mk[::-1]),'valid'))[s0:s0+n]
        q=np.arange(n)+s0
        en=np.sqrt(np.maximum(e[q+s1-s0]-e[q],0))*np.linalg.norm(mk)
        out+=c/(en+1e-12)
    return out/K
def rake(x,m,W_ms=5.0,passo=16):
    """fração da energia do trecho explicada por cópias atrasadas do molde (0..W ms)"""
    x=sosfiltfilt(E._BANDA,x); xa=hilbert(x); ma=hilbert(m)
    L=len(m); W=int(W_ms*FS/1000)
    c=np.abs(fftconvolve(xa,np.conj(ma[::-1]),'valid'))**2   # len n
    n=len(c)-W
    acc=np.zeros(n)
    for t in range(0,W+1,passo): acc+=c[t:t+n]
    e=_cs(np.abs(xa)**2); q=np.arange(n)
    en=(e[q+L+W]-e[q])*np.sum(np.abs(ma)**2)
    return np.sqrt(acc/(en+1e-12))
