// node sched3.js <id> : exact copy of index.html cutFrame schedule (round 3, guaranteed blinks), 0-10.2 s
const fs=require('fs'),S=__dirname+'/../..';const id=process.argv[2];
function rng(s){return()=>{s=(s*16807)%2147483647;return(s-1)/2147483646}}
const CJ=JSON.parse(fs.readFileSync(`${S}/pub/i7/cut/${id}/cut.json`));
for(const [fig,c] of Object.entries(CJ)){const C={gs:c.gestures};
 let hs=7;for(const ch of id+":"+fig)hs=(hs*31+ch.charCodeAt(0))%2147483647;const r=rng(hs||1);const S=[];let tt=.3+r()*.8,prev=-1;
  const wsum=C.gs.reduce((a,q)=>a+(q.weight||1),0),pick=()=>{let u=r()*wsum;for(let k=0;k<C.gs.length;k++){u-=C.gs[k].weight||1;if(u<=0)return k}return C.gs.length-1};
  while(tt<400){let k;let tries=0;do{k=pick()}while(C.gs.length>1&&k===prev&&++tries<10);const G=C.gs[k],d=G.frames/G.fps;S.push([tt,k,d]);prev=k;tt+=d+.4+r()*1.8}
  const BK=C.gs.map((q,k)=>/blink$/.test(q.name)?k:-1).filter(k=>k>=0);if(BK.length){const m=BK.length*2,sw=5.8/m;for(let j=0;j<m;j++){const bk=BK[j%BK.length],d=C.gs[bk].frames/C.gs[bk].fps,b0=2.6+j*sw+r()*Math.max(.05,sw-d-.2);for(let i=S.length-1;i>=0;i--){if(S[i][0]<b0+d+.3&&S[i][0]+S[i][2]>b0-.3)S.splice(i,1)}S.push([b0,bk,d])}S.sort((a,c)=>a[0]-c[0])}
 console.log(fig.padEnd(6), S.filter(s=>s[0]<10.2).map(s=>`${C.gs[s[1]].name}@${s[0].toFixed(2)}-${(s[0]+s[2]).toFixed(2)}`).join('  '))}
