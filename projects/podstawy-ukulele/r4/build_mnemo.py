import json, os, sys, numpy as np
from PIL import Image
OUT='/home/user/MusicGames/ukulele-warmup/art/podstawy/'
FW,FH=int(sys.argv[1]),int(sys.argv[2]); Q=int(sys.argv[3])
from PIL import ImageFilter, ImageChops
def shadow(f, dx=None, dy=None):
    W,H=f.size; dx=dx if dx is not None else max(2,round(W*0.006)); dy=dy if dy is not None else max(3,round(W*0.009))
    al=f.getchannel('A'); sh=Image.new('L',f.size,0); sh.paste(al,(dx,dy)); sh=sh.filter(ImageFilter.GaussianBlur(W*0.008)).point(lambda v:int(v*0.30))
    base=Image.new('RGBA',f.size,(70,45,25,0)); base.putalpha(sh); base.alpha_composite(f); return base
boxes=json.load(open('boxes.json'))
meta={'pl':dict(down=[2,9,15,22,29,35,42,48],up=[6,12,19,26,31,38,44],
        who=['alpaca (left)','witch on the stump','alpaca (right)'],
        beats='0-2.4 s: the witch strums down-up and nods to the alpacas, smiling (Grube Czarownice Edukują); 2.4-4.3 s: both alpacas strum along and sing-smile with her (Alpaki); ends on the home frame'),
      'en':dict(down=[10,16,22,30,37],up=[8,14,19,25,34,41],
        who=['white cat with an apple (left)','cat on the stump with the ukulele','tabby cat with an apple (right)'],
        beats='0-2.2 s: the middle cat strums down-up and nods (Good Cats); 2.2-4.2 s: the two cats lift their apples and take a bite while it strums on (Eat Apples); ends on the home frame')}
for l in ['pl','en']:
    j=json.load(open(f'lock-{l}/atlas.json')); A=Image.open(f'lock-{l}/atlas.png'); cols=j['cols']; n=j['gestures'][0]['frames']-1  # last = home = frame 0
    C=10; R=(n+C-1)//C; S=Image.new('RGBA',(FW*C,FH*R),(0,0,0,0))
    for k in range(n):
        f=A.crop(((k%cols)*1024,(k//cols)*768,(k%cols+1)*1024,(k//cols+1)*768)).resize((FW,FH),Image.LANCZOS)
        f=shadow(f); a=np.array(f); a[...,:3][a[...,3]==0]=0; S.paste(Image.fromarray(a),((k%C)*FW,(k//C)*FH))
    S.save(OUT+f'mnemo-{l}.webp','WEBP',quality=Q,method=6,alpha_quality=60)
    m=meta[l]
    js={'image':f'mnemo-{l}.webp','frameWidth':FW,'frameHeight':FH,'frames':n,'cols':C,'rows':R,'fps':12,'loop':True,
        'layout':'grid, left to right then top to bottom; frame k at column k % cols, row floor(k / cols)',
        'canvas':'every frame is the whole 4:3 backdrop (mnemo-%s-bg.webp, same aspect): draw it over the backdrop at the same size, no offset'%l,
        'homeFrame':0,'downstrokeBottomFrame':m['down'][0],'strumBottomFrames':m['down'],'strumTopFrames':m['up'],
        'beats':m['beats'],
        'characters':[dict(who=w,box_pct=dict(x0=b['x0'],x1=b['x1'],y0=b['y0'],y1=b['y1'])) for w,b in zip(m['who'],boxes[l])],
        'source':'MiniMax-H3 first=last frame on #2F6BD8, cut with sprite-pipeline lock.py (--reach 90, --step 2), every other pixel is the home picture'}
    json.dump(js,open(OUT+f'mnemo-{l}.json','w'),indent=1,ensure_ascii=False)
    print(l,n,S.size,round(os.path.getsize(OUT+f'mnemo-{l}.webp')/1024),'KB')

for l in ['pl','en']:
    bg=Image.open(f'{l}-bg.png').convert('RGBA').resize((1024,768),Image.LANCZOS)
    home=shadow(Image.open(f'{l}-home-768c.png').convert('RGBA'))
    bg.alpha_composite(home); bg.convert('RGB').resize((800,600),Image.LANCZOS).save(OUT+f'mnemo-{l}-still.webp','WEBP',quality=82,method=6)
    Image.open(f'{l}-bg.png').convert('RGB').resize((800,600),Image.LANCZOS).save(OUT+f'mnemo-{l}-bg.webp','WEBP',quality=82,method=6)
