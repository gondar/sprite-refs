// node sched.js <id> : reproduce engine gesture schedule (index.html cutFrame) for 0-10.2 s
const fs=require('fs'),S=__dirname+'/../..';const id=process.argv[2];
function rng(s){return()=>{s=(s*16807)%2147483647;return(s-1)/2147483646}}
const C=JSON.parse(fs.readFileSync(`${S}/pub/i7/cut/${id}/cut.json`));
for(const [fig,c] of Object.entries(C)){const gs=c.gestures.map(g=>({...g,fps:g.fps||12}));
 let hs=7;for(const ch of id+":"+fig)hs=(hs*31+ch.charCodeAt(0))%2147483647;const r=rng(hs||1);const Sx=[];let tt=.3+r()*.8,prev=-1;
 const wsum=gs.reduce((a,q)=>a+(q.weight||1),0),pick=()=>{let u=r()*wsum;for(let k=0;k<gs.length;k++){u-=gs[k].weight||1;if(u<=0)return k}return gs.length-1};
 while(tt<400){let k;let tries=0;do{k=pick()}while(gs.length>1&&k===prev&&++tries<10);const G=gs[k],d=G.frames/G.fps;Sx.push([tt,k,d]);prev=k;tt+=d+.4+r()*1.8}
 /* mirrors index.html cutFrame (~l.752): every gesture whose name ENDS in "blink" (blink, jblink; not blink2) plays twice in 2.6-8.4 s,
    slots of 5.8/(2*nBlink) s taken in turn, each pushed in at a random offset inside its slot, overlapping gestures removed */
 const BK=gs.map((q,k)=>/blink$/.test(q.name)?k:-1).filter(k=>k>=0);
 if(BK.length){const m=BK.length*2,sw=5.8/m;for(let j=0;j<m;j++){const bk=BK[j%BK.length],d=gs[bk].frames/gs[bk].fps,b0=2.6+j*sw+r()*Math.max(.05,sw-d-.2);
   for(let i=Sx.length-1;i>=0;i--){if(Sx[i][0]<b0+d+.3&&Sx[i][0]+Sx[i][2]>b0-.3)Sx.splice(i,1)}Sx.push([b0,bk,d])}Sx.sort((a,c)=>a[0]-c[0])}
 console.log(fig, Sx.filter(s=>s[0]<10.2).map(s=>`${gs[s[1]].name}@${s[0].toFixed(2)}-${(s[0]+s[2]).toFixed(2)}`).join('  '))}
