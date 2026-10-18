import numpy as np, json, os, sys
from PIL import Image
from scipy import ndimage as ndi
S='..'; OUT=S+'/pub/i7/cut'; os.makedirs(OUT,exist_ok=True); os.makedirs('frames',exist_ok=True)
FPS=12
plate=np.asarray(Image.open(S+'/pub/i5/R1_plate.jpg').convert('RGB')).astype(np.float32)
OVJ=json.load(open('ov.json'))
def smooth(u): return u*u*(3-2*u)
def track(keys,t):
    if t<=keys[0][0]: return keys[0][1]
    for (t0,v0),(t1,v1) in zip(keys,keys[1:]):
        if t<=t1: return v0+(v1-v0)*smooth((t-t0)/(t1-t0))
    return keys[-1][1]
def ellipse(W,H,cx,cy,rx,ry,blur):
    Y,X=np.mgrid[0:H,0:W]; m=(((X-cx)/rx)**2+((Y-cy)/ry)**2<=1).astype(np.float32)
    return np.clip(ndi.gaussian_filter(m,blur)*1.0,0,1) if blur else m
def ramp(H,W,y_full,y_zero):
    Y=np.mgrid[0:H,0:W][0].astype(np.float32); u=np.clip((y_zero-Y)/(y_zero-y_full),0,1); return smooth(u)

CFG={
 'mary':dict(fig=(578,218),mode='opaque',
   deformers={'head':dict(pivot=(184,122)),'torso':dict(pivot=(190,225))},
   glow=None),
 'angel':dict(fig=(253,79),mode='opaque',
   deformers={'head':dict(pivot=(372,192)),'torso':dict(pivot=(300,335)),'body':dict(pivot=(272,505))},
   glow=True),
}
def weights(name,W,H,a):
    if name=='mary':
        head=ellipse(W,H,192,55,62,62,0); head=np.maximum(head,ellipse(W,H,222,110,22,30,0))  # head + kerchief tail
        head=ndi.gaussian_filter(head,7); head[head<0.02]=0; head=np.clip((head-0.02)/0.5,0,1)
        Y=np.mgrid[0:H,0:W][0]; head*=np.clip((150-Y)/25,0,1)
        torso=ramp(H,W,150,212)
        return {'head':head,'torso':torso}
    else:
        head=ellipse(W,H,428,172,62,58,0); head=np.maximum(head,ellipse(W,H,440,215,30,22,0))
        head=ndi.gaussian_filter(head,12); head=np.clip(head/0.6,0,1); head[head<0.01]=0
        torso=ramp(H,W,120,335)
        Y=np.mgrid[0:H,0:W][0]; body=np.clip((480-Y)/60,0,1).astype(np.float32); body=smooth(body)
        return {'head':head,'torso':torso,'body':body}

def render(name,G,ovs,Wt,src,a,base_plate):
    H,W=a.shape; Y,X=np.mgrid[0:H,0:W].astype(np.float32)
    frames=[]
    N=int(round(G['dur']*FPS))+1
    for i in range(N):
        t=i/FPS
        p={ch:track(k,t) for ch,k in G['tracks'].items()}
        if i==0 or i==N-1: frames.append(HOME.copy()); continue
        # overlays in rest space
        S_=src.copy(); A_=a.copy()
        for o,img in ovs.items():
            al=p.get('ov.'+o,0)
            if o.endswith('blink'): al=1.0 if al>=0.5 else 0.0   # eyes open or closed, never cross-faded
            if al>0:
                m=img[...,3:]*al; S_=S_*(1-m)+img[...,:3]*m
        DX=np.zeros((H,W),np.float32); DY=np.zeros((H,W),np.float32)
        for d,cfg in CFG[name]['deformers'].items():
            rot=p.get(d+'.rot',0); dx=p.get(d+'.dx',0); dy=p.get(d+'.dy',0); sx=p.get(d+'.sx',1); sy=p.get(d+'.sy',1)
            if rot==0 and dx==0 and dy==0 and sx==1 and sy==1: continue
            px,py=cfg['pivot']; th=np.deg2rad(rot); c,s=np.cos(th),np.sin(th)
            u=(X-px)*sx; v=(Y-py)*sy
            fx=px+c*u-s*v+dx; fy=py+s*u+c*v+dy
            DX+=Wt[d]*(fx-X); DY+=Wt[d]*(fy-Y)
        # inverse map (2 fixed-point iterations)
        if DX.any() or DY.any():
            qx,qy=X-DX,Y-DY
            for _ in range(2):
                ddx=ndi.map_coordinates(DX,[qy,qx],order=1,mode='nearest'); ddy=ndi.map_coordinates(DY,[qy,qx],order=1,mode='nearest')
                qx,qy=X-ddx,Y-ddy
            moved=(np.abs(DX)>1e-6)|(np.abs(DY)>1e-6)
            moved=ndi.binary_dilation(moved,iterations=3)
            def samp(img):
                out=img.copy()
                if img.ndim==2:
                    v=ndi.map_coordinates(img,[qy,qx],order=1,mode='constant',cval=0); out[moved]=v[moved]
                else:
                    for k in range(img.shape[2]):
                        v=ndi.map_coordinates(img[...,k],[qy,qx],order=1,mode='constant',cval=0); out[...,k][moved]=v[moved]
                return out
            S_=samp(S_); A_=samp(A_)
        g=p.get('glow',0)
        if CFG[name]['mode']=='opaque':
            rgb=S_; alpha=A_
            if g: rgb=rgb*(1+0.11*g*Wt['glow'][...,None])+g*np.array([14,11,4])*Wt['glow'][...,None]*alpha[...,None]
            # S_ is premultiplied
            out=np.dstack([np.where(alpha[...,None]>0, rgb/np.maximum(alpha[...,None],1e-6),0)*1, alpha*255])
        else:
            L=S_  # light (signed), already premult by a
            if g: L=L*(1+0.22*g*Wt['glow'][...,None])+g*np.array([30,24,12])*Wt['glow'][...,None]*A_[...,None]
            alpha=np.maximum(a,A_)
            C=base_plate+L
            rgb=(C-base_plate*(1-alpha[...,None]))/np.maximum(alpha[...,None],1e-6)
            out=np.dstack([rgb,alpha*255])
        fr=np.clip(np.round(out),0,255).astype(np.uint8)
        diff=np.abs(S_-src).max(-1)>1e-4
        diff|=np.abs(A_-a)>1e-6
        if g: diff|=Wt['glow']*a>1e-3
        fr[~diff]=HOME[~diff]
        frames.append(fr)
    return frames

GEST=json.load(open('gestures.json'))
manifest={}
for name in ['mary','angel']:
    HOME=np.asarray(Image.open(S+'/pub/i5/R1_fig_%s.png'%name).convert('RGBA'))
    H,W=HOME.shape[:2]; fx,fy=CFG[name]['fig']
    a=HOME[...,3].astype(np.float32)/255; rgb=HOME[...,:3].astype(np.float32)
    bp=plate[fy:fy+H,fx:fx+W]
    Wt=weights(name,W,H,a)
    if name=='angel':
        src=a[...,None]*rgb
        gm=ellipse(W,H,296,92,70,62,14)+0.8*ellipse(W,H,372,148,18,16,6)+0.35*ellipse(W,H,200,170,140,90,30)
        Wt['glow']=np.clip(gm,0,1)
    else:
        src=a[...,None]*rgb
    Image.fromarray(np.dstack([sum(Wt[k] for k in Wt if k in('head',))*255,Wt.get('torso')*255,Wt.get('body',Wt['torso']*0)*255]).clip(0,255).astype(np.uint8)).save('w_%s.png'%name)
    ovs={}
    for k,o in OVJ.items():
        if not k.startswith(name+'_'): continue
        im=np.asarray(Image.open('ov_%s.png'%k)).astype(np.float32); x,y=o['xy']; h,w=im.shape[:2]
        E=np.zeros((H,W,3),np.float32); M=np.zeros((H,W),np.float32)
        x0,y0=max(x,0),max(y,0); x1,y1=min(x+w,W),min(y+h,H)
        E[y0:y1,x0:x1]=im[y0-y:y1-y,x0-x:x1-x,:3]; M[y0:y1,x0:x1]=im[y0-y:y1-y,x0-x:x1-x,3]/255
        if name=='angel': M*=(a>0.99); tgt=E*a[...,None]
        else: M*=a; tgt=E*a[...,None]
        ovs[k.split('_',1)[1]]=np.dstack([tgt,M])
    Image.fromarray(HOME).save(OUT+'/%s_home.png'%name)
    gl=[]; peaks=[]
    for G in GEST[name]:
        fr=render(name,G,ovs,Wt,src,a,bp)
        n=len(fr); cols=min(n,max(1,4096//W)); rows=-(-n//cols)
        sheet=np.zeros((rows*H,cols*W,4),np.uint8)
        for j,f in enumerate(fr): sheet[(j//cols)*H:(j//cols+1)*H,(j%cols)*W:(j%cols+1)*W]=f
        fn='%s_%s.webp'%(name,G['name'])
        Image.fromarray(sheet).save(OUT+'/'+fn,'WEBP',quality=88,method=6)
        pk=G.get('peak',G['dur']/2); pi=int(round(pk*FPS))
        peaks.append((G['name'],fr[pi]))
        for j,f in enumerate(fr): Image.fromarray(f).save('frames/%s_%s_%02d.png'%(name,G['name'],j))
        e0=np.abs(fr[0].astype(int)-HOME).mean(); e1=np.abs(fr[-1].astype(int)-HOME).mean()
        mx=max(np.abs(f.astype(int)-HOME).max(-1).__gt__(40).sum() for f in fr)
        print(name,G['name'],n,'frames',cols,'x',rows,sheet.shape[1],'x',sheet.shape[0],'ends',e0,e1,'chg>40',mx,'KB',os.path.getsize(OUT+'/'+fn)//1024)
        gl.append(dict(name=G['name'],file='i7/cut/'+fn,cols=cols,rows=rows,frames=n,fps=FPS,weight=G.get('weight',1)))
    manifest[name]=dict(home='i7/cut/%s_home.png'%name,w=W,h=H,gestures=gl)
    np.save('peaks_%s.npy'%name,np.array([p[1] for p in peaks])); json.dump([p[0] for p in peaks],open('peaks_%s.json'%name,'w'))
json.dump(manifest,open(OUT+'/cut.json','w'),indent=1)
