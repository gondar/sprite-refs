// node schedcheck.js : for all scenes check blink count in [2.6,8.4] and max idle gap in window
const {execSync}=require('child_process'),fs=require('fs');
for(const id of fs.readdirSync(__dirname+'/../../pub/i7/cut').filter(d=>/^[RSBC]\d$/.test(d))){
 const out=execSync(`node ${__dirname}/sched4.js ${id}`).toString().trim().split('\n');
 for(const l of out){const [fig,...rest]=l.trim().split(/\s+/);const ev=rest.map(e=>{const m=e.match(/(.+)@([\d.]+)-([\d.]+)/);return{n:m[1],a:+m[2],b:+m[3]}});
  const bl=ev.filter(e=>/blink$/.test(e.n)&&e.a>=2.6&&e.a<=8.4).length;
  let gap=0,last=2.6;for(const e of ev){if(e.b<2.6||e.a>8.4)continue;gap=Math.max(gap,e.a-last);last=Math.max(last,e.b)}gap=Math.max(gap,8.4-last);
  console.log(id,fig.padEnd(12),'blinks',bl,'maxgap',gap.toFixed(2),(gap>2.5?'GAP':''),(bl<2&&ev.some(e=>/blink$/.test(e.n))?'FEW':''))}}
