# Generic cutout idle bags for C2..C5 (adapted from i7x/render.py, R1 renderer).
# usage: python3 cut.py ID [ov]      (run from i7c/)
#   ov   -> build overlays from registered face edits first
# config: cfg_ID.json, all coords in FRAME px (1376x768)
import numpy as np, json, os, sys
from PIL import Image
from scipy import ndimage as ndi, optimize
S='/tmp/claude-0/-home-user/7ead4a65-9a3f-5f74-8eac-6850f8d7f07d/scratchpad'
FPS=12
ID=sys.argv[1]; CFG=json.load(open('cfg_%s.json'%ID))
FIGJ={f['name']:f for f in json.load(open(S+'/scripts/i5/work/%s_figs.json'%ID))['figs']}
full=np.asarray(Image.open(S+'/pub/i5/%s_full.jpg'%ID).convert('RGB')).astype(np.float32)
os.makedirs('ov',exist_ok=True); os.makedirs('/tmp/claude-0/-home-user/7ead4a65-9a3f-5f74-8eac-6850f8d7f07d/scratchpad/work/fix8/B4/regen/frames',exist_ok=True)

def sm(u): return u*u*(3-2*u)
def track(keys,t):
    if t<=keys[0][0]: return keys[0][1]
    for (t0,v0),(t1,v1) in zip(keys,keys[1:]):
        if t<=t1: return v0+(v1-v0)*sm((t-t0)/(t1-t0))
    return keys[-1][1]

# ---------- overlays from face edits ----------
def register(O,E):
    def warp(im,s,dx,dy):
        H,W=im.shape[:2]; c=(H-1)/2
        return np.dstack([ndi.affine_transform(im[...,k],[1/s,1/s],offset=[c-(c+dy)/s,c-(c+dx)/s],order=1,mode='nearest') for k in range(3)])
    Ob=ndi.gaussian_filter(O,(2,2,0)); Eb=ndi.gaussian_filter(E,(2,2,0)); m=max(8,O.shape[0]//12)
    f=lambda p: np.abs(warp(Eb,*p)-Ob)[m:-m,m:-m].mean()
    best=min(((f((s,dx,dy)),(s,dx,dy)) for s in (0.98,1.0,1.02) for dx in range(-8,9,2) for dy in range(-8,9,2)))
    r=optimize.minimize(f,best[1],method='Nelder-Mead',options=dict(xatol=0.05,fatol=0.01))
    print('  reg',np.round(r.x,2),'err',round(float(r.fun),2))
    return warp(E,*r.x)
def build_ovs():
    for on,o in CFG.get('ovs',{}).items():
        cx,cy,cs=o['crop']; O=full[cy:cy+cs,cx:cx+cs]
        E=np.asarray(Image.open('ed/%s_%s_raw.png'%(ID,on)).convert('RGB').resize((cs,cs),Image.LANCZOS)).astype(np.float32)
        print(on); E=register(O,E); E=ndi.gaussian_filter(E,(0.5,0.5,0))
        d=np.abs(ndi.gaussian_filter(E,(1,1,0))-ndi.gaussian_filter(O,(1,1,0))).max(2)
        views=[]
        for fg,b in o['boxes'].items():
            x0,y0,x1,y1=b[0]-cx,b[1]-cy,b[2]-cx,b[3]-cy
            box=np.zeros((cs,cs),bool); box[y0:y1,x0:x1]=True
            ch=(d>o.get('thr',18))&box; ch=ndi.binary_opening(ch,iterations=1)
            lab,k=ndi.label(ch); sz=ndi.sum(ch,lab,range(1,k+1)); ch=np.isin(lab,1+np.nonzero(sz>=5)[0])
            if o.get('hull'):
                # blink: cover the WHOLE original eye + the edited lid: face-ellipse filter, then convex hull per eye
                hx,hy,rx,ry=CFG['figs'][fg]['head']; Yc,Xc=np.mgrid[0:cs,0:cs]
                face=(((Xc-(hx-cx))/(rx*0.95))**2+((Yc-(hy-cy))/(ry*0.95))**2)<=1
                ch&=face
                lab,k=ndi.label(ndi.binary_dilation(ch,iterations=2)); hull=np.zeros_like(ch)
                from scipy.spatial import ConvexHull
                from PIL import ImageDraw
                for j in range(1,k+1):
                    ys,xs=np.nonzero((lab==j)&ch)
                    if len(xs)<8: continue
                    pts=np.c_[xs,ys].astype(float)
                    try: hv=pts[ConvexHull(pts).vertices]
                    except Exception: continue
                    pim=Image.new('L',(cs,cs),0); ImageDraw.Draw(pim).polygon([tuple(p) for p in hv],fill=1)
                    hull|=np.asarray(pim)>0
                ch=ndi.binary_dilation(hull|ch,iterations=o.get('grow',3))&box&ndi.binary_dilation(face,iterations=2)
            else:
                ch=ndi.binary_dilation(ch,iterations=3)&box
            m=np.clip(ndi.gaussian_filter(ch.astype(np.float32),1.2)*1.6,0,1)*box
            ring=ndi.binary_dilation(ch,iterations=8)&~ndi.binary_dilation(ch,iterations=2)
            Ec=E.copy(); wr=ring.astype(np.float32); den=ndi.gaussian_filter(wr,4)+1e-6
            for c in range(3): Ec[...,c]+=ndi.gaussian_filter((O[...,c]-Ec[...,c])*wr,4)/den
            an=o.get('as',on)
            Image.fromarray(np.dstack([np.clip(Ec,0,255),m*255]).astype(np.uint8)).save('ov/%s_%s_%s.png'%(ID,fg,an))
            json.dump(dict(xy=[cx,cy]),open('ov/%s_%s_%s.json'%(ID,fg,an),'w'))
            v=O*(1-m[...,None])+Ec*m[...,None]
            pad=12; r0,r1,c0,c1=max(0,y0-pad),min(cs,y1+pad),max(0,x0-pad),min(cs,x1+pad)
            views.append(np.hstack([O[r0:r1,c0:c1],v[r0:r1,c0:c1]]))
            print('  ',fg,'changed px',int(ch.sum()))
        if views:
            Wm=max(v.shape[1] for v in views)
            st=np.vstack([np.pad(v,((0,4),(0,Wm-v.shape[1]),(0,0))) for v in views])
            Image.fromarray(st.astype(np.uint8)).resize((st.shape[1]*3,st.shape[0]*3),Image.LANCZOS).save('ovview_%s_%s.jpg'%(ID,on))

# ---------- gesture library (keyframes) ----------
def G(name,dur,peak,w,tr): return dict(name=name,dur=dur,peak=peak,weight=w,tracks=tr)
def LIB(n,s=1.0):
    s=float(s)
    L={
     'breath':G('breath',2.4,1.1,3,{'torso.sy':[[0,1],[1.1,1+0.008*s],[2.4,1]],'torso.sx':[[0,1],[1.1,1+0.003*s],[2.4,1]]}),
     'tilt':G('tilt',2.2,1.1,2,{'head.rot':[[0,0],[0.7,-2.2*s],[1.5,-2.2*s],[2.2,0]],'head.dx':[[0,0],[0.7,-0.8*s],[1.5,-0.8*s],[2.2,0]]}),
     'tilt_r':G('tilt_r',2.2,1.1,2,{'head.rot':[[0,0],[0.7,2.2*s],[1.5,2.2*s],[2.2,0]],'head.dx':[[0,0],[0.7,0.8*s],[1.5,0.8*s],[2.2,0]]}),
     'nod':G('nod',1.6,0.6,2,{'head.dy':[[0,0],[0.45,1.2*s],[0.8,0],[1.15,0.9*s],[1.6,0]],'head.rot':[[0,0],[0.45,0.6*s],[1.6,0]]}),
     'look_up':G('look_up',2.4,1.2,2,{'head.rot':[[0,0],[0.7,-1.6*s],[1.7,-1.6*s],[2.4,0]],'head.dy':[[0,0],[0.7,-1.0*s],[1.7,-1.0*s],[2.4,0]]}),
     'sway':G('sway',2.8,1.0,2,{'torso.rot':[[0,0],[1.0,0.6*s],[1.9,-0.25*s],[2.8,0]]}),
     'lift':G('lift',2.6,1.3,2,{'torso.dy':[[0,0],[1.3,-3.0*s],[2.6,0]],'head.rot':[[0,0],[1.3,-0.8*s],[2.6,0]]}),
     'blink':G('blink',0.75,0.33,3,{'ov.blink':[[0,0],[0.2,0],[0.26,1],[0.42,1],[0.5,0],[0.75,0]]}),
     'blink2':G('blink2',1.25,0.33,2,{'ov.blink':[[0,0],[0.2,0],[0.26,1],[0.38,1],[0.45,0],[0.62,0],[0.68,1],[0.8,1],[0.88,0],[1.25,0]]}),
     'smile':G('smile',2.2,1.1,2,{'ov.smile':[[0,0],[0.3,0],[0.55,1],[1.65,1],[1.9,0],[2.2,0]],'head.rot':[[0,0],[0.6,-1.0*s],[1.6,-1.0*s],[2.2,0]]}),
     'open':G('open',2.6,1.2,2,{'ov.open':[[0,0],[0.35,0],[0.75,1],[1.9,1],[2.3,0],[2.6,0]],'head.rot':[[0,0],[0.8,-0.6*s],[1.9,-0.6*s],[2.6,0]]}),
     'breath20':G('breath',1.6,0.8,3,{'torso.sy':[[0,1],[0.8,1+0.008*s],[1.6,1]],'torso.sx':[[0,1],[0.8,1+0.003*s],[1.6,1]]}),
     'jnod':G('jnod',1.8,0.6,3,{'jhead.dy':[[0,0],[0.5,1.4*s],[0.9,0.2*s],[1.3,1.0*s],[1.8,0]],'jhead.rot':[[0,0],[0.5,1.5*s],[1.3,1.0*s],[1.8,0]]}),
     'jsigh':G('jsigh',2.8,1.3,3,{'jhead.dy':[[0,0],[1.2,1.6*s],[2.0,1.6*s],[2.8,0]],'jhead.rot':[[0,0],[1.2,1.8*s],[2.0,1.8*s],[2.8,0]],'ov.jblink':[[0,0],[0.9,0],[1.2,1],[2.0,1],[2.3,0],[2.8,0]]}),
     'jblink':G('jblink',0.75,0.33,3,{'ov.jblink':[[0,0],[0.2,0],[0.26,1],[0.42,1],[0.5,0],[0.75,0]]}),
     'sigh':G('sigh',3.0,1.4,2,{'torso.sy':[[0,1],[1.3,1+0.012*s],[3.0,1]],'head.dy':[[0,0],[1.3,-0.6*s],[2.2,0.5*s],[3.0,0]],'head.rot':[[0,0],[1.4,0.8*s],[3.0,0]]}),
     'laugh':G('laugh',2.0,1.0,2,{'ov.smile':[[0,0],[0.25,0],[0.45,1],[1.5,1],[1.7,0],[2.0,0]],'head.dy':[[0,0],[0.5,-0.8*s],[0.75,0.2*s],[1.0,-0.8*s],[1.25,0.2*s],[1.6,0],[2.0,0]]}),
    }
    return L[n]

# ---------- render (same maths as R1 renderer) ----------
def render(defs,Gs,ovs,Wt,src,a,HOME):
    H,W=a.shape; Y,X=np.mgrid[0:H,0:W].astype(np.float32); frames=[]
    N=int(round(Gs['dur']*FPS))+1
    for i in range(N):
        t=i/FPS; p={ch:track(k,t) for ch,k in Gs['tracks'].items()}
        if i==0 or i==N-1: frames.append(HOME.copy()); continue
        S_=src.copy(); A_=a.copy()
        for o,img in ovs.items():
            al=p.get('ov.'+o,0)
            if o.endswith('blink'): al=1.0 if al>=0.5 else 0.0   # eyes open or closed, never cross-faded
            if al>0: m=img[...,3:]*al; S_=S_*(1-m)+img[...,:3]*m
        DX=np.zeros((H,W),np.float32); DY=np.zeros((H,W),np.float32)
        for d,(px,py) in defs.items():
            rot=p.get(d+'.rot',0); dx=p.get(d+'.dx',0); dy=p.get(d+'.dy',0); sx=p.get(d+'.sx',1); sy=p.get(d+'.sy',1)
            if rot==0 and dx==0 and dy==0 and sx==1 and sy==1: continue
            th=np.deg2rad(rot); c,s=np.cos(th),np.sin(th); u=(X-px)*sx; v=(Y-py)*sy
            DX+=Wt[d]*(px+c*u-s*v+dx-X); DY+=Wt[d]*(py+s*u+c*v+dy-Y)
        if DX.any() or DY.any():
            qx,qy=X-DX,Y-DY
            for _ in range(2):
                ddx=ndi.map_coordinates(DX,[qy,qx],order=1,mode='nearest'); ddy=ndi.map_coordinates(DY,[qy,qx],order=1,mode='nearest'); qx,qy=X-ddx,Y-ddy
            moved=ndi.binary_dilation((np.abs(DX)>1e-6)|(np.abs(DY)>1e-6),iterations=3)
            def samp(img):
                out=img.copy()
                if img.ndim==2: v=ndi.map_coordinates(img,[qy,qx],order=1,mode='constant',cval=0); out[moved]=v[moved]
                else:
                    for k in range(img.shape[2]): v=ndi.map_coordinates(img[...,k],[qy,qx],order=1,mode='constant',cval=0); out[...,k][moved]=v[moved]
                return out
            S_=samp(S_); A_=samp(A_)
        out=np.dstack([np.where(A_[...,None]>0,S_/np.maximum(A_[...,None],1e-6),0),A_*255])
        fr=np.clip(np.round(out),0,255).astype(np.uint8)
        diff=(np.abs(S_-src).max(-1)>1e-4)|(np.abs(A_-a)>1e-6)
        fr[~diff]=HOME[~diff]; frames.append(fr)
    return frames

def weights(fc,W,H,ox,oy):
    Y,X=np.mgrid[0:H,0:W].astype(np.float32)
    hx,hy,rx,ry=fc['head']; hx-=ox; hy-=oy
    head=((((X-hx)/rx)**2+((Y-hy)/ry)**2)<=1).astype(np.float32)
    head=np.clip(ndi.gaussian_filter(head,6)/0.5,0,1)
    ny=fc['neck'][1]-oy
    head*=sm(np.clip((ny+6-Y)/22,0,1))       # fade out below the chin
    t0,t1=fc['torso']; t0-=oy; t1-=oy       # full weight above t0, zero at/below t1 (feet stay fixed)
    torso=sm(np.clip((t1-Y)/(t1-t0),0,1))
    out={'head':head,'torso':torso}
    if 'jhead' in fc:
        jx,jy,jrx,jry=fc['jhead']; jx-=ox; jy-=oy
        jh=((((X-jx)/jrx)**2+((Y-jy)/jry)**2)<=1).astype(np.float32)
        jh=np.clip(ndi.gaussian_filter(jh,6)/0.5,0,1)
        jh*=sm(np.clip((fc['jneck'][1]-oy+6-Y)/22,0,1))
        out['jhead']=jh
    return out

if __name__=='__main__':
    if 'ov' in sys.argv[2:]: build_ovs()
    OUT='/tmp/claude-0/-home-user/7ead4a65-9a3f-5f74-8eac-6850f8d7f07d/scratchpad/work/fix8/B4/regen'; os.makedirs(OUT,exist_ok=True)
    manifest={}; sheet_v=[]
    for name,fc in CFG['figs'].items():
        fj=FIGJ[name]; ox,oy,W,H=fj['px']
        HOME=np.asarray(Image.open(S+'/pub/'+fj['file']).convert('RGBA')).copy()
        a=HOME[...,3].astype(np.float32)/255; src=a[...,None]*HOME[...,:3].astype(np.float32)
        Wt=weights(fc,W,H,ox,oy)
        defs={'head':(fc['neck'][0]-ox,fc['neck'][1]-oy),'torso':(fc['foot'][0]-ox,fc['foot'][1]-oy)}
        if 'jhead' in fc: defs['jhead']=(fc['jneck'][0]-ox,fc['jneck'][1]-oy)
        ovs={}
        for on in sorted(set(o.get('as',k) for k,o in CFG.get('ovs',{}).items())):
            pth='ov/%s_%s_%s.png'%(ID,name,on)
            if not os.path.exists(pth): continue
            im=np.asarray(Image.open(pth)).astype(np.float32); cx,cy=json.load(open(pth[:-4]+'.json'))['xy']
            x,y=cx-ox,cy-oy; h,w=im.shape[:2]
            E=np.zeros((H,W,3),np.float32); M=np.zeros((H,W),np.float32)
            x0,y0=max(x,0),max(y,0); x1,y1=min(x+w,W),min(y+h,H)
            E[y0:y1,x0:x1]=im[y0-y:y1-y,x0-x:x1-x,:3]; M[y0:y1,x0:x1]=im[y0-y:y1-y,x0-x:x1-x,3]/255
            M*=(a>0.99)
            if M.sum()>3: ovs[on]=np.dstack([E*a[...,None],M])
        Image.fromarray(HOME).save(OUT+'/%s_home.png'%name)
        gl=[]; peaks=[]
        for gspec in fc['gestures']:
            gname,_,gsc=gspec.partition(':')
            Gs=LIB(gname,float(gsc) if gsc else fc.get('scale',1.0))
            if any(ch.startswith('ov.') and ch[3:] not in ovs for ch in Gs['tracks']): print('skip',name,gname); continue
            fr=render(defs,Gs,ovs,Wt,src,a,HOME); n=len(fr)
            cols=min(n,max(1,4096//W)); rows=-(-n//cols); assert rows*H<=4096
            sh=np.zeros((rows*H,cols*W,4),np.uint8)
            for j,f in enumerate(fr): sh[(j//cols)*H:(j//cols+1)*H,(j%cols)*W:(j%cols+1)*W]=f
            fn='%s_%s.webp'%(name,Gs['name']); Image.fromarray(sh).save(OUT+'/'+fn,'WEBP',quality=int(os.environ.get('Q','80')),method=6)
            pi=int(round(Gs['peak']*FPS)); peaks.append(fr[pi])
            e0=np.abs(fr[0].astype(int)-HOME).mean(); e1=np.abs(fr[-1].astype(int)-HOME).mean()
            bot=int(H*0.85); stat=max(np.abs(f[bot:].astype(int)-HOME[bot:]).mean() for f in fr)
            print(ID,name,gname,n,'fr ends',e0,e1,'bottom15%',round(stat,3),'KB',os.path.getsize(OUT+'/'+fn)//1024)
            gl.append(dict(name=Gs['name'],file='i7/cut/%s/%s'%(ID,fn),cols=cols,rows=rows,frames=n,fps=FPS,weight=fc.get('weights',{}).get(gname,Gs['weight'])))
        manifest[name]=dict(home='i7/cut/%s/%s_home.png'%(ID,name),w=W,h=H,gestures=gl)
        # review strip: home + peaks, face zoom
        hx,hy,rx,ry=fc['head']; x0=max(0,int(hx-ox-2.2*rx)); x1=min(W,int(hx-ox+2.2*rx)); y0=max(0,int(hy-oy-2.2*ry)); y1=min(H,int(hy-oy+2.2*ry))
        tiles=[HOME]+peaks
        def flat(im):
            al=im[...,3:]/255.; return (im[...,:3]*al+np.array([90,90,90])*(1-al))
        row=np.hstack([flat(t[y0:y1,x0:x1]) for t in tiles])
        sheet_v.append((name,[g['name'] for g in gl],row))
    json.dump(manifest,open(OUT+'/cut.json','w'),indent=1)
    Wm=max(r.shape[1] for _,_,r in sheet_v)
    st=np.vstack([np.pad(r,((0,6),(0,Wm-r.shape[1]),(0,0)),constant_values=255) for _,_,r in sheet_v])
    sc=min(3.0,2400/st.shape[1])
    Image.fromarray(st.clip(0,255).astype(np.uint8)).resize((int(st.shape[1]*sc),int(st.shape[0]*sc)),Image.LANCZOS).save('/tmp/claude-0/-home-user/7ead4a65-9a3f-5f74-8eac-6850f8d7f07d/scratchpad/work/fix8/B4/regen/peaks_%s.jpg'%ID,quality=88)
    for n,g,_ in sheet_v: print(n,'home +',g)
