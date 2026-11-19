# Satellites see the storm, not the downpour: testing 9 rainfall datasets against Florida's most extreme hours

On the afternoon of 26 May 2020, the rain gauge at Miami International Airport recorded **84.6 mm of rain in a single hour**. Streets flooded within minutes.

Gauges like that one are sparse. So when we study extreme rainfall, whether for drainage design, flood forecasting or climate change, we often turn to **gridded datasets**: radar, satellite and reanalysis products that cover every square kilometre.

That raises a simple question: **when it really pours, do these datasets see it?**

![What four rainfall products showed over the Miami gauge during the 84.6 mm hour](../figures/li_fig1_miami.png)

Over the gauge, the radar products show about **50–55 mm**. The IMERG satellite product shows **5 mm**. The ERA5 reanalysis shows **3 mm**. All four "saw" the storm, but only radar came close to how hard it rained.

One storm proves nothing, so I tested it systematically.

## What I did
* **Ground truth:** 79 quality-controlled hourly rain gauges across Florida (GHCNh), 2015–2025. Each station needed at least 5 years with at least 30 complete 24-hour days.
* **Extremes:** every hour above 20, 30, 40 and 50 mm. That is thousands of events, from sea-breeze thunderstorms to hurricanes.
* **Nine gridded products:**
  * radar: MRMS and Stage IV;
  * satellite: IMERG, CMORPH, PERSIANN-CCS;
  * models/reanalyses: NLDAS-2, ERA5, MERRA-2.
* **The test:** for each extreme hour, did the product also reach the same threshold? I checked the pixel above the gauge, then 2×2, 3×3 and 4×4 groups of nearby pixels to forgive small position errors.

## What I found

![Pixel size versus detection of extreme rainfall](../figures/li_fig2_resolution.png)

**1. Resolution decides almost everything.**
* Radar products (1–4 km pixels) reach the threshold in **53–66% of ≥30 mm/h events**, using a 3×3 neighborhood.
* Satellite products (4–10 km) reach it in **2–6%**.
* Global reanalyses (25–60 km) essentially never do.

**2. Satellites see the storm, but not the downpour.** Satellite products usually show rain in the right place and hour, but typically only **about 10% of the peak intensity** the gauge measured. Global reanalyses show about **2%**. A 25 km grid cell averages a 2 km thunderstorm into a drizzle.

**3. Even radar underestimates.** The best products show **62–71%** of the gauge peak at the station pixel, and they fall further short for the most intense events.

![Detection by storm type](../figures/li_fig3_stormtype.png)

**4. Storm type matters, and each satellite fails differently.**
* IMERG catches only **2%** of isolated summer thunderstorms, the most common type of extreme in my data, but **13%** of cool-season frontal events.
* PERSIANN-CCS, which relies on infrared cloud-top temperatures, does the opposite: better in summer convection, worse in winter fronts.
* ERA5 shows skill almost only in **tropical cyclones**, where rain is driven by large-scale circulation it can resolve.

**5. The "truth" needs scrutiny too.** Radar agreed much better with airport (ASOS) gauges than with cooperative-network gauges. About half of that gap came from timing errors in the cooperative records. Before validating a product, validate your gauges.

## Why this matters
* **Infrastructure design:** intensity–duration–frequency curves built from satellite or reanalysis data would understate design storms, leaving culverts and storm drains undersized.
* **Flood modeling and risk:** low rainfall inputs mean low peak flows, smaller flood maps and underestimated risk, especially in fast-responding urban catchments.
* **Climate research:** studies of how extreme rainfall scales with temperature, or of trends in extremes, can be biased low if they rely on coarse products, and the bias changes with storm type.
* **Data-poor regions:** many places rely on satellites alone. Florida suggests those hazard estimates may be substantially low.

## Caveats
* The radar products partly ingest gauge data, so they aren't fully independent of the ground truth.
* Storm types are classified with simple proxies.
* This is one state and one decade.
* Coarse products are *expected* to smooth point extremes. The point is that they are often used for point-scale questions anyway.

## What's next
I'm interested in **storm-type-aware bias correction**, and in using high-resolution radar to build **point-to-area conversion factors**, so coarse products can be translated into the point intensities engineers actually design for.

If you work with rainfall extremes, which dataset do you trust for hourly peaks, and why? I'd love to hear from hydrologists, engineers and remote-sensing folks.

#Hydrology #ExtremeRainfall #RemoteSensing #ClimateChange #FloodRisk #StormwaterManagement #IMERG #ERA5 #Radar #Florida
