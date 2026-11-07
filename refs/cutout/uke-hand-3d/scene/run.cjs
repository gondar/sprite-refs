// node run.cjs script.js outdir : loads scene.html, runs script.js in the page (async fn body; may call save(name, mode)), writes PNGs + out.json
const {chromium}=require('/opt/node22/lib/node_modules/playwright'); const fs=require('fs');
(async()=>{const [script,out]=process.argv.slice(2); fs.mkdirSync(out,{recursive:true});
const b=await chromium.launch({args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist']});
const p=await b.newPage(); p.on('console',m=>console.log('C:',m.text())); p.on('pageerror',e=>console.log('E',e));
if(process.env.STATES) await p.addInitScript(`window.STATES=${require('fs').readFileSync(process.env.STATES,'utf8')}`);
if(process.env.OPT) await p.addInitScript(`window.OPT=${process.env.OPT}`);
await p.goto('http://127.0.0.1:8765/h3d/scene.html'); await p.waitForFunction('window.ready'); await p.evaluate('window.ready');
const res=await p.evaluate(`(async()=>{const shots={}; const save=(n,m)=>{shots[n]=renderMode(m)}; const dsave=(n,...a)=>{shots[n]=renderDebug(...a)}; const R=await (async()=>{${fs.readFileSync(script,'utf8')}})(); return {shots,R};})()`);
for(const n in res.shots) fs.writeFileSync(out+'/'+n+'.png',Buffer.from(res.shots[n].split(',')[1],'base64'));
fs.writeFileSync(out+'/out.json',JSON.stringify(res.R,null,1)); await b.close();})();
