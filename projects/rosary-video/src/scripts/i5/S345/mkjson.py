import json
B='/tmp/claude-0/-home-user/7ead4a65-9a3f-5f74-8eac-6850f8d7f07d/scratchpad/'
BRE='slow breath scaleY 1->1.006 from the pivot; keep tiny'
D={
'S3':dict(land=[0.52,0.948],light=[0.39,0.05],fx={"foliage":None,"water":[0.3,0.48],"glow":None},figs={
  'jesus':((470,450),'seated on the boat rim, talking: '+BRE+'; tiny forward lean 0.4deg toward the listeners'),
  'boy':((880,440),'standing in the water with a rope: '+BRE+' from the feet; tiny sway 0.3deg'),
  'child':((805,612),'sitting hugging her knees: '+BRE+' from the seat; tiny rock 0.4deg toward Jesus'),
  'fisherman':((1050,560),'seated mending the net: '+BRE+' from the seat; no rotation (net on the ground is part of the layer)')}),
'S4':dict(land=[0.709,0.872],light=[0.64,0.24],fx={"foliage":[0.86,0.76],"water":None,"glow":[0.64,0.3,0.06]},figs={
  'jesus':((880,430),'standing in the light: '+BRE+' from the feet; no sway (stillness)'),
  'peter':((270,615),'kneeling, shielding his eyes: '+BRE+' from the knees; tiny lean back 0.4deg'),
  'john':((530,495),'sitting back on the rocks: '+BRE+' from the seat; NO rotation (James overlaps him)'),
  'james':((460,690),'kneeling, face in his arms: '+BRE+' from the knees; NO rotation (overlaps John)')}),
'S5':dict(land=[0.167,0.898],light=[0.2,0.23],fx={"foliage":None,"water":None,"glow":None},figs={
  'john':((380,590),'kneeling at the table: '+BRE+' from the knees; tiny lean 0.4deg toward Jesus'),
  'jesus':((860,520),'seated, breaking the bread: '+BRE+' from the seat; no rotation (table in front)'),
  'peter':((1150,560),'seated with the cup: '+BRE+' from the seat; tiny lean 0.3deg')})}
for i,d in D.items():
    fj=json.load(open(B+'scripts/i5/S345/work/%s_figs.json'%i))['figs']
    figs=[]
    for f in fj:
        (px,py),mot=d['figs'][f['name']]; x,y,w,h=f['px']
        figs.append(dict(name=f['name'],file=f['file'],bbox=[float(v) for v in f['bbox']],pivot=[round((px-x)/w,3),round((py-y)/h,3)],motion=mot))
    json.dump(dict(id=i,full='i5/%s_full.jpg'%i,plate='i5/%s_plate.jpg'%i,figs=figs,land=d['land'],light=d['light'],fx=d['fx']),open(B+'pub/i5/%s.json'%i,'w'),indent=1)
    print(i,[(f['name'],f['pivot']) for f in figs])
