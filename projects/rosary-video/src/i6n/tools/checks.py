# checks.py : ends against home, colour drift, fringe crops, pounce offset, swat peaks
import json, numpy as np
from PIL import Image
S='/tmp/claude-0/-home-user/7ead4a65-9a3f-5f74-8eac-6850f8d7f07d/scratchpad'
def cells(name, prevdir):
    E=json.load(open(f'{prevdir}/{name}.entry.json'))[name]
    sh=np.asarray(Image.open(f'{prevdir}/{name}_sheet.png').convert('RGBA'),float)
    cw,ch,cols=E['cw'],E['ch'],E['cols']
    return E,[sh[(i//cols)*ch:(i//cols+1)*ch,(i%cols)*cw:(i%cols+1)*cw] for i in range(E['frames'])]
def feet(c):
    h=c[...,3]>128; yy,xx=np.nonzero(h); yb=yy.max(); sel=yy>=yb-3; return float(xx[sel].mean()), float(yb)
def place(c, anchor, W=1100, H=500, at=(550,420)):
    out=np.zeros((H,W,4)); dx=int(round(at[0]-anchor[0])); dy=int(round(at[1]-anchor[1]))
    h,w=c.shape[:2]; out[dy:dy+h,dx:dx+w]=c; return out
def diff(a,b):
    pa=a[...,3:4]/255; pb=b[...,3:4]/255
    A=np.dstack([a[...,:3]*pa,a[...,3:4]]); B=np.dstack([b[...,:3]*pb,b[...,3:4]])
    d=np.abs(A-B); m=(a[...,3]>0)|(b[...,3]>0)
    return d[m].mean(), int((d.max(2)>40).sum())
rep={}
Eh_sit,Ch_sit=cells('idle_look',S+'/i6/prev'); Eh_land,Ch_land=cells('stop_sniff',S+'/i6/prev')
homes={'sit':(Ch_sit[0],Eh_sit['anchor']),'land':(Ch_land[0],Eh_land['anchor'])}
src={'look_up_follow':'sit','bat_reach':'sit','happy_hop':'sit','sniff_up':'sit','pounce':'land','crouch_takeoff':'land'}
for nm,h in src.items():
    E,C=cells(nm,'prev'); hc,ha=homes[h]
    H=place(hc,ha); F0=place(C[0],E['anchor'])
    r={'first_vs_home':diff(F0,H)}
    if nm=='pounce':
        a0=feet(C[0]); a1=feet(C[-1]); off=[round(a1[0]-a0[0],1),round(a1[1]-a0[1],1)]; r['end_offset_px']=off
        L=place(C[-1],[E['anchor'][0]+off[0],E['anchor'][1]+off[1]]); r['last_vs_home_shifted']=diff(L,H)
    elif nm=='crouch_takeoff':
        r['last_vs_home']=diff(place(C[-1],E['anchor']),H)
    else:
        r['last_vs_home']=diff(place(C[-1],E['anchor']),H)
    # colour drift: mean RGB of the opaque interior per frame vs home
    from scipy import ndimage as ndi
    hm=ndi.binary_erosion(hc[...,3]>250,iterations=3); mu0=hc[...,:3][hm].mean(0)
    dr=[]
    for c in C:
        m=ndi.binary_erosion(c[...,3]>250,iterations=3); dr.append(np.abs(c[...,:3][m].mean(0)-mu0).sum())
    r['colour_drift_max']=round(float(max(dr)),1); r['colour_drift_mean']=round(float(np.mean(dr)),1)
    # fringe: semi-transparent edge pixels whose colour is bluish (ground spill) or very dark (halo)
    fr=[]
    for c in C:
        e=(c[...,3]>10)&(c[...,3]<240); px=c[...,:3][e]
        blue=(px[:,2]>px[:,0]+10)&(px[:,2]>px[:,1]); fr.append(blue.mean() if len(px) else 0)
    r['edge_bluish_frac_max']=round(float(max(fr)),3)
    rep[nm]=r
print(json.dumps(rep,indent=1))
json.dump(rep,open('checks.json','w'),indent=1)
