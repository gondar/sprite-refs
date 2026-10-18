# lid.py JOB : hand-placed procedural closed eyes on a copy of the figure home PNG.
# Only RGB inside the eye ellipses (minus the hand 'keep' lines) changes; alpha never changes.
# writes fix6/<JOB>_closed.png and a x8 home|closed check fix6/<JOB>_chk.png
import json,sys,numpy as np,cv2
from PIL import Image
D='/tmp/claude-0/-home-user/7ead4a65-9a3f-5f74-8eac-6850f8d7f07d/scratchpad/'
J=json.load(open(D+'fix6/jobs.json'))[sys.argv[1]]
home=np.asarray(Image.open(D+'pub/'+J['home']).convert('RGBA')).copy()
H,W=home.shape[:2]; rgb=home[...,:3].astype(np.float32); A=home[...,3]
L=cv2.cvtColor(np.ascontiguousarray(home[...,:3]),cv2.COLOR_RGB2LAB)[...,0].astype(np.float32)
Yg,Xg=np.mgrid[0:H,0:W].astype(np.float32)
keep=np.zeros((H,W),np.uint8)
for ln in J.get('keep',[]):   # contour / brow / nose pieces that must stay untouched
    cv2.polylines(keep,[np.array(ln['pts'],np.int32)],False,1,thickness=ln.get('t',1))
keep=keep>0
eyemask=np.zeros((H,W),bool)
for e in J['eyes']:
    cx,cy=e['c']; rx,ry=e['r']
    eyemask|=(((Xg-cx)/rx)**2+((Yg-cy)/ry)**2)<=1
fill=eyemask&~keep&(A>250)
# skin shade from figure pixels in a ring around the eyes only
ring=(cv2.dilate(eyemask.astype(np.uint8),np.ones((9,9),np.uint8))>0)&~eyemask&(A>250)
lo,hi=J.get('skinL',[120,235])
ring&=(L>lo)&(L<hi)
out=rgb.copy()
for e in J['eyes']:   # per eye: least-squares plane of the skin colour in its own ring
    cx,cy=e['c']; rx,ry=e['r']; m=(((Xg-cx)/rx)**2+((Yg-cy)/ry)**2)<=1
    if 'plane_of' in e:   # tiny patch: use the plane of a bigger neighbour eye
        e2=J['eyes'][e['plane_of']]; cx,cy=e2['c']; rx,ry=e2['r']
    rg=ring&((((Xg-cx)/(rx+4))**2+((Yg-cy)/(ry+4))**2)<=1)
    M=np.c_[Xg[rg]-cx,Yg[rg]-cy,np.ones(rg.sum())]
    for k in range(3):
        co=np.linalg.lstsq(M,rgb[...,k][rg],rcond=None)[0]
        pl=co[0]*(Xg-cx)+co[1]*(Yg-cy)+co[2]
        out[...,k][m&fill]=pl[m&fill]
    print(' eye',e['c'],'ring px',int(rg.sum()),'skin',np.round(np.median(rgb[rg],0)))
# soften the seam: 1 px band around each ellipse edge (skin pixels only) takes a light blur
k3=np.ones((3,3),np.uint8); em=eyemask.astype(np.uint8)
band=((cv2.dilate(em,k3)>0)&~(cv2.erode(em,k3)>0))&~keep&(A>250)&((L>lo)|eyemask)
ww=(((L>lo)&(A>250))|fill).astype(np.float32); sgm=J.get('seam',0.9)
dn=cv2.GaussianBlur(ww,(0,0),sgm)+1e-6
bl=np.dstack([cv2.GaussianBlur(out[...,k]*ww,(0,0),sgm)/dn for k in range(3)])
band&=(L>lo)|fill; out[band]=bl[band]
S=8; big=cv2.resize(out,(W*S,H*S),interpolation=cv2.INTER_CUBIC)
dark=tuple(float(v) for v in J['line'])
for lid in J['lids']:
    p0,p1,p2=[np.array([x*S+S/2,y*S+S/2],np.float32) for x,y in lid]
    t=np.linspace(0,1,24)[:,None]
    curve=((1-t)**2*p0+2*(1-t)*t*p1+t**2*p2).astype(np.int32)
    cv2.polylines(big,[curve],False,dark,thickness=max(1,int(J.get('lw',1.2)*S)),lineType=cv2.LINE_AA)
for ln in J.get('paint',[]):   # re-draw a contour piece that the open eye had drawn over
    pts=np.array([[x*S+S/2,y*S+S/2] for x,y in ln['pts']],np.int32)
    cv2.polylines(big,[pts],False,dark,thickness=max(1,int(ln.get('w',1.3)*S)),lineType=cv2.LINE_AA)
pm=np.zeros((H*S,W*S),np.uint8)
for ln in J.get('paint',[]):
    pts=np.array([[x*S+S/2,y*S+S/2] for x,y in ln['pts']],np.int32)
    cv2.polylines(pm,[pts],False,255,thickness=max(1,int(ln.get('w',1.3)*S)),lineType=cv2.LINE_AA)
paintm=cv2.resize(pm,(W,H),interpolation=cv2.INTER_AREA)>40
small=cv2.resize(big,(W,H),interpolation=cv2.INTER_AREA)
# lid line may extend a little beyond the fill; allow change only in the eye mask minus keep
chg=((eyemask|band)&~keep&(A>250))|(paintm&(A>200))
res=home.copy(); res[...,:3][chg]=np.clip(small[chg],0,255).astype(np.uint8)
Image.fromarray(res).save(D+'fix6/%s_closed.png'%sys.argv[1])
diff=np.abs(res.astype(int)-home.astype(int)).max(2)>0; ys,xs=np.nonzero(diff)
print(sys.argv[1],'changed px',int(diff.sum()),'box',(xs.min(),ys.min(),xs.max(),ys.max()) if len(xs) else None)
x0,y0,x1,y1=J['view']
def fl(a):
    a=a.astype(np.float32); al=a[...,3:]/255; return (a[...,:3]*al+128*(1-al)).astype(np.uint8)
v=np.hstack([fl(home)[y0:y1,x0:x1],np.full((y1-y0,1,3),255,np.uint8),fl(res)[y0:y1,x0:x1]])
Image.fromarray(v).resize((v.shape[1]*8,v.shape[0]*8),Image.NEAREST).save(D+'fix6/%s_chk.png'%sys.argv[1])
