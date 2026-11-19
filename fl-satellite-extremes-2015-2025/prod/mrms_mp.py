
import sys, os, gzip, time, json, numpy as np, pandas as pd, requests, eccodes, concurrent.futures as cf
sys.path.insert(0,'prod'); from common import *
prod=sys.argv[1]; SHARD=int(sys.argv[2]); NSH=int(sys.argv[3])
H=hours(); n=len(H)
H1=set(pd.read_parquet('out/needed_hours_pm1.parquet').hour_start_utc)
todo=[k for k in range(n) if H[k] in H1]
def url(h):
    t=h+pd.Timedelta(hours=1)
    if prod=='mrms_radaronly':
        return [f'https://mtarchive.geol.iastate.edu/{t:%Y/%m/%d}/mrms/ncep/RadarOnly_QPE_01H/RadarOnly_QPE_01H_00.00_{t:%Y%m%d-%H}0000.grib2.gz']
    return [f'https://mtarchive.geol.iastate.edu/{t:%Y/%m/%d}/mrms/ncep/MultiSensor_QPE_01H_Pass2/MultiSensor_QPE_01H_Pass2_00.00_{t:%Y%m%d-%H}0000.grib2.gz',
            f'https://mtarchive.geol.iastate.edu/{t:%Y/%m/%d}/mrms/ncep/GaugeCorr_QPE_01H/GaugeCorr_QPE_01H_00.00_{t:%Y%m%d-%H}0000.grib2.gz']
# MRMS regular grid: lat 54.995 -> 20.005 step 0.01, lon -129.995 -> -60.005
lat=54.995-0.01*np.arange(3500); lon=-129.995+0.01*np.arange(7000)
ii=np.where((lat>23.5)&(lat<31.5))[0]; jj=np.where((lon>-88.5)&(lon<-79.5))[0]
la2,lo2=np.meshgrid(lat[ii],lon[jj],indexing='ij'); WIDX=window_index(la2,lo2)
def work(k):
    h=H[k]
    for u in url(h):
        for a in range(3):
            try:
                r=requests.get(u,timeout=(20,60))
                if r.status_code==404: break
                if r.ok:
                    b=gzip.decompress(r.content); gid=eccodes.codes_new_from_message(b)
                    v=eccodes.codes_get_values(gid).reshape(3500,7000)[ii[0]:ii[-1]+1,jj[0]:jj[-1]+1].astype(np.float32); eccodes.codes_release(gid)
                    v[(v<0)|(v>9000)]=np.nan
                    return k,cut(v,WIDX),u.split('/')[-1][:12]
            except Exception: time.sleep(2)
    return k,None,''
if __name__=='__main__':
    os.makedirs(f'prod/ck_{prod}',exist_ok=True)
    chunks=[todo[i:i+250] for i in range(0,len(todo),250)]
    t0=time.time()
    if SHARD>=0:
        with cf.ThreadPoolExecutor(3) as ex:
            for ci,ch in enumerate(chunks):
                if ci%NSH!=SHARD: continue
                fn=f'prod/ck_{prod}/c{ci:03d}.npz'
                if os.path.exists(fn): continue
                ks=[];arrs=[];srcs=[]
                for k,a,s_ in ex.map(work,ch):
                    if a is not None: ks.append(k);arrs.append(a);srcs.append(s_)
                np.savez(fn+'.tmp.npz',k=np.array(ks),a=np.array(arrs) if arrs else np.zeros((0,len(WIDX),W,W),np.float32),s=np.array(srcs)); os.replace(fn+'.tmp.npz',fn)
                open(f'prod/{prod}_progress_{SHARD}.txt','w').write(f'chunk {ci} of {len(chunks)} {round((time.time()-t0)/60,1)} min\n')
    else:
        out=np.full((n,len(WIDX),W,W),np.nan,np.float32); src=['']*n; miss=0
        for ci in range(len(chunks)):
            fn=f'prod/ck_{prod}/c{ci:03d}.npz'
            if not os.path.exists(fn): miss+=1; continue
            z=np.load(fn)
            for k,a,s_ in zip(z['k'],z['a'],z['s']): out[k]=a; src[k]=str(s_)
        save(prod,out,WIDX,H,extra=dict(source=src))
        print(prod,'merged; missing chunks',miss,'hours with data',int(np.isfinite(out[:,:,OFF,OFF]).any(1).sum()),'of',len(todo))
