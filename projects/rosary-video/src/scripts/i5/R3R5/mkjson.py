import json,sys
B='/tmp/claude-0/-home-user/7ead4a65-9a3f-5f74-8eac-6850f8d7f07d/scratchpad/'
META={
'R3':dict(land=[0.29,0.93],light=[0.375,0.775],fx={"foliage":None,"water":None,"glow":[0.375,0.775,0.05]},figs={
  'joseph':([0.6,0.96],"kneeling, blowing on the fire: slow breath scaleY 1->1.008 from the knees, tiny lean toward the fire (rotate <=0.6deg)"),
  'mary':([0.75,0.95],"reclining, exhausted and tender: very slow breath scaleY 1->1.006, keep rotation <=0.3deg (she lies on the straw)")}),
'R4':dict(land=[0.30,0.94],light=[0.40,0.42],fx={"foliage":None,"water":None,"glow":None},figs={
  'simeon':([0.5,0.97],"tender rocking of the child: rotate +-0.5deg around the feet, slow breath scaleY 1->1.006"),
  'mary':([0.5,0.98],"a little worried, hands raised: slow breath scaleY 1->1.006, tiny lean toward simeon (rotate <=0.5deg)"),
  'joseph':([0.5,0.98],"standing with the basket: slow breath scaleY 1->1.005, rotate <=0.4deg")}),
'R5':dict(land=[0.40,0.885],light=[0.42,0.32],fx={"foliage":[0.12,0.15],"water":None,"glow":None},figs={
  'joseph':([0.5,0.98],"relieved, hand on Mary's shoulder: slow breath scaleY 1->1.006; keep rotation <=0.3deg (overlaps mary)"),
  'mary':([0.5,0.98],"relieved, hands on her chest: slow breath scaleY 1->1.008, rotate <=0.4deg"),
  'jesus':([0.4,0.95],"eager, leaning to the scroll: slow breath scaleY 1->1.006, tiny lean (rotate <=0.5deg); finger stays on the scroll"),
  'teacher1':([0.5,0.95],"surprised listener: slow breath scaleY 1->1.005, rotate <=0.4deg"),
  'teacher2':([0.4,0.95],"thoughtful, hand at beard: slow breath scaleY 1->1.005, rotate <=0.3deg; long scroll near the bottom stays still")})}
for i in sys.argv[1:]:
    m=META[i]; F=json.load(open(B+f'scripts/i5/work/{i}_figs.json'))['figs']
    figs=[dict(name=f['name'],file=f['file'],bbox=f['bbox'],pivot=m['figs'][f['name']][0],motion=m['figs'][f['name']][1]) for f in F]
    out=dict(id=i,full=f'i5/{i}_full.jpg',plate=f'i5/{i}_plate.jpg',figs=figs,land=m['land'],light=m['light'],fx=m['fx'])
    json.dump(out,open(B+f'pub/i5/{i}.json','w'),indent=1); print(i,[f['name'] for f in figs])
