import numpy as np, sys
S='/tmp/claude-1000/-home-willj-audioFSK/0605c850-c58c-4c68-a96a-b8b620ad16f4/scratchpad'
sys.path.insert(0,S+'/det'); from det import *
from scipy.signal import fftconvolve, butter, sosfiltfilt
tx=np.load(f'{S}/tocado.npy').astype(float)
marcas=[('chamada', 0), ('chamada', 43200), ('chamada', 86400), ('quadro', 129600), ('quadro', 167040), ('quadro', 204480), ('sonda', 241920), ('sonda', 279360), ('sonda', 316800)]
for rec in ('rec_vol','rec_wdm'):
    x=np.load(f'{S}/{rec}.npy').astype(float)
    c=fftconvolve(sosfiltfilt(E._BANDA,x),tx[::-1][:len(tx)],'valid') if False else None
    y=sosfiltfilt(E._BANDA,x); c=np.abs(fftconvolve(y,tx[::-1],'full'))[len(tx)-1:]
    t0=int(np.argmax(c[:int(15*FS)]))
    print(f"=== {rec}: rodada 1 começa em {t0/FS:.3f}s")
    sc={k:real(x,E.MOLDES[k]) for k in ('chamada','quadro','sonda')}
    for k,off in marcas:
        p=t0+off; w=sc[k][p-480:p+480]; print(f"  {k} {w.max():.2f} (desvio {np.argmax(w)-480:+d} amostras)", end=';')
    print()
    for i,off in ((0,354240),(1,588000)):
        d=E.ABORDAGENS[i]; p0=t0+off+E.LQ+E.HUSH; nsym=d.nsym
        n=np.arange(408)
        def en(sig,p,j): 
            seg=sig[p+j*480+72:p+j*480+480]
            return np.array([abs(np.sum(seg*np.exp(-2j*np.pi*f*n/FS)))**2 for f in d.tons])
        sent=np.array([np.argmax(en(tx,off+E.LQ+E.HUSH,j)) for j in range(nsym)])
        R=np.array([en(x,p0,j) for j in range(nsym)])
        win=np.argmax(R,1); err=win!=sent
        chg=np.r_[True,sent[1:]!=sent[:-1]]
        for k,f in enumerate(d.tons):
            print(f"  ola{i} tom {f}: ligado/desligado {10*np.log10(np.median(R[sent==k,k])/np.median(R[sent!=k,k])):+.1f} dB, erro quando enviado {err[sent==k].mean():.2f}")
        print(f"  ola{i} erro duro {err.mean():.2f}; logo após troca {err[chg].mean():.2f} (n={chg.sum()}), dentro de sequência {err[~chg].mean():.2f} (n={(~chg).sum()})")
    # cauda: depois da chamada (fim em 3600), ref = trecho pleno 60-20 ms antes do fim (antes do fade de 12.5ms)
    for k,off,L,f in (('chamada',0,9600,3450),('quadro',129600,3840,3250),('sonda',241920,3840,850)):
        sos=butter(4,(f-150,f+150),btype='bandpass',fs=FS,output='sos'); yy=sosfiltfilt(sos,x)
        # instante em que o sweep passa por f
        f0,f1,dur=E.MARCAS[k]; tf=(f-f0)/(f1-f0)*dur; pf=t0+off+int(tf*FS)
        ref=10*np.log10(np.mean(yy[pf-120:pf+120]**2))
        print(f"  cauda {k} em {f} Hz (nível {ref:.0f} dB): "+' '.join(f"{ms}ms:{10*np.log10(np.mean(yy[pf+int(ms*48)-120:pf+int(ms*48)+120]**2))-ref:+.1f}" for ms in (10,20,40,80,160)))
    print("  piso na banda 3450:", end=' ')
    sos=butter(4,(3300,3600),btype='bandpass',fs=FS,output='sos'); print('%.0f dB'%(10*np.log10(np.mean(sosfiltfilt(sos,x[:FS])**2))))
