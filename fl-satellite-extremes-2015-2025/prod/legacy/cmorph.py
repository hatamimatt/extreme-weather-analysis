import sys, os, io, time, numpy as np, pandas as pd, requests, xarray as xr, concurrent.futures as cf
sys.path.insert(0,'prod'); from common import *
H=hours(); n=len(H)
B='https://www.ncei.noaa.gov/data/cmorph-high-resolution-global-precipitation-estimates/access/30min/8km/'
# subset box indices from a reference file
ref=xr.open_dataset('cm_test.nc'); la=ref.lat.values; lo=ref.lon.values
ii=np.where((la>23.0)&(la<32.5))[0]; jj=np.where((lo>360-89.5)&(lo<360-78.5))[0]
la2,lo2=np.meshgrid(la[ii],lo[jj]-360,indexing='ij'); widx=window_index(la2,lo2); print('ok st',sum(w['ok'] for w in widx),flush=True)
def get(k):
    h=H[k]; u=f'{B}{h:%Y/%m/%d}/CMORPH_V1.0_ADJ_8km-30min_{h:%Y%m%d%H}.nc'   # file HH holds HH:00 and HH:30 half-hours
    for a in range(4):
        try:
            r=requests.get(u,timeout=180)
            if r.status_code==404: return k,None
            if r.ok:
                ds=xr.open_dataset(io.BytesIO(r.content),engine='h5netcdf')
                v=ds.cmorph.values[:,ii[0]:ii[-1]+1,jj[0]:jj[-1]+1]
                return k,cut(np.nanmean(v,0) if np.isfinite(v).all(0).any() else v.mean(0),widx)   # mean of two 30-min rates = mm in hour
        except Exception: time.sleep(3*(a+1))
    return k,None
out=np.full((n,len(widx),W,W),np.nan,np.float32); t0=time.time()
with cf.ThreadPoolExecutor(12) as ex:
    for i,(k,a) in enumerate(ex.map(get,range(n))):
        if a is not None: out[k]=a
        if (i+1)%3000==0: print(i+1,round((time.time()-t0)/60,1),'min',flush=True)
save('cmorph',out,widx,H)
print('cmorph done; hours with data',int(np.isfinite(out[:,:,OFF,OFF]).any(1).sum()),'of',n,round((time.time()-t0)/60,1),'min')
