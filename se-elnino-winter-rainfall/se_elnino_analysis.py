# %% [markdown]
# # Strong El Niño winters and US Southeast rainfall: analysis notebook
# 
# These are the **cells that produced the results and figures, verbatim and in the order they ran** (Nov 2026).
# Changes from the session are limited to the four items listed in the README ("What differs from the original session").
# Run top to bottom with the project folder as the working directory. All outputs are written to the working directory.

# %% [markdown]
# ## 1. ENSO index: rank El Niño events by peak RONI (and ONI)

# %%
# [original cell 1] download NOAA CPC RONI table
import requests
r = requests.get("https://www.cpc.ncep.noaa.gov/data/indices/RONI.ascii.txt", timeout=60)
print(r.status_code, len(r.text)); print(r.text[:300]); print(r.text[-400:])
open('RONI.ascii.txt','w').write(r.text)

# %%
# [original cell 2] per-winter peak RONI / ONI -> el_nino_event_ranking_roni_oni.csv
import pandas as pd, io, numpy as np
seas = ['DJF','JFM','FMA','MAM','AMJ','MJJ','JJA','JAS','ASO','SON','OND','NDJ']
def load(txt, valcol):
    df = pd.read_csv(io.StringIO(txt), sep=r'\s+')
    df.columns=['SEAS','YR','ANOM'] if valcol=='ANOM' else df.columns
    return df
roni = pd.read_csv('RONI.ascii.txt', sep=r'\s+')
o = requests.get("https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt", timeout=60); print(o.status_code, o.text[:120].replace('\n',' | '))
open('oni.ascii.txt','w').write(o.text)
oni = pd.read_csv('oni.ascii.txt', sep=r'\s+')
def events(df, col):
    df = df.copy(); df['k']=df.SEAS.map(seas.index)
    rows=[]
    for y in range(1950, 2026):
        # winter Y/Y+1: seasons JJA..NDJ of Y and DJF..MAM of Y+1
        a = df[((df.YR==y)&(df.k>=6))|((df.YR==y+1)&(df.k<=3))]
        if len(a)==0: continue
        i = a[col].idxmax()
        djf = df[(df.YR==y+1)&(df.SEAS=='DJF')][col]
        rows.append(dict(winter=f"{y}-{str(y+1)[-2:]}", peak=a.loc[i,col], peak_seas=f"{a.loc[i,'SEAS']} {a.loc[i,'YR']}", DJF=djf.iloc[0] if len(djf) else np.nan))
    return pd.DataFrame(rows).set_index('winter')
er = events(roni,'ANOM'); eo = events(oni, oni.columns[-1])
t = er.join(eo, rsuffix='_ONI').sort_values('peak', ascending=False)
t = t[(t.peak>=1.0)|(t.peak_ONI>=1.0)].round(2)
print(t.to_string())
t.to_csv('el_nino_event_ranking_roni_oni.csv')

# %% [markdown]
# ## 2. Rainfall data: NOAA nClimGrid monthly precipitation (~1.8 GB)

# %%
# [original cell 5] download nClimGrid
# (shell cell in the notebook; same command via subprocess here)
import subprocess
subprocess.run('mkdir -p data && curl -sS -L -o data/nclimgrid_prcp.nc https://www.ncei.noaa.gov/data/nclimgrid-monthly/access/nclimgrid_prcp.nc && ls -l data/nclimgrid_prcp.nc', shell=True, check=True)

# %%
# [original cell 6] open nClimGrid
import xarray as xr
ds = xr.open_dataset('data/nclimgrid_prcp.nc')
print(ds)
print(ds.time.values[[0,-1]])

# %%
# [original cell 7] Southeast subset and Dec-Feb totals (winter labelled by December year)
import numpy as np, pandas as pd
print(ds.prcp.attrs)
sub = ds.prcp.sel(lat=slice(37.6, 24.4), lon=slice(-95.5, -74.5)).load()
print(sub.shape, float(sub.isel(time=0).count()))
# DJF: Dec of year Y + Jan, Feb of Y+1 ; label by Dec year Y
t = pd.to_datetime(sub.time.values)
wy = np.where(t.month==12, t.year, t.year-1)
m = np.isin(t.month,[12,1,2])
s = sub.isel(time=m).assign_coords(wy=('time', wy[m]))
cnt = s.groupby('wy').count('time').max(['lat','lon'])
djf = s.groupby('wy').sum('time', min_count=3)
full = cnt.wy.values[cnt.values==3]
djf = djf.sel(wy=full)
print(djf.wy.values[[0,-1]], djf.sizes)
djf.to_netcdf('data/se_djf_prcp.nc')

# %%
# [original cell 8] state polygons (Natural Earth via regionmask)
import regionmask
try:
    st = regionmask.defined_regions.natural_earth_v5_0_0.us_states_50
    print(len(st), st.names[:5])
except Exception as e:
    print('ERR', repr(e)[:400])

# %% [markdown]
# ## 3. Analog composites, sign counts, resampling test and FDR

# %%
# [original cells 9 + 10] composites vs 1991-2020 normal, 5,000-draw resampling test, FDR, per-state table
import xarray as xr, numpy as np, pandas as pd
djf = xr.open_dataarray('data/se_djf_prcp.nc')
SE7 = ['Alabama','Florida','Georgia','Mississippi','North Carolina','South Carolina','Tennessee']
st = regionmask.defined_regions.natural_earth_v5_0_0.us_states_50
mask3d = st.mask_3D(djf.lon, djf.lat)
idx = [st.map_keys(n) for n in SE7]
se_mask = mask3d.sel(region=idx).any('region') & djf.isel(wy=0).notnull()
print('SE7 cells', int(se_mask.sum()))

base = djf.sel(wy=slice(1990,2019))   # DJF 1990-91 ... 2019-20
clim = base.mean('wy')
tierA = [1982,1997,2015,1991]; tierB = tierA+[1965,1972,1957]
pct = 100*djf/clim   # percent of normal per winter
def comp(yrs): return pct.sel(wy=yrs).mean('wy')
cA, cB = comp(tierA), comp(tierB)
signA = (pct.sel(wy=tierA)>100).sum('wy'); signB=(pct.sel(wy=tierB)>100).sum('wy')

# resampling: random sets of n non-analog winters (1895-2025), 5000 draws, two-sided
rng = np.random.default_rng(42)
pool = [y for y in djf.wy.values if y not in tierB]
P = pct.sel(wy=pool).values  # (n, lat, lon)
def pvals(comp_da, n, ndraw=5000):
    c = comp_da.values; ge = np.zeros_like(c); le=np.zeros_like(c)
    for _ in range(ndraw):
        r = P[rng.choice(len(pool), n, replace=False)].mean(0)
        ge += r>=c; le += r<=c
    p = 2*np.minimum(ge,le)/ndraw
    return xr.DataArray(np.minimum(p,1), coords=comp_da.coords)
pA, pB = pvals(cA,4), pvals(cB,7)
def fdr(p, m, alpha=0.10):
    v = p.values[m.values]; v = v[np.isfinite(v)]; s=np.sort(v); n=len(s)
    ok = s <= alpha*np.arange(1,n+1)/n
    return s[ok].max() if ok.any() else 0.0
thrA, thrB = fdr(pA, se_mask), fdr(pB, se_mask)
w = np.cos(np.deg2rad(djf.lat))
def aavg(da, m=se_mask): return float(da.where(m).weighted(w).mean(['lat','lon']))
# --- (original cell 9 failed at its summary print; the rerun of that print, original cell 10, follows) ---
def frac(cond): return float(cond.where(se_mask).sum()/se_mask.sum())
for nm,c,sg,p,thr,n in [('A (4)',cA,signA,pA,thrA,4),('B (7)',cB,signB,pB,thrB,7)]:
    print(f"{nm}: SE7 mean {aavg(c):.0f}% of normal | cells >100%: {frac(c>100):.2f} | all {n} wetter: {frac(sg==n):.2f} | p<0.05: {frac(p<0.05):.2f} | FDR(0.10) thr {thr:.4f} sig frac {frac(p<=thr) if thr>0 else 0:.2f}")
for s_ in SE7:
    m = mask3d.sel(region=st.map_keys(s_)) & se_mask
    print(f"{s_:15s} A {aavg(cA,m):4.0f}%  B {aavg(cB,m):4.0f}%  " + ' '.join(f"{y}:{aavg(pct.sel(wy=y),m):.0f}" for y in tierB))
print('SE7 per event', {y: round(aavg(pct.sel(wy=y))) for y in tierB})

# %%
# [original cell 11] regional series, ranks, strength-rainfall regressions, trend check
from scipy import stats
roni = pd.read_csv('RONI.ascii.txt', sep=r'\s+') if False else None
import shutil, os
shutil.copy('/'.join(os.getcwd().split('/'))+'/RONI.ascii.txt','RONI.ascii.txt') if not os.path.exists('RONI.ascii.txt') else None
roni = pd.read_csv('RONI.ascii.txt', sep=r'\s+')
djf_roni = roni[roni.SEAS=='DJF'].set_index('YR').ANOM; djf_roni.index = djf_roni.index-1  # label by Dec year
fl_m = mask3d.sel(region=st.map_keys('Florida')) & se_mask
tn_m = mask3d.sel(region=st.map_keys('Tennessee')) & se_mask
def series(m):
    return (pct.where(m).weighted(w).mean(['lat','lon'])).to_series()
reg = pd.DataFrame({'SE7':series(se_mask),'Florida':series(fl_m),'Tennessee':series(tn_m)})
reg['RONI_DJF'] = djf_roni.reindex(reg.index)
reg.index.name='winter_dec_year'
reg.to_csv('se_djf_pct_normal_by_winter.csv')
# ranks among 1895-2025 winters (1 = wettest)
rk = reg[['SE7','Florida','Tennessee']].rank(ascending=False).astype(int)
N=len(reg); print('N winters', N)
print(rk.loc[tierB].assign(**{f'{c}_pct':reg.loc[tierB,c].round(0) for c in ['SE7','Florida']}))
# regression 1950-2025
d = reg.dropna()
for col in ['SE7','Florida','Tennessee']:
    lr = stats.linregress(d.RONI_DJF, d[col]); 
    ep = d[d.RONI_DJF>=0.5]; lr2 = stats.linregress(ep.RONI_DJF, ep[col])
    sp = stats.spearmanr(d.RONI_DJF, d[col])
    print(f"{col}: all n={len(d)} slope {lr.slope:.1f}%/°C r={lr.rvalue:.2f} p={lr.pvalue:.1g} | El Niño only n={len(ep)} slope {lr2.slope:.1f} r={lr2.rvalue:.2f} p={lr2.pvalue:.2g}")
# trend in SE7 & FL
for col in ['SE7','Florida']:
    tr = stats.linregress(reg.index, reg[col]); tr2=stats.linregress(reg.loc[1951:].index, reg.loc[1951:,col])
    print(col,'trend 1895-2025 %.2f %%/decade p=%.2g; 1951-2025 %.2f p=%.2g'%(tr.slope*10,tr.pvalue,tr2.slope*10,tr2.pvalue))
print('2025-26 SE7/FL', reg.loc[2025].round(1).to_dict())

# %% [markdown]
# ## 4. Analysis figures (fig1, fig2, fig3)

# %%
# [replaces original cells 12-13]
from plot_style import apply_figure_style, panel_letter   # replaces the in-session helper library (same settings)

# %%
# [original cell 14] fig1 first draft
import matplotlib as mpl, matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm, ListedColormap
apply_figure_style(sizes=(8,7,6))
geoms = st.polygons
nbr = ['Louisiana','Arkansas','Kentucky','Virginia','Missouri','Texas','Oklahoma','Illinois','Indiana','Ohio','West Virginia','Maryland','Delaware']
def outlines(ax):
    for n in SE7+nbr:
        g = geoms[st.map_keys(n)]
        for poly in (g.geoms if g.geom_type=='MultiPolygon' else [g]):
            x,y = poly.exterior.xy
            ax.plot(x,y,color='k' if n in SE7 else '0.7', lw=0.5 if n in SE7 else 0.4, zorder=3)
    ax.set_xlim(-91.8,-75.2); ax.set_ylim(24.4,37.0); ax.set_aspect(1/np.cos(np.deg2rad(31)))
    ax.set_xticks([-90,-85,-80]); ax.set_xticklabels(['90°W','85°W','80°W'])
    ax.set_yticks([25,30,35]); ax.set_yticklabels(['25°N','30°N','35°N'])
lev = [40,60,75,90,110,125,150,175,200,250]
cm_ = plt.get_cmap('BrBG', len(lev)+1); cols = cm_(np.arange(len(lev)+1))
cmap = ListedColormap(cols[1:-1]); cmap.set_under(cols[0]); cmap.set_over(cols[-1])
norm = BoundaryNorm(lev, cmap.N)
def stipple(ax, p, thr, step=6):
    sig = (p<=thr)&se_mask
    s = sig.isel(lat=slice(None,None,step), lon=slice(None,None,step))
    yy,xx = np.meshgrid(s.lat, s.lon, indexing='ij')
    ax.scatter(xx[s.values], yy[s.values], s=0.6, c='k', lw=0, zorder=4)

fig, axs = plt.subplots(2,2, figsize=(7.2,5.6), constrained_layout=True)
titles = ['Top 4 analogs (peak RONI ≥ 2.0 °C)','All 7 analogs (peak RONI ≥ 1.85 °C)']
for j,(c,p,thr,sg,n) in enumerate([(cA,pA,thrA,signA,4),(cB,pB,thrB,signB,7)]):
    ax=axs[0,j]
    im = ax.pcolormesh(c.lon,c.lat,c.where(se_mask),cmap=cmap,norm=norm,shading='auto',rasterized=True)
    stipple(ax,p,thr); outlines(ax); ax.set_title(titles[j], loc='left')
    ax.text(0.03,0.04,f"7-state mean {aavg(c):.0f}%", transform=ax.transAxes, fontsize=7)
    ax=axs[1,j]
    scm = ListedColormap(plt.get_cmap('PuOr_r')(np.linspace(0.05,0.95,n+1)))
    im2 = ax.pcolormesh(sg.lon,sg.lat,sg.where(se_mask),cmap=scm,norm=BoundaryNorm(np.arange(-0.5,n+1),n+1),shading='auto',rasterized=True)
    outlines(ax); ax.set_title(f'Winters wetter than normal, out of {n}', loc='left')
    cb2=fig.colorbar(im2, ax=ax, shrink=0.8, ticks=range(n+1)); cb2.set_label('number of analog winters')
cb=fig.colorbar(im, ax=axs[0,:], shrink=0.8, extend='both', ticks=lev); cb.set_label('DJF precipitation, % of 1991–2020 normal')
for ax,l in zip(axs.flat,'abcd'): panel_letter(ax,l)
for ax in axs[:,1]: ax.set_yticklabels([])
for ax in axs[0,:]: ax.set_xticklabels([])
fig.savefig('fig1_composite_signcount.png', dpi=300)
print(thrA, thrB)

# %%
# [original cell 15] fig1 final (sign-count panels re-coloured)
for j,(sg,n) in enumerate([(signA,4),(signB,7)]):
    ax=axs[1,j]
    for coll in list(ax.collections): coll.remove()
    scm = ListedColormap(plt.get_cmap('BrBG')(np.linspace(0.12,0.92,n+1)))
    im2 = ax.pcolormesh(sg.lon,sg.lat,sg.where(se_mask),cmap=scm,norm=BoundaryNorm(np.arange(-0.5,n+1),n+1),shading='auto',rasterized=True)
# replace colorbars of row 2
for cbax in [a for a in fig.axes if a not in axs.flat]:
    pass
fig.clf()
fig, axs = plt.subplots(2,2, figsize=(7.2,5.6), constrained_layout=True)
for j,(c,p,thr,sg,n) in enumerate([(cA,pA,thrA,signA,4),(cB,pB,thrB,signB,7)]):
    ax=axs[0,j]
    im = ax.pcolormesh(c.lon,c.lat,c.where(se_mask),cmap=cmap,norm=norm,shading='auto',rasterized=True)
    stipple(ax,p,thr); outlines(ax); ax.set_title(titles[j], loc='left')
    ax.text(0.03,0.04,f"7-state mean {aavg(c):.0f}%", transform=ax.transAxes, fontsize=7)
    ax=axs[1,j]
    scm = ListedColormap(plt.get_cmap('BrBG')(np.linspace(0.12,0.92,n+1)))
    im2 = ax.pcolormesh(sg.lon,sg.lat,sg.where(se_mask),cmap=scm,norm=BoundaryNorm(np.arange(-0.5,n+1),n+1),shading='auto',rasterized=True)
    outlines(ax); ax.set_title(f'Winters wetter than normal, out of {n}', loc='left')
    cb2=fig.colorbar(im2, ax=ax, shrink=0.8, ticks=range(n+1)); cb2.set_label('number of analog winters')
cb=fig.colorbar(im, ax=axs[0,:], shrink=0.8, extend='both', ticks=lev); cb.set_label('DJF precipitation, % of 1991–2020 normal')
for ax,l in zip(axs.flat,'abcd'): panel_letter(ax,l)
for ax in axs[:,1]: ax.set_yticklabels([])
for ax in axs[0,:]: ax.set_xticklabels([])
fig.savefig('fig1_composite_signcount.png', dpi=300)

# %%
# [original cell 16] fig2 and fig3 first drafts
peak = {1982:2.40,1997:2.28,2015:2.25,1991:2.12,1965:1.99,1972:1.97,1957:1.89}  # from el_nino_event_ranking_roni_oni.csv
fig2, axs2 = plt.subplots(2,4, figsize=(7.2,4.4), constrained_layout=True)
for k,y in enumerate(tierB):
    ax = axs2.flat[k]; v = pct.sel(wy=y)
    im = ax.pcolormesh(v.lon,v.lat,v.where(se_mask),cmap=cmap,norm=norm,shading='auto',rasterized=True)
    outlines(ax); ax.set_title(f"{y}–{str(y+1)[-2:]}  (RONI {peak[y]:.2f})", loc='left', fontsize=7)
    ax.text(0.03,0.04,f"7-state {reg.loc[y,'SE7']:.0f}% (rank {rk.loc[y,'SE7']}/{N})\nFlorida {reg.loc[y,'Florida']:.0f}% (rank {rk.loc[y,'Florida']}/{N})",
            transform=ax.transAxes, fontsize=6)
    if k%4: ax.set_yticklabels([])
    if k<3: ax.set_xticklabels([])
axs2.flat[-1].axis('off')
cb=fig2.colorbar(im, ax=axs2.flat[-1], location='left', shrink=0.9, extend='both', ticks=lev, fraction=0.25)
cb.set_label('DJF precipitation, % of 1991–2020 normal')
fig2.savefig('fig2_per_event_maps.png', dpi=300)

# Fig 3: scatter
fig3, axs3 = plt.subplots(1,3, figsize=(7.2,2.7), sharey=False, constrained_layout=True)
d = reg.dropna(); preds={}
for ax,col in zip(axs3,['SE7','Florida','Tennessee']):
    other = d[~d.index.isin(tierB)]
    ax.scatter(other.RONI_DJF, other[col], s=10, c='0.6', lw=0, label='other winters 1949–2024')
    ax.scatter(d.loc[[y for y in tierB if y not in tierA],'RONI_DJF'], d.loc[[y for y in tierB if y not in tierA],col], s=18, facecolor='none', edgecolor='#1b7f79', lw=1, label='analogs, peak 1.85–2.0 °C')
    ax.scatter(d.loc[tierA,'RONI_DJF'], d.loc[tierA,col], s=22, c='#1b7f79', lw=0, label='analogs, peak ≥ 2.0 °C')
    # El Niño-only linear fit with 80% prediction interval
    ep = d[d.RONI_DJF>=0.5]; X=ep.RONI_DJF.values; Y=ep[col].values
    lr = stats.linregress(X,Y); xs=np.linspace(0.5,2.7,50); yh=lr.intercept+lr.slope*xs
    n_=len(X); s=np.sqrt(np.sum((Y-(lr.intercept+lr.slope*X))**2)/(n_-2))
    se = s*np.sqrt(1+1/n_+(xs-X.mean())**2/np.sum((X-X.mean())**2)); tq=stats.t.ppf(0.9,n_-2)
    ax.plot(xs,yh,color='k',lw=0.8); ax.fill_between(xs,yh-tq*se,yh+tq*se,color='k',alpha=0.08,lw=0)
    ax.axvspan(2.0,2.5,color='#e08214',alpha=0.15,lw=0)
    ax.axhline(100,color='0.3',lw=0.5,ls=':')
    for y in tierA: ax.annotate(f"{str(y)[-2:]}–{str(y+1)[-2:]}",(d.loc[y,'RONI_DJF'],d.loc[y,col]),xytext=(-3,3),textcoords='offset points',fontsize=6,ha='right')
    for xv in (2.0,2.5):
        i=np.argmin(abs(xs-xv)); preds[(col,xv)]=(yh[i],yh[i]-tq*se[i],yh[i]+tq*se[i])
    ax.set_title({'SE7':'7-state average','Florida':'Florida','Tennessee':'Tennessee'}[col], loc='left')
    ax.set_xlabel('DJF RONI (°C)'); ax.margins(0.04)
axs3[0].set_ylabel('DJF precipitation, % of normal')
axs3[1].text(2.25, axs3[1].get_ylim()[1]*0.97, '2026–27\nforecast\nrange', ha='center', va='top', fontsize=6, color='#a3520c')
axs3[0].legend(loc='upper left', fontsize=6, handletextpad=0.2)
for ax,l in zip(axs3,'abc'): panel_letter(ax,l)
fig3.savefig('fig3_roni_vs_rainfall.png', dpi=300)
for k,v in preds.items(): print(k, [round(x) for x in v])

# %%
# [original cell 17] fig2 and fig3 layout fixes
plt.close('all')
fig2, axs2 = plt.subplots(2,4, figsize=(7.2,4.3), constrained_layout=True)
for k,y in enumerate(tierB):
    ax = axs2.flat[k]; v = pct.sel(wy=y)
    im = ax.pcolormesh(v.lon,v.lat,v.where(se_mask),cmap=cmap,norm=norm,shading='auto',rasterized=True)
    outlines(ax); ax.set_title(f"{y}–{str(y+1)[-2:]}, peak RONI {peak[y]:.2f} °C", loc='left', fontsize=7)
    ax.text(0.02,0.03,f"7 states: {reg.loc[y,'SE7']:.0f}% (#{rk.loc[y,'SE7']})\nFlorida: {reg.loc[y,'Florida']:.0f}% (#{rk.loc[y,'Florida']})",
            transform=ax.transAxes, fontsize=6, va='bottom', bbox=dict(fc='white', ec='none', alpha=0.85, pad=1))
    ax.set_xlim(-94.5,-75.2)
    if k%4: ax.set_yticklabels([])
    if k<4 and k!=3: ax.set_xticklabels([])
ax=axs2.flat[-1]; ax.set_visible(False)
cb=fig2.colorbar(im, ax=list(axs2.flat[:7]), location='right', shrink=0.7, extend='both', ticks=lev)
cb.set_label('DJF precipitation, % of 1991–2020 normal')
fig2.savefig('fig2_per_event_maps.png', dpi=300)

fig3, axs3 = plt.subplots(1,3, figsize=(7.2,2.7), constrained_layout=True)
for ax,col in zip(axs3,['SE7','Florida','Tennessee']):
    other = d[~d.index.isin(tierB)]; tb=[y for y in tierB if y not in tierA]
    ax.scatter(other.RONI_DJF, other[col], s=10, c='0.6', lw=0, label='other winters, 1949–50 to 2025–26')
    ax.scatter(d.loc[tb,'RONI_DJF'], d.loc[tb,col], s=18, facecolor='none', edgecolor='#1b7f79', lw=1, label='analogs, peak RONI 1.85–2.0 °C')
    ax.scatter(d.loc[tierA,'RONI_DJF'], d.loc[tierA,col], s=22, c='#1b7f79', lw=0, label='analogs, peak RONI ≥ 2.0 °C')
    ep = d[d.RONI_DJF>=0.5]; X=ep.RONI_DJF.values; Y=ep[col].values
    lr = stats.linregress(X,Y); xs=np.linspace(0.5,2.7,50); yh=lr.intercept+lr.slope*xs
    n_=len(X); s=np.sqrt(np.sum((Y-(lr.intercept+lr.slope*X))**2)/(n_-2))
    se = s*np.sqrt(1+1/n_+(xs-X.mean())**2/np.sum((X-X.mean())**2)); tq=stats.t.ppf(0.9,n_-2)
    ax.plot(xs,yh,color='k',lw=0.8); ax.fill_between(xs,yh-tq*se,yh+tq*se,color='k',alpha=0.08,lw=0)
    ax.axvspan(2.0,2.5,color='#e08214',alpha=0.15,lw=0); ax.axhline(100,color='0.3',lw=0.5,ls=':')
    if col!='Tennessee':
        for y in tierA: ax.annotate(f"{str(y)[-2:]}–{str(y+1)[-2:]}",(d.loc[y,'RONI_DJF'],d.loc[y,col]),xytext=(-4,2),textcoords='offset points',fontsize=6,ha='right')
    ax.set_title({'SE7':'7-state average','Florida':'Florida','Tennessee':'Tennessee'}[col]+f"  (El Niño-winter slope {lr.slope:+.0f} %/°C)", loc='left', fontsize=7)
    ax.set_xlabel('DJF RONI (°C)'); ax.margins(0.04)
axs3[0].set_ylabel('DJF precipitation, % of normal')
yl=axs3[1].get_ylim(); axs3[1].text(2.25, yl[0]+0.03*(yl[1]-yl[0]), '2026–27\nforecast', ha='center', va='bottom', fontsize=6, color='#a3520c')
axs3[0].legend(loc='upper left', fontsize=6, handletextpad=0.2)
for ax,l in zip(axs3,'abc'): panel_letter(ax,l)
fig3.savefig('fig3_roni_vs_rainfall.png', dpi=300)

# %%
# [original cell 18] fig2 and fig3 final
fig2.set_size_inches(7.2,3.5); fig2.savefig('fig2_per_event_maps.png', dpi=300)
for ax,col in zip(axs3,['SE7','Florida','Tennessee']):
    t = ax.get_title(loc='left'); name, slope = t.split('  (')
    ax.set_title(name, loc='left', fontsize=8)
    ax.text(0.98,0.03,'El Niño-winter fit:\n'+slope.rstrip(')').replace('El Niño-winter slope ',''), transform=ax.transAxes, ha='right', va='bottom', fontsize=6)
axs3[0].get_legend().remove()
h,l = axs3[0].get_legend_handles_labels()
fig3.legend(h,l,loc='outside lower center', ncol=3, fontsize=6, frameon=False)
fig3.set_size_inches(7.2,3.0)
# move forecast text in Florida panel away from slope text
for t in axs3[1].texts:
    if t.get_text().startswith('2026'): t.set_position((2.25, 240)); t.set_va('top'); t.set_ha('left') ; t.set_x(2.52)
fig3.savefig('fig3_roni_vs_rainfall.png', dpi=300)

# %%
# [original cell 19] save composites NetCDF and regional CSV
out = xr.Dataset({'pct_normal_top4':cA.where(se_mask),'pct_normal_all7':cB.where(se_mask),
                  'p_top4':pA.where(se_mask),'p_all7':pB.where(se_mask),
                  'n_wetter_top4':signA.where(se_mask),'n_wetter_all7':signB.where(se_mask),
                  'clim_djf_mm_1991_2020':clim.where(se_mask)})
out.attrs = dict(source='NOAA nClimGrid monthly prcp', season='DJF', top4='1982-83,1997-98,2015-16,1991-92',
                 all7='top4 + 1965-66,1972-73,1957-58', test='5000 random draws of non-analog winters 1895-2025; FDR alpha=0.10 thresholds top4 %.4f all7 %.4f'%(thrA,thrB))
out.to_netcdf('se_strong_elnino_djf_composites.nc')
reg.round(2).to_csv('se_djf_pct_normal_by_winter.csv')
import os; print({f: os.path.getsize(f)//1024 for f in ['se_strong_elnino_djf_composites.nc','se_djf_pct_normal_by_winter.csv']})

# %% [markdown]
# ## 5. 48-state comparison (California vs Florida) and hook map

# %%
# [original cell 20] CONUS composites and statewide table -> conus_state_strong_elnino_djf.csv
t = pd.to_datetime(ds.time.values); wyall = np.where(t.month==12, t.year, t.year-1)
keep = np.isin(t.month,[12,1,2]) & np.isin(wyall, list(range(1990,2020))+tierB)
P_ = ds.prcp.isel(time=np.where(keep)[0]).load().assign_coords(wy=('time', wyall[keep]))
djf_us = P_.groupby('wy').sum('time', min_count=3)
clim_us = djf_us.sel(wy=slice(1990,2019)).mean('wy')
pct_us = 100*djf_us/clim_us
cA_us = pct_us.sel(wy=tierA).mean('wy'); cB_us = pct_us.sel(wy=tierB).mean('wy')
m3 = st.mask_3D(ds.lon, ds.lat)
wl = np.cos(np.deg2rad(ds.lat))
rows=[]
for k in m3.region.values:
    m = m3.sel(region=k) & cA_us.notnull()
    if int(m.sum())<50: continue
    f = lambda da: float(da.where(m).weighted(wl).mean(['lat','lon']))
    rows.append(dict(state=st[k].name, top4=f(cA_us), all7=f(cB_us),
                     clim_mm=f(clim_us), **{str(y):f(pct_us.sel(wy=y)) for y in tierA},
                     extra_mm_top4=f(cA_us/100*clim_us - clim_us)))
us = pd.DataFrame(rows).set_index('state').sort_values('top4', ascending=False).round(0)
us.to_csv('conus_state_strong_elnino_djf.csv')
print(us.head(12).to_string()); print(us.loc[['California','Arizona','Texas','Louisiana','Oregon','Washington']].to_string())
print('rank of FL by top4:', list(us.index).index('Florida')+1, 'CA:', list(us.index).index('California')+1, 'of', len(us))
print('FL wetter than CA in events:', {y: (us.loc['Florida',str(y)], us.loc['California',str(y)]) for y in tierA})

# %%
# [original cell 21] fig_hook_conus.png
plt.close('all')
figH, axH = plt.subplots(1,2, figsize=(7.2,2.6), constrained_layout=True)
def us_outline(ax):
    for k in m3.region.values:
        g = geoms[k]
        if st[k].name in ('Alaska','Hawaii'): continue
        for poly in (g.geoms if g.geom_type=='MultiPolygon' else [g]):
            x,y = poly.exterior.xy; ax.plot(x,y,color='0.35',lw=0.25)
    ax.set_xlim(-125,-66.5); ax.set_ylim(24.3,49.5); ax.set_aspect(1/np.cos(np.deg2rad(37))); ax.axis('off')
crs = 4
for ax,(da,ttl) in zip(axH,[(pct_us.sel(wy=2015),'2015–16 "Godzilla" El Niño'),(cA_us,'Average of the 4 strongest El Niños')]):
    v = da.isel(lat=slice(None,None,crs), lon=slice(None,None,crs))
    im = ax.pcolormesh(v.lon,v.lat,v,cmap=cmap,norm=norm,shading='auto',rasterized=True)
    us_outline(ax); ax.set_title(ttl, loc='left')
fl_y = {'2015':us.loc['Florida','2015'],'ca15':us.loc['California','2015']}
axH[0].text(-123.5,26.0,f"California {us.loc['California','2015']:.0f}%\nFlorida {us.loc['Florida','2015']:.0f}%",fontsize=7)
axH[1].text(-123.5,26.0,f"California {us.loc['California','top4']:.0f}%\nFlorida {us.loc['Florida','top4']:.0f}%",fontsize=7)
cb=figH.colorbar(im, ax=axH, shrink=0.85, extend='both', ticks=lev); cb.set_label('Dec–Feb rainfall, % of 1991–2020 normal')
for ax,l in zip(axH,'ab'): panel_letter(ax,l)
figH.savefig('fig_hook_conus.png', dpi=300)

# %% [markdown]
# ## 6. LinkedIn covers (1920x1080)

# %%
# [original cell 22] cover draft 1
import matplotlib.font_manager as fm, matplotlib.patheffects as pe
fams = {f.name for f in fm.fontManager.ttflist}
FONT = next((f for f in ['Inter','Helvetica Neue','Avenir Next','Helvetica','Arial','DejaVu Sans'] if f in fams))
print('font', FONT)
plt.rcdefaults(); plt.rcParams['font.family']=FONT
BG='#0f1623'; EDGE='#3a4556'; SUB='#c3c8d1'
def cover(field, nums, title, subtitle, foot, fname):
    fig = plt.figure(figsize=(19.2,10.8), dpi=100, facecolor=BG)
    fig.text(0.5,0.915,title,ha='center',va='center',color='white',fontsize=44,fontweight='bold')
    fig.text(0.5,0.845,subtitle,ha='center',va='center',color=SUB,fontsize=20)
    specs = [('California',(-119.4,37.3),'CALIFORNIA','where El Niño headlines go',[0.045,0.155,0.44,0.635]),
             ('Florida',(-83.4,27.9),'FLORIDA','where the extra rain went',[0.515,0.155,0.44,0.635])]
    for name,(lonc,latc),lab,sublab,rect in specs:
        ax = fig.add_axes(rect, facecolor='#141c2b')
        m = m3.sel(region=st.map_keys(name))
        sel = field.sel(lon=slice(lonc-9,lonc+9), lat=slice(latc+7,latc-7)); mm = m.sel(lon=sel.lon, lat=sel.lat)
        ax.pcolormesh(sel.lon,sel.lat,sel.where(~mm),cmap=cmap,norm=norm,shading='auto',alpha=0.28,rasterized=True)
        ax.pcolormesh(sel.lon,sel.lat,sel.where(mm),cmap=cmap,norm=norm,shading='auto',rasterized=True)
        for k in m3.region.values:
            g = geoms[k]
            for poly in (g.geoms if g.geom_type=='MultiPolygon' else [g]):
                x,y = poly.exterior.xy
                ax.plot(x,y,color='white',lw=2.2 if st[k].name==name else 0.6, alpha=1 if st[k].name==name else 0.45)
        # fit box to data aspect
        w_in, h_in = rect[2]*19.2, rect[3]*10.8; asp = 1/np.cos(np.deg2rad(latc))
        half_h = 6.1 if name=='California' else 4.0; half_w = half_h*(w_in/h_in)/asp
        ax.set_xlim(lonc-half_w+ (0 if name=='California' else 0.6), lonc+half_w+(0 if name=='California' else 0.6)); ax.set_ylim(latc-half_h,latc+half_h)
        ax.set_aspect(asp, adjustable='box'); ax.set_xticks([]); ax.set_yticks([])
        for s in ax.spines.values(): s.set_color(EDGE); s.set_linewidth(1.2)
        bb = dict(fc=BG, ec='none', alpha=0.85, pad=6)
        ax.text(0.03,0.95,lab,transform=ax.transAxes,color='white',fontsize=30,fontweight='bold',va='top',bbox=bb)
        ax.text(0.03,0.82,sublab,transform=ax.transAxes,color=SUB,fontsize=17,va='top',bbox=bb)
        ax.text(0.96,0.20,'winter rain vs normal, statewide',transform=ax.transAxes,color=SUB,fontsize=14,ha='right',va='bottom',bbox=dict(fc=BG,ec='none',alpha=0.85,pad=4))
        ax.text(0.96,0.04,f"{nums[name]:.0f}%",transform=ax.transAxes,color='white',fontsize=64,fontweight='bold',ha='right',va='bottom',bbox=dict(fc=BG,ec='none',alpha=0.9,pad=8))
    fig.text(0.045,0.085,foot,color=SUB,fontsize=15,va='center')
    cax = fig.add_axes([0.70,0.075,0.255,0.022])
    cb = fig.colorbar(mpl.cm.ScalarMappable(norm=norm,cmap=cmap),cax=cax,orientation='horizontal',extend='both',ticks=[60,90,110,150,200])
    cb.ax.tick_params(colors=SUB,labelsize=13,length=0); cb.outline.set_edgecolor(EDGE)
    cb.ax.set_xticklabels(['60%','90%','110%','150%','200%'])
    fig.text(0.70,0.115,'drier',color=SUB,fontsize=13); fig.text(0.955,0.115,'wetter',color=SUB,fontsize=13,ha='right')
    fig.savefig(fname, dpi=100, facecolor=BG); plt.close(fig)
foot = 'Dec–Feb rainfall as % of the 1991–2020 normal  ·  data: NOAA nClimGrid  ·  index: NOAA RONI'
cover(cA_us, {'California':us.loc['California','top4'],'Florida':us.loc['Florida','top4']},
      'California gets the El Niño headlines. Florida gets the rain.',
      'Winter rainfall in the 4 strongest El Niños on record (1982–83, 1991–92, 1997–98, 2015–16)',
      foot, 'cover_A_top4_1920x1080.png')
cover(pct_us.sel(wy=2015), {'California':us.loc['California','2015'],'Florida':us.loc['Florida','2015']},
      'California gets the El Niño headlines. Florida gets the rain.',
      'Winter 2015–16, the "Godzilla" El Niño billed as California\'s drought-breaker',
      foot, 'cover_B_godzilla_1920x1080.png')

# %%
# [original cell 23] cover draft 2
def cover(field, nums, title, subtitle, foot, fname):
    fig = plt.figure(figsize=(19.2,10.8), dpi=100, facecolor=BG)
    fig.text(0.5,0.915,title,ha='center',va='center',color='white',fontsize=44,fontweight='bold')
    fig.text(0.5,0.845,subtitle,ha='center',va='center',color=SUB,fontsize=20)
    specs = [('California',(-117.6,38.3),5.9,'CALIFORNIA','where the El Niño headlines go',[0.035,0.155,0.455,0.635]),
             ('Florida',(-82.9,28.6),4.6,'FLORIDA','where the extra rain goes',[0.51,0.155,0.455,0.635])]
    for name,(lonc,latc),half_h,lab,sublab,rect in specs:
        ax = fig.add_axes(rect, facecolor='#141c2b')
        m = m3.sel(region=st.map_keys(name))
        sel = field.sel(lon=slice(lonc-12,lonc+12), lat=slice(latc+8,latc-8)); mm = m.sel(lon=sel.lon, lat=sel.lat)
        ax.pcolormesh(sel.lon,sel.lat,sel.where(mm),cmap=cmap,norm=norm,shading='auto',rasterized=True)
        for k in m3.region.values:
            g = geoms[k]
            for poly in (g.geoms if g.geom_type=='MultiPolygon' else [g]):
                x,y = poly.exterior.xy
                ax.plot(x,y,color='white',lw=2.2 if st[k].name==name else 0.7, alpha=1 if st[k].name==name else 0.35)
        asp = 1/np.cos(np.deg2rad(latc)); w_in,h_in = rect[2]*19.2, rect[3]*10.8
        half_w = half_h*(w_in/h_in)/asp
        ax.set_xlim(lonc-half_w,lonc+half_w); ax.set_ylim(latc-half_h,latc+half_h); ax.set_aspect(asp, adjustable='box')
        ax.set_xticks([]); ax.set_yticks([])
        for s in ax.spines.values(): s.set_color(EDGE); s.set_linewidth(1.2)
        bb = dict(fc=BG, ec='none', alpha=0.85, pad=6)
        ax.text(0.025,0.955,lab,transform=ax.transAxes,color='white',fontsize=30,fontweight='bold',va='top',bbox=bb)
        ax.text(0.025,0.835,sublab,transform=ax.transAxes,color=SUB,fontsize=17,va='top',bbox=bb)
        ax.text(0.97,0.255,'winter rain vs normal, statewide',transform=ax.transAxes,color=SUB,fontsize=14,ha='right',va='bottom',bbox=dict(fc=BG,ec='none',alpha=0.85,pad=4))
        ax.text(0.97,0.04,f"{nums[name]:.0f}%",transform=ax.transAxes,color='white',fontsize=64,fontweight='bold',ha='right',va='bottom',bbox=dict(fc=BG,ec='none',alpha=0.9,pad=8))
    fig.text(0.035,0.085,foot,color=SUB,fontsize=15,va='center')
    cax = fig.add_axes([0.71,0.075,0.255,0.022])
    cb = fig.colorbar(mpl.cm.ScalarMappable(norm=norm,cmap=cmap),cax=cax,orientation='horizontal',extend='both',ticks=[60,90,150,200])
    cb.ax.tick_params(colors=SUB,labelsize=13,length=0); cb.outline.set_edgecolor(EDGE)
    cb.ax.set_xticklabels(['60%','90%','150%','200%'])
    fig.text(0.71,0.115,'drier',color=SUB,fontsize=13); fig.text(0.965,0.115,'wetter',color=SUB,fontsize=13,ha='right')
    fig.savefig(fname, dpi=100, facecolor=BG); plt.close(fig)
cover(cA_us, {'California':us.loc['California','top4'],'Florida':us.loc['Florida','top4']},
      'California gets the El Niño headlines. Florida gets the rain.',
      'Dec–Feb rainfall in the 4 strongest El Niños since 1950 (1982–83, 1991–92, 1997–98, 2015–16)',
      'colour: Dec–Feb rainfall as % of the 1991–2020 normal  ·  data: NOAA nClimGrid  ·  El Niño strength: NOAA RONI',
      'cover_A_top4_1920x1080.png')
cover(pct_us.sel(wy=2015), {'California':us.loc['California','2015'],'Florida':us.loc['Florida','2015']},
      'California gets the El Niño headlines. Florida gets the rain.',
      'Winter 2015–16: the "Godzilla" El Niño, billed as California\'s drought-breaker',
      'colour: Dec–Feb rainfall as % of the 1991–2020 normal  ·  data: NOAA nClimGrid',
      'cover_B_godzilla_1920x1080.png')

# %%
# [original cell 24] cover draft 3 (aspect fix)
import inspect, re
src = inspect.getsource(cover).replace("half_w = half_h*(w_in/h_in)/asp","half_w = half_h*(w_in/h_in)*asp")
src = src.replace("('California',(-117.6,38.3),5.9","('California',(-116.2,37.6),5.7").replace("('Florida',(-82.9,28.6),4.6","('Florida',(-82.6,28.2),4.1")
exec(src)
cover(cA_us, {'California':us.loc['California','top4'],'Florida':us.loc['Florida','top4']},
      'California gets the El Niño headlines. Florida gets the rain.',
      'Dec–Feb rainfall in the 4 strongest El Niños since 1950 (1982–83, 1991–92, 1997–98, 2015–16)',
      'colour: Dec–Feb rainfall as % of the 1991–2020 normal  ·  data: NOAA nClimGrid  ·  El Niño strength: NOAA RONI',
      'cover_A_top4_1920x1080.png')
cover(pct_us.sel(wy=2015), {'California':us.loc['California','2015'],'Florida':us.loc['Florida','2015']},
      'California gets the El Niño headlines. Florida gets the rain.',
      'Winter 2015–16: the "Godzilla" El Niño, billed as California\'s drought-breaker',
      'colour: Dec–Feb rainfall as % of the 1991–2020 normal  ·  data: NOAA nClimGrid',
      'cover_B_godzilla_1920x1080.png')

# %%
# [original cell 25] covers final: cover_A_top4 and cover_B_godzilla
src2 = src.replace("('California',(-116.2,37.6),5.7","('California',(-116.0,38.6),6.2").replace("('Florida',(-82.6,28.2),4.1","('Florida',(-82.6,28.6),4.4")
exec(src2)
cover(cA_us, {'California':us.loc['California','top4'],'Florida':us.loc['Florida','top4']},
      'California gets the El Niño headlines. Florida gets the rain.',
      'Dec–Feb rainfall in the 4 strongest El Niños since 1950 (1982–83, 1991–92, 1997–98, 2015–16)',
      'colour: Dec–Feb rainfall as % of the 1991–2020 normal  ·  data: NOAA nClimGrid  ·  El Niño strength: NOAA RONI',
      'cover_A_top4_1920x1080.png')
cover(pct_us.sel(wy=2015), {'California':us.loc['California','2015'],'Florida':us.loc['Florida','2015']},
      'California gets the El Niño headlines. Florida gets the rain.',
      'Winter 2015–16: the "Godzilla" El Niño, billed as California\'s drought-breaker',
      'colour: Dec–Feb rainfall as % of the 1991–2020 normal  ·  data: NOAA nClimGrid',
      'cover_B_godzilla_1920x1080.png')

# %% [markdown]
# ## 7. Numbers for the article and LinkedIn figures

# %%
# [original cell 26] South Florida, inch conversions, last winter, La Niña winters
fl = mask3d.sel(region=st.map_keys('Florida')) & se_mask
sfl = fl & (djf.lat < 28.0)
f = lambda da,m: float(da.where(m).weighted(w).mean(['lat','lon']))
print('South FL (<28N) top4 %:', round(f(cA,sfl)), ' per event', {y: round(f(pct.sel(wy=y),sfl)) for y in tierA})
print('FL clim mm', round(f(clim,fl)), 'in', round(f(clim,fl)/25.4,1), '| extra top4 mm', round(f(cA/100*clim-clim,fl)), 'in', round(f(cA/100*clim-clim,fl)/25.4,1))
print('South FL clim mm', round(f(clim,sfl)), 'in', round(f(clim,sfl)/25.4,1))
print('CA clim/extra in', round(us.loc['California','clim_mm']/25.4,1), round(us.loc['California','extra_mm_top4']/25.4,1))
fl97 = f(djf.sel(wy=1997),fl); print('FL 1997-98 total mm', round(fl97), 'in', round(fl97/25.4,1))
print('FL 2025-26 %', round(reg.loc[2025,'Florida']), 'rank dry (1=driest):', int(reg['Florida'].rank().loc[2025]), 'of', len(reg))
# La Nina side: strong La Nina DJF RONI <= -1
ln = reg[reg.RONI_DJF<=-1.0]; print('La Niña DJF RONI<=-1: n', len(ln), 'FL mean %', round(ln.Florida.mean()), 'SE7', round(ln.SE7.mean()), 'FL below normal in', int((ln.Florida<100).sum()))
# How often FL above normal in El Nino >=1 vs others
en = reg[reg.RONI_DJF>=1.0]; print('El Niño DJF RONI>=1: n',len(en),'FL >100 in', int((en.Florida>100).sum()))
print('FL fraction cells >100 top4', round(float(((cA>100)&fl).sum()/fl.sum()),2), ' >150', round(float(((cA>150)&fl).sum()/fl.sum()),2))

# %%
# [original cell 27] li_fig1, li_fig2, li_fig3 drafts
plt.rcdefaults(); apply_figure_style(sizes=(13,12,11)); plt.rcParams['font.family']=FONT
# ---- li_fig1: 2015-16 national map
fig, ax = plt.subplots(figsize=(10,5.6), constrained_layout=True)
v = pct_us.sel(wy=2015).isel(lat=slice(None,None,3), lon=slice(None,None,3))
im = ax.pcolormesh(v.lon,v.lat,v,cmap=cmap,norm=norm,shading='auto',rasterized=True); us_outline(ax)
ax.set_title('Winter 2015–16, the "Godzilla" El Niño: Dec–Feb rainfall vs normal', loc='left', fontsize=15)
ax.annotate(f"California {us.loc['California','2015']:.0f}%", xy=(-120.0,36.8), xytext=(-124.5,27.6), fontsize=15, fontweight='bold',
            arrowprops=dict(arrowstyle='-', color='0.3', lw=1))
ax.annotate(f"Florida {us.loc['Florida','2015']:.0f}%", xy=(-81.2,26.8), xytext=(-93.5,25.2), fontsize=15, fontweight='bold',
            arrowprops=dict(arrowstyle='-', color='0.3', lw=1))
cb = fig.colorbar(im, ax=ax, orientation='horizontal', shrink=0.55, pad=0.02, extend='both', ticks=[40,60,90,110,150,200,250])
cb.set_label('% of 1991–2020 normal  (brown = drier, green = wetter)')
fig.savefig('li_fig1_2015_16_conus.png', dpi=200); plt.close(fig)

# ---- li_fig2: Southeast top-4 composite + count
fig, axs = plt.subplots(1,2, figsize=(11,5.4), constrained_layout=True)
ax=axs[0]; im=ax.pcolormesh(cA.lon,cA.lat,cA.where(se_mask),cmap=cmap,norm=norm,shading='auto',rasterized=True)
stipple(ax,pA,thrA,step=7); outlines(ax); ax.set_xticks([]); ax.set_yticks([])
ax.set_title('Average of the 4 strongest El Niños', loc='left')
ax.text(0.03,0.04,f"7-state average {aavg(cA):.0f}%\nSouth Florida ~{f(cA,sfl):.0f}%", transform=ax.transAxes, fontsize=12)
cb=fig.colorbar(im, ax=ax, orientation='horizontal', shrink=0.85, pad=0.02, extend='both', ticks=[60,90,110,150,200]); cb.set_label('Dec–Feb rainfall, % of normal')
ax=axs[1]; scm = ListedColormap(plt.get_cmap('BrBG')(np.linspace(0.12,0.92,5)))
im2=ax.pcolormesh(signA.lon,signA.lat,signA.where(se_mask),cmap=scm,norm=BoundaryNorm(np.arange(-0.5,5),5),shading='auto',rasterized=True)
outlines(ax); ax.set_xticks([]); ax.set_yticks([]); ax.set_title('How many of the 4 were wetter than normal', loc='left')
cb2=fig.colorbar(im2, ax=ax, orientation='horizontal', shrink=0.85, pad=0.02, ticks=range(5)); cb2.set_label('number of the 4 winters')
for a in axs:
    for s in a.spines.values(): s.set_visible(False)
fig.savefig('li_fig2_southeast_top4.png', dpi=200); plt.close(fig)

# ---- li_fig3: Florida scatter
fig, ax = plt.subplots(figsize=(9,5.6), constrained_layout=True)
col='Florida'; other=d[~d.index.isin(tierA)]
ax.scatter(other.RONI_DJF, other[col], s=34, c='0.65', lw=0, label='other winters, 1949–50 to 2025–26')
ax.scatter(d.loc[tierA,'RONI_DJF'], d.loc[tierA,col], s=60, c='#1b7f79', lw=0, label='4 strongest El Niños')
ep=d[d.RONI_DJF>=0.5]; X=ep.RONI_DJF.values; Y=ep[col].values; lr=stats.linregress(X,Y)
xs=np.linspace(0.5,2.7,50); yh=lr.intercept+lr.slope*xs; n_=len(X); s_=np.sqrt(np.sum((Y-(lr.intercept+lr.slope*X))**2)/(n_-2))
se_=s_*np.sqrt(1+1/n_+(xs-X.mean())**2/np.sum((X-X.mean())**2)); tq=stats.t.ppf(0.9,n_-2)
ax.plot(xs,yh,color='k',lw=1.2); ax.fill_between(xs,yh-tq*se_,yh+tq*se_,color='k',alpha=0.08,lw=0)
ax.axvspan(2.0,2.5,color='#e08214',alpha=0.18,lw=0); ax.axhline(100,color='0.3',lw=0.8,ls=':')
ax.text(2.25, 30, 'this\nwinter?', ha='center', va='bottom', fontsize=12, color='#a3520c')
for y in tierA: ax.annotate(f"{y}–{str(y+1)[-2:]}",(d.loc[y,'RONI_DJF'],d.loc[y,col]),xytext=(-7,3),textcoords='offset points',fontsize=11,ha='right')
ax.annotate('2025–26\n(La Niña)', (d.loc[2025,'RONI_DJF'], d.loc[2025,col]), xytext=(-1.75, 30), fontsize=11, arrowprops=dict(arrowstyle='-',color='0.4',lw=0.8))
ax.text(-1.9, 100, 'normal', fontsize=11, va='bottom', color='0.3')
ax.set_xlabel('El Niño strength, Dec–Feb RONI (°C)   ← La Niña | El Niño →'); ax.set_ylabel('Florida Dec–Feb rainfall, % of normal')
ax.set_title('Stronger El Niño, wetter Florida winter', loc='left')
ax.legend(loc='upper left', frameon=False); ax.set_ylim(25,255); ax.margins(x=0.03)
fig.savefig('li_fig3_florida_strength.png', dpi=200); plt.close(fig)
print('saved')

# %%
# [original cell 28] li_fig3 final
fig, ax = plt.subplots(figsize=(9,5.6), constrained_layout=True)
ax.scatter(other.RONI_DJF, other[col], s=34, c='0.65', lw=0, label='other winters, 1949–50 to 2025–26')
ax.scatter(d.loc[tierA,'RONI_DJF'], d.loc[tierA,col], s=60, c='#1b7f79', lw=0, label='4 strongest El Niños')
ax.plot(xs,yh,color='k',lw=1.2); ax.fill_between(xs,yh-tq*se_,yh+tq*se_,color='k',alpha=0.08,lw=0)
ax.axvspan(2.0,2.5,color='#e08214',alpha=0.18,lw=0); ax.axhline(100,color='0.3',lw=0.8,ls=':')
ax.text(2.25, 30, 'this\nwinter?', ha='center', va='bottom', fontsize=12, color='#a3520c')
for y in tierA:
    dx = 7 if y==2015 else -7
    ax.annotate(f"{y}–{str(y+1)[-2:]}",(d.loc[y,'RONI_DJF'],d.loc[y,col]),xytext=(dx,-14 if y==2015 else 3),textcoords='offset points',fontsize=11,ha='left' if y==2015 else 'right')
ax.annotate('2025–26\n(La Niña)', (d.loc[2025,'RONI_DJF'], d.loc[2025,col]), xytext=(-1.75, 30), fontsize=11, arrowprops=dict(arrowstyle='-',color='0.4',lw=0.8))
ax.text(-1.35, 102, 'normal', fontsize=11, va='bottom', color='0.3')
ax.set_xlabel('Dec–Feb RONI (°C):  negative = La Niña, positive = El Niño'); ax.set_ylabel('Florida Dec–Feb rainfall, % of normal')
ax.set_title('Stronger El Niño, wetter Florida winter', loc='left')
ax.legend(loc='upper left', frameon=False); ax.set_ylim(25,255); ax.margins(x=0.03)
fig.savefig('li_fig3_florida_strength.png', dpi=200); plt.close(fig)

# %% [markdown]
# ## 8. Jet stream animation (NCEP/NCAR Reanalysis 1, daily 200 hPa winds)

# %%
# [original cell 32] OPeNDAP access test (defines `base`)
base="https://psl.noaa.gov/thredds/dodsC/Datasets/ncep.reanalysis/Dailies/pressure/{v}.{y}.nc"
t0=__import__('time').time()
dsu = xr.open_dataset(base.format(v='uwnd',y=1997))
print(dsu)
x = dsu.uwnd.sel(level=200, lat=slice(60,5), lon=slice(180,340)).load()
print(x.shape, round(__import__('time').time()-t0,1),'s')

# %%
# [original cell 35] download 200 hPa u/v for 33 years (~10-20 min)
from concurrent.futures import ThreadPoolExecutor
import os, time
os.makedirs('data/ncep200', exist_ok=True)
years = [1982,1983] + list(range(1990,2021))
def get(args):
    v,y = args; fn=f'data/ncep200/{v}.{y}.nc'
    if os.path.exists(fn): return fn
    for k in range(3):
        try:
            da = xr.open_dataset(base.format(v=v,y=y))[v].sel(level=200, lat=slice(62,0), lon=slice(175,345)).load()
            da.to_netcdf(fn); return fn
        except Exception as e:
            err=str(e)[:100]; time.sleep(5)
    return 'FAIL '+fn+' '+err
t0=time.time()
with ThreadPoolExecutor(6) as ex: res=list(ex.map(get, [(v,y) for y in years for v in ('uwnd','vwnd')]))
print([r for r in res if r.startswith('FAIL')], len(res), round(time.time()-t0),'s')

# %%
# [original cell 38] 15-day running means, normal vs top-4 El Niño, Gulf/Florida box speeds
import glob
def load(v,y): return xr.open_dataarray(f'data/ncep200/{v}.{y}.nc')
def winter(y):
    out={}
    for v in ('uwnd','vwnd'):
        a = xr.concat([load(v,y), load(v,y+1)], 'time').sel(time=slice(f'{y}-10-17', f'{y+1}-04-14'))
        a = a.sel(time=~((a.time.dt.month==2)&(a.time.dt.day==29)))
        a = a.rolling(time=15, center=True).mean().sel(time=slice(f'{y}-11-01', f'{y+1}-03-31'))
        out[v]=a.values
    return out
wint = {y: winter(y) for y in list(range(1990,2020))+[1982]}
print({k: v['uwnd'].shape for k,v in list(wint.items())[:2]})
U = lambda ys: np.mean([wint[y]['uwnd'] for y in ys],0); V = lambda ys: np.mean([wint[y]['vwnd'] for y in ys],0)
clim_years = list(range(1990,2020))
Uc,Vc = U(clim_years),V(clim_years); Ue,Ve = U(tierA),V(tierA)
ref = load('uwnd',1990); lat200, lon200 = ref.lat.values, ref.lon.values
days = pd.date_range('2001-11-01','2002-03-31')
spd_c, spd_e = np.hypot(Uc,Vc), np.hypot(Ue,Ve)
# Gulf/Florida box 25-32.5N, 92.5-77.5W  (lon 267.5-282.5)
bl = (lat200>=25)&(lat200<=32.5); bo=(lon200>=267.5)&(lon200<=282.5)
box_c = spd_c[:,bl][:,:,bo].mean((1,2)); box_e = spd_e[:,bl][:,:,bo].mean((1,2))
for dd in ['2001-11-15','2001-12-15','2002-01-15','2002-02-15','2002-03-15']:
    i = list(days).index(pd.Timestamp(dd)); print(dd[5:], f"normal {box_c[i]:.0f} m/s, El Niño {box_e[i]:.0f} m/s")
print('DJF mean box: normal %.1f, El Niño %.1f'%(box_c[30:120].mean(), box_e[30:120].mean()))
# latitude of max zonal wind along 85W (lon 275)
j = np.where(lon200==275)[0][0]
for nm,uu in [('normal',Uc),('El Niño',Ue)]:
    prof = uu[30:120,:,j].mean(0); print(nm,'max u along 85W: %.0f m/s at %.1fN'%(prof.max(), lat200[prof.argmax()]))

# %%
# [original cell 39] test frame
import imageio_ffmpeg; mpl.rcParams['animation.ffmpeg_path']=imageio_ffmpeg.get_ffmpeg_exe()
try:
    ctry = regionmask.defined_regions.natural_earth_v5_0_0.countries_50; print('countries ok', len(ctry))
except Exception as e: print('countries ERR', str(e)[:200]); ctry=None
plt.rcdefaults(); plt.rcParams['font.family']=FONT
lon_w = lon200-360  # -185..-15
sl_lat = (lat200>=10)&(lat200<=57.5); sl_lon=(lon_w>=-160)&(lon_w<=-55)
LAT, LON = lat200[sl_lat], lon_w[sl_lon]
def sub(a): return a[:, sl_lat][:,:,sl_lon]
Uc_s,Vc_s,Ue_s,Ve_s = map(sub,(Uc,Vc,Ue,Ve)); Sc_s, Se_s = np.hypot(Uc_s,Vc_s), np.hypot(Ue_s,Ve_s)
# interpolate to 1.25° for smoother shading
from scipy.ndimage import zoom
jetcmap = plt.get_cmap('magma').copy(); jetcmap.set_under((0,0,0,0))
jnorm = mpl.colors.Normalize(25, 65)
polys=[]
for reg in ([ctry] if ctry is not None else [])+[st]:
    for k in reg.numbers:
        g = reg[k].polygon
        for p in (g.geoms if g.geom_type=='MultiPolygon' else [g]):
            x,y = p.exterior.xy; x=np.array(x); y=np.array(y)
            if (x.max()<-165) or (x.min()>-50) or (y.max()<8) or (y.min()>60): continue
            polys.append((x,y))
print('polys', len(polys))
latc_ = np.deg2rad(33)
def draw_panel(ax, U_, V_, S_, i, label, sublab, boxval):
    ax.clear(); ax.set_facecolor('#141c2b')
    ax.pcolormesh(LON, LAT, S_[i], cmap=jetcmap, norm=jnorm, shading='gouraud', rasterized=True)
    for x,y in polys: ax.plot(x,y,color='white',lw=0.5,alpha=0.55)
    ax.streamplot(LON, LAT[::-1], U_[i][::-1], V_[i][::-1], color='white', density=1.1, linewidth=0.6, arrowsize=0.7)
    for c in ax.collections[-1:]: c.set_alpha(0.45)
    ax.plot([-92.5,-77.5,-77.5,-92.5,-92.5],[25,25,32.5,32.5,25], color='#7fe3d8', lw=1.6, ls='--')
    ax.set_xlim(-160,-55); ax.set_ylim(10,57.5); ax.set_aspect(1/np.cos(latc_)); ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values(): s.set_color(EDGE)
    bb=dict(fc=BG,ec='none',alpha=0.85,pad=5)
    ax.text(0.02,0.96,label,transform=ax.transAxes,color='white',fontsize=24,fontweight='bold',va='top',bbox=bb)
    ax.text(0.02,0.845,sublab,transform=ax.transAxes,color=SUB,fontsize=14,va='top',bbox=bb)
    ax.text(0.98,0.20,'jet speed over Gulf & Florida (dashed box)',transform=ax.transAxes,color=SUB,fontsize=12,ha='right',va='bottom',bbox=dict(fc=BG,ec='none',alpha=0.85,pad=3))
    ax.text(0.98,0.04,f"{boxval*2.237:.0f} mph",transform=ax.transAxes,color='white',fontsize=40,fontweight='bold',ha='right',va='bottom',bbox=dict(fc=BG,ec='none',alpha=0.9,pad=6))
fig = plt.figure(figsize=(19.2,10.8), dpi=100, facecolor=BG)
fig.text(0.5,0.925,'In strong El Niño winters, the jet stream dives south over Florida',ha='center',color='white',fontsize=38,fontweight='bold')
fig.text(0.5,0.865,'Winds about 7 miles up (200 hPa), smoothed over 15 days  ·  normal winter vs. the 4 strongest El Niños',ha='center',color=SUB,fontsize=18)
axL = fig.add_axes([0.03,0.15,0.46,0.68]); axR = fig.add_axes([0.51,0.15,0.46,0.68])
date_txt = fig.text(0.03,0.075,'',color='white',fontsize=30,fontweight='bold',va='center')
# timeline
axT = fig.add_axes([0.20,0.065,0.36,0.02], facecolor=BG); axT.set_xlim(0,150); axT.set_ylim(0,1); axT.axis('off')
for k,(m,dd) in enumerate([('Nov',0),('Dec',30),('Jan',61),('Feb',92),('Mar',120)]):
    axT.text(dd+2,1.6,m,color=SUB,fontsize=13,transform=axT.transData)
axT.add_patch(mpl.patches.Rectangle((0,0),150,1,color='#2a3446'))
prog = mpl.patches.Rectangle((0,0),0,1,color='#7fe3d8'); axT.add_patch(prog)
cax = fig.add_axes([0.71,0.07,0.255,0.022])
cb = fig.colorbar(mpl.cm.ScalarMappable(norm=jnorm,cmap=jetcmap),cax=cax,orientation='horizontal',extend='max',ticks=[25,35,45,55,65])
cb.ax.set_xticklabels([f"{t*2.237:.0f}" for t in [25,35,45,55,65]]); cb.ax.tick_params(colors=SUB,labelsize=13,length=0); cb.outline.set_edgecolor(EDGE)
fig.text(0.71,0.108,'wind speed (mph); calmer than ~55 mph not shaded',color=SUB,fontsize=13)
fig.text(0.03,0.025,'Data: NCEP/NCAR Reanalysis 1 (NOAA PSL), daily 200 hPa winds. Normal = 1990–91 to 2019–20 winters. El Niños: 1982–83, 1991–92, 1997–98, 2015–16.',color=SUB,fontsize=12)
def frame(i):
    draw_panel(axL, Uc_s,Vc_s,Sc_s,i,'NORMAL WINTER','1991–2020 average', box_c[i])
    draw_panel(axR, Ue_s,Ve_s,Se_s,i,'STRONG EL NIÑO','average of the 4 strongest', box_e[i])
    date_txt.set_text(days[i].strftime('%-d %b')); prog.set_width(i)
frame(list(days).index(pd.Timestamp('2002-01-20')))
fig.savefig('jet_test_frame.png', dpi=100, facecolor=BG)

# %%
# [original cell 40] full render -> jet_stream_elnino.mp4 / .gif, jet_frame_20jan.png
import imageio.v2 as iio
from PIL import Image
sl_lat = (lat200>=5)&(lat200<=60); LAT = lat200[sl_lat]
def sub(a): return a[:, sl_lat][:,:,sl_lon]
Uc_s,Vc_s,Ue_s,Ve_s = map(sub,(Uc,Vc,Ue,Ve)); Sc_s, Se_s = np.hypot(Uc_s,Vc_s)*2.237, np.hypot(Ue_s,Ve_s)*2.237
jnorm = mpl.colors.Normalize(55, 145)
def draw_panel(ax, U_, V_, S_, i, label, sublab, boxval):
    ax.clear(); ax.set_facecolor('#141c2b')
    ax.pcolormesh(LON, LAT, S_[i], cmap=jetcmap, norm=jnorm, shading='gouraud', rasterized=True)
    for x,y in polys: ax.plot(x,y,color='white',lw=0.5,alpha=0.55)
    sp = ax.streamplot(LON, LAT[::-1], U_[i][::-1], V_[i][::-1], color='white', density=1.1, linewidth=0.6, arrowsize=0.8)
    sp.lines.set_alpha(0.4); sp.arrows.set_alpha(0.6)
    ax.plot([-92.5,-77.5,-77.5,-92.5,-92.5],[25,25,32.5,32.5,25], color='#7fe3d8', lw=1.8, ls='--')
    ax.set_xlim(-160,-55); ax.set_ylim(5,60); ax.set_aspect(1/np.cos(latc_)); ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values(): s.set_color(EDGE)
    bb=dict(fc=BG,ec='none',alpha=0.85,pad=5)
    ax.text(0.02,0.965,label,transform=ax.transAxes,color='white',fontsize=26,fontweight='bold',va='top',bbox=bb)
    ax.text(0.02,0.87,sublab,transform=ax.transAxes,color=SUB,fontsize=15,va='top',bbox=bb)
    ax.text(0.98,0.175,'jet speed over the Gulf & Florida (dashed box)',transform=ax.transAxes,color=SUB,fontsize=13,ha='right',va='bottom',bbox=dict(fc=BG,ec='none',alpha=0.85,pad=3))
    ax.text(0.98,0.03,f"{boxval*2.237:.0f} mph",transform=ax.transAxes,color='white',fontsize=44,fontweight='bold',ha='right',va='bottom',bbox=dict(fc=BG,ec='none',alpha=0.9,pad=6))
plt.close('all')
fig = plt.figure(figsize=(19.2,10.8), dpi=100, facecolor=BG)
fig.text(0.5,0.935,'In strong El Niño winters, the jet stream shifts south and speeds up over Florida',ha='center',color='white',fontsize=34,fontweight='bold')
fig.text(0.5,0.88,'Winds about 7 miles up (200 hPa), 15-day averages  ·  normal winter vs. the 4 strongest El Niños',ha='center',color=SUB,fontsize=18)
axL = fig.add_axes([0.025,0.15,0.47,0.71]); axR = fig.add_axes([0.505,0.15,0.47,0.71])
date_txt = fig.text(0.035,0.085,'',color='white',fontsize=32,fontweight='bold',va='center')
axT = fig.add_axes([0.17,0.072,0.38,0.02], facecolor=BG); axT.set_xlim(0,150); axT.set_ylim(0,1); axT.axis('off')
for m,dd in [('Nov',0),('Dec',30),('Jan',61),('Feb',92),('Mar',120)]: axT.text(dd+2,1.6,m,color=SUB,fontsize=13)
axT.add_patch(mpl.patches.Rectangle((0,0),150,1,color='#2a3446')); prog = mpl.patches.Rectangle((0,0),0,1,color='#7fe3d8'); axT.add_patch(prog)
cax = fig.add_axes([0.71,0.075,0.255,0.022])
cb = fig.colorbar(mpl.cm.ScalarMappable(norm=jnorm,cmap=jetcmap),cax=cax,orientation='horizontal',extend='max',ticks=[60,80,100,120,140])
cb.ax.tick_params(colors=SUB,labelsize=13,length=0); cb.outline.set_edgecolor(EDGE)
fig.text(0.71,0.112,'wind speed (mph); below 55 mph not shaded',color=SUB,fontsize=13)
fig.text(0.035,0.025,'Data: NCEP/NCAR Reanalysis 1 (NOAA PSL), daily 200 hPa winds. Normal = winters 1990–91 to 2019–20. El Niños: 1982–83, 1991–92, 1997–98, 2015–16.',color=SUB,fontsize=12)
def frame(i):
    draw_panel(axL, Uc_s,Vc_s,Sc_s,i,'NORMAL WINTER','1991–2020 average', box_c[i])
    draw_panel(axR, Ue_s,Ve_s,Se_s,i,'STRONG EL NIÑO','average of the 4 strongest', box_e[i])
    date_txt.set_text(days[i].strftime('%-d %b')); prog.set_width(i)
mp4 = iio.get_writer('jet_stream_elnino.mp4', fps=10, codec='libx264', quality=8, macro_block_size=8, pixelformat='yuv420p')
gif_frames=[]
for i in range(len(days)):
    frame(i); fig.canvas.draw()
    img = np.asarray(fig.canvas.buffer_rgba())[:,:,:3]
    mp4.append_data(img)
    if i==len(days)-1:
        for _ in range(15): mp4.append_data(img)
    if i%2==0 or i==len(days)-1: gif_frames.append(Image.fromarray(img).resize((960,540), Image.LANCZOS))
    if i==list(days).index(pd.Timestamp('2002-01-20')): fig.savefig('jet_frame_20jan.png', dpi=100, facecolor=BG)
mp4.close()
pal = [f.convert('P', palette=Image.ADAPTIVE, colors=128) for f in gif_frames]
pal[0].save('jet_stream_elnino.gif', save_all=True, append_images=pal[1:], duration=[200]*(len(pal)-1)+[2000], loop=0, optimize=True)
print({f: round(os.path.getsize(f)/1e6,1) for f in ['jet_stream_elnino.mp4','jet_stream_elnino.gif','jet_frame_20jan.png']})
