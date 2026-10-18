import json,numpy as np
from PIL import Image
P='../pub/'
def flat(f): a=f[...,3:]/255.; return f[...,:3]*a+128*(1-a)
for i in ['C2','C3','C4','C5']:
    cut=json.load(open(P+'i7/cut/%s/cut.json'%i))
    for fg,c in cut.items():
        home=np.asarray(Image.open(P+c['home'])).astype(float); W,H=c['w'],c['h']; hf=flat(home)
        for G in c['gestures']:
            if not G['name'].startswith('blink'): continue
            sh=np.asarray(Image.open(P+G['file'])).astype(float)
            frs=[flat(sh[(k//G['cols'])*H:(k//G['cols']+1)*H,(k%G['cols'])*W:(k%G['cols']+1)*W]) for k in range(G['frames'])]
            pk=frs[4]; reg=(np.abs(pk-hf).max(2)>40)&(home[...,3]>250)
            st=[]
            for f in frs:
                dh=np.abs(f-hf)[reg].mean(); dp=np.abs(f-pk)[reg].mean()
                st.append('O' if dh<6 else ('C' if dp<6 else '[X%.0f/%.0f]'%(dh,dp)))
            e0=np.abs(frs[0]-hf)[home[...,3]>250].mean(); e1=np.abs(frs[-1]-hf)[home[...,3]>250].mean()
            print(i,fg,G['name'],''.join(st),'ends mean',round(e0,2),round(e1,2),'eye px',int(reg.sum()))
