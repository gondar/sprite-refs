// node snap.js <n> <id> t1,t2,...  -> review/<id>/snap/t_<t>.png (1280x720) + dm.json
const http=require('http'),fs=require('fs'),path=require('path');const {chromium}=require('playwright');
const S=path.join(__dirname,'..','..');const ROOT=path.join(S,'pub');const n=+process.argv[2],id=process.argv[3],T=process.argv[4].split(',').map(Number),mode=process.argv[5]||'';
const OUT=path.join(S,'review',id,'snap'+(mode?'_'+mode:''));fs.mkdirSync(OUT,{recursive:true});
const MIME={'.html':'text/html; charset=utf-8','.js':'text/javascript','.json':'application/json','.jpg':'image/jpeg','.png':'image/png','.webp':'image/webp','.mp3':'audio/mpeg'};
const srv=http.createServer((q,r)=>{const f=path.join(ROOT,decodeURIComponent(q.url.split('?')[0]));fs.readFile(f,(e,d)=>{if(e){r.writeHead(404);r.end();return}r.writeHead(200,{'Content-Type':MIME[path.extname(f)]||'application/octet-stream'});r.end(d)})});
srv.listen(0,async()=>{const port=srv.address().port;const b=await chromium.launch();const p=await b.newPage({viewport:{width:1300,height:900}});
 await p.goto(`http://localhost:${port}/index.html`,{waitUntil:'domcontentloaded',timeout:60000});await p.waitForTimeout(7000);
 const res=await p.evaluate(({n,T,mode})=>{const c=document.createElement('canvas');c.width=1280;c.height=720;const x=c.getContext('2d');const out=[];
  const F=FXL[Math.floor(n/5)+'_'+n%5];
  for(const t of T){x.clearRect(0,0,1280,720);if(mode&&mode!=='stab_all')scene(x,n,t,mode);else renderTo(x,INTRO+n*M+t);
   let st=null;try{st=dmState(n,t,F,{ox:0,oy:0,w:W,h:H},H*.14)}catch(e){st=String(e)}
   out.push({t,url:c.toDataURL("image/png"),st:JSON.stringify(st),b:JSON.stringify(x.__b||null)})}
  return {out,W,H,TIN,M,JOUT}},{n,T,mode});
 const meta=[];for(const o of res.out){fs.writeFileSync(path.join(OUT,'t_'+o.t.toFixed(2)+'.png'),Buffer.from(o.url.split(',')[1],'base64'));meta.push({t:o.t,st:JSON.parse(o.st),b:JSON.parse(o.b)})}
 fs.writeFileSync(path.join(OUT,'dm.json'),JSON.stringify({W:res.W,H:res.H,TIN:res.TIN,M:res.M,JOUT:res.JOUT,meta},null,0));console.log('ok',OUT,res.TIN,res.M);await b.close();srv.close()});
