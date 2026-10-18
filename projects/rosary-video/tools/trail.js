// node trail.js <n> <out.jpg> : ślad paciorka (żółty) i głowy orzesznicy (biały) w tajemnicy n, na tle klatek t=1.5,5,8.4
const http=require('http'),fs=require('fs'),path=require('path');const {chromium}=require('playwright');
const ROOT=path.join(__dirname,'..','..','pub');const n=+process.argv[2],out=process.argv[3];
const srv=http.createServer((q,r)=>{const f=path.join(ROOT,decodeURIComponent(q.url.split('?')[0]));fs.readFile(f,(e,d)=>{if(e){r.writeHead(404);r.end();return}r.writeHead(200,f.endsWith('.html')?{'Content-Type':'text/html; charset=utf-8'}:{});r.end(d)})}).listen(0,async()=>{
 const b=await chromium.launch();const p=await b.newPage({viewport:{width:1300,height:900}});await p.goto(`http://localhost:${srv.address().port}/index.html`,{waitUntil:'domcontentloaded',timeout:60000});await p.waitForTimeout(9000);
 const url=await p.evaluate(n=>{const c=document.createElement('canvas');c.width=1280;c.height=720;const x=c.getContext('2d');
  const sh=document.createElement('canvas');sh.width=1280*2;sh.height=720*2;const s=sh.getContext('2d');
  const T=[[0.6,0],[2.6,1],[5.4,2],[8.9,3]];window.__trace=[];for(let t=0;t<M;t+=1/30)renderTo(x,INTRO+n*M+t);const tr=window.__trace;window.__trace=null;
  T.forEach(([t,k])=>{renderTo(x,INTRO+n*M+t);const ox=(k%2)*1280,oy=Math.floor(k/2)*720;s.drawImage(c,ox,oy);
   s.lineWidth=2;for(const [col,i0] of [["rgba(255,215,60,.95)",1],["rgba(255,255,255,.8)",3]]){s.strokeStyle=col;s.beginPath();tr.forEach((r,j)=>{const X=ox+r[i0],Y=oy+r[i0+1];j?s.lineTo(X,Y):s.moveTo(X,Y)});s.stroke()}
   tr.forEach(r=>{if(Math.abs(r[0]-t)<1/60){s.fillStyle='#f00';s.beginPath();s.arc(ox+r[1],oy+r[2],7,0,7);s.fill()}if(Math.abs((r[0]*2)%1)<1/30){s.fillStyle='#ff0';s.font='14px sans-serif';s.fillText(r[0].toFixed(1),ox+r[1]+6,oy+r[2]-6)}});
   s.fillStyle='rgba(0,0,0,.6)';s.fillRect(ox,oy,120,34);s.fillStyle='#fff';s.font='22px sans-serif';s.fillText('t='+t,ox+8,oy+25)});
  return sh.toDataURL('image/jpeg',.8)},n);
 fs.writeFileSync(out,Buffer.from(url.split(',')[1],'base64'));await b.close();srv.close()});
