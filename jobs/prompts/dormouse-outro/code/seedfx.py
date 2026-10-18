import numpy as np, cv2, math
def draw_seed(img, x, y, ang=0.0, glow=1.0, scale=1.0):
    """img float32 BGR 0..255. Additive warm halo + painted teardrop seed pointing up (ang radians tilt)."""
    H,W=img.shape[:2]; R=int(60*scale)
    x0,x1=max(0,int(x)-R),min(W,int(x)+R); y0,y1=max(0,int(y)-R),min(H,int(y)+R)
    if x0>=x1 or y0>=y1: return img
    yy,xx=np.mgrid[y0:y1,x0:x1].astype(np.float32); d=np.hypot(xx-x,yy-y)/scale
    halo=(np.exp(-(d/26)**2)*0.55+np.exp(-(d/9)**2)*0.5)*glow
    col=np.array([70,175,255],np.float32)
    img[y0:y1,x0:x1]=img[y0:y1,x0:x1]+(255-img[y0:y1,x0:x1])*np.clip(halo[...,None]*col/255,0,1)
    # teardrop at 4x supersample
    S=4; s=int(16*scale)+4; L=np.zeros((2*s*S,2*s*S,4),np.float32); c=s*S
    pts=[]
    for t in np.linspace(0,2*math.pi,60):
        r=1-0.55*(1+math.sin(t))/2   # pointed top
        px=math.cos(t)*5.0*r; py=-math.sin(t)*7.5 + 1.5
        pts.append((px,py))
    pts=np.array(pts)*scale
    ca,sa=math.cos(ang),math.sin(ang); pts=pts@np.array([[ca,sa],[-sa,ca]])
    P=np.round((pts*S)+c).astype(np.int32)
    cv2.fillPoly(L,[P],(30,120,200,1),cv2.LINE_AA)
    inner=np.round(pts*0.72*S+c).astype(np.int32); cv2.fillPoly(L,[inner],(80,205,255,1),cv2.LINE_AA)
    core=np.round(pts*0.35*S+c+np.array([0,2*S])).astype(np.int32); cv2.fillPoly(L,[core],(200,245,255,1),cv2.LINE_AA)
    L=cv2.resize(L,(2*s,2*s),interpolation=cv2.INTER_AREA)
    ix,iy=int(round(x))-s,int(round(y))-s
    a0,b0=max(0,ix),max(0,iy); a1,b1=min(W,ix+2*s),min(H,iy+2*s)
    if a0<a1 and b0<b1:
        l=L[b0-iy:b1-iy,a0-ix:a1-ix]; al=l[...,3:4]
        img[b0:b1,a0:a1]=img[b0:b1,a0:a1]*(1-al)+l[...,:3]*al
    return img
if __name__=='__main__':
    im=cv2.imread('ODr.png').astype(np.float32)
    draw_seed(im,650,531)
    draw_seed(im,800,300,0.3)
    cv2.imwrite('seedtest.png',cv2.resize(im[250:600,560:880].astype(np.uint8),(960,1050)))
