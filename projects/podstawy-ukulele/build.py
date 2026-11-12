import json, numpy as np, os, shutil
from PIL import Image
OUT='/home/user/MusicGames/ukulele-warmup/art/podstawy'
def crop(im,pad=8):
    b=im.getbbox(); x0,y0,x1,y1=b
    return im.crop((max(0,x0-pad),max(0,y0-pad),min(im.width,x1+pad),min(im.height,y1+pad)))
def fit(im,maxside):
    s=min(1,maxside/max(im.size)); return im.resize((round(im.width*s),round(im.height*s)),Image.LANCZOS) if s<1 else im
def clean(im):
    # kill green spill on soft edges, zero RGB under alpha 0
    a=np.array(im).astype(float); r,g,b,al=a[...,0],a[...,1],a[...,2],a[...,3]
    m=np.maximum(r,b); spill=(g>m)&(al<250); a[...,1]=np.where(spill,np.minimum(g,m+4),g)
    a[...,:3][al==0]=0
    return Image.fromarray(a.clip(0,255).astype('uint8'),'RGBA')
def save(im,name,q=86):
    p=f'{OUT}/{name}'; im.save(p,'WEBP',quality=q,method=6); return {'file':name,'w':im.width,'h':im.height,'kb':round(os.path.getsize(p)/1024,1)}
info={}
# stills
info['kid-hold']=save(clean(fit(crop(Image.open('keyed/kid-hold.png')),1024)),'kid-hold.webp')
for src,name in [('keyed/fret-tip-nb.png','hand-fret-tip.webp'),('keyed/fret-flat.png','hand-fret-flat.webp')]:
    im=Image.open(src).convert('RGBA'); info[name]=save(clean(fit(im,1024)),name)   # keep full canvas so tip/flat align
im=clean(fit(crop(Image.open('keyed/numbers.png'),0),1024))
# keep empty space above fingertips: crop only sides/bottom, keep top margin = 18% of hand height
a=np.array(Image.open('keyed/numbers.png'))[...,3]; ys,xs=np.nonzero(a>128)
H=ys.max()-ys.min(); top=max(0,ys.min()-int(.22*H)); num=Image.open('keyed/numbers.png').crop((max(0,xs.min()-40),top,min(a.shape[1],xs.max()+40),a.shape[0]))
num=clean(fit(num,768)); info['hand-numbers']=save(num,'hand-numbers.webp')
for n in ['witch','alpaca','cat','apple']:
    im=Image.open(f'cut/{n}.webp').convert('RGBA'); info[n]=save(clean(im),f'{n}.webp')
json.dump(info,open('build-info.json','w'),indent=1); print(json.dumps(info,indent=1))
