import numpy as np,cv2,os,glob,json
S='/tmp/claude-0/-home-user/7ead4a65-9a3f-5f74-8eac-6850f8d7f07d/scratchpad'
A=[cv2.imread('fa2g/%04d.png'%i) for i in range(1,125)]
B=[cv2.imread('fbg/%04d.png'%i) for i in range(1,125)]
b1=B[0]
dis=cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)
H,W=b1.shape[:2];X,Y=np.meshgrid(np.arange(W,dtype=np.float32),np.arange(H,dtype=np.float32))
N=10
g1=cv2.cvtColor(b1,cv2.COLOR_BGR2GRAY)
for k in range(N):
    j=124-N+k  # index in A (0-based) ; last one j=123
    t=(k+1)/N
    a=A[j]; ga=cv2.cvtColor(a,cv2.COLOR_BGR2GRAY)
    f=dis.calc(ga,g1,None)   # flow a->b1: a(x) ~ b1(x+f)
    # warp a toward b1 by t: sample a at x - t*f ; and b1 toward a by (1-t): sample b1 at x+(1-t)f... approximate
    wa=cv2.remap(a,X-t*f[...,0],Y-t*f[...,1],cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE)
    fb=dis.calc(g1,ga,None)
    wb=cv2.remap(b1,X-(1-t)*fb[...,0],Y-(1-t)*fb[...,1],cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE)
    A[j]=np.clip((1-t)*wa.astype(np.float32)+t*wb.astype(np.float32),0,255).astype(np.uint8)
src=A+B[1:]   # 247 frames, 24 fps
FPS=30; INTRO=0.859+4*2.0434; TOT=INTRO+2.4
n=int(round(TOT*FPS))
speed=(len(src)-1)/24/INTRO
os.makedirs(S+'/pub/intro',exist_ok=True)
for f in glob.glob(S+'/pub/intro/f*.jpg'): os.remove(f)
mp=[]
for i in range(n):
    t=i/FPS
    s=min(len(src)-1,int(round(t*speed*24)))
    mp.append(s)
    im=src[s][15:753,16:1328]   # 1312x738, drop replicated borders
    im=cv2.resize(im,(1280,720),interpolation=cv2.INTER_AREA)
    cv2.imwrite(S+'/pub/intro/f%04d.jpg'%i,im,[cv2.IMWRITE_JPEG_QUALITY,90])
json.dump({'speed':speed,'map':mp},open('map.json','w'))
print(n,'frames speed',speed)
