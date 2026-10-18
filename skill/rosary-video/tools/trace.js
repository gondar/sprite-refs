const http=require('http'),fs=require('fs'),path=require('path');const {chromium}=require('playwright');
const ROOT='/tmp/claude-0/-home-user/7ead4a65-9a3f-5f74-8eac-6850f8d7f07d/scratchpad/pub';
const srv=http.createServer((q,r)=>{const f=path.join(ROOT,decodeURIComponent(q.url.split('?')[0]));fs.readFile(f,(e,d)=>{if(e){r.writeHead(404);r.end();return}r.writeHead(200,f.endsWith('.html')?{'Content-Type':'text/html; charset=utf-8'}:{});r.end(d)})}).listen(0,async()=>{
 const b=await chromium.launch();const p=await b.newPage({viewport:{width:1300,height:900}});await p.goto(`http://localhost:${srv.address().port}/index.html`,{waitUntil:'domcontentloaded',timeout:60000});await p.waitForTimeout(15000);
 const out=await p.evaluate(()=>{const c=document.createElement('canvas');c.width=1280;c.height=720;const x=c.getContext('2d');
  const _dd=drawDormouse;drawDormouse=function(cc,n,l,st,h,orbP){window.__st={act:st.act,ta:st.ta,flip:st.flip,X:st.X,Y:st.Y,jp:st.jump?st.jump.p:null,jA:st.jump?st.jump.A:null,jB:st.jump?st.jump.B:null,play:st.play?st.play.act:null};return _dd.apply(this,arguments)};
  const res={};for(let n=0;n<20;n++){window.__trace=[];const rows=[];for(let i=0;i<=Math.round(M*30);i++){const l=Math.min(i/30,M-1e-4);window.__st=null;const k=window.__trace.length;renderTo(x,INTRO+n*M+l);const tr=window.__trace[k];rows.push({l,tr:tr||null,st:window.__st})}
   res[n]={rows,route:FXL[Math.floor(n/5)+"_"+n%5]&&FXL[Math.floor(n/5)+"_"+n%5].route,xd:exitDirOf(n),tr:trFor(n),plays:(FXL[Math.floor(n/5)+"_"+n%5]||{}).__plays}}
  window.__trace=null;return {res,M,TIN,JOUT,INTRO,intro:SEQ.intro&&{seedLast:SEQ.intro.seedLast,frames:SEQ.intro.frames,fps:SEQ.intro.fps},outro:SEQ.outro&&{frames:SEQ.outro.frames,fps:SEQ.outro.fps,keys:Object.keys(SEQ.outro)}}});
 fs.writeFileSync(process.argv[2],JSON.stringify(out));await b.close();srv.close()});
