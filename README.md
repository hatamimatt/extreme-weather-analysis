# Extreme weather analysis

Analyses of extreme rainfall and the climate patterns behind it, with a focus on Florida and the US Southeast. Each folder is a self-contained project with its own README, environment file and code.

## Projects

| Folder | Question | Data | Status |
|---|---|---|---|
| [`se-elnino-winter-rainfall/`](se-elnino-winter-rainfall/) | How do the strongest El Niños change winter rainfall in the US Southeast, and how does Florida compare with California? | NOAA nClimGrid, NOAA CPC RONI, NCEP/NCAR Reanalysis 1 | Done (Nov 2026) |

## Conventions

- One folder per project, named `<region>-<topic>`.
- Each project has a `README.md` (question, key results, method, how to run, data sources, caveats) and an `environment.yml`.
- Downloaded data go in `<project>/data/`, which is not tracked by git. Large outputs (NetCDF, video) are also untracked; figures and small tables can be committed.
