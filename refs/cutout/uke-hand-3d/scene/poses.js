window.OPT=Object.assign({down:150},window.OPT||{});
eval(await (await fetch('/h3d/ik.js')).text());
const G=geo, hw=G.halfW, O=window.OPT||{};
const cross=(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];
function palm(F, MCP){ let best=null; const AC=[1,0,0];
  for (const sg of [1,-1]) { const D=cross(F,AC).map(v=>v*sg); setPose({wrist:{p:[0,0,0],F,D,r:[0,0,0]}}); const J=joints(); if (J.index[1][0] < J.pinky[1][0]) best={D,J}; }
  const w0=best.J.wrist, m0=best.J.middle[1];
  return {p:[MCP[0]-(m0[0]-w0[0]), MCP[1]-(m0[1]-w0[1]), MCP[2]-(m0[2]-w0[2])], F, D:best.D, r:[0,0,0]}; }
const hov=(f,s,fr,l,dy)=>{const t=IK.tipTarget(f,s,fr,l); t[1]+=dy; return t;};
const C=O.curl||{index:[.45,0,1.25,.6], middle:[.5,0,1.35,.7], ring:[.5,0,1.35,.75], pinky:[.35,0,1.25,.65]};
const HY=O.hy ?? 0, HL=O.hl ?? 0;
const HF=O.hyf||[0,0,0,0];
const tips={ index:{p:hov(1,'A',.7,.008+HL,HY+HF[0]),w:1,xw:.3}, middle:{p:hov(2,'A',.6,.009+HL,HY+HF[1]),w:1,xw:.3},
  ring:{p:hov(3,'A',.5,.009+HL,HY+HF[2]),w:1,xw:.3}, pinky:{p:hov(4,'A',.35,.012+HL,.003+HY+HF[3]),w:.6,xw:.2} };
const F=O.F||[0.12,-.5,1], M=O.M||[G.X(600),hw+.015,.02];
let p=Object.assign({wrist:palm(F,M), thumb:[-.27,.86,1.4,1.84], _freeWrist:true, _noThumb:true, _free:[]}, JSON.parse(JSON.stringify(C)));
const T={tips, wristReg:.05};
let r=IK.minimize(p,T,600,.08); r=IK.minimize(r.pose,T,400,.03);
p=r.pose;
const rt=IK.minimize(Object.assign({},p,{_free:['thumb'],_freeWrist:false}),{thumb:[G.X(430),.003,-(G.boardT+G.neckD)-.008],thumbLim:true},300,.08); p.thumb=rt.pose.thumb;
const out={rest:p, states:{}};
const ST={e1:['index',1,'E',.72], c1:['index',1,'C',.72], e2:['middle',2,'E',.62], c2:['middle',2,'C',.62], e3:['ring',3,'E',.55], c3:['ring',3,'C',.55]};
const want=(O.only||Object.keys(ST));
for (const k of want) { const [f,fret,s,fr]=ST[k];
  const tp=IK.tipTarget(fret,s,fr,O.tipZ ?? .0015); tp[1]+=(O.pdy ?? 0); const t={p:tp, xw:.5, press:true, down:O.down ?? 30};
  const others=['index','middle','ring','pinky'].filter(g=>g!==f);
  const r=IK.solveFinger(p,f,t,{nat:2, mcp0:p[f][0], pip0:O.pip0 ?? p[f][2], avoid:[], abdMax:.12, dipMax:1.0});
  setPose(r.pose); const J=joints()[f];
  out.states[k]={a:r.a, c:r.c, tip:J[4], tipPx:proj({x:J[4][0],y:G.yS[s],z:G.strZ}), dip:J[3]};
  for (const m of (O.modes||['shaded'])) save(k+'-'+m, m);
}
if (O.restModes!==false) { setPose(p); for (const m of (O.modes||['shaded'])) save('rest-'+m, m); }
return out;
