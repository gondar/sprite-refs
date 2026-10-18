import sys; from PIL import Image
ims=[Image.open(p).convert("RGBA") for p in sys.argv[2:]]
H=max(i.height for i in ims); W=sum(i.width for i in ims)+20*len(ims)
bg=Image.new("RGBA",(W,H),(255,255,255,255))
for y in range(0,H,16):
    for x in range(0,W,16):
        if (x//16+y//16)%2: bg.paste((200,200,200,255),(x,y,x+16,y+16))
x=0
for i in ims: bg.alpha_composite(i,(x,0)); x+=i.width+20
bg.convert("RGB").save(sys.argv[1])
