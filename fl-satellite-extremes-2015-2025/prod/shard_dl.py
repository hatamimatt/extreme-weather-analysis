import sys, os, gzip, time, numpy as np, pandas as pd, requests, eccodes, concurrent.futures as cf
sys.path.insert(0,'prod'); from common import *
prod=sys.argv[1]; SHARD=int(sys.argv[2]); NSH=int(sys.argv[3]); NT=int(sys.argv[4]) if len(sys.argv)>4 else 3
H=hours(); n=len(H)
H1=set(pd.read_parquet('out/needed_hours_pm1.parquet').hour_start_utc)
todo=[k for k in range(n) if H[k] in H1]
if prod=='stage4':
    import json
    def url(h):
        t=h+pd.Timedelta(hours=1); return f'https://mesonet.agron.iastate.edu/archive/data/{t:%Y/%m/%d}/stage4/ST4.{t:%Y%m%d%H}.01h.grib'
    def grid():
        r=requests.get(url(pd.Timestamp('2020-05-26 22:00')),timeout=60); gid=eccodes.codes_new_from_message(r.content)
        ni=eccodes.codes_get(gid,'Ni'); nj=eccodes.codes_get(gid,'Nj')
        la=eccodes.codes_get_array(gid,'latitudes').reshape(nj,ni); lo=eccodes.codes_get_array(gid,'longitudes').reshape(nj,ni); lo=np.where(lo>180,lo-360,lo)
        eccodes.codes_release(gid); return la,lo
    def decode(b):
        gid=eccodes.codes_new_from_message(b); ni=eccodes.codes_get(gid,'Ni'); nj=eccodes.codes_get(gid,'Nj')
        v=eccodes.codes_get_values(gid).reshape(nj,ni).astype(np.float32); mv=eccodes.codes_get(gid,'missingValue'); eccodes.codes_release(gid)
        v[v==mv]=np.nan; v[v<0]=np.nan; return v
elif prod=='pccs':
    lat_p=59.98-0.04*np.arange(3000); lon_p=0.02+0.04*np.arange(9000)
    ii=np.where((lat_p>23.0)&(lat_p<32.5))[0]; jj=np.where((lon_p>360-89.5)&(lon_p<360-78.5))[0]
    def url(h): return f'https://persiann.eng.uci.edu/CHRSdata/PERSIANN-CCS/hrly/{h:%Y}/rgccs1h{h:%y}{h.dayofyear:03d}{h:%H}.bin.gz'
    def grid(): return np.meshgrid(lat_p[ii],lon_p[jj]-360,indexing='ij')
    def decode(b):
        x=np.frombuffer(gzip.decompress(b),'>i2').reshape(3000,9000)[ii[0]:ii[-1]+1,jj[0]:jj[-1]+1].astype(np.float32); x[x<0]=np.nan; return x/100.
elif prod=='cmorph':
    import netCDF4
    _r=netCDF4.Dataset('cm_test.nc'); _la=_r['lat'][:].data; _lo=_r['lon'][:].data; _r.close()
    ii=np.where((_la>23.0)&(_la<32.5))[0]; jj=np.where((_lo>360-89.5)&(_lo<360-78.5))[0]
    def url(h): return f'https://www.ncei.noaa.gov/data/cmorph-high-resolution-global-precipitation-estimates/access/30min/8km/{h:%Y/%m/%d}/CMORPH_V1.0_ADJ_8km-30min_{h:%Y%m%d%H}.nc'
    def grid(): return np.meshgrid(_la[ii],_lo[jj]-360,indexing='ij')
    import h5py, io
    def decode(b):
        with h5py.File(io.BytesIO(b),'r') as f:
            v=f['cmorph']; raw=v[:,ii[0]:ii[-1]+1,jj[0]:jj[-1]+1].astype(np.float32); sf=float(v.attrs['scale_factor'][0]); mv=v.attrs['missing_value']
        raw[raw==float(np.atleast_1d(mv)[0])]=np.nan; raw[raw<0]=np.nan
        return (raw*sf).mean(0)
la2,lo2=grid(); WIDX=window_index(la2,lo2)
def work(k):
    for a in range(3):
        try:
            r=requests.get(url(H[k]),timeout=(20,90))
            if r.status_code==404: return k,None
            if r.ok: return k,cut(decode(r.content),WIDX)
        except Exception: time.sleep(2)
    return k,None
os.makedirs(f'prod/ck_{prod}',exist_ok=True)
chunks=[todo[i:i+250] for i in range(0,len(todo),250)]; t0=time.time()
if SHARD>=0:
    with cf.ThreadPoolExecutor(NT) as ex:
        for ci,ch in enumerate(chunks):
            if ci%NSH!=SHARD: continue
            fn=f'prod/ck_{prod}/c{ci:03d}.npz'
            if os.path.exists(fn): continue
            ks=[];arrs=[]
            for k,a in ex.map(work,ch):
                if a is not None: ks.append(k);arrs.append(a)
            np.savez(fn+'.tmp.npz',k=np.array(ks),a=np.array(arrs) if arrs else np.zeros((0,len(WIDX),W,W),np.float32)); os.replace(fn+'.tmp.npz',fn)
            open(f'prod/{prod}_progress_{SHARD}.txt','w').write(f'chunk {ci} of {len(chunks)} {round((time.time()-t0)/60,1)} min\n')
else:
    out=np.full((n,len(WIDX),W,W),np.nan,np.float32); miss=0
    for ci in range(len(chunks)):
        fn=f'prod/ck_{prod}/c{ci:03d}.npz'
        if not os.path.exists(fn): miss+=1; continue
        z=np.load(fn)
        for k,a in zip(z['k'],z['a']): out[k]=a
    save(prod,out,WIDX,H)
    print(prod,'merged; missing chunks',miss,'hours with data',int(np.isfinite(out[:,:,OFF,OFF]).any(1).sum()),'of',len(todo))
