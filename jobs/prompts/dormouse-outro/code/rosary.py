import numpy as np, cv2, json, math
SS=3; W,H=1280,720
TOP=[(600,540),(630,535),(650,532),(700,527),(750,530),(800,540),(850,558),(900,578),(950,595),(1000,605),(1050,610),(1100,600),(1150,585)]
tx=np.array([p[0] for p in TOP],float); ty=np.array([p[1] for p in TOP],float)
def top(x): return np.interp(x,tx,ty)
rS,rL,rJ=7.0,9.5,8.0
seq=[]  # radii along loop starting after join
for d in range(5):
    seq+= ['S']*10
    if d<4: seq.append('L')
rad={'S':rS,'L':rL}
gaps=[rJ+rS+1.5]+[rad[a]+rad[b]+1.5 for a,b in zip(seq[:-1],seq[1:])]+[rS+rJ+1.5]
PER=sum(gaps)
B=24.0  # half thickness of the oval
def curve(a,xl,n=4000):
    th=np.linspace(math.pi,-math.pi,n)  # start at left end, go along far (top) strand first? sin<0 => far
    x=xl+a*(1+np.cos(th)); y=top(x)+5+B*np.sin(th)*-1*-1
    # th from pi to -pi: sin goes 0 -> -? at th=pi/2.. ; use sin(th): for th in (0,pi) sin>0 => near strand (lower)
    return x,y
def arclen(x,y): return np.concatenate([[0],np.cumsum(np.hypot(np.diff(x),np.diff(y)))])
xl=650.0
lo,hi=100,300
for _ in range(50):
    a=(lo+hi)/2; x,y=curve(a,xl); L=arclen(x,y)[-1]
    if L<PER: lo=a
    else: hi=a
x,y=curve(a,xl); s=arclen(x,y)
print('a',round(a,1),'span x',round(x.min()),round(x.max()))
pos=np.cumsum(gaps)[:-1]
beads=[]
for p,k in zip(pos,seq):
    i=np.searchsorted(s,p); beads.append((float(x[i]),float(y[i]),rad[k],k, float(np.sin(np.linspace(math.pi,-math.pi,4000)[i]))))
J=(float(x[0]),float(y[0]))
# pendant hangs straight down from the join with a slight sway to the right
pend=[];cy=J[1]
for k,r in (('L',rL),('S',rS),('S',rS),('S',rS),('L',rL)):
    prev=pend[-1][2] if pend else rJ
    cy+=prev+r+1.5; pend.append((J[0]+0.06*(cy-J[1]),cy,r,k))
cross_top=cy+rL+2; crossC=(J[0]+0.06*(cross_top+15-J[1]),cross_top+13)
# --- render
cv=np.zeros((H*SS,W*SS,4),np.float32)
sh=np.zeros((H*SS,W*SS),np.float32)
rng=np.random.default_rng(7)
def P(v): return int(round(v*SS))
OUT=(22,28,45)  # BGR dark brown outline
def bead(img,cx,cy,r,tone=1.0):
    c=(P(cx),P(cy)); R=P(r)
    base=np.array([45,68,100])*tone*rng.uniform(0.9,1.08); shade=np.array([30,42,64])*tone
    cv2.circle(img,c,R,(*OUT,1),-1,cv2.LINE_AA)
    cv2.circle(img,c,R-SS,(*base.tolist(),1),-1,cv2.LINE_AA)
    cv2.ellipse(img,(c[0]+R//4,c[1]+R//4),(int(R*0.7),int(R*0.6)),0,0,360,(*shade.tolist(),1),-1,cv2.LINE_AA)
    cv2.ellipse(img,c,(R-2*SS,R-2*SS),0,200,290,(85,135,190,1),max(1,SS),cv2.LINE_AA)
    cv2.circle(img,(c[0]-R//3,c[1]-R//3),max(1,R//6),(120,165,210,1),-1,cv2.LINE_AA)
# cord
pts=np.stack([x,y],1)
far=[i for i in range(len(x)) if np.sin(np.linspace(math.pi,-math.pi,4000)[i])<0]
def poly(img,P_,col,w): cv2.polylines(img,[np.round(P_*SS).astype(np.int32)],False,col,w,cv2.LINE_AA)
poly(cv,pts,(*[30,45,70],1),SS*2)
for b in beads: cv2.circle(sh,(P(b[0]+2),P(b[1]+3)),P(b[2]),0.45,-1,cv2.LINE_AA)
# far strand first (darker), then near
for b in sorted(beads,key=lambda b:b[4]):
    bead(cv,b[0],b[1],b[2]*(0.94 if b[4]<0 else 1.0)*rng.uniform(0.95,1.05),0.85 if b[4]<0 else 1.0)
# pendant cord
poly(cv,np.array([J]+[(p[0],p[1]) for p in pend]+[(crossC[0],cross_top)]),(*[30,45,70],1),SS*2)
# join knot
cv2.ellipse(cv,(P(J[0]),P(J[1])),(P(rJ),P(rJ*0.8)),0,0,360,(*OUT,1),-1,cv2.LINE_AA)
cv2.ellipse(cv,(P(J[0]),P(J[1])),(P(rJ)-SS,P(rJ*0.8)-SS),0,0,360,(60,100,150,1),-1,cv2.LINE_AA)
for p in pend:
    cv2.circle(sh,(P(p[0]+2),P(p[1]+3)),P(p[2]),0.35,-1,cv2.LINE_AA); bead(cv,p[0],p[1],p[2])
# cross: two twigs tied
cx,cyc=crossC
def twig(x0,y0,x1,y1,w):
    cv2.line(cv,(P(x0),P(y0)),(P(x1),P(y1)),(*OUT,1),P(w)+2*SS,cv2.LINE_AA)
    cv2.line(cv,(P(x0),P(y0)),(P(x1),P(y1)),(38,60,92,1),P(w),cv2.LINE_AA)
    cv2.line(cv,(P(x0),P(y0)),(P(x1),P(y1)),(70,110,160,1),max(1,SS),cv2.LINE_AA)
cv2.line(sh,(P(cx+2),P(cross_top+3)),(P(cx+2),P(cross_top+33)),0.35,P(5),cv2.LINE_AA)
twig(cx,cross_top-1,cx+0.6,cross_top+40,5.0)
twig(cx-13,cyc-3,cx+13,cyc-3.6,4.6)
for k in range(3): cv2.line(cv,(P(cx-3),P(cyc-6+k*1.6)),(P(cx+3),P(cyc-3.5+k*1.6)),(120,170,200,1),max(1,SS),cv2.LINE_AA)
layer=cv2.resize(cv,(W,H),interpolation=cv2.INTER_AREA)
nz=np.random.default_rng(3).normal(0,6,(H,W,1)).astype(np.float32); layer[...,:3]=np.clip(layer[...,:3]+nz*(layer[...,3:4]>0),0,255)
shadow=cv2.GaussianBlur(cv2.resize(sh,(W,H),interpolation=cv2.INTER_AREA),(0,0),2.0)
np.save('rosary_layer.npy',layer); np.save('rosary_shadow.npy',shadow)
order=[{'kind':'pendant-'+p[3],'xy':[round(p[0],1),round(p[1],1)]} for p in reversed(pend)]+[{'kind':'join','xy':[round(J[0],1),round(J[1],1)]}]+[{'kind':b[3],'xy':[round(b[0],1),round(b[1],1)]} for b in beads]
json.dump({'cross':[round(cx,1),round(cyc,1)],'beads':order},open('rosary.json','w'))
print('cross bottom2',cross_top+40);print('beads',len(order),'cross',cx,cyc,'join',J, 'cross bottom',cross_top+30)
