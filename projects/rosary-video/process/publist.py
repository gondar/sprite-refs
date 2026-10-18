# Lista plików strony do publikacji (tylko te, do których odwołują się dane sceny)
import json,glob,os,sys
os.chdir(os.path.join(os.path.dirname(__file__),'..','pub'))
fs=set(['index.html','i4/dm_run.png','i4/dm_leap.png','i4/dm_land.png','i4/dm_sit.png','utwor.mp3','i6/dm/dm.json','i7/jump/jump.json','i7/cut/cut.json'])
fs|=set(glob.glob('i6/dm/*.webp'))|set(glob.glob('i7/jump/j*.png'))
for p in glob.glob('i5/*.json'):
  j=json.load(open(p));fs|={p,j['plate']}|{f['file'] for f in j['figs']}
for p in glob.glob('i6/fx/*.json'):
  j=json.load(open(p));fs.add(p);fs|={s['file'] for s in j.get('sway',[])}
  c=p.replace('.json','_plate_clean.jpg')
  if os.path.exists(c):fs.add(c)
for p in glob.glob('i7/cut/cut.json')+glob.glob('i7/cut/*/cut.json'):
  j=json.load(open(p));fs.add(p)
  for k,v in j.items():
    fs|={g['file'] for g in v['gestures']}
fs={f for f in fs if f and os.path.exists(f)}
tot=sum(os.path.getsize(f) for f in fs)
print(json.dumps(sorted(fs)),file=open('../publist.json','w'));print(len(fs),'files',round(tot/1e6,1),'MB',file=sys.stderr)
