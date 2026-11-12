import json, numpy as np, os
from PIL import Image
OUT='/home/user/MusicGames/ukulele-warmup/art/podstawy'
def frames(p):
    im=Image.open(p); fr=[]
    for i in range(im.n_frames): im.seek(i); fr.append(im.convert('RGBA'))
    return fr
def union(fr,pad=6):
    bs=[f.getbbox() for f in fr]; x0=min(b[0] for b in bs);y0=min(b[1] for b in bs);x1=max(b[2] for b in bs);y1=max(b[3] for b in bs)
    W,H=fr[0].size; return (max(0,x0-pad),max(0,y0-pad),min(W,x1+pad),min(H,y1+pad))
def strip(fr,box,height,name,fps,order,extra,feather=None):
    cr=[f.crop(box) for f in fr]; s=height/cr[0].height; w=round(cr[0].width*s)
    cr=[c.resize((w,height),Image.LANCZOS) for c in cr]
    if feather:
        yy,xx=np.mgrid[0:height,0:w]; d=(xx/w+yy/height)
        fa=np.clip((d-feather[0])/(feather[1]-feather[0]),0,1); fa=fa*fa*(3-2*fa)
        out=[]
        for c in cr:
            a=np.array(c).astype(float); a[...,3]*=fa; out.append(Image.fromarray(a.astype('uint8'),'RGBA'))
        cr=out
    seq=[cr[i] for i in order]
    S=Image.new('RGBA',(w*len(seq),height),(0,0,0,0))
    for i,c in enumerate(seq): S.paste(c,(i*w,0))
    p=f'{OUT}/{name}.webp'; S.save(p,'WEBP',quality=85,method=6)
    # fingertip / lowest point per frame, % of the frame
    tips=[]
    for c in seq:
        a=np.array(c)[...,3]>128; ys,xs=np.nonzero(a); yb=ys.max(); xb=xs[ys>=yb-2].mean()
        tips.append([round(100*xb/w,1),round(100*yb/height,1)])
    man={'image':f'{name}.webp','frameWidth':w,'frameHeight':height,'frames':len(seq),'fps':fps,
         'layout':'one row, left to right; background-size: %d00%% 100%%'%len(seq),'loop':True,
         'sourceFrames':order,**extra,'lowestPointPerFrame':tips}
    json.dump(man,open(f'{OUT}/{name}.json','w'),indent=1)
    print(name,w,height,len(seq),round(os.path.getsize(p)/1024,1),'kb'); return man
kid=frames('gif/kid-strum.gif')
strip(kid,union(kid[:4]),420,'kid-strum',8,[0,1,2,3,3,2,1,0],
  {'downstrokeBottomFrame':3,'upstrokeTopFrame':7,
   'note':'GIF frames 0-3 are the down sweep; played as a ping-pong (0,1,2,3,3,2,1,0) so the up-stroke mirrors it. Frames 3 and 4 = hand at the bottom (sound of the down-strum), frames 7 and 0 = hand at the top (sound of the up-strum). One full down-up per second at 8 fps. Neck points to the viewer\'s RIGHT, up; the kid faces the viewer, right hand on the viewer\'s left.'})
hand=frames('gif/hand-strum.gif')
m=strip(hand,union(hand),360,'hand-strum',10,list(range(8)),
  {'downstrokeBottomFrame':3,'upstrokeTopFrame':0,
   'note':'Raw GIF order is already a smooth down-up loop (index-tip y: down 0->3, back up 4->7->0). The sleeve enters from the top-left and is faded out there (alpha ramp) so the strip can sit over the SVG body without a hard cut edge. Code may add a vertical translate (about 1/4 of the frame height) in sync with the frames to make the sweep across the strings bigger.',
   'pivot':{'x':20,'y':30,'what':'wrist, % of the frame; rotate/translate the whole frame around this point'},
   'strikePoint':'the index fingertip (lowestPointPerFrame) is the point that touches the strings'},feather=(0.10,0.30))
