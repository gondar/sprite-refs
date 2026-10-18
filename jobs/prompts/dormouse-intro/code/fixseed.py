import cv2,json,numpy as np,sys
F=sys.argv[1]; D=sys.argv[2]; anchors=json.loads(sys.argv[3])  # {frame:[x,y]}
d=json.load(open(F)); s=d['seed']
A={int(k):v for k,v in anchors.items()}; ks=sorted(A)
def feat(im):
    b,g,r=[im[...,k].astype(np.float32) for k in range(3)]
    return cv2.GaussianBlur(np.clip(np.minimum(np.minimum(r-225,g-180),170-b),0,None),(0,0),2.0)
for i in range(ks[0],ks[-1]+1):
    j=max(k for k in ks if k<=i); k2=min(k for k in ks if k>=i)
    t=0 if k2==j else (i-j)/(k2-j)
    px=A[j][0]*(1-t)+A[k2][0]*t; py=A[j][1]*(1-t)+A[k2][1]*t
    y=feat(cv2.imread(D+'/f%04d.jpg'%i)); R=18
    x0,y0=int(px),int(py); sub=y[y0-R:y0+R,x0-R:x0+R]
    if sub.max()<1: s[i]=[round(px,1),round(py,1)]; continue
    yy,xx=np.unravel_index(sub.argmax(),sub.shape); cx,cy=x0-R+xx,y0-R+yy; r=8
    sub2=y[cy-r:cy+r,cx-r:cx+r]; ys,xs=np.mgrid[cy-r:cy+r,cx-r:cx+r]; w=sub2**2
    s[i]=[round(float((xs*w).sum()/w.sum()),1),round(float((ys*w).sum()/w.sum()),1)]
json.dump(d,open(F,'w'))
