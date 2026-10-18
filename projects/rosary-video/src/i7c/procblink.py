# procblink.py : paint closed eyes procedurally (no AI edit): inpaint each eye with skin, draw one lid line.
# writes ov/<ID>_<fig>_blink.png/.json (frame-box coords) and a x4 check strip procblink.jpg
import json,numpy as np,cv2
from PIL import Image
from scipy import ndimage as ndi
P='../pub/'
import sys; JOBS=json.load(open(sys.argv[1] if len(sys.argv)>1 else 'procblink.json')); SEEDS=json.load(open('procseeds.json')); OPTS={'C2':{'kneel':{'xmin':1090,'keepdark':90}}}; LINES={'C4':{'mary':[[(746,116),(747.5,124),(748,131),(747.8,138),(747.2,142)]]}}   # {"C3":{"mary":[x0,y0,x1,y1],...},...}
strip=[]
for i,figs in JOBS.items():
    full=cv2.imread(P+'i5/%s_full.jpg'%i)
    AL=np.zeros(full.shape[:2],np.float32)
    for f_ in json.load(open('../scripts/i5/work/%s_figs.json'%i))['figs']:
        im_=np.asarray(Image.open(P+f_['file']))[...,3]/255.; x_,y_,w_,h_=f_['px']; AL[y_:y_+h_,x_:x_+w_]=np.maximum(AL[y_:y_+h_,x_:x_+w_],im_)
    for fg,(x0,y0,x1,y1) in figs.items():
        pad=6; X0,Y0,X1,Y1=x0-pad,y0-pad,x1+pad,y1+pad
        crop=full[Y0:Y1,X0:X1].copy(); h,w=crop.shape[:2]
        hsv=cv2.cvtColor(crop,cv2.COLOR_BGR2HSV); L=cv2.cvtColor(crop,cv2.COLOR_BGR2LAB)[...,0].astype(float)
        inner=np.zeros((h,w),bool); inner[pad:-pad,pad:-pad]=True
        thrL=max(np.percentile(L[inner],92),L[inner].mean()+25)
        scl=(L>thrL*0.97)&(hsv[...,1]<70)&inner
        scl=ndi.binary_opening(scl,iterations=1)
        lab,n=ndi.label(scl); sz=ndi.sum(scl,lab,range(1,n+1))
        keep=[]
        Yg,Xg=np.mgrid[0:h,0:w]
        for sd in SEEDS[i][fg]:
            sx,sy=sd[0],sd[1]; rr=sd[2] if len(sd)>2 else 11
            sx-=X0; sy-=Y0; near=((Xg-sx)**2+(Yg-sy)**2)<=rr**2
            if len(sd)>=5:
                lab[(((Xg-sx)/sd[3])**2+((Yg-sy)/sd[4])**2)<=1]=1000+len(keep); keep.append(1000+len(keep)); continue
            cand=(L>np.percentile(L[near],70))&(hsv[...,1]<90)&near
            cl,cn=ndi.label(cand)
            if cn==0: continue
            dd=[((Xg[cl==k]-sx)**2+(Yg[cl==k]-sy)**2).min() for k in range(1,cn+1)]
            lab[cl==1+int(np.argmin(dd))]=1000+len(keep); keep.append(1000+len(keep))
        eyes=[]
        out=crop.copy(); fill=np.zeros((h,w),bool); eyecore=np.zeros((h,w),bool)
        darkpx=L<np.percentile(L[inner],35)
        for j in keep:
            e=ndi.binary_fill_holes(ndi.binary_closing(lab==j,iterations=2))
            ring=ndi.binary_dilation(e,iterations=5)
            reg=e|(ring&darkpx)
            reg=ndi.binary_closing(reg,iterations=2); reg=ndi.binary_fill_holes(reg)
            # keep the part of the dark outline only within 4px of the sclera (not the brow)
            reg&=ndi.binary_dilation(e,iterations=4)|(ndi.binary_dilation(e,iterations=7)&(np.roll(ndi.binary_dilation(e,iterations=4),-3,axis=0)))
            fill|=ndi.binary_dilation(reg,iterations=1); eyecore|=ndi.binary_dilation(e,iterations=1)
            ys,xs=np.nonzero(e); ex0,ex1,ey0,ey1=xs.min(),xs.max(),ys.min(),ys.max()
            eyes.append(((ex0+ex1)/2,(ey0+ey1)/2,(ex1-ex0)/2+2,(ey1-ey0)/2+2))
        figa=AL[Y0:Y1,X0:X1]>0.99
        ringall=ndi.binary_dilation(fill,iterations=7)&~ndi.binary_dilation(fill,iterations=2)&figa
        skin=ringall&(L>np.percentile(L[ringall],35))&(L<np.percentile(L[ringall],90))
        col=np.median(crop[skin],axis=0)
        # smooth fill: skin colour with the local low-frequency shading taken from the ring
        fill&=figa
        op=OPTS.get(i,{}).get(fg,{})
        if 'xmin' in op: fill[:,:max(0,op['xmin']-X0)]=False
        if 'keepdark' in op: fill&=~((L<op['keepdark'])&~ndi.binary_dilation(eyecore,iterations=1))
        wr=skin.astype(np.float32); den=cv2.GaussianBlur(wr,(0,0),4)+1e-6
        shade=np.dstack([cv2.GaussianBlur(crop[...,k].astype(np.float32)*wr,(0,0),4)/den for k in range(3)])
        shade=np.where(den[...,None]>0.05,shade,col)
        # never paint skin over sky / bluish background
        bgr=crop.astype(int); fill&=~((bgr[...,0]>bgr[...,2]+6)&(L<200)&~eyecore)
        # box limit: never fill outside the job box (keeps cheek/hair contour)
        lim=np.zeros((h,w),bool); lim[pad:h-pad,pad:w-pad]=True; fill&=lim
        # specks: small dark bits left just above/around the filled eyes -> fill too
        near=ndi.binary_dilation(fill,iterations=6)&~fill&lim
        thrd=np.percentile(L[skin] if skin.any() else L,50)-35
        dkall=(L<thrd)&~fill            # dark pixels in the whole crop (outside the filled eyes)
        sl,sn=ndi.label(dkall,structure=np.ones((3,3)))
        for k in range(1,sn+1):
            comp=sl==k
            ys_,xs_=np.nonzero(comp)
            if comp.sum()<=10 and (comp&near).any() and ys_.min()>0 and xs_.min()>0 and ys_.max()<h-1 and xs_.max()<w-1:   # isolated tiny speck next to the eye (not a line piece)
                fill|=ndi.binary_dilation(comp,iterations=1)&lim
        out=crop.astype(np.float32); out[fill]=shade[fill]; out=out.astype(np.uint8)
        fill=fill.astype(np.uint8)
        # lid line: downward-curved arc across the eye centre, colour = darkest outline nearby
        dark=np.percentile(crop.reshape(-1,3)[L.ravel()<np.percentile(L,8)],50,axis=0) if (L<np.percentile(L,8)).any() else np.array([40,40,50])
        S=4; big=cv2.resize(out,(w*S,h*S),interpolation=cv2.INTER_CUBIC)
        # re-draw long outlines (face contour, nose line) that pass THROUGH the filled area
        dl=(L<thrd)&~(fill>0)
        cl,cn=ndi.label(dl,structure=np.ones((3,3)))
        F=fill>0; Fd=ndi.binary_dilation(F,iterations=2)
        for k in range(1,cn+1):
            comp=cl==k
            if comp.sum()<25 or not (comp&Fd).any(): continue
            ys,xs=np.nonzero(comp&ndi.binary_dilation(F,iterations=8))
            fy=np.nonzero(F.any(1))[0]
            above=ys<fy.min()+2; below=ys>fy.max()-2
            touch=np.nonzero(comp&Fd)
            ty0,ty1=touch[0].min(),touch[0].max()
            pts_y=ys; 
            if len(ys)<8: continue
            # only near-vertical lines that leave the fill on two sides
            sel=(np.abs(ys-ty0)<=8)|(np.abs(ys-ty1)<=8)
            if (ys.max()-ys.min())<6: continue
            p=np.polyfit(ys[sel].astype(float),xs[sel].astype(float),1 if sel.sum()<12 else 2)
            # gap rows: rows inside fill bbox where the line would be inside F
            yy=np.arange(max(0,ty0-1),min(h,ty1+2)); xx=np.polyval(p,yy)
            inF=[F[int(y),int(round(x))] if 0<=int(round(x))<w else False for x,y in zip(xx,yy)]
            if not any(inF): continue
            idx=np.nonzero(inF)[0]; a0,a1=max(0,idx.min()-1),min(len(yy)-1,idx.max()+1)
            seg=np.array([[xx[t]*S+S/2,yy[t]*S+S/2] for t in range(a0,a1+1)],np.int32)
            col=np.median(crop[comp].reshape(-1,3),axis=0)
            cv2.polylines(big,[seg],False,tuple(int(v) for v in col),thickness=int(1.5*S),lineType=cv2.LINE_AA)
        for (cx,cy,rx,ry) in eyes:
            pts=[]
            for t in np.linspace(0.12,0.88,24)*np.pi:
                pts.append([ (cx+(rx-2)*np.cos(np.pi-t))*S, (cy+0.1*ry+ max(1.2,0.3*ry)*np.sin(t))*S ])
            cv2.polylines(big,[np.array(pts,np.int32)],False,tuple(int(v) for v in dark),thickness=int(1.6*S),lineType=cv2.LINE_AA)
        for line in LINES.get(i,{}).get(fg,[]):
            seg=np.array([[(px-X0)*S+S/2,(py-Y0)*S+S/2] for px,py in line],np.int32)
            cv2.polylines(big,[seg],False,tuple(int(v) for v in dark),thickness=int(1.7*S),lineType=cv2.LINE_AA)
            for px,py in line: fill[max(0,int(py-Y0)-1):int(py-Y0)+2,max(0,int(px-X0)-1):int(px-X0)+2]=1
        out=cv2.resize(big,(w,h),interpolation=cv2.INTER_AREA)
        changed=cv2.dilate(fill,np.ones((5,5),np.uint8)).astype(np.float32)
        a=np.clip(cv2.GaussianBlur(changed,(0,0),1.0)*1.5,0,1)
        rgba=np.dstack([cv2.cvtColor(out,cv2.COLOR_BGR2RGB),(a*255).astype(np.uint8)])
        Image.fromarray(rgba).save('ov/%s_%s_blink.png'%(i,fg)); json.dump(dict(xy=[int(X0),int(Y0)]),open('ov/%s_%s_blink.json'%(i,fg),'w'))
        comp=(crop*(1-a[...,None])+out*a[...,None]).astype(np.uint8)
        print(i,fg,'eyes',[(round(e[2]),round(e[3])) for e in eyes])
        strip.append(np.hstack([crop,comp]))
Wm=max(s.shape[1] for s in strip)
st=np.vstack([np.pad(s,((0,3),(0,Wm-s.shape[1]),(0,0)),constant_values=255) for s in strip])
cv2.imwrite('procblink.jpg',cv2.resize(st,(st.shape[1]*4,st.shape[0]*4),interpolation=cv2.INTER_CUBIC))
