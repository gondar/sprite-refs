import librosa,numpy as np,sys
D=sys.argv[1]; y,sr=librosa.load(D+'/mono.wav',sr=22050)
h=128; o=librosa.onset.onset_strength(y=y,sr=sr,hop_length=h)
ac=librosa.autocorrelate(o,max_size=400); ac/=ac[0]
lag=lambda s:int(round(s*sr/h))
b=0.51084
for name,s in [('1/4 beat',b/4),('1/3 beat (triplet 8th)',b/3),('1/2 beat',b/2),('2/3 beat',2*b/3),('3/4 beat',3*b/4),('beat',b)]:
    i=lag(s); print(name,round(s,3),round(float(ac[i-2:i+3].max()),3))
bt=np.load(D+'/beats.npy'); ot=librosa.frames_to_time(np.arange(len(o)),sr=sr,hop_length=h)
# onset strength by position within beat (12 bins)
hist=np.zeros(12);cnt=np.zeros(12)
for a,c in zip(bt[:-1],bt[1:]):
    m=(ot>=a)&(ot<c); ph=((ot[m]-a)/(c-a)*12).astype(int); np.add.at(hist,ph,o[m]); np.add.at(cnt,ph,1)
print('intra-beat profile /12',np.round(hist/cnt/(hist/cnt).mean(),2))
print('downbeats (every 4th from 0.859):',np.round(bt[::4][:6],3), 'bar len',np.median(np.diff(bt[::4])))
print('last beat',bt[-1])
