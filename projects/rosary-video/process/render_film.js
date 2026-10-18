// Renderuje cały film klatka po klatce do MP4: node process/render_film.js <out.mp4> [fps=30] [t0=0] [t1=DUR] [crf=18]
// (z katalogu scratchpad, NODE_PATH=$(npm root -g)). Czas jest deterministyczny: renderTo(ctx, t) z index.html.
const http=require('http'),fs=require('fs'),path=require('path'),{spawn}=require('child_process');
const {chromium}=require('playwright');
const ROOT=path.join(__dirname,'..','pub');
const out=process.argv[2]||'film.mp4',FPS=+(process.argv[3]||30),T0=+(process.argv[4]||0),T1a=process.argv[5],CRF=process.argv[6]||'18';
const MIME={'.html':'text/html; charset=utf-8','.js':'text/javascript','.json':'application/json','.jpg':'image/jpeg','.png':'image/png','.webp':'image/webp','.mp3':'audio/mpeg'};
const srv=http.createServer((q,r)=>{const f=path.join(ROOT,decodeURIComponent(q.url.split('?')[0]));fs.readFile(f,(e,d)=>{if(e){r.writeHead(404);r.end();return}r.writeHead(200,{'Content-Type':MIME[path.extname(f)]||'application/octet-stream'});r.end(d)})});
const TS=Date.now();srv.listen(0,async()=>{
 const port=srv.address().port;const b=await chromium.launch();const p=await b.newPage({viewport:{width:1300,height:900}});
 const errs=[];p.on('pageerror',e=>errs.push(String(e.stack||e)));p.on('console',m=>{if(m.text().startsWith('tm'))process.stderr.write(m.text()+'\n')});
 await p.goto(`http://localhost:${port}/index.html`);
 // czekamy, aż wszystkie obrazy się wczytają (sceny, cutout, fx, orzesznica)
 await p.waitForTimeout(6000);
 await p.evaluate(async()=>{const c=document.createElement('canvas');c.width=1280;c.height=720;const x=c.getContext('2d');
  for(let k=0;k<22;k++){renderTo(x,k<21?INTRO+(k-1)*M+5:OUTRO+2)}window.__fc=c;window.__fx=x});
 await p.waitForFunction(()=>[...performance.getEntriesByType('resource')].length>0&&document.readyState==='complete');
 await p.waitForTimeout(8000);
 const DUR=await p.evaluate(()=>DUR);const T1=T1a?+T1a:DUR;const N=Math.round((T1-T0)*FPS);
 const ff=spawn('ffmpeg',['-y','-loglevel','error','-f','image2pipe','-framerate',String(FPS),'-c:v','mjpeg','-i','-',
  '-ss',String(T0),'-i',path.join(ROOT,'utwor.mp3'),'-map','0:v','-map','1:a','-c:v','libx264','-preset','slow','-crf',CRF,'-tune','animation','-pix_fmt','yuv420p',
  '-c:a','aac','-b:a','160k','-shortest','-movflags','+faststart',out],{stdio:['pipe','inherit','inherit']});
 const B=24;const t0=Date.now();process.stderr.write('start '+((Date.now()-TS)/1000)+'\n');
 for(let k=0;k<N;k+=B){
  const frames=await p.evaluate(async({k,B,N,T0,FPS})=>{const x=window.__fx,c=window.__fc,res=[];
   for(let j=k;j<Math.min(N,k+B);j++){renderTo(x,T0+j/FPS);const bl=await new Promise(r=>c.toBlob(r,'image/jpeg',.95));
    const u=new Uint8Array(await bl.arrayBuffer());let s='';for(let i=0;i<u.length;i+=0x8000)s+=String.fromCharCode.apply(null,u.subarray(i,i+0x8000));res.push(btoa(s))}
   return res},{k,B,N,T0,FPS});
  for(const f of frames){if(!ff.stdin.write(Buffer.from(f,'base64')))await new Promise(r=>ff.stdin.once('drain',r))}
  if(process.env.DBG||(k/B)%25===0)process.stderr.write(`\r${k}/${N} ${((Date.now()-t0)/1000).toFixed(0)}s   `+(process.env.DBG?'\n':''));
 }
 ff.stdin.end();await new Promise(r=>ff.on('close',r));
 console.log(JSON.stringify({out,frames:N,sec:(Date.now()-t0)/1000,errors:errs}));
 await b.close();srv.close();
});
