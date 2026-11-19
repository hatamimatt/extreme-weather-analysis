import os
import xarray as xr, numpy as np, pandas as pd, aiohttp, sys, time
key=os.environ['DESTINE_EDH_TOKEN']
so={'client_kwargs':{'auth':aiohttp.BasicAuth('edh',key),'trust_env':True}}
base='https://data.earthdatahub.destine.eu/era5/'
for ds,nm in [('era5','reanalysis-era5-single-levels-v0.zarr'),('era5land','reanalysis-era5-land-no-antartica-v0.zarr')]:
    t0=time.time()
    X=xr.open_zarr(base+nm,storage_options=so,chunks={})
    lon=X.longitude.values; lonc=np.where(lon>180,lon-360,lon)
    sel=X.tp.isel(longitude=np.where((lonc>=-89.5)&(lonc<=-78.5))[0]).sel(latitude=slice(32.5,23.0)).sel(valid_time=slice('2015-01-01T00:00','2026-01-01T01:00'))
    sel=sel.assign_coords(longitude=np.where(sel.longitude.values>180,sel.longitude.values-360,sel.longitude.values))
    out=sel.load()
    out.to_dataset(name='tp').to_netcdf(f'prod/era5/{ds}_edh.nc')
    print(ds,out.shape,str(out.valid_time.values[0]),str(out.valid_time.values[-1]),round((time.time()-t0)/60,1),'min',flush=True)
