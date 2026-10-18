import json, numpy as np
from PIL import Image
S='/tmp/claude-0/-home-user/7ead4a65-9a3f-5f74-8eac-6850f8d7f07d/scratchpad/'; P=S+'pub/'
cj=json.load(open(P+'i7/cut/B2/cut.json'))['jesus']; W,H=cj['w'],cj['h']
pm=lambda im: np.dstack([im[...,:3]*im[...,3:]/255.,im[...,3:]])
home=pm(np.asarray(Image.open(P+cj['home']).convert('RGBA')).astype(float))
ox,oy=425,162
def frames(g):
    sh=np.asarray(Image.open(P+g['file']).convert('RGBA')).astype(int)
    return [pm(sh[(i//g['cols'])*H:(i//g['cols']+1)*H,(i%g['cols'])*W:(i%g['cols']+1)*W]) for i in range(g['frames'])]
def flat(im):
    a=im[...,3:]/255.; return (im[...,:3]+np.array([40,40,70])*(1-a)).clip(0,255).astype(np.uint8)
rows=[]; info=[]
for g in cj['gestures']:
    fr=frames(g)
    d=[np.abs(f-home).mean() for f in fr]
    hreg=[np.abs(f[265-oy:430-oy,0:482-ox]-home[265-oy:430-oy,0:482-ox]).mean() for f in fr]
    eye=[int((np.abs(f[190-oy:222-oy,512-ox:556-ox,:3]-home[190-oy:222-oy,512-ox:556-ox,:3]).max(2)>40).sum()) for f in fr]
    pk=int(np.argmax(d))
    info.append((g['name'],len(fr),'ends',round(d[0],2),round(d[-1],2),'max',round(max(d),2),'@',pk,'hands max',round(max(hreg),3),'eye px',eye))
    sel=[0,pk]+[i for i in range(len(fr)) if eye[i]>40][:1]
    if g['name']=='blink': sel=list(range(2,14))
    tiles=[flat(fr[i])[170-oy:270-oy,495-ox:600-ox] for i in sel]
    rows.append(np.hstack([np.kron(t,np.ones((4,4,1),np.uint8)) for t in tiles]))
for i in info: print(*i)
Wm=max(r.shape[1] for r in rows)
im=np.vstack([np.pad(r,((0,8),(0,Wm-r.shape[1]),(0,0)),constant_values=255) for r in rows])
Image.fromarray(im).save(S+'review/B2/zoom_eyes_jesus.jpg',quality=88); print(im.shape)
# targeted strip: eye at x4
G={g['name']:g for g in cj['gestures']}
picks=[('blink',i) for i in (3,4,8,9,10,11,17,18)]+[('lift',3),('lift',8),('lift',17),('lift',27),('bow',14)]
tiles=[]
for n,i in picks:
    f=frames(G[n])[i]; t=flat(f)[180-oy:245-oy,500-ox:575-ox]
    tiles.append(np.kron(t,np.ones((4,4,1),np.uint8)))
a=np.hstack(tiles[:7]); b=np.hstack(tiles[7:]); w=max(a.shape[1],b.shape[1])
im=np.vstack([np.pad(a,((0,6),(0,w-a.shape[1]),(0,0)),constant_values=255),np.pad(b,((0,0),(0,w-b.shape[1]),(0,0)),constant_values=255)])
Image.fromarray(im).save(S+'review/B2/zoom_faces_jesus.jpg',quality=90); print('strip',im.shape)
# arms / pillar sliver at sigh + breath peaks, composited on plate, x3
plate=np.asarray(Image.open(P+'i5/B2_plate.jpg').convert('RGB')).astype(float)
def comp(f):
    out=plate.copy(); a=f[...,3:]/255.
    out[oy:oy+H,ox:ox+W]=f[...,:3]+out[oy:oy+H,ox:ox+W]*(1-a); return out
tiles=[]
for n,i in (('sigh',0),('sigh',15),('breath',14)):
    c=comp(frames(G[n])[i])[250:440,415:600]; tiles.append(np.kron(c.clip(0,255).astype(np.uint8),np.ones((3,3,1),np.uint8)))
d=np.abs(comp(frames(G['sigh'])[15])-comp(home)).max(2)[250:440,415:600]
tiles.append(np.kron(np.dstack([np.clip(d*6,0,255)]*3).astype(np.uint8),np.ones((3,3,1),np.uint8)))
Image.fromarray(np.hstack(tiles)).save(S+'review/B2/zoom_cut_jesus.jpg',quality=88)
