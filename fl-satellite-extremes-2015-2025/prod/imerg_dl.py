import requests, os, pandas as pd, concurrent.futures as cf, time, threading
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
hrs=pd.read_parquet('out/needed_hours.parquet').hour_start_utc
lon0,lon1,lat0,lat1=914,1010,1135,1219
ce=f'/Grid/precipitation[0:1:0][{lon0}:1:{lon1}][{lat0}:1:{lat1}]'
jobs=[]
for h in hrs:
    for m in (0,30):
        t=h+pd.Timedelta(minutes=m); e=t+pd.Timedelta(minutes=29,seconds=59)
        nm=f"3B-HHR.MS.MRG.3IMERG.{t:%Y%m%d}-S{t:%H%M%S}-E{e:%H%M%S}.{t.hour*60+t.minute:04d}.V07B.HDF5"
        jobs.append(nm)
base='https://opendap.earthdata.nasa.gov/collections/C2723754847-GES_DISC/granules/GPM_3IMERGHH.07%3A'
def get(nm):
    fn=f'prod/imerg/{nm}.nc4'
    if os.path.exists(fn): return 'skip'
    for a in range(4):
        try:
            r=S().get(base+nm+'.dap.nc4',params={'dap4.ce':ce},timeout=180)
            if r.status_code==404: return '404'
            if r.ok and r.content[:4]==b'\x89HDF': open(fn,'wb').write(r.content); return 'ok'
        except Exception: pass
        time.sleep(3*(a+1))
    return 'fail'
from collections import Counter
t0=time.time()
with cf.ThreadPoolExecutor(16) as ex: res=list(ex.map(get,jobs))
c=Counter(res); print(c, round((time.time()-t0)/60,1),'min')
open('prod/imerg_status.txt','w').write(str(c))
