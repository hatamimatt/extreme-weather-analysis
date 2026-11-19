import sys, os, gzip, time, json, numpy as np, pandas as pd, requests, eccodes, concurrent.futures as cf
sys.path.insert(0,'prod'); from common import *
prod=sys.argv[1]
H=hours(); n=len(H)
def url(h):
    t=h+pd.Timedelta(hours=1)   # files are stamped at hour end
    if prod=='stage4':
        return [f'https://mesonet.agron.iastate.edu/archive/data/{t:%Y/%m/%d}/stage4/ST4.{t:%Y%m%d%H}.01h.grib']
    if prod=='mrms_radaronly':
        return [f'https://mtarchive.geol.iastate.edu/{t:%Y/%m/%d}/mrms/ncep/RadarOnly_QPE_01H/RadarOnly_QPE_01H_00.00_{t:%Y%m%d-%H}0000.grib2.gz']
    if prod=='mrms_gaugecorr':
        return [f'https://mtarchive.geol.iastate.edu/{t:%Y/%m/%d}/mrms/ncep/MultiSensor_QPE_01H_Pass2/MultiSensor_QPE_01H_Pass2_00.00_{t:%Y%m%d-%H}0000.grib2.gz',
                f'https://mtarchive.geol.iastate.edu/{t:%Y/%m/%d}/mrms/ncep/GaugeCorr_QPE_01H/GaugeCorr_QPE_01H_00.00_{t:%Y%m%d-%H}0000.grib2.gz']
def decode(b, want_ll=False):
    if b[:2]==b'\x1f\x8b': b=gzip.decompress(b)
    gid=eccodes.codes_new_from_message(b)
    try:
        ni=eccodes.codes_get(gid,'Ni'); nj=eccodes.codes_get(gid,'Nj'); v=eccodes.codes_get_values(gid).reshape(nj,ni).astype(np.float32)
        mv=eccodes.codes_get(gid,'missingValue'); v[v==mv]=np.nan
        ll=None
        if want_ll:
            la=eccodes.codes_get_array(gid,'latitudes').reshape(nj,ni); lo=eccodes.codes_get_array(gid,'longitudes').reshape(nj,ni); lo=np.where(lo>180,lo-360,lo); ll=(la,lo)
        return v,ll
    finally: eccodes.codes_release(gid)
def fetch(h):
    for u in url(h):
        for a in range(3):
            try:
                r=requests.get(u,timeout=120)
                if r.status_code==404: break
                if r.ok: return r.content, u
            except Exception: time.sleep(3)
    return None, None
# grid from a reference hour
ref=None
for h in H[len(H)//2:]:
    b,u=fetch(h)
    if b: ref=decode(b,True); break
v,(la,lo)=ref
if prod.startswith('mrms'): v[v<0]=np.nan  # -3 = no coverage
widx=window_index(la,lo); print(prod,'grid',v.shape,'stations ok',sum(w['ok'] for w in widx),flush=True)
del la,lo
WIDX=widx
def work(k):
    b,u=fetch(H[k])
    if b is None: return k,None,None
    try:
        f,_=decode(b)
        if prod.startswith('mrms'): f[f<0]=np.nan
        return k,cut(f,WIDX),u.split('/')[-1][:20]
    except Exception as e: return k,None,'err'
out=np.full((n,len(widx),W,W),np.nan,np.float32); src=['']*n
t0=time.time(); done=0
with cf.ThreadPoolExecutor(12) as ex:
    for k,arr,s in ex.map(work,range(n)):
        done+=1
        if arr is not None: out[k]=arr; src[k]=s
        if done%2000==0: print(done,round((time.time()-t0)/60,1),'min',flush=True)
save(prod,out,widx,H,extra=dict(source=src))
print(prod,'done; hours with data',int(np.isfinite(out[:,:,OFF,OFF]).any(1).sum()),'of',n, round((time.time()-t0)/60,1),'min')
