import numpy as np,cv2,json,glob,math
fs=sorted(glob.glob('fog/*.png')); bg=cv2.imread('O1f.png').astype(np.float32)
path=json.load(open('outro_seedpath.json')); T=np.array(path['t']); P=np.array(path['xy'],float)
def cr(t):
    if t<=T[0]: return P[0]
    if t>=T[-1]: return P[-1]
    i=np.searchsorted(T,t)-1; u=(t-T[i])/(T[i+1]-T[i]); p0=P[max(i-1,0)];p1=P[i];p2=P[i+1];p3=P[min(i+2,len(P)-1)]
    return 0.5*((2*p1)+(-p0+p2)*u+(2*p0-5*p1+4*p2-p3)*u*u+(-p0+3*p1-3*p2+p3)*u**3)
N=201; out=[]
for i in range(N):
    t=i/30; s=min(len(fs)-1,int(round(t*24)))
    im=cv2.resize(cv2.imread(fs[s])[15:753,16:1328],(1280,720),interpolation=cv2.INTER_AREA).astype(np.float32)
    d=cv2.GaussianBlur(np.abs(im-bg).mean(2),(0,0),2)
    m=(d>28).astype(np.uint8); m=cv2.morphologyEx(m,cv2.MORPH_OPEN,np.ones((5,5),np.uint8))
    m[495:,600:]=0   # ignore the rosary/branch zone (rosary is not in these frames anyway)
    dist=cv2.distanceTransform(1-m,cv2.DIST_L2,5)
    p=cr(t).copy(); target=40 if t<4.6 else 0
    for _ in range(60):
        x,y=int(round(p[0])),int(round(p[1]))
        if dist[y,x]>=target: break
        gx=dist[y,min(1279,x+3)]-dist[y,max(0,x-3)]; gy=dist[min(719,y+3),x]-dist[max(0,y-3),x]
        g=np.hypot(gx,gy)+1e-6; p+=np.array([gx,gy])/g*3
    out.append(p)
out=np.array(out)
# temporal smoothing (keep the settled end fixed)
k=np.ones(9)/9; sm=out.copy()
for j in (0,1): sm[:,j]=np.convolve(np.pad(out[:,j],4,mode='edge'),k,'valid')
end=int(5.2*30); sm[end:]=P[-1]
json.dump({'xy':sm.round(1).tolist()},open('outro_seed_frames.json','w'))
print('max push',np.abs(out-np.array([cr(i/30) for i in range(N)])).max())
