import numpy as np, json
from PIL import Image
from scipy import ndimage as ndi
full=np.asarray(Image.open('../pub/i5/R1_full.jpg').convert('RGB')).astype(np.float32)
FIG={'mary':(578,218),'angel':(253,79)}
CROP={'mary':(668,198),'angel':(583,139)}   # crop origin in frame, crop size 200
# boxes in crop coords (x0,y0,x1,y1) where the change may be taken
BOX={'mary_blink':(40,45,125,100),'mary_up':(40,40,125,100),'mary_wonder':(58,94,96,124),'mary_smile':(55,92,110,126),
     'angel_open':(95,85,140,125),'angel_lips':(90,120,130,150)}
out={}
for n,b in BOX.items():
    fig=n.split('_')[0]; cx,cy=CROP[fig]
    E=np.asarray(Image.open('ed/%s_raw.png'%n).convert('RGB').resize((200,200),Image.LANCZOS)).astype(np.float32)
    E=ndi.gaussian_filter(E,(0.6,0.6,0))
    O=full[cy:cy+200,cx:cx+200]
    x0,y0,x1,y1=b
    box=np.zeros((200,200),bool); box[y0:y1,x0:x1]=True
    d=np.abs(ndi.gaussian_filter(E,(1,1,0))-ndi.gaussian_filter(O,(1,1,0))).max(2)
    ch=(d>(28 if fig=="mary" else 12))&box
    ch=ndi.binary_opening(ch,iterations=1)
    lab,k=ndi.label(ch); sz=ndi.sum(ch,lab,range(1,k+1))
    ch=np.isin(lab,1+np.nonzero(sz>=6)[0])
    ch=ndi.binary_dilation(ch,iterations=3)&ndi.binary_dilation(box,iterations=0)
    m=ndi.gaussian_filter(ch.astype(np.float32),1.3)*box
    m=np.clip(m*1.6,0,1)
    # colour match edit->orig on box ring where unchanged
    ring=box&~ndi.binary_dilation(ch,iterations=4)
    ring=ndi.binary_dilation(ch,iterations=10)&~ndi.binary_dilation(ch,iterations=2)
    sm=ndi.binary_dilation(ch,iterations=2)
    # local tone match: smooth offset O-E learned on the unchanged ring, spread by normalized convolution
    wr=ring.astype(np.float32); sg=5
    den=ndi.gaussian_filter(wr,sg)+1e-6
    for c in range(3):
        off=ndi.gaussian_filter((O[...,c]-E[...,c])*wr,sg)/den
        E[...,c]=E[...,c]+off
    # into figure canvas coords
    fx,fy=FIG[fig]; ox,oy=cx-fx,cy-fy
    out[n]=dict(xy=[int(ox),int(oy)],px=int(ch.sum()))
    rgba=np.dstack([np.clip(E,0,255),m*255]).astype(np.uint8)
    Image.fromarray(rgba).save('ov_%s.png'%n)
    print(n,'changed px',ch.sum(),'ring',ring.sum())
json.dump(out,open('ov.json','w'))
