// Renderuje jedną tajemnicę do przeglądu: node process/render_scene.js <n> <id>   (z katalogu scratchpad, NODE_PATH=$(npm root -g))
const http=require('http'),fs=require('fs'),path=require('path');
const { chromium }=require('playwright');
const ROOT=path.join(__dirname,'..','pub'),n=+process.argv[2],id=process.argv[3];
const OUT=path.join(__dirname,'..','review',id);fs.mkdirSync(OUT,{recursive:true});
const MIME={'.html':'text/html; charset=utf-8','.js':'text/javascript','.json':'application/json','.jpg':'image/jpeg','.png':'image/png','.webp':'image/webp','.mp3':'audio/mpeg'};
const srv=http.createServer((q,r)=>{const f=path.join(ROOT,decodeURIComponent(q.url.split('?')[0]));fs.readFile(f,(e,d)=>{if(e){r.writeHead(404);r.end();return}r.writeHead(200,{'Content-Type':MIME[path.extname(f)]||'application/octet-stream'});r.end(d)})});
srv.listen(0,async()=>{
 const port=srv.address().port;const b=await chromium.launch();const p=await b.newPage({viewport:{width:1300,height:900}});
 const errs=[];p.on('pageerror',e=>errs.push(String(e.stack||e)));
 await p.goto(`http://localhost:${port}/index.html`);await p.waitForTimeout(7000);
 const T=[0.4,1.2,2.0,2.6,3.4,4.2,5.0,6.0,7.0,8.0,9.0,9.9];
 const res=await p.evaluate(({n,T})=>{
  const c=document.createElement('canvas');c.width=1280;c.height=720;const x=c.getContext('2d');
  const sheet=document.createElement('canvas');sheet.width=4*640;sheet.height=3*360;const sx=sheet.getContext('2d');
  T.forEach((t,k)=>{renderTo(x,INTRO+n*M+t);sx.drawImage(c,(k%4)*640,Math.floor(k/4)*360,640,360);sx.fillStyle='rgba(0,0,0,.6)';sx.fillRect((k%4)*640,Math.floor(k/4)*360,90,30);sx.fillStyle='#fff';sx.font='20px sans-serif';sx.fillText(t.toFixed(1)+'s',(k%4)*640+8,Math.floor(k/4)*360+22)});
  const lay=document.createElement('canvas');lay.width=3*640;lay.height=2*360;const lx=lay.getContext('2d');
  ['plate','figs','debug'].forEach((m,k)=>{x.clearRect(0,0,1280,720);scene(x,n,5,m);lx.drawImage(c,k*640,0,640,360)});
  // dwa zbliżenia: twarze postaci (środek górnej części bboxów)
  const s=scnOf(n);x.clearRect(0,0,1280,720);renderTo(x,INTRO+n*M+6);
  (s&&s.figs?s.figs.slice(0,3):[]).forEach((g,k)=>{const bb=g.bbox;lx.drawImage(c,bb[0]*1280,bb[1]*720,bb[2]*1280,Math.min(bb[3],.35)*720,k*640,360,640,360)});
  // ruch postaci: średnia zmiana pikseli w bboxie między chwilami
  const mot={};if(s&&s.figs){const ts=[2.5,3.5,4.5,5.5,6.5,7.5];const shots=ts.map(t=>{x.clearRect(0,0,1280,720);scene(x,n,t,'figs');return x.getImageData(0,0,1280,720).data});
   s.figs.forEach(g=>{const bb=g.bbox,x0=Math.floor(bb[0]*1280),y0=Math.floor(bb[1]*720),w=Math.floor(bb[2]*1280),h=Math.floor(bb[3]*720);const out=[];
    for(let k=1;k<shots.length;k++){let d=0,N=0;for(let yy=y0;yy<y0+h;yy+=3)for(let xx=x0;xx<x0+w;xx+=3){const i=(yy*1280+xx)*4;d+=Math.abs(shots[k][i]-shots[k-1][i])+Math.abs(shots[k][i+1]-shots[k-1][i+1]);N++}out.push(+(d/N).toFixed(2))}
    mot[g.name]=out})}
  return {sheet:sheet.toDataURL('image/jpeg',.82),lay:lay.toDataURL('image/jpeg',.82),mot,cut:Object.keys(CUT||{}),jump:Object.keys(JUMP.poses||{}),fx:!!FXL[Math.floor(n/5)+'_'+n%5]};
 },{n,T});
 fs.writeFileSync(path.join(OUT,'frames.jpg'),Buffer.from(res.sheet.split(',')[1],'base64'));
 fs.writeFileSync(path.join(OUT,'layers.jpg'),Buffer.from(res.lay.split(',')[1],'base64'));
 fs.writeFileSync(path.join(OUT,'motion.json'),JSON.stringify({figureMotionPerSecond:res.mot,cutoutLoaded:res.cut,jumpPoses:res.jump,fxLoaded:res.fx,pageErrors:errs},null,1));
 console.log(JSON.stringify({out:OUT,errors:errs,cut:res.cut,jump:res.jump,fx:res.fx}));
 await b.close();srv.close();
});
