# python3 choreo/metric.py trace.json : skoki paciorka (zmiana prędkości > 25 px/klatkę) poza wejściem, plus odwrócenia sprite'a
import json,math,sys
D=json.load(open(sys.argv[1]));TIN=D['TIN'];M=D['M'];tE=M-1.55;tot=0;flips=0
for n in range(20):
  rows=D['res'][str(n)]['rows'];bad=[]
  P=[(r['l'],r['tr'][1],r['tr'][2]) if r['tr'] else None for r in rows]
  for k in range(2,len(P)):
    a,b,c=P[k-2],P[k-1],P[k]
    if not(a and b and c) or c[0]<TIN+.25: continue
    dv=math.hypot((c[1]-b[1])-(b[1]-a[1]),(c[2]-b[2])-(b[2]-a[2]))
    if dv>25: bad.append((round(c[0],2),round(dv)))
  fl=[round(rows[k]['l'],2) for k in range(1,len(rows)) if rows[k]['st'] and rows[k-1]['st'] and rows[k]['st']['flip']!=rows[k-1]['st']['flip'] and rows[k]['l']>TIN]
  tot+=len(bad);flips+=len(fl)
  print(n,'jumps',bad[:6],'flips',fl)
print('TOTAL jumps',tot,'flips',flips)
