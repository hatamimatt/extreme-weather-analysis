import numpy as np, pandas as pd, json, os
W=8; OFF=3   # window rows i0-3..i0+4
def stations():
    V=pd.read_csv('out/valid_stations.csv'); return V[['id','lat','lon']].reset_index(drop=True)
def hours():
    return pd.read_parquet('out/needed_hours.parquet').hour_start_utc.reset_index(drop=True)
def _dist(lat1,lon1,lat2,lon2):
    p=np.pi/180; a=np.sin((lat2-lat1)*p/2)**2+np.cos(lat1*p)*np.cos(lat2*p)*np.sin((lon2-lon1)*p/2)**2
    return 6371*2*np.arcsin(np.sqrt(a))
def window_index(lat2d, lon2d):
    """lat2d/lon2d: cell-centre arrays of the (sub)grid. Returns per-station dict with window origin and signs."""
    S=stations(); out=[]
    ny,nx=lat2d.shape
    for _,s in S.iterrows():
        d=_dist(s.lat,s.lon,lat2d,lon2d); i0,j0=np.unravel_index(np.nanargmin(d),d.shape)
        def dd(i,j): return d[i,j] if 0<=i<ny and 0<=j<nx else np.inf
        si=1 if dd(i0+1,j0)<dd(i0-1,j0) else -1; sj=1 if dd(i0,j0+1)<dd(i0,j0-1) else -1
        r0,c0=i0-OFF,j0-OFF
        ok = r0>=0 and c0>=0 and r0+W<=ny and c0+W<=nx
        # pixel size km (mean spacing)
        dy=_dist(lat2d[i0,j0],lon2d[i0,j0],lat2d[min(i0+1,ny-1),j0],lon2d[min(i0+1,ny-1),j0])
        dx=_dist(lat2d[i0,j0],lon2d[i0,j0],lat2d[i0,min(j0+1,nx-1)],lon2d[i0,min(j0+1,nx-1)])
        out.append(dict(id=s.id,i0=int(i0),j0=int(j0),r0=int(r0),c0=int(c0),si=si,sj=sj,ok=bool(ok),dist_km=float(d[i0,j0]),dx_km=float(dx),dy_km=float(dy),
                        win_lat=lat2d[max(r0,0):r0+W,max(c0,0):c0+W].tolist(), win_lon=lon2d[max(r0,0):r0+W,max(c0,0):c0+W].tolist()))
    return out
def cut(field, widx):
    """field 2D on same grid -> array (nstations,W,W)"""
    o=np.full((len(widx),W,W),np.nan,np.float32)
    for k,w in enumerate(widx):
        if w['ok']: o[k]=field[w['r0']:w['r0']+W, w['c0']:w['c0']+W]
    return o
def neighborhood_masks(w):
    """boolean masks (W,W) for N1,N4,N9,N16 in window coords"""
    i,j=OFF,OFF; si,sj=w['si'],w['sj']; m={}
    def blk(rows,cols):
        a=np.zeros((W,W),bool); a[np.ix_(rows,cols)]=True; return a
    m['N1']=blk([i],[j])
    m['N4']=blk(sorted([i,i+si]),sorted([j,j+sj]))
    m['N9']=blk([i-1,i,i+1],[j-1,j,j+1])
    m['N16']=blk(sorted([i-si,i,i+si,i+2*si]),sorted([j-sj,j,j+sj,j+2*sj]))
    return m
def save(name, arr, widx, hrs, extra=None):
    np.save(f'prod/{name}_win.npy', arr)
    meta=dict(name=name,hours=[str(h) for h in hrs],stations=[w['id'] for w in widx],widx=widx,extra=extra or {})
    json.dump(meta,open(f'prod/{name}_meta.json','w'))
