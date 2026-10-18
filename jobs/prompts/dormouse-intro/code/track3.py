import cv2,numpy as np,json,sys
D=sys.argv[1]; N=int(sys.argv[2]); OUT=sys.argv[3]
def feat(im):
    b,g,r=[im[...,k].astype(np.float32) for k in range(3)]
    y=np.clip(np.minimum(np.minimum(r-225,g-180),170-b),0,None)
    return cv2.GaussianBlur(y,(0,0),2.0)
C=[];F=[]
NOSE=json.load(open('track_nose.json'))['nose'] if len(sys.argv)>4 else None
for i in range(N):
    im=cv2.imread(D+'/f%04d.jpg'%i); y=feat(im)
    mx=cv2.dilate(y,np.ones((21,21),np.uint8))
    pk=np.argwhere((y==mx)&(y>1.5))
    sc=y[pk[:,0],pk[:,1]]; o=np.argsort(-sc)[:10]
    if NOSE is not None and NOSE[i] is not None:
        keep=[k for k in o if np.hypot(pk[k,1]-NOSE[i][0],pk[k,0]-NOSE[i][1])>24]; o=np.array(keep,dtype=int)
    m=sc[o].max() if len(o) else 1
    cands=[(float(pk[k,1]),float(pk[k,0]),float(sc[k]),float(sc[k]/m)) for k in o]
    C.append(cands)
# viterbi with a 'missing' state
SIG=40.0; MISS=6.0
states=[list(cc)+[None] for cc in C]
cost=[];back=[]
def emit(s): return MISS if s is None else 6*(1-s[3])
prevc=[emit(s) for s in states[0]]; cost.append(prevc); back.append([None]*len(states[0]))
lastpos=[ (s[0],s[1]) if s else None for s in states[0]]
for i in range(1,N):
    cur=[];bk=[];lp=[]
    for s in states[i]:
        best=1e18;bj=0
        for j,p in enumerate(states[i-1]):
            q=lastpos[j]
            if s is None: tr=0.5
            elif q is None: tr=3.0
            else: tr=((s[0]-q[0])**2+(s[1]-q[1])**2)/(2*SIG**2)
            c=prevc[j]+tr
            if c<best: best=c;bj=j
        cur.append(best+emit(s)); bk.append(bj)
        lp.append((s[0],s[1]) if s else lastpos[bj])
    prevc=cur;back.append(bk);lastpos=lp
j=int(np.argmin(prevc)); path=[None]*N
for i in range(N-1,-1,-1):
    s=states[i][j]; path[i]=None if s is None else [round(s[0],1),round(s[1],1)]; j=back[i][j] if i>0 else j
# refine centroid on core
out=[]
for i,p in enumerate(path):
    if p is None: out.append(None); continue
    im=cv2.imread(D+'/f%04d.jpg'%i); y=feat(im); x0,y0=int(p[0]),int(p[1]); r=10
    sub=y[max(0,y0-r):y0+r,max(0,x0-r):x0+r]; ys,xs=np.mgrid[max(0,y0-r):max(0,y0-r)+sub.shape[0],max(0,x0-r):max(0,x0-r)+sub.shape[1]]
    w=sub**2; out.append([round(float((xs*w).sum()/w.sum()),1),round(float((ys*w).sum()/w.sum()),1)])
json.dump({'seed':out},open(OUT,'w'))
print('missing',sum(p is None for p in out))
