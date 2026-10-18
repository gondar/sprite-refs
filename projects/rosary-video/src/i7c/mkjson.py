import json
B='/tmp/claude-0/-home-user/7ead4a65-9a3f-5f74-8eac-6850f8d7f07d/scratchpad/'
W,H=1376,768
BRE='slow breath scaleY 1->1.006 from the feet pivot; keep tiny'
D={
'C2':dict(land=[0.26,0.885],light=[0.39,0.2],fx={"foliage":[0.59,0.65],"water":None,"glow":None},figs={
  'young':((910,598),'shading his eyes: '+BRE+'; slow lean back ~0.6deg as he looks up'),
  'old':((1015,598),'old man with staff: '+BRE+'; tiny head-and-body sway 0.5deg; staff hand stays'),
  'kneel':((1110,632),'kneeling: '+BRE+' from the knees; tiny forward rock 0.5deg'),
  'waver':((1225,622),'waving goodbye: '+BRE+'; gentle sway 0.6deg')}),
'C3':dict(land=[0.80,0.95],light=[0.48,0.33],fx={"foliage":None,"water":None,"glow":None},figs={
  'old':((230,700),'astonished, arms half open: '+BRE+'; tiny lean back 0.5deg (flame above his head moves with him)'),
  'mary':((510,560),'seated, hands open: '+BRE+' from the seat; tiny lean 0.4deg toward the flame'),
  'young':((910,630),'laughing in the wind: small laugh bounce translateY 0..-2px at ~2 Hz in bursts; '+BRE),
  'kneel':((1090,690),'kneeling on the mat: '+BRE+' from the knees; tiny upward lift 0.4deg')}),
'C4':dict(land=[0.42,0.905],light=[0.52,0.2],fx={"foliage":[0.57,0.62],"water":None,"glow":None},figs={
  'mary':((680,430),'rising: very slow hover translateY 0..-3px (6 s ease) and breath; keep it tiny because her soft glow is part of the layer; NO extra glow'),
  'old':((1045,665),'stopped in amazement, hands raised: '+BRE+'; tiny lean back 0.5deg'),
  'young':((1220,700),'kneeling with a rose: '+BRE+' from the knees; tiny forward rock 0.4deg')}),
'C5':dict(land=[0.30,0.60],light=[0.716,0.355],fx={"foliage":None,"water":None,"glow":None},figs={
  'mary':((962,532),'seated on the cloud: '+BRE+' from the seat; very slow cloud bob translateY 0..2px (7 s); the crown of 12 stars is drawn by the engine (see i6/fx/C5.json crown) and must follow this bob')})}
for i,d in D.items():
    fj=json.load(open(B+'scripts/i5/work/%s_figs.json'%i))['figs']
    figs=[]
    for f in fj:
        (px,py),mot=d['figs'][f['name']]; x,y,w,h=f['px']
        figs.append(dict(name=f['name'],file=f['file'],bbox=f['bbox'],pivot=[round((px-x)/w,3),round((py-y)/h,3)],motion=mot))
    json.dump(dict(id=i,full='i5/%s_full.jpg'%i,plate='i5/%s_plate.jpg'%i,figs=figs,land=d['land'],light=d['light'],fx=d['fx']),open(B+'pub/i5/%s.json'%i,'w'),indent=1)
    print(i,[(f['name'],f['pivot']) for f in figs])
