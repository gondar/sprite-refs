import json
c=json.load(open('cfg_C2.json'))
c['ovs']['blink']['boxes']['kneel']=[1082,436,1126,464]
c['ovs']['smile']['boxes']={'young':[896,354,922,372],'old':[999,341,1018,365]}
c['figs']['kneel']['gestures']=["blink","blink2","breath","look_up","nod"]
c['figs']['waver']['gestures']=["blink","breath","tilt","sway","nod"]
json.dump(c,open('cfg_C2.json','w'),indent=1)
