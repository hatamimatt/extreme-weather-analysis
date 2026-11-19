import sys, os, gzip, time, numpy as np, pandas as pd, requests, concurrent.futures as cf
sys.path.insert(0,'prod'); from common import *
H=hours(); n=len(H)
B='https://persiann.eng.uci.edu/CHRSdata/PERSIANN-CCS/hrly/'
lat_p=59.98-0.04*np.arange(3000); lon_p=0.02+0.04*np.arange(9000)
ii=np.where((lat_p>23.0)&(lat_p<32.5))[0]; jj=np.where((lon_p>360-89.5)&(lon_p<360-78.5))[0]
la2,lo2=np.meshgrid(lat_p[ii],lon_p[jj]-360,indexing='ij'); widx=window_index(la2,lo2); print('ok st',sum(w['ok'] for w in widx),flush=True)
def get(k):
    h=H[k]; u=f'{B}{h:%Y}/rgccs1h{h:%y}{h.dayofyear:03d}{h:%H}.bin.gz'
    for a in range(4):
        try:
            r=requests.get(u,timeout=180)
            if r.status_code==404: return k,None
            if r.ok:
                x=np.frombuffer(gzip.decompress(r.content),'>i2').reshape(3000,9000)[ii[0]:ii[-1]+1,jj[0]:jj[-1]+1].astype(np.float32)
                x[x<0]=np.nan; return k,cut(x/100.,widx)
        except Exception: time.sleep(3*(a+1))
    return k,None
out=np.full((n,len(widx),W,W),np.nan,np.float32); t0=time.time()
with cf.ThreadPoolExecutor(10) as ex:
    for i,(k,a) in enumerate(ex.map(get,range(n))):
        if a is not None: out[k]=a
        if (i+1)%3000==0: print(i+1,round((time.time()-t0)/60,1),'min',flush=True)
save('pccs',out,widx,H)
print('pccs done; hours with data',int(np.isfinite(out[:,:,OFF,OFF]).any(1).sum()),'of',n,round((time.time()-t0)/60,1),'min')
