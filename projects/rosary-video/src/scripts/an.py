import librosa, numpy as np, json, sys
D=sys.argv[1]
y,sr=librosa.load(D+'/mono.wav',sr=22050)
print('dur',len(y)/sr)
oenv=librosa.onset.onset_strength(y=y,sr=sr)
tempo,beats=librosa.beat.beat_track(onset_envelope=oenv,sr=sr)
bt=librosa.frames_to_time(beats,sr=sr)
print('tempo',tempo,'nbeats',len(bt),'first beats',np.round(bt[:12],3))
ibi=np.diff(bt); print('median ibi',np.median(ibi), 'bpm',60/np.median(ibi))
# tempogram for alternatives
ac=librosa.autocorrelate(oenv,max_size=600)
lags=np.arange(len(ac))*512/sr
for lo,hi in [(0.25,0.6),(0.6,1.2),(1.2,3.0),(3,6)]:
    m=(lags>lo)&(lags<hi); i=np.argmax(ac*m); print('ac peak',lo,hi,lags[i],ac[i]/ac[0])
# meter: beat-synchronous onset strength, check periodicity 2 vs 3 vs 4
bs=librosa.util.sync(oenv[None,:],beats,aggregate=np.mean)[0]
bs=(bs-bs.mean())/bs.std()
for k in [2,3,4,6]:
    print('period',k,'acf',np.mean(bs[:-k]*bs[k:]))
    ph=[bs[p::k].mean() for p in range(k)]; print('  phase means',np.round(ph,2))
# low-freq (kick) by phase
S=np.abs(librosa.stft(y)); fr=librosa.fft_frequencies(sr=sr)
low=S[fr<150].sum(0); lbs=librosa.util.sync(low[None,:],beats)[0]
for k in [3,4]:
    print('low phase',k,np.round([lbs[p::k].mean()/lbs.mean() for p in range(k)],2))
rms=librosa.feature.rms(y=y)[0]; t=librosa.frames_to_time(np.arange(len(rms)),sr=sr)
w5=[float(rms[(t>=s)&(t<s+5)].mean()) for s in range(0,int(len(y)/sr)+1,5)]
mx=max(w5); print('rms5',[round(v/mx,2) for v in w5])
# energy json ~180
n=180; seg=np.array_split(rms,n); e=np.array([s.mean() for s in seg]); json.dump([round(float(v),3) for v in e/e.max()],open(D+'/energy.json','w'))
seg=np.array_split(np.abs(y),300); p=np.array([s.max() for s in seg]); json.dump([round(float(v),3) for v in p/p.max()],open(D+'/peaks.json','w'))
# segmentation
chroma=librosa.feature.chroma_cqt(y=y,sr=sr); mf=librosa.feature.mfcc(y=y,sr=sr,n_mfcc=13)
F=np.vstack([librosa.util.normalize(librosa.util.sync(chroma,beats),axis=0),librosa.util.normalize(librosa.util.sync(mf,beats),axis=1)])
for k in [8,10,12]:
    b=librosa.segment.agglomerative(F,k); print('agg',k,np.round(bt[np.clip(b,0,len(bt)-1)],1))
# novelty via checkerboard on recurrence
R=librosa.segment.recurrence_matrix(F,mode='affinity',sym=True,width=3)
L=16; g=np.outer(np.r_[-np.ones(L),np.ones(L)],np.r_[-np.ones(L),np.ones(L)])
Rp=np.pad(R,L); nov=np.array([np.sum(Rp[i:i+2*L,i:i+2*L]*g) for i in range(R.shape[0])])
pk=librosa.util.peak_pick(nov,pre_max=8,post_max=8,pre_avg=8,post_avg=8,delta=nov.std()*0.3,wait=16)
print('novelty peaks',np.round(bt[pk],1))
np.save(D+'/beats.npy',bt)
