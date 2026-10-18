// node strip.js <absTime0> <absTime1> <step> <out.jpg> [cols=6] : miniatury filmu w czasie bezwzględnym
const http=require('http'),fs=require('fs'),path=require('path');const {chromium}=require('playwright');
const ROOT=path.join(__dirname,'..','..','pub');const [t0,t1,st]=process.argv.slice(2,5).map(Number),out=process.argv[5],C=+(process.argv[6]||6),CR=(process.argv[7]||'0,0,1,1').split(',').map(Number);
const srv=http.createServer((q,r)=>{const f=path.join(ROOT,decodeURIComponent(q.url.split('?')[0]));fs.readFile(f,(e,d)=>{if(e){r.writeHead(404);r.end();return}r.writeHead(200,f.endsWith('.html')?{'Content-Type':'text/html; charset=utf-8'}:{});r.end(d)})}).listen(0,async()=>{
 const b=await chromium.launch();const p=await b.newPage({viewport:{width:1300,height:900}});await p.goto(`http://localhost:${srv.address().port}/index.html`,{waitUntil:'domcontentloaded',timeout:60000});await p.waitForTimeout(14000);
 const url=await p.evaluate(({t0,t1,st,C,CR})=>{const c=document.createElement('canvas');c.width=1280;c.height=720;const x=c.getContext('2d');const T=[];for(let t=t0;t<=t1+1e-6;t+=st)T.push(t);
  const w=420,h=236,R=Math.ceil(T.length/C);const sh=document.createElement('canvas');sh.width=C*w;sh.height=R*h;const s=sh.getContext('2d');
  T.forEach((t,k)=>{renderTo(x,t);s.drawImage(c,CR[0]*1280,CR[1]*720,(CR[2]-CR[0])*1280,(CR[3]-CR[1])*720,(k%C)*w,Math.floor(k/C)*h,w,h);s.fillStyle='rgba(0,0,0,.6)';s.fillRect((k%C)*w,Math.floor(k/C)*h,70,20);s.fillStyle='#fff';s.font='14px sans-serif';s.fillText(t.toFixed(2),(k%C)*w+4,Math.floor(k/C)*h+15)});
  return sh.toDataURL('image/jpeg',.82)},{t0,t1,st,C,CR});
 fs.writeFileSync(out,Buffer.from(url.split(',')[1],'base64'));await b.close();srv.close()});
