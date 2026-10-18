import json,numpy as np
from PIL import Image
P='/tmp/claude-0/-home-user/7ead4a65-9a3f-5f74-8eac-6850f8d7f07d/scratchpad/'
cj=json.load(open(P+'pub/i7/cut/B5/cut.json'))['mary']; w,h=cj['w'],cj['h']
plate=np.asarray(Image.open(P+'pub/i5/B5_plate.jpg').convert('RGB')).astype(float)
john=np.asarray(Image.open(P+'pub/i5/B5_fig_john.png')).astype(float)
def comp(fr):
    c=plate.copy()
    for g,(x,y) in ((fr,(853,235)),(john,(949,205))):
        a=g[...,3:]/255; hh,ww=g.shape[:2]; c[y:y+hh,x:x+ww]=c[y:y+hh,x:x+ww]*(1-a)+g[...,:3]*a
    return c[236:326,858:948]
def frames(name):
    g=[x for x in cj['gestures'] if x['name']==name][0]
    sh=np.asarray(Image.open(P+'pub/'+g['file']).convert('RGBA')).astype(float)
    return [sh[(k//g['cols'])*h:(k//g['cols']+1)*h,(k%g['cols'])*w:(k%g['cols']+1)*w] for k in range(g['frames'])]
home=np.asarray(Image.open(P+'pub/'+cj['home']).convert('RGBA')).astype(float)
old=np.asarray(Image.open(P+'work/b5age/backup/B5_fig_mary.png').convert('RGBA')).astype(float)
def save(tiles,fn):
    v=np.hstack([np.pad(comp(t),((0,0),(0,3),(0,0)),constant_values=255) for t in tiles])
    Image.fromarray(v.clip(0,255).astype(np.uint8)).resize((v.shape[1]*4,v.shape[0]*4),Image.LANCZOS).save(P+'review/B5/'+fn,quality=92)
save([old,home],'zoom_age_home.jpg')                      # before | after
b=frames('blink'); save([b[0],b[3],b[4],b[6],b[9]],'zoom_age_blink.jpg')   # f0 | peak | peak | open | last
b2=frames('blink2'); save([b2[3],b2[8],b2[9]],'zoom_age_blink2.jpg')
t=frames('tilt'); n=frames('nod'); br=frames('breath'); save([t[13],n[7],br[13]],'zoom_age_warp.jpg')
