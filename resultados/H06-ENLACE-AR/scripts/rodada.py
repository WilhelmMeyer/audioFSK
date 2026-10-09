import numpy as np, sys
sys.path.insert(0,sys.argv[2]+'/det')
from det import *
S=sys.argv[2]
x=np.load(sys.argv[1]).astype(float); fs=FS
print("piso rms %.4f, pico %.3f"%(np.sqrt(np.mean(x[:fs]**2)),abs(x).max()))
marcas=[('chamada', 0), ('chamada', 43200), ('chamada', 86400), ('quadro', 129600), ('quadro', 167040), ('quadro', 204480), ('sonda', 241920), ('sonda', 279360), ('sonda', 316800), ('ola0', 354240), ('ola1', 588000)]
sc={k:real(x,E.MOLDES[k]) for k in ('chamada','quadro','sonda')}
# round starts: top chamada peaks
s=sc['chamada'].copy(); pk=[]
for _ in range(6):
    k=np.argmax(s); pk.append(k); s[max(0,k-fs//3):k+fs//3]=0
pk=sorted(pk); t1=pk[0]; a=t1+int(20.0*fs); t2=a+np.argmax(sc['chamada'][a:a+int(1.6*fs)]); inicios=[t1,t2]
LQ=E.LQ
for r,(t0,vol) in enumerate(zip(inicios,('1.00','0.20'))):
    print(f"--- volume {vol} (início {t0/fs:.2f}s)")
    for rot,off in marcas:
        if rot.startswith('ola'):
            d=E.ABORDAGENS[int(rot[-1])]; p1=t0+off
            sq=sc['quadro']; a=p1-fs//50; p1=a+np.argmax(sq[a:p1+fs//50])
            nom=LQ+2*E.HUSH+d.nsym*E.SPS; b=p1+nom-fs//50; p2=b+np.argmax(sq[b:b+fs//25])
            corpo,llr=E.le_quadro(x,p1,d,p2)
            import fec
            ref=np.array(list(fec.frame(E.empacota(E.OLA,0x5A,b'teste',E.CTRL_N),repeat=d.rep)))
            ref=ref[len(ref)-len(llr):] if llr is not None else ref
            ber=None if llr is None else np.mean((np.asarray(llr)[:len(ref)]<0)!=(ref==1)) 
            ber2=None if llr is None else np.mean((np.asarray(llr)[:len(ref)]>0)!=(ref==1))
            print(f"  {rot} {d.nome}: marcas {sq[p1]:.2f}/{sq[p2]:.2f}, período medido {(p2-p1-LQ-2*E.HUSH)/d.nsym:.2f}, bits errados {min(ber,ber2) if ber is not None else '-'}, CRC {'OK '+repr(E.abre(corpo)) if corpo is not None else 'falhou'}")
        else:
            p=t0+off; s=sc[rot]; a=p-fs//50; k=a+np.argmax(s[a:p+fs//50])
            outros=max(sc[o][k-fs//50:k+fs//50].max() for o in sc if o!=rot)
            print(f"  {rot:8s} {s[k]:.2f}  (outros moldes ali: {outros:.2f})")
# falsos: quadro mold sobre o miolo dos OLA (dados)
for t0 in inicios:
    for off,d in ((354240,E.ABORDAGENS[0]),(588000,E.ABORDAGENS[1])):
        a=t0+off+LQ+E.HUSH+fs//20; b=t0+off+LQ+E.HUSH+d.nsym*E.SPS-fs//20
        print("  falso nos dados %s: quadro %.2f chamada %.2f sonda %.2f"%(d.nome,*(sc[k][a:b].max() for k in ('quadro','chamada','sonda'))))
