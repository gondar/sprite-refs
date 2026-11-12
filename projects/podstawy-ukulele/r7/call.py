import json, sys, time, uuid, base64, urllib.request, os
sys.path.insert(0,'/home/user/MusicGames/.claude/skills/sprite-pipeline/scripts')
import gen_image as g
fields={"model":"gpt-image-2","prompt":open(sys.argv[1]).read(),"size":"1536x1024","quality":"medium","n":"1","stream":"true","partial_images":"1"}
data,h=g.multipart(fields,[("image","r7/base.png"),("mask","r7/mask.png")])
rec={"job_id":time.strftime('%Y%m%d-%H%M%S')+'-mask',"tag":"fret-flat-mask","model":"gpt-image-2","state":"submitting"}
g.log(rec); t=time.time()
try:
  res=g.sse(g.HOST+"/v1/images/edits",data,h,timeout=300)
except Exception as e:
  body=getattr(e,'read',lambda:b'')()[:400]; g.log({**rec,"state":"error","err":str(e),"body":body.decode('utf8','replace')}); print("ERR",e,body); sys.exit(1)
u=res.get("usage",{}); ti=u.get("input_tokens",0); to=u.get("output_tokens",0)
cost=ti*5e-6+to*30e-6+100*30e-6
open(sys.argv[2],"wb").write(base64.b64decode(res["data"][0]["b64_json"]))
g.log({**rec,"state":"ok","s":round(time.time()-t,1),"usage":u,"cost_usd":round(cost,4)}); print("ok",round(cost,4),u)
