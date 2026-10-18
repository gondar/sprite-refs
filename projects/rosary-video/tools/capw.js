const http=require('http'),fs=require('fs'),path=require('path');const {chromium}=require('playwright');
const S=path.join(__dirname,'..','..');const ROOT=path.join(S,'pub');
const MIME={'.html':'text/html; charset=utf-8','.js':'text/javascript','.json':'application/json','.jpg':'image/jpeg','.png':'image/png','.webp':'image/webp'};
const srv=http.createServer((q,r)=>{const f=path.join(ROOT,decodeURIComponent(q.url.split('?')[0]));fs.readFile(f,(e,d)=>{if(e){r.writeHead(404);r.end();return}r.writeHead(200,{'Content-Type':MIME[path.extname(f)]||'application/octet-stream'});r.end(d)})});
srv.listen(0,async()=>{const port=srv.address().port;const b=await chromium.launch();const p=await b.newPage({viewport:{width:1300,height:900}});
 await p.goto(`http://localhost:${port}/index.html`);
 for(const wait of [0,3000,7000]){await p.waitForTimeout(wait);
 const r=await p.evaluate(()=>{const c=document.createElement('canvas');c.width=1280;c.height=720;const x=c.getContext('2d');const out={};
  for(const n of [16,17,18,19]){const rec=[];const orig=x.fillText.bind(x);x.fillText=(s,a,bb)=>{rec.push([s,a,x.font,Math.round(x.measureText(s).width)]);return orig(s,a,bb)};renderTo(x,INTRO+n*M+6);x.fillText=orig;out[n]=rec.filter(q=>q[2].includes('Uncial'))}
  return {fonts:[...document.fonts].filter(f=>f.family.includes('Uncial')).map(f=>f.status),out}});
 console.log(wait,JSON.stringify(r))}
 await b.close();srv.close()});
