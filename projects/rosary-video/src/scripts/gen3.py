import os, sys, json, base64, urllib.request, io
from PIL import Image
model, ar, out, promptfile = sys.argv[1:5]
refs = sys.argv[5:]
prompt = open(promptfile).read()
parts=[]
for ref in refs:
    mt = "image/jpeg" if ref.lower().endswith((".jpg",".jpeg")) else "image/png"
    parts.append({"inlineData":{"mimeType":mt,"data":base64.b64encode(open(ref,"rb").read()).decode()}})
parts.append({"text":prompt})
body = {"contents":[{"parts":parts}],
        "generationConfig":{"responseModalities":["IMAGE"],"imageConfig":dict({"aspectRatio":ar}, **({"imageSize":os.environ["IMGSIZE"]} if os.environ.get("IMGSIZE") else {}))}}
req = urllib.request.Request(f"https://api.apiyi.com/v1beta/models/{model}:generateContent",
    data=json.dumps(body).encode(), headers={"Content-Type":"application/json"})
r = json.load(urllib.request.urlopen(req, timeout=300))
for p in r["candidates"][0]["content"]["parts"]:
    if "inlineData" in p:
        raw = base64.b64decode(p["inlineData"]["data"])
        open(out.replace(".jpg","_raw.png"),"wb").write(raw)
        im = Image.open(io.BytesIO(raw)).convert("RGB")
        MW=int(os.environ.get("MAXW","1600"))
        if im.width > MW:
            im = im.resize((MW, round(im.height*MW/im.width)), Image.LANCZOS)
        im.save(out, "JPEG", quality=82, optimize=True, progressive=True)
        print(out, im.size, r.get("usageMetadata"))
        break
else:
    print(json.dumps(r)[:1500])
