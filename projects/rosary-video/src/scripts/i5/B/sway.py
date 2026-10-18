import numpy as np, cv2, json, sys
from PIL import Image
from scipy import ndimage as ndi
S='/tmp/claude-0/-home-user/7ead4a65-9a3f-5f74-8eac-6850f8d7f07d/scratchpad/pub/'
W,H=1376,768
def layer(ID,name,alpha,clean):
    ys,xs=np.where(alpha>0.02); y0,y1,x0,x1=ys.min(),ys.max()+1,xs.min(),xs.max()+1
    full=np.asarray(Image.open(S+f'i5/{ID}_full.jpg').convert('RGB'))
    rgba=np.dstack([full[y0:y1,x0:x1],(alpha[y0:y1,x0:x1]*255).astype(np.uint8)])
    Image.fromarray(rgba,'RGBA').save(S+f'i6/fx/{ID}_{name}.png',optimize=True)
    return [round(x0/W,4),round(y0/H,4),round((x1-x0)/W,4),round((y1-y0)/H,4)],(x0,y0,x1,y1)
def inpaint_under(plate,mask,r=6):
    m=(ndi.binary_dilation(mask,iterations=r)*255).astype(np.uint8)
    return cv2.inpaint(plate,m,7,cv2.INPAINT_TELEA)
ID=sys.argv[1]
plate=np.asarray(Image.open(S+f'i5/{ID}_plate.jpg').convert('RGB')).copy()
full=np.asarray(Image.open(S+f'i5/{ID}_full.jpg').convert('RGB')).astype(float)
Y,X=np.mgrid[0:H,0:W]
out={}
if ID=='B3':
    r,g,b=full[...,0],full[...,1],full[...,2]
    box=(X>=925)&(X<1065)&(Y>=480)&(Y<590)
    m=box&(r>g+35)&(r>b+5)
    m=ndi.binary_closing(m,iterations=3); m=ndi.binary_fill_holes(m); m=ndi.binary_opening(m,iterations=2)
    lab,n=ndi.label(m); sz=ndi.sum(m,lab,range(1,n+1)); m=lab==(np.argmax(sz)+1)
    m=ndi.binary_dilation(m,iterations=2)
    a=np.clip(ndi.gaussian_filter(m.astype(float),0.8),0,1)
    bb,px=layer(ID,'rag',a,None)
    clean=inpaint_under(plate,m,4)
    out['rag']=bb
elif ID=='B5':
    r,g,b=full[...,0],full[...,1],full[...,2]
    # tree crown: greener/darker than indigo sky, left part, above y 0.56
    region=(X<445)&(Y<360)
    sky=((b-r>28)&(b-g>20)&((b>70)|(Y<40)))|ndi.binary_dilation(r>b+6,iterations=4)
    m=region&~sky
    m=ndi.binary_opening(m,iterations=1); m=ndi.binary_closing(m,iterations=2)
    lab,n=ndi.label(m); sz=ndi.sum(m,lab,range(1,n+1)); m=lab==(np.argmax(sz)+1)
    m=ndi.binary_fill_holes(ndi.binary_closing(m,iterations=6))
    # keep only crown (not the trunk lower part / hill): above the hill line approx y<360 or x<300
    pass
    a=np.clip(ndi.gaussian_filter(m.astype(float),0.7),0,1)
    bb,px=layer(ID,'olive',a,None)
    clean=inpaint_under(plate,m,5)
    out['olive']=bb
else:
    clean=plate
Image.fromarray(clean).save(S+f'i6/fx/{ID}_plate_clean.jpg',quality=86)
print(ID,out)
json.dump(out,open(f'/tmp/claude-0/-home-user/7ead4a65-9a3f-5f74-8eac-6850f8d7f07d/scratchpad/scripts/i5/B/sway_{ID}.json','w'))
