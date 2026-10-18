# python cutfaces.py <id>  -> review/<id>/zoom_cut_<fig>.jpg : per gesture home | peak frame | |diff|*4 , cropped to region of change (padded)
import json,sys,numpy as np
from PIL import Image,ImageDraw
S='/tmp/claude-0/-home-user/7ead4a65-9a3f-5f74-8eac-6850f8d7f07d/scratchpad'
id=sys.argv[1];C=json.load(open(f'{S}/pub/i7/cut/{id}/cut.json'))
for fig,c in C.items():
    home=Image.open(f"{S}/pub/{c['home']}").convert('RGBA');w,h=c['w'],c['h']
    H0=np.asarray(home).astype(float);H=np.concatenate([H0[...,:3]*H0[...,3:]/255,H0[...,3:]],2)
    rows=[]
    for g in c['gestures']:
        sh=Image.open(f"{S}/pub/{g['file']}").convert('RGBA')
        fr=[(lambda a:np.concatenate([a[...,:3]*a[...,3:]/255,a[...,3:]],2))(np.asarray(sh.crop(((k%g['cols'])*w,(k//g['cols'])*h,(k%g['cols']+1)*w,(k//g['cols']+1)*h))).astype(float)) for k in range(g['frames'])]
        d=[np.abs(f-H).mean() for f in fr];pk=int(np.argmax(d))
        e0=np.abs(fr[0]-H).mean();e1=np.abs(fr[-1]-fr[0]).max();H=fr[0];d=[np.abs(f-H).mean() for f in fr];pk=int(np.argmax(d))
        D=np.abs(fr[pk][...,:3]-H[...,:3]).max(2)
        ys,xs=np.where(D>20)
        if len(xs)==0: box=(0,0,w,h)
        else:
            # region of change on face: use top 45% if there
            box=(max(0,xs.min()-20),max(0,ys.min()-20),min(w,xs.max()+20),min(h,ys.max()+20))
        print(fig,g['name'],'frames',g['frames'],'peak',pk,'meanΔ %.2f'%d[pk],'home-vs-f0 meanΔ %.2f end-vs-f0 maxΔ %.0f'%(e0,e1),'changebox',box)
        bg=lambda a:Image.alpha_composite(Image.new('RGBA',(w,h),(60,60,60,255)),Image.fromarray(np.concatenate([a[...,:3],np.full(a.shape[:2]+(1,),255.)],2).astype('uint8'))).convert('RGB')
        hm=bg(H).crop(box);pm=bg(fr[pk]).crop(box);dm=Image.fromarray((D*4).clip(0,255).astype('uint8')).convert('RGB').crop(box)
        bw,bh=hm.size;s=min(2.0,400/max(bh,1),300/max(bw,1))
        R=Image.new('RGB',(int(bw*s)*3+8,int(bh*s)+14),(0,0,0))
        for k,im in enumerate([hm,pm,dm]):R.paste(im.resize((int(bw*s),int(bh*s)),Image.LANCZOS),(k*(int(bw*s)+4),14))
        ImageDraw.Draw(R).text((2,1),f'{fig} {g["name"]} peak {pk}',fill=(255,255,0));rows.append(R)
    W=max(r.size[0] for r in rows);Ht=sum(r.size[1] for r in rows)
    O=Image.new('RGB',(W,Ht));y=0
    for r in rows:O.paste(r,(0,y));y+=r.size[1]
    O.save(f'{S}/review/{id}/zoom_cut_{fig}.jpg',quality=90)
