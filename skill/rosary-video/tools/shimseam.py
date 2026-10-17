# python shimseam.py <id> [t1 t2] -> per shimmer rect: diff energy inside/outside 4px bands along top/bottom/left/right edges (warped frames), + review/<id>/zoom_shim_<k>.jpg (frame t1 | |diff|*6), 2x
import json,sys,numpy as np
from PIL import Image
S='/tmp/claude-0/-home-user/7ead4a65-9a3f-5f74-8eac-6850f8d7f07d/scratchpad'
id=sys.argv[1];t1,t2=(float(sys.argv[2]),float(sys.argv[3])) if len(sys.argv)>3 else (4.0,6.0)
d=f'{S}/review/{id}/snap';meta={m['t']:m for m in json.load(open(d+'/dm.json'))['meta']};PW,PH=1376,768
def warp(t):
    b=meta[t]['b'];return Image.open(d+'/t_%.2f.png'%t).convert('RGB').transform((PW,PH),Image.AFFINE,(b['w']/PW,0,b['ox'],0,b['h']/PH,b['oy']),resample=Image.BICUBIC)
A=warp(t1);B=warp(t2);D=np.abs(np.asarray(A).astype(float)-np.asarray(B).astype(float)).mean(2)
Dm=Image.fromarray(np.clip(D*6,0,255).astype('uint8')).convert('RGB')
F=json.load(open(f'{S}/pub/i6/fx/{id}.json'))
for k,s in enumerate(F.get('shimmer',[])):
    X0,X1,Y0,Y1=int(s.get('x0',0)*PW),int(s.get('x1',1)*PW),int(s['y0']*PH),int(s['y1']*PH)
    inner=D[Y0:Y1,X0:X1].mean()
    bands={'top':(D[Y0:Y0+4,X0:X1],D[max(0,Y0-4):Y0,X0:X1]),'bot':(D[Y1-4:Y1,X0:X1],D[Y1:Y1+4,X0:X1]),
           'left':(D[Y0:Y1,X0:X0+4],D[Y0:Y1,max(0,X0-4):X0]),'right':(D[Y0:Y1,X1-4:X1],D[Y0:Y1,X1:X1+4])}
    txt=' '.join(f"{n}:{a.mean():.1f}/{b.mean():.1f}" if b.size else f"{n}:{a.mean():.1f}/-" for n,(a,b) in bands.items())
    print(f"{id} shim{k} {s.get('note','')[:28]:28s} inner {inner:.2f}  in/out {txt}")
    box=(max(0,X0-40),max(0,Y0-40),min(PW,X1+40),min(PH,Y1+40))
    ims=[i.crop(box) for i in (A,Dm)];w,h=ims[0].size;sc=2 if w<500 else 1
    O=Image.new('RGB',(w*sc,h*sc*2+4));[O.paste(im.resize((w*sc,h*sc)),(0,j*(h*sc+4))) for j,im in enumerate(ims)];O.save(f'{S}/review/{id}/zoom_shim_{k}.jpg',quality=92)
