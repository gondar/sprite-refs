import json,numpy as np
from PIL import Image, ImageDraw
S='/tmp/claude-0/-home-user/7ead4a65-9a3f-5f74-8eac-6850f8d7f07d/scratchpad/'
c=json.load(open(S+'pub/i7/cut/C5/cut.json'))['mary']; w,h=c['w'],c['h']
plate=Image.open(S+'pub/i5/C5_plate.jpg').convert('RGBA').crop((765,282,1065,692))
def fr(name,k):
    g=[g for g in c['gestures'] if g['name']==name][0]; sh=Image.open(S+'pub/'+g['file']).convert('RGBA')
    f=sh.crop(((k%g['cols'])*w,(k//g['cols'])*h,(k%g['cols']+1)*w,(k//g['cols']+1)*h)); b=plate.copy(); b.alpha_composite(f); return b.convert('RGB')
home=plate.copy(); home.alpha_composite(Image.open(S+'pub/i7/cut/C5/mary_home.png')); home=home.convert('RGB')
def lab(im,t):
    d=ImageDraw.Draw(im); d.rectangle([0,0,8*len(t)+8,16],fill=(0,0,0)); d.text((4,2),t,fill=(255,255,0)); return im
face=(180,40,280,120)   # local coords
tiles=[('home',home),('blink f4',fr('blink',4)),('blink f0',fr('blink',0)),('blink2 f9',fr('blink2',9)),('smile f13',fr('smile',13)),('look_up f14',fr('look_up',14)),('tilt_r f13',fr('tilt_r',13)),('breath f15',fr('breath',15))]
row=[lab(t.crop(face).resize((400,320),Image.LANCZOS),n) for n,t in tiles]
W=Image.new('RGB',(400*4+12,320*2+4),(255,255,255))
for i,r in enumerate(row): W.paste(r,((i%4)*403,(i//4)*324))
W.save(S+'review/C5/zoom_spirit_face.jpg',quality=90)
g1=home.crop((20,90,300,410)).resize((1120,1280),Image.LANCZOS); g2=fr('breath',15).crop((20,90,300,410)).resize((1120,1280),Image.LANCZOS)
G=Image.new('RGB',(2244,1280),(255,255,255)); G.paste(lab(g1,'home x4'),(0,0)); G.paste(lab(g2,'breath peak x4 (glow pulse)'),(1124,0)); G.save(S+'review/C5/zoom_spirit_garment.jpg',quality=88)
# blink ring check x4 tight
e=(200,58,252,80); B=[lab(t.crop(e).resize((208,88),Image.NEAREST),n) for n,t in tiles[:4]]
E=Image.new('RGB',(212*4,88),(255,255,255))
for i,b in enumerate(B): E.paste(b,(i*212,0))
E=E.resize((E.width*2,E.height*2),Image.NEAREST); E.save(S+'review/C5/zoom_spirit_eyes_x8.jpg',quality=92)
