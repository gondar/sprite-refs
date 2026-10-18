import sys, json, base64, urllib.request, io
from PIL import Image
model, ar, out, promptfile = sys.argv[1:5]
ref = sys.argv[5] if len(sys.argv)>5 else None
prompt = open(promptfile).read()
parts=[]
if ref: parts.append({"inlineData":{"mimeType":"image/png","data":base64.b64encode(open(ref,"rb").read()).decode()}})
parts.append({"text":prompt})
body = {"contents":[{"parts":parts}],
        "generationConfig":{"responseModalities":["IMAGE"],"imageConfig":{"aspectRatio":ar}}}
req = urllib.request.Request(f"https://api.apiyi.com/v1beta/models/{model}:generateContent",
    data=json.dumps(body).encode(), headers={"Content-Type":"application/json"})
r = json.load(urllib.request.urlopen(req, timeout=300))
for p in r["candidates"][0]["content"]["parts"]:
    if "inlineData" in p:
        raw = base64.b64decode(p["inlineData"]["data"])
        open(out.replace(".jpg","_raw.png"),"wb").write(raw)
        im = Image.open(io.BytesIO(raw)).convert("RGB")
        if im.width > 1280:
            im = im.resize((1280, round(im.height*1280/im.width)), Image.LANCZOS)
        im.save(out, "JPEG", quality=82, optimize=True, progressive=True)
        print(out, im.size, r.get("usageMetadata"))
        break
else:
    print(json.dumps(r)[:1500])
