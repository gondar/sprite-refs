import json,sys,numpy as np
from PIL import Image
S='/tmp/claude-0/-home-user/7ead4a65-9a3f-5f74-8eac-6850f8d7f07d/scratchpad'
id=sys.argv[1]; boxes=json.loads(sys.argv[2]); PW,PH=1376,768
d=f'{S}/review/{id}/snap_dense'; meta=json.load(open(d+'/dm.json'))['meta']
rows=[]
for nm,(x0,y0,x1,y1) in boxes.items():
    res=[]
    for m in meta:
        b=m['b']; sx=b['w']/PW; sy=b['h']/PH
        X0,Y0,X1,Y1=b['ox']+x0*sx,b['oy']+y0*sy,b['ox']+x1*sx,b['oy']+y1*sy
        im=Image.open(d+'/t_%.2f.png'%m['t']).convert('RGB')
        L=np.asarray(im.convert('L').crop((int(X0),int(Y0),int(X1),int(Y1)))).astype(float)
        res.append((m['t'],np.percentile(L,97),(int(X0)-12,int(Y0)-12,int(X1)+12,int(Y1)+12)))
    p=np.array([r[1] for r in res]); med=np.median(p)
    bl=[r for r in res if r[1]<med-15]
    print(id,nm,'median p97 %.0f'%med,'blink frames',[(r[0],round(r[1])) for r in bl])
    pick=sorted(bl,key=lambda r:r[1])[:3]
    home=[r for r in res if abs(r[1]-med)<3][0]
    for r in [home]+pick:
        im=Image.open(d+'/t_%.2f.png'%r[0]).convert('RGB').crop(r[2]); rows.append(im.resize((im.width*4,im.height*4),Image.LANCZOS))
W=sum(r.width for r in rows); H=max(r.height for r in rows)
out=Image.new('RGB',(W,H),'white'); x=0
for r in rows: out.paste(r,(x,0)); x+=r.width
out.save(f'{S}/review/{id}/zoom_r2_blink.jpg',quality=92)
