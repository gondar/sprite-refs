# g2.py scene fig gesture frame x0 y0 x1 y1 out : home | frame, bicubic x12 with grid every 2px
import sys,json,numpy as np,cv2
from PIL import Image
P='/tmp/claude-0/-home-user/7ead4a65-9a3f-5f74-8eac-6850f8d7f07d/scratchpad/pub/'
sc,fig,gn,k=sys.argv[1:5]; x0,y0,x1,y1=map(int,sys.argv[5:9]); out=sys.argv[9]
c=json.load(open(P+'i7/cut/%s/cut.json'%sc))[fig]; w,h=c['w'],c['h']
H=np.asarray(Image.open(sys.argv[10] if len(sys.argv)>10 else P+c['home']).convert('RGBA')).astype(np.float32)
if gn=='-': F=np.asarray(Image.open(k).convert('RGBA')).astype(np.float32)
else:
    g=[g for g in c['gestures'] if g['name']==gn][0]; k=int(k)
    sh=np.asarray(Image.open(P+g['file']).convert('RGBA')).astype(np.float32)
    F=sh[(k//g['cols'])*h:(k//g['cols']+1)*h,(k%g['cols'])*w:(k%g['cols']+1)*w]
fl=lambda a:(a[...,:3]*a[...,3:]/255+128*(1-a[...,3:]/255)).astype(np.uint8)
Z=12; tiles=[]
for a in (H,F):
    c_=fl(a)[y0:y1,x0:x1]; b=cv2.resize(c_,(c_.shape[1]*Z,c_.shape[0]*Z),interpolation=cv2.INTER_CUBIC)
    b=np.pad(b,((18,0),(26,6),(0,0)),constant_values=255).copy()
    for x in range(x0,x1):
        if x%2==0: cv2.line(b,(26+(x-x0)*Z,18),(26+(x-x0)*Z,b.shape[0]),(0,200,0) if x%10 else (255,0,255),1)
        if x%10==0: cv2.putText(b,str(x),(26+(x-x0)*Z,13),0,0.4,(0,0,0),1)
    for y in range(y0,y1):
        if y%2==0: cv2.line(b,(26,18+(y-y0)*Z),(b.shape[1]-6,18+(y-y0)*Z),(0,200,0) if y%10 else (255,0,255),1)
        if y%10==0: cv2.putText(b,str(y),(0,22+(y-y0)*Z),0,0.4,(0,0,0),1)
    tiles.append(b)
Image.fromarray(np.concatenate(tiles,1)).save(out)
