#!/usr/bin/env python3
"""fullkey2.py CLIP HOMECUT X,Y OUTDIR [--end ENDCUT --end-at X,Y] [--t0 s] [--t1 s] [--step 2] [--ease 3]
fullkey.py plus a different END picture (a shifted home after a pounce, a drawn crouch peak): the last frame IS that
picture and the last --ease frames ease into it.
Per-frame dominance key for clips where the WHOLE body moves (run in place, leap, climb):
colour of the clip mapped to the painted home by a per-channel linear fit on frame 0, alpha from how much the
ground's channel dominates, colour un-mixed from the ground, the ends eased into the exact home picture.
With --twig (a prop mask): where the clip shows the prop or bare ground, the home prop is used, so the prop never moves."""
import argparse, os, subprocess, glob
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
ap=argparse.ArgumentParser(); ap.add_argument('clip'); ap.add_argument('home'); ap.add_argument('at'); ap.add_argument('out')
ap.add_argument('--twig'); ap.add_argument('--t0',type=float,default=0); ap.add_argument('--t1',type=float,default=99)
ap.add_argument('--step',type=int,default=2); ap.add_argument('--end'); ap.add_argument('--end-at'); ap.add_argument('--colnorm',action='store_true'); ap.add_argument('--ease',type=int,default=3)
a=ap.parse_args(); os.makedirs(a.out,exist_ok=True)
for f in glob.glob(a.out+'/*.png'): os.remove(f)
pr=subprocess.run(['ffprobe','-v','error','-select_streams','v','-show_entries','stream=width,height','-of','csv=p=0',a.clip],capture_output=True,text=True).stdout.split(',')
W,H=int(pr[0]),int(pr[1])
raw=subprocess.run(['ffmpeg','-v','error','-i',a.clip,'-f','rawvideo','-pix_fmt','rgb24','-'],capture_output=True).stdout
F=np.frombuffer(raw,np.uint8).reshape(-1,H,W,3)
cut=np.asarray(Image.open(a.home).convert('RGBA'),float); ox,oy=map(int,a.at.split(','))
home=np.zeros((H,W,4)); home[oy:oy+cut.shape[0],ox:ox+cut.shape[1]]=cut; ha=home[...,3]/255
fig=ndi.binary_erosion(ha>0.9,iterations=3)
f0=F[0].astype(float); lut=[np.polyfit(f0[...,c][fig],home[...,c][fig],1) for c in range(3)]
print('lut',[np.round(l,3).tolist() for l in lut])
tw=(np.asarray(Image.open(a.twig).convert('L'))>128) if a.twig else None
i0=int(a.t0*24); i1=min(len(F)-1,int(a.t1*24)); idx=list(range(i0,i1+1,a.step))
if idx[-1]!=i1: idx.append(i1)
out=[]
for i in idx:
    rgb=F[i].astype(float)
    border=np.concatenate([rgb[:6].reshape(-1,3),rgb[-6:].reshape(-1,3),rgb[:,:6].reshape(-1,3),rgb[:,-6:].reshape(-1,3)]); bg=np.median(border,0)
    dom=rgb[...,2]-rgb[...,:2].max(2)
    al=np.clip((70-dom)/50,0,1)
    m=al>0.5; m=ndi.binary_opening(m,iterations=1)
    lab,n=ndi.label(m); 
    if n:
        sz=ndi.sum(m,lab,range(1,n+1)); m=np.isin(lab,1+np.nonzero(sz>=250)[0])
    m=ndi.binary_dilation(m,iterations=3); al=al*m
    # un-mix the ground colour from soft edges, then the colour fit to home
    col=(rgb-(1-al[...,None])*bg)/np.maximum(al,0.2)[...,None]
    col=np.clip(col,0,255)
    edge=(al<0.98)
    col[...,2]=np.where(edge,np.minimum(col[...,2],col[...,:2].max(2)),col[...,2])
    col=np.dstack([np.polyval(lut[c],col[...,c]) for c in range(3)]).clip(0,255)
    fr=np.dstack([col,al*255])
    if tw is not None:
        # prop pixels: home wherever the clip shows prop-like colour close to home, or bare ground
        diff=np.abs(col-home[...,:3]).max(2)
        use_home=tw&((diff<45)|(al<0.5))
        fr[use_home]=home[use_home]
    out.append(fr)
n=len(out)
if a.colnorm:
    # colour drift: H3 relights the figure when its backdrop drifts. Per frame, match each channel's mean and spread
    # on the figure's interior to frame 0 (= the home picture after the LUT), gains smoothed over +-3 frames, capped.
    st=[]
    for f in out:
        m=ndi.binary_erosion(f[...,3]>250,iterations=3); px=f[...,:3][m]
        st.append((px.mean(0),px.std(0)))
    mu=np.array([s_[0] for s_ in st]); sd=np.array([s_[1] for s_ in st])
    hm=ndi.binary_erosion(ha>0.98,iterations=3); hpx=home[...,:3][hm]; mu0,sd0=hpx.mean(0),hpx.std(0)
    k_=np.clip(sd0/sd,0.85,1.15); b_=mu0-k_*mu; b_=np.clip(b_,-40,40)
    k_=ndi.median_filter(k_,size=(7,1),mode='nearest'); b_=ndi.median_filter(b_,size=(7,1),mode='nearest')
    print('colour drift before (mean RGB off home):',' '.join('%.0f'%np.abs(mu[i]-mu0).sum() for i in range(0,n,4)))
    for i,f in enumerate(out): f[...,:3]=np.clip(f[...,:3]*k_[i]+b_[i],0,255)
    print('after:',' '.join('%.0f'%np.abs(out[i][...,:3][ndi.binary_erosion(out[i][...,3]>250,iterations=3)].mean(0)-mu0).sum() for i in range(0,n,4)))
endp=home
if a.end:
    ec=np.asarray(Image.open(a.end).convert('RGBA'),float); ex,ey=map(int,a.end_at.split(','))
    endp=np.zeros((H,W,4)); endp[ey:ey+ec.shape[0],ex:ex+ec.shape[1]]=ec
def blend(f,t,w):
    ta=t[...,3:4]/255; pa=f[...,3:4]/255*w+ta*(1-w)
    c=(f[...,:3]*f[...,3:4]/255*w+t[...,:3]*ta*(1-w))/np.maximum(pa,1e-3)
    return np.dstack([c,pa*255])
out[0]=home.copy(); out[-1]=endp.copy()
for j in range(1,n-1):
    if j<a.ease: out[j]=blend(out[j],home,j/a.ease)
    elif n-1-j<a.ease: out[j]=blend(out[j],endp,(n-1-j)/a.ease)
for j,f in enumerate(out): Image.fromarray(np.clip(np.round(f),0,255).astype(np.uint8),'RGBA').save(f'{a.out}/f_{j:03d}.png')
print(n,'frames from',i0/24,'to',i1/24,'s')
