# Prompt for a follow-up animation (not yet run)

Ready-to-paste prompt written in the session, for a new session to build an animation of the event's thermodynamic and dynamic ingredients.

```
Make an animation of the atmospheric conditions before, during and after the 1–3 November 2026 extreme rainfall event in Southeast Florida. I want to SEE separately (a) the thermodynamic ingredients (how much moisture and warmth was available) and (b) the dynamic ingredients (wind, moisture inflow, lift, and why the storms didn't move), and how they came together over the rain centres.

EVENT CONTEXT (from my earlier analysis in this project; check the saved artifacts and memory first)
- Rain centres: N Palm Beach (3 W Riviera Beach, 26.78N 80.13W; 589 mm/72 h; MRMS 327 mm in 6 h ending 02 UTC 2 Nov), S Brevard (Grant-Valkaria/Malabar, 27.96N 80.56W; 627 mm), W Broward (Lauderhill/Sunrise, 26.15N 80.27W; 286 mm, mostly evening of 2 Nov).
- Diagnosis so far: not a tropical cyclone and not a classic atmospheric river. The moisture flux was a broad easterly sheet under a strong Mid-Atlantic/NW Atlantic high, with a coastal trough along the Atlantic coast and a weak upper low/shortwave over the eastern Gulf. Miami sounding PWAT was 53–56 mm (86–98th pct for early Nov). Steering flow (850–300 hPa) was only 2–4 m/s under 7–9 m/s easterly low-level inflow. Storms back-built and stayed in place. SST was about +1 °C over the Gulf Stream.

TIME WINDOW
- 29 Oct 2026 00 UTC to 5 Nov 2026 00 UTC (about 3 days before to 2 days after), hourly frames.
- Label each frame in both UTC and local time. Note that DST ended at 2 am on 1 Nov (EDT → EST).

DATA (all worked earlier; AWS buckets and NCEI were already granted)
- HRRR 3 km hourly analyses (f00) from AWS noaa-hrrr-bdp-pds for the mesoscale view: PWAT, CAPE, MSLP, 10 m and 925/850 hPa winds, 850–300 hPa winds, low-level moisture-flux convergence, composite reflectivity. Request network access if blocked. Use .idx byte-range downloads so only the needed fields are fetched.
- GFS 0.25° analyses (00/06/12/18 UTC, AWS noaa-gfs-bdp-pds) for the synoptic view: IVT (1000–300 hPa), PWAT, 500 hPa height/vorticity, 250 hPa jet, MSLP. Interpolate to hourly only for smooth display, and state this in the caption.
- MRMS MultiSensor_QPE_01H_Pass2 (AWS noaa-mrms-pds) for hourly rainfall, plus a running storm-total accumulation.
- NOAA OISST v2.1 daily anomaly (NCEI) for SST.
- KMFL (Miami) radiosonde PWAT from the IEM raob.py service, with the 1–15 Nov 1991–2025 percentile climatology.
- Set cartopy.config['data_dir'] to a workspace folder before plotting coastlines.

ANIMATION LAYOUT (one synchronised MP4 plus a GIF, about 6–8 frames per second, 1920×1080)
- Left column, "THERMODYNAMICS – fuel":
  1. PWAT (shading) with its anomaly contour, plus the SST anomaly underneath over the ocean.
  2. CAPE, or a warm-cloud-depth proxy.
- Right column, "DYNAMICS – delivery and focusing":
  1. Synoptic map: IVT shading and vectors, MSLP contours (the high), 500 hPa heights (the Gulf upper low).
  2. Mesoscale map: 925 hPa wind streamlines, low-level moisture-flux convergence (the coastal trough line), and the 850–300 hPa steering-wind arrow drawn next to the low-level inflow arrow at the Palm Beach core. This should make the "inflow strong, steering weak = storms stay put" mechanism obvious.
- Bottom-centre map: MRMS hourly rain, with the growing storm-total contours, the three rain centres marked, and NWS flood reports appearing at their report times.
- Bottom strip, time series with a moving cursor:
  1. MRMS hourly rain at the three centres.
  2. Miami sounding PWAT against its 90th/99th percentile lines.
  3. IVT magnitude and direction at Palm Beach.
  4. Steering-wind speed vs inflow speed.

STYLE AND QUALITY
- Fixed colour scales across all frames (no per-frame rescaling).
- Colour-blind-safe colour maps.
- A short caption-style annotation that changes by phase: "build-up" (29–31 Oct), "Palm Beach burst" (1 Nov evening), "Brevard MCS" (2 Nov), "Broward" (2–3 Nov evening), "clearing" (3–4 Nov).
- Also save 4–6 key still frames as PNGs for slides, plus a one-page README explaining each panel in plain language.

DELIVERABLES
- The MP4 and GIF, the key-frame PNGs, the README, and the processed fields as compressed NetCDF, all saved as artifacts.
- Keep the plotting code clean and parameterised (event dates, domain, centre points) so I can reuse it for other events.
- Report any data gaps, interpolation, or fields you couldn't get.
```
