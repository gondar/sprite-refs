import numpy as np,cv2,json,os,glob,sys,math
from seedfx import draw_seed
S='/tmp/claude-0/-home-user/7ead4a65-9a3f-5f74-8eac-6850f8d7f07d/scratchpad'
SRC=sys.argv[1]   # geo-fixed frames dir (1344x768, 24 fps)
fs=sorted(glob.glob(SRC+'/*.png'))
L=np.load('rosary_layer.npy');SH=np.load('rosary_shadow.npy')
R=json.load(open('rosary.json'))
FPS=30; N=int(round(6.7*FPS)); speed=float(sys.argv[2]) if len(sys.argv)>2 else 1.0
path=json.load(open('outro_seedpath.json'))  # {"t":[...], "xy":[[x,y],...]}
T=np.array(path['t']); P=np.array(path['xy'],float)
def seed_at(t):
    if t<=T[0]: return P[0]
    if t>=T[-1]: return P[-1]
    i=np.searchsorted(T,t)-1; u=(t-T[i])/(T[i+1]-T[i])
    p0=P[max(i-1,0)];p1=P[i];p2=P[i+1];p3=P[min(i+2,len(P)-1)]
    u2,u3=u*u,u*u*u
    return 0.5*((2*p1)+(-p0+p2)*u+(2*p0-5*p1+4*p2-p3)*u2+(-p0+3*p1-3*p2+p3)*u3)
os.makedirs(S+'/pub/outro',exist_ok=True)
for f in glob.glob(S+'/pub/outro/f*.jpg'): os.remove(f)
seeds=[]
for i in range(N):
    t=i/FPS; s=min(len(fs)-1,int(round(t*speed*24)))
    im=cv2.imread(fs[s])[15:753,16:1328]
    im=cv2.resize(im,(1280,720),interpolation=cv2.INTER_AREA).astype(np.float32)
    im=im*(1-SH[...,None]); a=L[...,3:4]; im=im*(1-a)+L[...,:3]*a
    FR=json.load(open('outro_seed_frames.json'))['xy']
    x,y=FR[i]; seeds.append([round(float(x),1),round(float(y),1)])
    # tilt the teardrop along motion
    x2,y2=FR[min(i+1,N-1)]; vx,vy=x2-x,y2-y; ang=math.atan2(vx,-vy)*0.5 if math.hypot(vx,vy)>0.5 else 0
    pulse=1.0+0.08*math.sin(t*5.0)
    draw_seed(im,x,y,ang,glow=pulse,scale=1.35)
    cv2.imwrite(S+'/pub/outro/f%04d.jpg'%i,np.clip(im,0,255).astype(np.uint8),[cv2.IMWRITE_JPEG_QUALITY,90])
J={'fps':FPS,'frames':N,'duration_s':round(N/FPS,3),'seed':seeds,'seedInVideo':False,'seedDrawnInFrames':True,
   'rosary':{'cross':R['cross'],'beads':[b['xy'] for b in R['beads']],'beadKinds':[b['kind'] for b in R['beads']]},
   'notes':''}
json.dump(J,open(S+'/pub/outro/outro.json','w'))
print('frames',N)
