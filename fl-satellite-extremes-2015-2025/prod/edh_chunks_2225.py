import numpy as np, pandas as pd, requests, numcodecs, json, os, time, concurrent.futures as cf, xarray as xr, aiohttp
key=os.environ['DESTINE_EDH_TOKEN']; base='https://data.earthdatahub.destine.eu/era5/'
so={'client_kwargs':{'auth':aiohttp.BasicAuth('edh',key),'trust_env':True}}
for ds,nm in [('era5','reanalysis-era5-single-levels-v0.zarr')]:
    out_fn=f'prod/era5/{ds}_edh_2022_2025.npz'
    if os.path.exists(out_fn): continue
    t0=time.time()
    X=xr.open_zarr(base+nm,storage_options=so,chunks={}); vt=pd.DatetimeIndex(X.valid_time.values); la=X.latitude.values; lo=X.longitude.values
    za=requests.get(base+nm+'/.zmetadata',auth=('edh',key),timeout=120).json()['metadata']['tp/.zarray']
    ct,cy,cx=za['chunks']; comp=numcodecs.get_codec(za['compressor']); T,NY,NX=za['shape']
    lonc=np.where(lo>180,lo-360,lo)
    ti=np.where((vt>=pd.Timestamp('2021-12-31 00:00'))&(vt<=pd.Timestamp('2026-01-01 01:00')))[0]
    yi=np.where((la<=32.5)&(la>=23.0))[0]; xi=np.where((lonc>=-89.5)&(lonc<=-78.5))[0]
    keys=[(a,b,c) for a in np.unique(ti//ct) for b in np.unique(yi//cy) for c in np.unique(xi//cx)]
    print(ds,'chunks',len(keys),flush=True)
    os.makedirs(f'prod/era5/ck_{ds}',exist_ok=True)
    def get(k):
        fn=f'prod/era5/ck_{ds}/{k[0]}.{k[1]}.{k[2]}.npy'
        if os.path.exists(fn): return k,'skip'
        for a in range(6):
            try:
                r=requests.get(base+nm+'/tp/'+'.'.join(map(str,k)),auth=('edh',key),timeout=(30,900))
                if r.ok:
                    arr=np.frombuffer(comp.decode(r.content),dtype=za['dtype'])
                    nt=min(ct,T-k[0]*ct); ny_=min(cy,NY-k[1]*cy); nx_=min(cx,NX-k[2]*cx)
                    arr=arr.reshape(ct,cy,cx)[:nt,:ny_,:nx_] if arr.size==ct*cy*cx else arr.reshape(nt,ny_,nx_)
                    np.save(fn+'.tmp.npy',arr); os.replace(fn+'.tmp.npy',fn); return k,'ok'
                if r.status_code==404: return k,'404'
            except Exception as e: pass
            time.sleep(10*(a+1))
        return k,'fail'
    with cf.ThreadPoolExecutor(6) as ex:
        res=list(ex.map(get,keys))
    print(ds,pd.Series([s for _,s in res]).value_counts().to_dict(),round((time.time()-t0)/60,1),'min',flush=True)
    # assemble subset
    sub=np.full((len(ti),len(yi),len(xi)),np.nan,np.float32)
    for (a,b,c),s in res:
        fn=f'prod/era5/ck_{ds}/{a}.{b}.{c}.npy'
        if not os.path.exists(fn): continue
        arr=np.load(fn); tg=np.arange(a*ct,a*ct+arr.shape[0]); yg=np.arange(b*cy,b*cy+arr.shape[1]); xg=np.arange(c*cx,c*cx+arr.shape[2])
        tm=np.isin(ti,tg); ym=np.isin(yi,yg); xm=np.isin(xi,xg)
        sub[np.ix_(tm,ym,xm)]=arr[np.ix_(np.isin(tg,ti),np.isin(yg,yi),np.isin(xg,xi))]
    np.savez(out_fn,tp=sub,vt=vt[ti].values,lat=la[yi],lon=lonc[xi])
    print(ds,'assembled',sub.shape,'nan frac',round(float(np.isnan(sub).mean()),4),flush=True)
