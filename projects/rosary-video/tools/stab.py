import json,sys,numpy as np
from PIL import Image
d=sys.argv[1];meta=json.load(open(d+'/dm.json'))['meta']
PW,PH=1376,768
def warp(m):
    b=m['b'];im=Image.open(d+'/t_%.2f.png'%m['t']).convert('RGB')
    # frame = ox + u*w ; u = plate_x/PW -> affine from plate coords to frame
    sx=b['w']/PW;sy=b['h']/PH
    return im.transform((PW,PH),Image.AFFINE,(sx,0,b['ox'],0,sy,b['oy']),resample=Image.BICUBIC)
ws=[np.asarray(warp(m)).astype(float) for m in meta]
def reg(A,B):
    A=A.mean(2)-A.mean();B=B.mean(2)-B.mean()
    F=np.fft.fft2(A)*np.conj(np.fft.fft2(B));r=np.fft.ifft2(F/(np.abs(F)+1e-9)).real
    i=np.unravel_index(r.argmax(),r.shape);return [v if v<s/2 else v-s for v,s in zip(i,r.shape)]
regions=json.loads(sys.argv[2])
for nm,(x0,y0,x1,y1) in regions.items():
    x0,y0,x1,y1=[int(v) for v in (x0*PW,y0*PH,x1*PW,y1*PH)]
    diffs=[np.abs(ws[k][y0:y1,x0:x1]-ws[0][y0:y1,x0:x1]).mean() for k in range(1,len(ws))]
    sh=[reg(ws[k][y0:y1,x0:x1],ws[0][y0:y1,x0:x1]) for k in range(1,len(ws))]
    print(nm,'maxdiff %.2f mean %.2f'%(max(diffs),np.mean(diffs)),'shifts',sh[::3])
if len(sys.argv)>3:
    x0,y0,x1,y1=[int(v) for v in json.loads(sys.argv[3])]
    fr=[Image.fromarray(w[y0:y1,x0:x1].astype('uint8')) for w in ws[::3]]
    S=Image.new('RGB',(fr[0].size[0]*len(fr),fr[0].size[1]))
    for k,f in enumerate(fr):S.paste(f,(k*f.size[0],0))
    S.save(sys.argv[4],quality=92)
    # diff max vs first
    D=np.max([np.abs(w[y0:y1,x0:x1]-ws[0][y0:y1,x0:x1]) for w in ws],axis=0).clip(0,255/4)*4
    Image.fromarray(D.astype('uint8')).save(sys.argv[4].replace('.jpg','_diff.jpg'))
