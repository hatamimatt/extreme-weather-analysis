# prod/ — download and extraction scripts

Run from the repository root (scripts use `prod/...` and `out/...` relative paths).

| Script | Purpose |
|---|---|
| `common.py` | station list, needed hours, 8×8 window indexing around each gauge (`window_index`, `cut`, `neighborhood_masks`) |
| `shard_dl.py` | sharded, checkpointed downloader + window extraction for Stage IV, PERSIANN-CCS and CMORPH (h5py decoder) |
| `mrms_mp.py` | same for MRMS gauge-corrected / radar-only (IEM mtarchive) |
| `imerg_dl.py` | IMERG V07 Final half-hourly granules via GES DISC Cloud OPeNDAP |
| `nasa_od.py` | MERRA-2 and NLDAS-2 via Cloud OPeNDAP (`python prod/nasa_od.py merra2|nldas2`) |
| `edh_dl.py`, `edh_chunks.py`, `edh_chunks_2225.py` | ERA5 from DestinE Earth Data Hub zarr (token from `DESTINE_EDH_TOKEN`); the `_2225` variant fetches 2022–2025 |
| `style.py` | figure style helper used by the notebooks |
| `legacy/` | first single-process versions (superseded; kept for the record) |

Credentials are read from environment variables (`EARTHDATA_USER`, `EARTHDATA_PASS`, `DESTINE_EDH_TOKEN`); never hard-code them.
