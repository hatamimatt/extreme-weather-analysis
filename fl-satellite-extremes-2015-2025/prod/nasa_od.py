import sys, os, io, time, numpy as np, pandas as pd, requests, xarray as xr, threading, concurrent.futures as cf
sys.path.insert(0,'prod'); from common import *
prod=sys.argv[1]
class EDSession(requests.Session):
    def __init__(s,u,p): super().__init__(); s.auth=(u,p)
    def rebuild_auth(s, pr, resp):
        h=pr.headers
        if 'Authorization' in h:
            o=requests.utils.urlparse(resp.request.url).hostname; n=requests.utils.urlparse(pr.url).hostname
            if o!=n and 'urs.earthdata' not in (n or '') and 'urs.earthdata' not in (o or ''): del h['Authorization']
loc=threading.local()
def S():
    if not hasattr(loc,'s'): loc.s=EDSession(os.environ['EARTHDATA_USER'],os.environ['EARTHDATA_PASS'])
    return loc.s
H=hours(); n=len(H); hidx={h:k for k,h in enumerate(H)}
cmr='https://cmr.earthdata.nasa.gov/search/granules.json'
if prod=='merra2':
    cid='C1276812838-GES_DISC'; ce='/PRECTOTCORR[0:1:23][220:1:252][136:1:172]'; lat=np.arange(220,253)*0.5-90; lon=np.arange(136,173)*0.625-180
    # granule titles per day (stream 400/401)
    titles={}; hdr={}
    params={'collection_concept_id':cid,'temporal':'2015-01-01T00:00:00Z,2025-12-31T23:59:59Z','page_size':2000}
    while True:
        r=requests.get(cmr,params=params,headers=hdr,timeout=120); ent=r.json()['feed']['entry']
        for e in ent: titles[e['title'].split(':')[1].split('.')[-2]]=e['title']
        sa=r.headers.get('CMR-Search-After')
        if not ent or not sa: break
        hdr={'CMR-Search-After':sa}
    units=pd.Series(H).dt.floor('D').unique()
    jobs=[(d, titles.get(f'{d:%Y%m%d}')) for d in units]
    print('merra days',len(jobs),'with granule',sum(t is not None for _,t in jobs),flush=True)
elif prod=='nldas2':
    cid='C2033151148-GES_DISC'; ce='/Rainf[0:1:0][0:1:62][286:1:370]'; lat=25.0625+np.arange(0,63)*0.125; lon=-124.9375+np.arange(286,371)*0.125
    jobs=[(h, f'NLDAS_FORA0125_H.2.0:NLDAS_FORA0125_H.A{h:%Y%m%d.%H}00.020.nc') for h in H]
la2,lo2=np.meshgrid(lat,lon,indexing='ij'); widx=window_index(la2,lo2); print('stations ok',sum(w['ok'] for w in widx),flush=True)
base=f'https://opendap.earthdata.nasa.gov/collections/{cid}/granules/'
def get(job):
    key,title=job
    if title is None: return key,None
    for a in range(4):
        try:
            r=S().get(base+title.replace(':','%3A')+'.dap.nc4',params={'dap4.ce':ce},timeout=180)
            if r.status_code==404: return key,None
            if r.ok:
                ds=xr.open_dataset(io.BytesIO(r.content),engine='h5netcdf')
                v=ds['PRECTOTCORR'].values*3600 if prod=='merra2' else ds['Rainf'].values   # -> mm per hour
                return key,v.astype(np.float32)
        except Exception as e: pass
        time.sleep(3*(a+1))
    return key,'fail'
out=np.full((n,len(widx),W,W),np.nan,np.float32); t0=time.time(); nf=0
with cf.ThreadPoolExecutor(12) as ex:
    for i,(key,v) in enumerate(ex.map(get,jobs)):
        if v is None or isinstance(v,str): nf+= isinstance(v,str); continue
        if prod=='merra2':
            for hh in range(24):   # MERRA-2 hour index hh = average over [hh:00, hh+1:00)
                k=hidx.get(key+pd.Timedelta(hours=hh))
                if k is not None: out[k]=cut(v[hh],widx)
        else:
            out[hidx[key]]=cut(v[0],widx)
        if (i+1)%2000==0: print(i+1,round((time.time()-t0)/60,1),'min',flush=True)
save(prod,out,widx,H)
print(prod,'done; fails',nf,'hours with data',int(np.isfinite(out[:,:,OFF,OFF]).any(1).sum()),'of',n,round((time.time()-t0)/60,1),'min')
