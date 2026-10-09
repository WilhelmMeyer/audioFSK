import numpy as np, sys
sys.path.insert(0,'/home/willj/audioFSK')
import enlace as E
x=np.load(sys.argv[1]).astype(np.float32)
o=E.Ouvido()
for i in range(0,len(x),2048): o.acrescenta(x[i:i+2048]); o.varre()
print("marcas achadas:"); [print(f"  {p/E.FS:7.2f}s {t:8s} {s:.2f}") for p,t,s in o.marcas]
qs=[p for p,t,_ in o.marcas if t=='quadro']
for p1 in qs:
    for d in E.ABORDAGENS:
        p2=[q for q in qs if abs(q-(p1+d.amostras-E.LQ))<=int(0.004*d.amostras)]
        if not p2: continue
        corpo,llr=E.le_quadro(x,p1,d,p2[0])
        import fec
        ber=None
        if llr is not None:
            bs=[]
            for i,a in enumerate([1,1,0,3]):
                r=np.array(list(fec.frame(E.empacota(E.OLA,0x40+i,bytes([a]),E.CTRL_N),repeat=d.rep)))[len(fec.SYNC):][:len(llr)]
                l=np.asarray(llr)[:len(r)]
                bs.append(min(np.mean((l>0)!=(r==1)),np.mean((l<0)!=(r==1))))
            ber=min(bs)
        msg='CRC OK '+repr(E.abre(corpo)) if corpo is not None else 'CRC falhou'
        print(f"  quadro {p1/E.FS:.2f}-{p2[0]/E.FS:.2f}s como {d.nome}: {msg}, bits errados {ber if ber is None else round(ber,3)}")
