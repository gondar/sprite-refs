// node sched3.js <id> : exact copy of index.html cutFrame schedule (round 3, guaranteed blinks), 0-10.2 s
const fs=require('fs'),S=__dirname+'/../..';const id=process.argv[2];
function rng(s){return()=>{s=(s*16807)%2147483647;return(s-1)/2147483646}}
const CJ=JSON.parse(fs.readFileSync(id==='R1'?`${S}/pub/i7/cut/cut.json`:`${S}/pub/i7/cut/${id}/cut.json`));
for(const [fig,c] of Object.entries(CJ)){const C={gs:c.gestures};
 let hs=7;for(const ch of id+":"+fig)hs=(hs*31+ch.charCodeAt(0))%2147483647;const r=rng(hs||1);const S=[];let tt=.3+r()*.8,prev=-1;
  const wsum=C.gs.reduce((a,q)=>a+(q.weight||1),0),pick=()=>{let u=r()*wsum;for(let k=0;k<C.gs.length;k++){u-=C.gs[k].weight||1;if(u<=0)return k}return C.gs.length-1};
  while(tt<400){let k;let tries=0;do{k=pick()}while(C.gs.length>1&&k===prev&&++tries<10);const G=C.gs[k],d=G.frames/G.fps;S.push([tt,k,d]);prev=k;tt+=d+.4+r()*1.8}
  const BK=C.gs.map((q,k)=>/blink$/.test(q.name)?k:-1).filter(k=>k>=0);if(BK.length){const m=BK.length*2,sw=5.8/m;for(let j=0;j<m;j++){const bk=BK[j%BK.length],d=C.gs[bk].frames/C.gs[bk].fps;let b0=2.6+j*sw+r()*Math.max(.05,sw-d-.2);const cov=S.find(s=>!s[3]&&s[0]<b0+d+.15&&s[0]+s[2]>b0-.15);if(cov){const a=cov[0]+cov[2]+.15,b=cov[0]-d-.15;b0=(a+d<=2.6+(j+1)*sw||b<2.6)?a:b}S.push([b0,bk,d,1]);S.sort((a,c)=>a[0]-c[0])}
   /* gesty przesuwamy za mrugnięcie zamiast je kasować; gdy przed mrugnięciem nie ma miejsca, ten gest idzie za mrugnięcie */
   for(let i=1;i<S.length;i++){const e=S[i-1][0]+S[i-1][2]+.15;if(S[i][0]<e){if(S[i][3]){if(S[i-1][3])S[i][0]=e+1;else{S[i-1][0]=S[i][0]+S[i][2]+.15;S.sort((a,c)=>a[0]-c[0]);i=0}}else S[i][0]=e}}
   /* losowe mrugnięcia bliżej niż 1.6 s od gwarantowanego wypadają (żeby nie było tiku) */
   for(let i=S.length-1;i>=0;i--){if(!S[i][3]&&/blink/.test(C.gs[S[i][1]].name)&&S.some(g=>g[3]&&Math.abs(g[0]-S[i][0])<1.6))S.splice(i,1)}
   /* dziury >2.2 s w oknie tajemnicy zapełnia krótki gest, który się mieści */
   for(let i=0;i<S.length-1;i++){const e=S[i][0]+S[i][2],g=S[i+1][0]-e;if(e>8.4)break;if(e+g<2.6||g<=2.2)continue;const fit=C.gs.map((q,k)=>[k,q.frames/q.fps]).filter(([k,d])=>!/blink/.test(C.gs[k].name)&&d<=g-.3);if(fit.length){const [k,d]=fit[Math.floor(r()*fit.length)];S.splice(i+1,0,[e+.15+r()*Math.max(0,g-d-.3),k,d])}}}
 console.log(fig.padEnd(6), S.filter(s=>s[0]<10.2).map(s=>`${C.gs[s[1]].name}@${s[0].toFixed(2)}-${(s[0]+s[2]).toFixed(2)}`).join('  '))}
