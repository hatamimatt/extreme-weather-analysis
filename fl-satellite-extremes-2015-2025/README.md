# Florida extreme hourly rainfall: how well do satellite, radar and reanalysis products capture it? (2015–2025)

Event-by-event evaluation of nine gridded precipitation products against hourly rain gauges in Florida,
plus a case study of the Miami flash flood of 26 May 2020.

**Headline result (≥30 mm/h events, 3×3 pixels around each gauge):** satellites show some rain in 82–94% of
gauge extremes, but reach the gauge's intensity in only 2–6% (IMERG 2%, CMORPH 3%, PERSIANN-CCS 6%); Stage IV radar reaches 66%.
Full results: [`writing/report.md`](writing/report.md).

## What is evaluated

| Role | Dataset |
|---|---|
| Ground truth | NOAA GHCNh hourly gauges; 79 of 256 Florida stations valid (≥5 years with ≥30 complete 24-h days each) |
| Radar | MRMS MultiSensor/GaugeCorr QPE 1 h (gauge-corrected), MRMS RadarOnly QPE 1 h, NCEP Stage IV 1 h (IEM archive) |
| Satellite | IMERG V07 Final (half-hourly), CMORPH CDR 8 km/30 min, PERSIANN-CCS 0.04° hourly |
| Reanalysis / land data assimilation | ERA5 (CDS 2015–2021, DestinE Earth Data Hub 2022–2025), MERRA-2 M2T1NXFLX PRECTOTCORR, NLDAS-2 FORA |

Extreme thresholds: ≥20, 30, 40, 50 mm/h. Neighbourhoods: station pixel (N1), 2×2 (N4), 3×3 (N9), 4×4 (N16).
2×2 and 4×4 blocks are the blocks whose centre is closest to the gauge; 3×3 is centred on the gauge pixel.

## Repository layout

```
notebooks/   session code, in execution order, split by stage (see table below)
prod/        download/extraction scripts used by the notebooks (final versions)
prod/legacy/ first versions superseded by prod/shard_dl.py and prod/mrms_mp.py
out/         derived data: station lists, events, labelled events, scores (see docs/data_dictionary.md)
figures/     all figures (report, LinkedIn articles, cover)
writing/     report and article drafts (links point to ../figures and ../out)
data_inputs/ NOAA Atlas 14 PFDS screenshot used for the highlighted table
docs/        data dictionary; cell_map.csv (notebook cell -> original session cell, status)
```

| Notebook | Content | Cells |
|---|---|---|
| `01_gauges_and_events.ipynb` | GHCNh download, METAR hourly rule, QC, validity, events | 29 |
| `02_product_access.ipynb` | access tests for every product; IBTrACS | 31 |
| `03_extraction_and_alignment.ipynb` | event-window extraction, timing lags, storm-type labels | 53 |
| `04_scoring_and_report.ipynb` | scores, conditional skill, report figures | 16 |
| `05_era5.ipynb` | ERA5 from CDS and Earth Data Hub | 19 |
| `06_final_scores_and_station_qc.ipynb` | final scores incl. ERA5; gauge-network check; 2-year rule | 7 |
| `07_article1_figures.ipynb` | first LinkedIn article figures | 8 |
| `08_satellite_article_figures.ipynb` | satellite article figures, cover | 11 |
| `09_miami_case_study.ipynb` | Miami 26 May 2020 maps, Storm Events, LSRs, Atlas 14 | 33 |
| `10_article_drafting.ipynb` | text edits to drafts (record only) | 12 |

## Important: what these notebooks are

**Outputs shown in the notebooks are the recorded outputs of the original run** (printed text and the figure each cell saved). They were attached from the run log, not produced by re-executing the notebooks, because re-running needs several hours of raw-data downloads. Very long outputs are truncated, with a note. Local file paths were shortened to `./` or `~/`, and one third-party contact email in a printed dataset readme was removed.


The code cells are an **exact export of the analysis session** (219 cells, in the order they ran), not a refactored package.
They include exploratory and failed cells (marked; 21 of 219) because later cells sometimes rely on their partial state.
Only two kinds of edits were made: credentials now come from environment variables / standard config files, and
platform artifact paths were replaced by repo paths (`out/…`, `writing/…`).
Notebooks 01–06 ran in one kernel (`precip` env) and share state across notebooks in that order; 07–10 also read files from `out/`.

**Reproducing from scratch** requires re-downloading raw data (GHCNh parquet, ~13,000 product hours per product
around event peaks, ERA5); this took several hours in the original run. Those raw files and the intermediate product
windows (`prod/*_win.npy`) are *not* in the repo (see `.gitignore`). Everything downstream of extraction is in `out/`:
`event_product_values.parquet` (every event × product × neighbourhood value) and `product_neighborhood_hourly.parquet`
(99 MB; all station-hours within ±1 h of events — publish it as a GitHub Release asset or on Zenodo, it is too large for a normal git commit).

## Hard-won conventions (keep these if you rerun or extend)

* **GHCNh METAR hourly totals:** the last FM-15 report at minute ≥45 in clock hour HH is the total for [HH, HH+1) UTC; on-the-hour sources are stamped at hour end. QC drops quality codes `2` and `G`.
* Military/AWOS stations omit zero-precipitation reports and fail the 24-h completeness rule.
* **Timing:** IMERG, CMORPH, PERSIANN-CCS, Stage IV and MRMS align at lag 0; **NLDAS-2 needs +1 h**; ERA5 accumulations are stamped at hour end.
* NASA GES DISC on-prem OPeNDAP (gpm1) is retired — use **Cloud OPeNDAP** (`opendap.earthdata.nasa.gov`) with the CMR collection IDs (IMERG C2723754847-GES_DISC, MERRA-2 C1276812838-GES_DISC, NLDAS-2 C2033151148-GES_DISC).
* CMORPH files are read with **h5py** (netCDF4 is not thread-safe in threaded downloads).
* MRMS: `GaugeCorr_QPE_01H` was replaced by `MultiSensor_QPE_01H_Pass2` in late 2020; the scripts try both.
* Downloads are sharded with per-chunk checkpoints so interrupted runs resume (`prod/shard_dl.py <product> <shard> <nshards> <threads>`, then `<product> -1 <nshards>` to merge).
* Coop HPD gauges score 21–26 points lower for radar than ASOS gauges (about half is timing); ASOS is the cleaner reference.

## Setup

```bash
conda env create -f environment.yml && conda activate precip
cp .env.example .env    # fill in; never commit .env
jupyter lab             # open notebooks/ (the first cell changes to the repo root)
```

Credentials: NASA Earthdata (`EARTHDATA_USER`/`EARTHDATA_PASS` or `~/.netrc`), Copernicus CDS (`~/.cdsapirc`),
DestinE Earth Data Hub (`DESTINE_EDH_TOKEN`).

## Data sources and terms

GHCNh, Stage IV, CMORPH CDR, IBTrACS, Storm Events and NOAA Atlas 14 are NOAA products; MRMS and Stage IV files come from the
Iowa Environmental Mesonet archive; IMERG, MERRA-2 and NLDAS-2 from NASA GES DISC; PERSIANN-CCS from UC Irvine CHRS;
ERA5 from the Copernicus Climate Change Service (contains modified Copernicus Climate Change Service information, 2026) and DestinE Earth Data Hub.
Cite the original datasets when reusing derived values.

## Licence and citation

No licence file is included yet — choose one before making the repo public (e.g. MIT or BSD-3-Clause for code, CC BY 4.0 for figures and text).
Add a `CITATION.cff` and archive a release on Zenodo to get a DOI.
