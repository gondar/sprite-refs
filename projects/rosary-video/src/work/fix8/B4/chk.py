from PIL import Image
S='/tmp/claude-0/-home-user/7ead4a65-9a3f-5f74-8eac-6850f8d7f07d/scratchpad/'
fu=Image.open(S+'pub/i5/B4_full.jpg').convert('RGB');pc=Image.open(S+'pub/i6/fx/B4_plate_clean.jpg').convert('RGB')
for nm,b,o in [('L',(120,310,530,490),(128,318)),('R',(960,90,1260,265),(975,95))]:
    L=Image.open(S+'pub/i6/fx/B4_dust%s.png'%nm); a=L.split()[3]
    w,h=b[2]-b[0],b[3]-b[1]
    O=Image.new('RGB',(w,h*3));O.paste(fu.crop(b),(0,0));O.paste(pc.crop(b),(0,h))
    sh=pc.copy(); sh.paste(L,(o[0]+6,o[1]),L)   # layer displaced 6 px (worse than max sway) to look for ghosts
    O.paste(sh.crop(b),(0,2*h))
    O.resize((w*2,h*6),Image.LANCZOS).save(S+'work/fix8/B4/chk_%s.jpg'%nm)
