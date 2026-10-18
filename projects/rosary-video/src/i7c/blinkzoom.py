# blinkzoom.py -> blinkzoom.jpg : home vs blink peak (x4) for listed figures, plus L stats
import json,numpy as np
from PIL import Image
P='../pub/'
rows=[]
JOBS=[(i,fg,g) for i in ['C2','C3','C4','C5'] for fg in json.load(open('cfg_%s.json'%i))['figs'] for g in ['blink','blink2'] if g in json.load(open('cfg_%s.json'%i))['figs'][fg]['gestures']]
for i,fg,g in JOBS:
    cut=json.load(open(P+'i7/cut/%s/cut.json'%i)); c=cut[fg]; G=[x for x in c['gestures'] if x['name']==g][0]
    sh=np.asarray(Image.open(P+G['file'])); W,H=c['w'],c['h']
    k=4; r,cc=divmod(k,G['cols']); fr=sh[r*H:(r+1)*H,cc*W:(cc+1)*W]
    home=np.asarray(Image.open(P+c['home']))
    cfg=json.load(open('cfg_%s.json'%i))['figs'][fg]; fj=[f for f in json.load(open('../scripts/i5/work/%s_figs.json'%i))['figs'] if f['name']==fg][0]
    hx,hy,rx,ry=cfg['head']; x0,y0=int(hx-fj['px'][0]-rx*1.1),int(hy-fj['px'][1]-ry*0.8); x1,y1=int(x0+rx*2.2),int(y0+ry*1.4)
    pl=np.asarray(Image.open(P+'i5/%s_plate.jpg'%i).convert('RGB')).astype(float); ox,oy=fj['px'][:2]
    def flat(im):
        al=im[...,3:]/255.; bg=pl[oy:oy+im.shape[0],ox:ox+im.shape[1]]; return (im[...,:3]*al+bg*(1-al)).astype(np.uint8)
    a,b=flat(home)[y0:y1,x0:x1],flat(fr)[y0:y1,x0:x1]
    if g=='smile':
        import scipy.ndimage as nd
        lap=lambda im: nd.laplace(im.mean(2).astype(float)).var()
        print(i,fg,'smile laplace var ratio',round(lap(b)/lap(a),2))
    rows.append(np.hstack([a,b])); print(len(rows),i,fg,g)
Wm=max(r.shape[1] for r in rows)
st=np.vstack([np.pad(r,((0,4),(0,Wm-r.shape[1]),(0,0)),constant_values=255) for r in rows])
Image.fromarray(st).resize((st.shape[1]*4,st.shape[0]*4),Image.LANCZOS).save('blinkzoom.jpg',quality=90)
