// node tint.js n1,n2,... -> tintFor(n) per scene
const http=require('http'),fs=require('fs'),path=require('path');const {chromium}=require('playwright');
const ROOT=path.join(__dirname,'..','..','pub');const N=process.argv[2].split(',').map(Number);
const srv=http.createServer((q,r)=>{const f=path.join(ROOT,decodeURIComponent(q.url.split('?')[0]));fs.readFile(f,(e,d)=>{if(e){r.writeHead(404);r.end();return}r.writeHead(200);r.end(d)})});
srv.listen(0,async()=>{const b=await chromium.launch();const p=await b.newPage();await p.goto(`http://localhost:${srv.address().port}/index.html`);await p.waitForTimeout(7000);
console.log(JSON.stringify(await p.evaluate(N=>N.map(n=>[n,tintFor(n)]),N)));await b.close();srv.close()});
