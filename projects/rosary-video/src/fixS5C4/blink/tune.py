import json,sys,subprocess
j=sys.argv[1]; specs=json.loads(sys.argv[2])
J=json.load(open('jobs.json'))
for k,v in specs.items():
    if k=='lws': J[j]['lws']=v
    elif k=='lids': J[j]['lids']=v
    else:
        i,key=k.split('.'); J[j]['eyes'][int(i)][key]=v
json.dump(J,open('jobs.json','w'))
subprocess.run(['python3','lid.py',j],capture_output=True); print(subprocess.run(['python3','lshift.py',j],capture_output=True,text=True).stdout.strip())
