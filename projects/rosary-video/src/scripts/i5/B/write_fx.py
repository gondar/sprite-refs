import json
S='/tmp/claude-0/-home-user/7ead4a65-9a3f-5f74-8eac-6850f8d7f07d/scratchpad/'
base=json.load(open(S+'pub/i6/fx/B1.json'))
def route(start,land,f_start,f_jump,f_watch,notes):
    sx,sy=start; lx,ly=land
    return [
     dict(t=0.0,x=sx,y=sy,act='stop_sniff',facing=f_start,note=notes[0]),
     dict(t=1.6,x=sx,y=sy,act='idle_look',facing=f_watch,note=notes[1]),
     dict(t=3.5,x=sx,y=sy,act='jump',facing=f_jump,note=notes[2]),
     dict(t=5.0,x=lx,y=ly,act='groom_wonder',facing=f_watch,note=notes[3]),
     dict(t=6.1,x=lx,y=ly,act='idle_look',facing=f_watch,note='patrzy z otwartymi oczami'),
     dict(t=8.0,x=lx,y=ly,act='idle_look',facing='right',note='odwraca się za paciorkiem'),
     dict(t=8.6,x=lx,y=ly,act='idle_look',facing='right')]
def sway(ID,name,bb,pivot,amp,speed,note):
    return dict(name=name,file=f'i6/fx/{ID}_{name}.png',bbox=[float(v) for v in bb],pivot=pivot,amp=amp,speed=speed,motion="bend: horizontal shift grows with distance from pivot (top moves, pivot row fixed)",note=note)
FX={
'B2':dict(sway=[],
  flicker=[dict(x=0.212,y=0.405,r=0.02,color="#ffb347",speed=7.0,glow=0.07,note="torch flame; small warm pool only")],
  shimmer=[dict(y0=0.25,y1=0.38,x0=0.195,x1=0.23,amp=0.002,note="heat haze above the torch")],
  beam=[], disc=[dict(x=0.512,y=0.052,r=0.028,kind="moon",note="small moon above the wall; halo pulse only")],
  particles=[dict(type="sparks",region=[0.18,0.2,0.25,0.38],note="a few rising embers from the torch"),dict(type="dust",region=[0.3,0.45,0.5,0.9],note="faint motes in the torch pool around Jesus")],
  route=route((0.575,0.935),(0.68,0.80),'left','right','left',["na płytach dziedzińca, na prawo od płaszcza","zauważa Jezusa przy kolumnie","jeden skok na kamienny stopień","na stopniu, patrzy w lewo na kolumnę"]),
  watch=[0.68,0.80],caption=dict(pos="top-right",x=0.64,y=0.035,w=0.33,h=0.1)),
'B3':dict(sway=[],
  flicker=[dict(x=0.835,y=0.488,r=0.018,color="#ffb347",speed=6.0,glow=0.06,note="oil-lamp flame")],
  shimmer=[dict(y0=0.36,y1=0.47,x0=0.82,x1=0.85,amp=0.002,note="heat haze above the lamp")],
  beam=[], disc=[dict(x=0.822,y=0.075,r=0.022,kind="moon",note="crescent in the window; halo pulse only")],
  particles=[dict(type="dust",region=[0.7,0.3,0.95,0.7],note="motes in the lamp glow")],
  route=route((0.30,0.93),(0.36,0.655),'right','right','right',["na ubitej ziemi, przy słomie","zauważa Jezusa w koronie","jeden skok na lewy koniec ławy","na końcu ławy, patrzy w prawo na Jezusa"]),
  watch=[0.36,0.655],caption=dict(pos="top-left",x=0.03,y=0.03,w=0.3,h=0.1)),
'B4':dict(sway=[],flicker=[],shimmer=[],beam=[],
  disc=[dict(x=0.43,y=0.37,r=0.04,kind="glow",note="last dusk glow at the end of the street; slow pulse, keep dim")],
  particles=[dict(type="dust",region=[0.33,0.3,0.62,0.8],note="dust hanging in the street glow"),dict(type="dust",region=[0.05,0.4,0.3,0.7],note="dust near the left dust spiral")],
  route=route((0.70,0.96),(0.87,0.785),'left','right','left',["na bruku za Szymonem","zauważa Jezusa z krzyżem","jeden skok na kamienny blok","na bloku, patrzy w lewo na Jezusa, Szymona i Weronikę"]),
  watch=[0.87,0.785],caption=dict(pos="top-right",x=0.66,y=0.03,w=0.31,h=0.1)),
'B5':dict(flicker=[dict(x=0.62,y=0.09,r=0.004,color="#e8f0ff",speed=1.4,note="star"),dict(x=0.9,y=0.06,r=0.004,color="#e8f0ff",speed=1.9,note="star")],
  shimmer=[],beam=[],
  disc=[dict(x=0.40,y=0.385,r=0.035,kind="glow",note="crimson horizon behind the cross; very slow faint pulse")],
  particles=[dict(type="fireflies",region=[0.0,0.62,0.5,0.95],note="few, slow, in the dry grass")],
  route=route((0.53,0.93),(0.86,0.82),'right','right','left',["na kamienistej ziemi","zauważa krzyż i Maryję","jeden skok na płaską skałę","na skale, patrzy w lewo na Maryję i krzyż"]),
  watch=[0.86,0.82],caption=dict(pos="bottom-left",x=0.03,y=0.855,w=0.3,h=0.1)),
}
sw={'B3':('rag',[0.3,0.0],0.012,0.3,"red rag hanging off the bench; hem drifts in the draught"),'B5':('olive',[0.5,1.0],0.006,0.25,"olive crown in the night wind; bottom row fixed")}
for ID,d in FX.items():
    if ID in sw:
        n,pv,a,sp,no=sw[ID]; bb=json.load(open(S+f'scripts/i5/B/sway_{ID}.json'))[n]
        d['sway']=[sway(ID,n,bb,pv,a,sp,no)]
    out=dict(id=ID,units=base['units'],draw_order=base['draw_order'])
    for k in ['sway','flicker','shimmer','beam','disc','particles','route','watch','caption']: out[k]=d[k]
    out['dormouse']=dict(height=0.14,note=base['dormouse']['note'])
    out['plate_clean']=f'i6/fx/{ID}_plate_clean.jpg'
    json.dump(out,open(S+f'pub/i6/fx/{ID}.json','w'),indent=1,ensure_ascii=False)
    print(ID,'ok',len(out['sway']))
