// Renderuje klatki filmu do JPG: node process/render_frames.js <dir> <fps> <frameStart> <frameEnd>
// (z katalogu scratchpad, NODE_PATH=$(npm root -g)). Czas deterministyczny: renderTo(ctx, i/fps). Potem ffmpeg skleja (process/make_film.sh).
const http=require('http'),fs=require('fs'),path=require('path');const {chromium}=require('playwright');
const ROOT=path.join(__dirname,'..','pub');const [dir,fpsA,f0A,f1A]=process.argv.slice(2);const FPS=+fpsA,F0=+f0A,F1=+f1A;fs.mkdirSync(dir,{recursive:true});
const MIME={'.html':'text/html; charset=utf-8','.js':'text/javascript','.json':'application/json','.jpg':'image/jpeg','.png':'image/png','.webp':'image/webp','.mp3':'audio/mpeg'};
const srv=http.createServer((q,r)=>{const f=path.join(ROOT,decodeURIComponent(q.url.split('?')[0]));fs.readFile(f,(e,d)=>{if(e){r.writeHead(404);r.end();return}r.writeHead(200,{'Content-Type':MIME[path.extname(f)]||'application/octet-stream'});r.end(d)})});
srv.listen(0,async()=>{
 const b=await chromium.launch();const p=await b.newPage({viewport:{width:1300,height:900}});const errs=[];p.on('pageerror',e=>errs.push(String(e.stack||e)));
 await p.goto(`http://localhost:${srv.address().port}/index.html`,{waitUntil:'domcontentloaded',timeout:60000});await p.waitForTimeout(15000);
 await p.evaluate(()=>{const c=document.createElement('canvas');c.width=1280;c.height=720;window.__fc=c;window.__fx=c.getContext('2d');for(let k=0;k<22;k++)renderTo(window.__fx,k<21?INTRO+(k-1)*M+5:OUTRO+2)});
 await p.waitForTimeout(8000);const t0=Date.now();
 for(let k=F0;k<F1;k+=12){
  const fr=await p.evaluate(({k,F1,FPS})=>{const x=window.__fx,c=window.__fc,o=[];for(let j=k;j<Math.min(F1,k+12);j++){renderTo(x,j/FPS);o.push(c.toDataURL('image/jpeg',.94).slice(23))}return o},{k,F1,FPS});
  fr.forEach((s,i)=>fs.writeFileSync(path.join(dir,`f${String(k+i).padStart(5,'0')}.jpg`),Buffer.from(s,'base64')));
  if((k-F0)%600===0)process.stderr.write(`[${F0}] ${k-F0}/${F1-F0} ${((Date.now()-t0)/1000)|0}s\n`);
 }
 console.log(JSON.stringify({F0,F1,sec:(Date.now()-t0)/1000,errors:errs}));await b.close();srv.close();
});
