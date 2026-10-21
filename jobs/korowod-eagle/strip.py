import sys
from PIL import Image
d=sys.argv[1]; idx=[int(x) for x in sys.argv[2].split(',')]; out=sys.argv[3]; tw=320
s=Image.new('RGB',(tw*min(6,len(idx)),tw*((len(idx)+5)//6)),(150,185,225))
for j,i in enumerate(idx):
    im=Image.open(f'{d}/k_{i:03d}.png').crop((150,150,900,900)).resize((tw,tw))
    bg=Image.new('RGBA',(tw,tw),(150,185,225,255)); bg.alpha_composite(im); s.paste(bg.convert('RGB'),((j%6)*tw,(j//6)*tw))
s.save(out)
