# fx + route for C2..C5, reusing work/cut.py and run()/check() from work/build.py
import sys,re,numpy as np,cv2,json
sys.path.insert(0,'/tmp/claude-0/-home-user/7ead4a65-9a3f-5f74-8eac-6850f8d7f07d/scratchpad/work')
import os; os.chdir('/tmp/claude-0/-home-user/7ead4a65-9a3f-5f74-8eac-6850f8d7f07d/scratchpad/work')
src=open('build.py').read()
head=src[:src.index('S={}')]; body=src[src.index('def glints'):src.index('for sid in (sys.argv')]
exec(head); exec(body)
S={}
def R(rect): x0,y0,x1,y1=rect; return [[x0,y0],[x1,y0],[x1,y1],[x0,y1]]
def route(start,watch,f0,fw,t_jump=3.5,first='stop_sniff',look_t=1.6,extra=None,fn=None):
    r=[(0.0,start[0],start[1],first,f0,'starts in the scene'),
       (look_t,start[0],start[1],'idle_look',fn or fw,'notices the mystery'),
       (t_jump,start[0],start[1],'jump',('right' if watch[0]>start[0] else 'left'),'one jump to the watching spot'),
       (t_jump+1.5,watch[0],watch[1],'idle_look',fw,'watches the mystery, eyes open'),
       (8.0,watch[0],watch[1],'idle_look','right','turns to the leaving bead'),
       (8.6,watch[0],watch[1],'idle_look','right')]
    return rt(r)
S['C2']=dict(
 sway=[dict(name='bush',poly=[[0.54,0.56],[0.6,0.545],[0.645,0.58],[0.645,0.705],[0.54,0.705]],pivot=(0.59,0.70),amp=0.012,speed=0.3,note='spiral bush on the hilltop')],
 flicker=[dict(x=x,y=y,r=0.008,color='#fffbe8',speed=sp,note='sparkle on a cloud spiral') for x,y,sp in [(0.31,0.32,1.5),(0.55,0.10,1.8),(0.47,0.37,1.3)]],
 shimmer=[dict(y0=0.64,y1=0.75,x0=0.0,x1=0.32,amp=0.0015,note='valley mist drift')],
 beam=[],disc=[],
 particles=[dict(type='gold motes',region=[0.2,0.3,0.6,0.62],note='slow, few, under the cloud'),dict(type='petals',region=[0.0,0.62,0.58,0.95],note='rare tiny white flower petals in the breeze, kept away from the apostles faces')],
 route=route((0.26,0.885),(0.50,0.80),'right','left',fn='right'),
 watch=[0.50,0.80],caption=dict(pos='top-right',x=0.70,y=0.04,w=0.27,h=0.12))
S['C3']=dict(
 sway=[dict(name='cloth',poly=[[0.735,0.14],[0.94,0.135],[0.94,0.30],[0.85,0.44],[0.73,0.45]],pivot=(0.93,0.15),amp=0.02,speed=0.55,note='linen cloth on a nail blown by the wind'),
       dict(name='paper1',poly=R([0.445,0.43,0.515,0.545]),pivot=(0.48,0.43),amp=0.02,speed=0.5,note='flying sheet: flutter'),
       dict(name='paper2',poly=R([0.53,0.57,0.63,0.645]),pivot=(0.58,0.57),amp=0.02,speed=0.45,note='flying sheet: flutter')],
 flicker=[dict(x=x,y=y,r=0.018,color='#ffcf70',speed=sp,glow=0.03,note='tongue of flame over a head (painted; flicker only, glow radius small)') for x,y,sp in [(0.178,0.234,6.0),(0.351,0.378,6.6),(0.658,0.289,7.1),(0.80,0.469,6.3)]],
 shimmer=[dict(y0=0.24,y1=0.56,x0=0.43,x1=0.86,amp=0.002,note='the white spiral wind ribbon ripples')],
 beam=[],disc=[],
 particles=[dict(type='dust',region=[0.55,0.25,0.95,0.62],note='dust whirling in the window light, follows the wind to the left')],
 route=route((0.62,0.93),(0.47,0.705),'left','left'),
 watch=[0.47,0.705],caption=dict(pos='bottom-left',x=0.02,y=0.86,w=0.36,h=0.11))
S['C4']=dict(
 sway=[dict(name='bush_mid',poly=[[0.515,0.55],[0.58,0.53],[0.64,0.57],[0.64,0.73],[0.515,0.73]],pivot=(0.575,0.73),amp=0.012,speed=0.3),
       dict(name='bush_left',poly=[[0.0,0.76],[0.12,0.76],[0.22,0.82],[0.24,1.0],[0.0,1.0]],pivot=(0.1,1.0),amp=0.012,speed=0.35),
       dict(name='tree_right',poly=[[0.77,0.0],[1.0,0.0],[1.0,0.42],[0.77,0.42]],pivot=(0.91,0.42),amp=0.006,speed=0.25,note='olive canopy only, trunk stays in plate')],
 flicker=[],
 shimmer=[dict(y0=0.40,y1=0.50,x0=0.58,x1=0.76,amp=0.0015,note='warm haze above the rising sun')],
 beam=[],
 disc=[dict(x=0.665,y=0.47,r=0.045,kind='sun',note='painted sun: pulse +-3% only, no added brightness')],
 particles=[dict(type='petals',region=[0.18,0.5,0.55,0.95],note='a few rose petals drifting from the tomb'),dict(type='gold motes',region=[0.42,0.05,0.62,0.6],note='few, slow, rising around Mary')],
 route=route((0.42,0.905),(0.63,0.885),'left','left',fn='right'),
 watch=[0.63,0.885],caption=dict(pos='top-right',x=0.59,y=0.03,w=0.25,h=0.12))
S['C5']=dict(
 sway=[],
 flicker=[],
 shimmer=[dict(y0=0.78,y1=0.86,x0=0.6,x1=1.0,amp=0.0015,note='haze over the dawn horizon'),dict(y0=0.08,y1=0.45,x0=0.0,x1=0.45,amp=0.0015,note='slow cloud breath'),dict(y0=0.58,y1=0.82,x0=0.0,x1=0.85,amp=0.0012,note='slow cloud breath on the cloud bank')],
 beam=[],
 disc=[dict(x=0.9,y=0.81,r=0.05,kind='glow',note='painted dawn glow at the horizon: pulse +-3% only')],
 particles=[dict(type='twinkle stars',region=[0.5,0.0,1.0,0.25],note='a few tiny faint stars fading as dawn comes'),dict(type='gold motes',region=[0.6,0.3,0.85,0.75],note='few, slow, around Mary')],
 route=route((0.27,0.62),(0.47,0.625),'right','right'),
 watch=[0.47,0.625],caption=dict(pos='top-right',x=0.69,y=0.04,w=0.28,h=0.12))
for sid in (sys.argv[1:] or S):
    run(sid)
    o=json.load(open(P+'i6/fx/%s.json'%sid))
    EXTRA={'C2':{'grade':{'mul':'#c9c2b8','alpha':0.35,'top':0.25}},
           'C4':{'dormouse':{'height':0.14,'tint':{'col':'#8a8670','a':0.18}}},
           'C5':{'dormouse':{'height':0.14,'tint':{'col':'#3c4658','a':0.32}}}}
    for k,v in EXTRA.get(sid,{}).items():
        if k=='dormouse': o['dormouse'].update(v)
        else: o[k]=v
    if sid=='C5' and not o.get('plate_clean'):
        import shutil; shutil.copy(P+'i5/C5_plate.jpg',P+'i6/fx/C5_plate_clean.jpg'); o['plate_clean']='i6/fx/C5_plate_clean.jpg'
    json.dump(o,open(P+'i6/fx/%s.json'%sid,'w'),indent=1)
    if sid=='C5':
        o=json.load(open(P+'i6/fx/C5.json'))
        o['crown']=dict(x=0.716,y=0.355,r=0.062,stars=12,note='engine draws a ring of exactly 12 small white light-stars above Mary\'s head, slightly tilted (ellipse ry~0.35*r), gentle twinkle, follows Mary\'s bob; r = ring radius as fraction of frame height')
        json.dump(o,open(P+'i6/fx/C5.json','w'),indent=1)
    print('done',sid)
