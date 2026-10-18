# Bag cutoutu dla duchów S4 (Mojżesz, Eliasz): bez edycji API — unoszenie, pochylenie ku Jezusowi, skinienie głową, puls światła.
import numpy as np, json
from PIL import Image
from scipy import ndimage as nd
S='/tmp/claude-0/-home-user/7ead4a65-9a3f-5f74-8eac-6850f8d7f07d/scratchpad'
OUT=S+'/pub/i7/cut/S4/'
def sm(u):u=np.clip(u,0,1);return u*u*(3-2*u)
def track(keys,t):
    for (t0,v0),(t1,v1) in zip(keys,keys[1:]):
        if t0<=t<=t1:return v0+(v1-v0)*sm((t-t0)/max(1e-6,t1-t0))
    return keys[-1][1]
def warp(im,head_w,ch,bot):
    """ch: dict dx,dy,rot(deg, + zgodnie ze wsk.), hrot,hdy (głowa), lift (rozjaśnienie), a (mnożnik alfa)"""
    H,W=im.shape[:2];yy,xx=np.mgrid[0:H,0:W].astype(float)
    # całość: obrót wokół dołu (bot) + przesunięcie
    th=np.radians(ch.get('rot',0));px,py=bot
    sx=xx-ch.get('dx',0);sy=yy-ch.get('dy',0)
    c,s=np.cos(-th),np.sin(-th);X=px+(sx-px)*c-(sy-py)*s;Y=py+(sx-px)*s+(sy-py)*c
    # głowa: obrót wokół podbródka ważony mapą
    hth=np.radians(ch.get('hrot',0))*head_w;hx,hy=ch['_chin'];c2,s2=np.cos(-hth),np.sin(-hth)
    X2=hx+(X-hx)*c2-(Y-hy)*s2;Y2=hy+(X-hx)*s2+(Y-hy)*c2-ch.get('hdy',0)*head_w
    out=np.dstack([nd.map_coordinates(im[...,k],[Y2,X2],order=1,mode='constant',cval=0) for k in range(4)])
    L=ch.get('lift',0);out[...,:3]=out[...,:3]*(1-L)+np.array([255,250,232])*L
    out[...,3]=np.clip(out[...,3]*ch.get('a',1),0,255)
    return out
SPEC={
 'moses':dict(chin=(.55,.31),head=(.53,.17,.12,.08),dir=1,gest=[
   ('float',2.4,{'dy':[[0,0],[1.1,-2],[1.4,-2],[2.4,0]],'lift':[[0,0],[1.2,.05],[2.4,0]]}),
   ('lean',2.0,{'rot':[[0,0],[.8,1.2],[1.2,1.2],[2.0,0]]}),
   ('nod',1.8,{'hrot':[[0,0],[.5,3.5],[.9,3.5],[1.3,0],[1.8,0]],'hdy':[[0,0],[.6,1.5],[1.2,0],[1.8,0]]}),
   ('glow',2.0,{'lift':[[0,0],[.9,.10],[1.2,.10],[2.0,0]],'a':[[0,1],[1.0,1.08],[2.0,1]]}),
   ('speak',2.2,{'rot':[[0,0],[.6,.6],[1.6,.6],[2.2,0]],'hrot':[[0,0],[.5,-2],[.8,1.5],[1.2,-1.5],[1.6,0],[2.2,0]]})]),
 'elijah':dict(chin=(.32,.30),head=(.33,.17,.14,.08),dir=-1,gest=[
   ('float',2.4,{'dy':[[0,0],[1.2,-2],[1.5,-2],[2.4,0]],'lift':[[0,0],[1.2,.05],[2.4,0]]}),
   ('bow',2.0,{'hrot':[[0,0],[.7,-3.5],[1.2,-3.5],[2.0,0]],'hdy':[[0,0],[.7,2],[1.2,2],[2.0,0]]}),
   ('lean',2.0,{'rot':[[0,0],[.8,-1.2],[1.2,-1.2],[2.0,0]]}),
   ('glow',2.0,{'lift':[[0,0],[.9,.10],[1.2,.10],[2.0,0]],'a':[[0,1],[1.0,1.08],[2.0,1]]})]),
}
cut=json.load(open(S+'/scripts/i5/S4sp/cut.json.bak'));fps=12;rep={}
for n,sp in SPEC.items():
    src=Image.open(S+f'/pub/i5/S4_fig_{n}.png').convert('RGBA');im=np.asarray(src,float);H,W=im.shape[:2]
    src.save(OUT+f'{n}_home.png')
    yy,xx=np.mgrid[0:H,0:W];hx,hy,hw,hh=sp['head'];cx,cy=hx*W,hy*H
    hw_=np.exp(-(((xx-cx)/(hw*W))**2+((yy-cy)/(hh*H))**2)*1.2);hw_=np.clip(hw_*1.6,0,1)
    hw_[yy>sp['chin'][1]*H+0.10*H]=0;hw_=nd.gaussian_filter(hw_,4)
    bot=(W*.5,H-14);gl=[]
    for name,dur,tr in sp['gest']:
        N=int(round(dur*fps));frames=[]
        for f in range(N):
            t=f/fps;ch={k:track(v,t) for k,v in tr.items()};ch['_chin']=(sp['chin'][0]*W,sp['chin'][1]*H)
            fr=im.copy() if f==0 or f==N-1 else warp(im,hw_,ch,bot)
            frames.append(fr.clip(0,255).astype('uint8'))
        cols=min(N,4096//W);rows=-(-N//cols);sheet=Image.new('RGBA',(cols*W,rows*H),(0,0,0,0))
        for k,fr in enumerate(frames):sheet.paste(Image.fromarray(fr,'RGBA'),((k%cols)*W,(k//cols)*H))
        sheet.save(OUT+f'{n}_{name}.webp',quality=80,method=6)
        peak=max(range(N),key=lambda k:np.abs(frames[k].astype(float)-im).mean())
        Image.fromarray(frames[peak],'RGBA').save(S+f'/review/S4/sp_{n}_{name}_peak.png')
        rep[f'{n}_{name}']=dict(frames=N,peak=peak,peak_diff=round(float(np.abs(frames[peak].astype(float)-im).mean()),2),ends=float(np.abs(frames[-1].astype(float)-im).mean()))
        gl.append({'name':name,'file':f'i7/cut/S4/{n}_{name}.webp','cols':cols,'rows':rows,'frames':N,'fps':fps,'weight':2 if name in('float','glow') else 1+ (name in('speak','bow','nod'))})
    cut[n]={'home':f'i7/cut/S4/{n}_home.png','w':W,'h':H,'gestures':gl}
json.dump(cut,open(OUT+'cut.json','w'))
print(json.dumps(rep,indent=0))
