import sys,glob,os
from PIL import Image,ImageDraw
d,box,out,scale=sys.argv[1],tuple(map(int,sys.argv[2].split(','))),sys.argv[3],float(sys.argv[4]) if len(sys.argv)>4 else 1
ts=sys.argv[5].split(',') if len(sys.argv)>5 else None
fs=sorted(glob.glob(d+'/t_*.png'))
if ts: fs=[f for f in fs if os.path.basename(f)[2:-4] in ts]
w,h=int((box[2]-box[0])*scale),int((box[3]-box[1])*scale)
cols=min(4,len(fs));rows=(len(fs)+cols-1)//cols
S=Image.new('RGB',(cols*w,rows*h))
for k,f in enumerate(fs):
    im=Image.open(f).convert('RGB').crop(box).resize((w,h),Image.LANCZOS);ImageDraw.Draw(im).text((4,4),os.path.basename(f)[2:-4],fill=(255,255,0))
    S.paste(im,((k%cols)*w,(k//cols)*h))
S.save(out,quality=90)
