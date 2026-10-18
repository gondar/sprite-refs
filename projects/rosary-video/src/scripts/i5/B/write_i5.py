import json
S='/tmp/claude-0/-home-user/7ead4a65-9a3f-5f74-8eac-6850f8d7f07d/scratchpad/'
spec={
 'B2':dict(land=[0.68,0.80],light=[0.212,0.405],fx={"foliage":None,"water":None,"glow":[0.212,0.405,0.06]},
   figs={'jesus':dict(pivot=[0.55,0.98],head=[0.62,0.1],motion="patient stillness: very slow breath scaleY 1->1.008 (5 s) from the feet, tiny head bow ~1 deg around the neck; wrists stay on the rope (keep tiny)")}),
 'B3':dict(land=[0.36,0.655],light=[0.835,0.49],fx={"foliage":None,"water":None,"glow":[0.835,0.49,0.05]},
   figs={'jesus':dict(pivot=[0.5,0.97],head=[0.45,0.17],motion="quiet dignity: slow seated breath scaleY 1->1.008 from the bench line (5 s), tiny head bow ~1 deg; no sway")}),
 'B4':dict(land=[0.87,0.79],light=[0.43,0.35],fx={"foliage":None,"water":None,"glow":[0.43,0.36,0.05]},
   figs={'jesus_simon':dict(pivot=[0.5,0.99],head=[0.36,0.24],motion="ONE layer (Jesus, cross, Simon joined by the cross): only breath scaleY 1->1.006 from the feet, 4.5 s; no rotation (the cross locks them)"),
         'veronica':dict(pivot=[0.5,0.97],head=[0.45,0.12],motion="kneeling offer: slow breath scaleY 1->1.01 from the knees, tiny lean toward Jesus (rotate <=0.8 deg) 5 s")}),
 'B5':dict(land=[0.86,0.82],light=[0.40,0.38],fx={"foliage":None,"water":None,"glow":[0.40,0.385,0.05]},
   figs={'mary':dict(pivot=[0.5,0.98],head=[0.4,0.12],motion="standing grief: slow breath scaleY 1->1.008 from the feet (5 s); figures touch (John's hand on her shoulder): tiny rotation only <=0.5 deg"),
         'john':dict(pivot=[0.5,0.98],head=[0.45,0.1],motion="breath scaleY 1->1.008 from the feet (5.5 s, out of phase with Mary); his hand rests on Mary: no rotation >0.5 deg")}),
}
for i,sp in spec.items():
    fj=json.load(open(S+f'scripts/i5/work/{i}_figs.json'))
    figs=[]
    for f in fj['figs']:
        d=sp['figs'][f['name']]
        figs.append(dict(name=f['name'],file=f['file'],bbox=f['bbox'],pivot=d['pivot'],head=d['head'],motion=d['motion']))
    out=dict(id=i,full=f'i5/{i}_full.jpg',plate=f'i5/{i}_plate.jpg',figs=figs,land=sp['land'],light=sp['light'],fx=sp['fx'])
    json.dump(out,open(S+f'pub/i5/{i}.json','w'),indent=1)
    print(i,[ (f['name'],f['bbox']) for f in figs])
