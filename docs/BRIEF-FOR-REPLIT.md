# Parcel-finder app for Happy Jack — brief for Replit

**21 November 2026 · prepared for Jackie Thresher / Realty ONE Group Mountain Desert**

The goal: an app on a phone that shows the client, in the field, exactly which parcel you are
standing on and where its boundary lines run — using Coconino County's own GIS parcel data,
with no subscription and no per-county vendor.

Everything below marked **(tested)** was run against the live county services on 21 November
2026 and returned the numbers quoted. Nothing here is estimated unless it says so.

---

## 1. What LandGlide is, and what it costs

LandGlide is the benchmark app for exactly this. It is a US-wide parcel map on phone and desktop.

| | |
|---|---|
| Coverage it claims | 157 million parcel records, 3,200+ counties, "more than 99% of the U.S. population" |
| Price | **$9.99/month or $99.99/year**, 7-day free trial; corporate/team plans |
| Vendor | Real Estate Portal, USA — U.S. Patent 8,255,418, registered trademark |

**What it does, from their own support documentation:**

- **GPS dot on a parcel map.** Tap a parcel to see owner, mailing address, site address, acreage,
  square footage, school district, sale price, transfer date.
- **Three base maps** — street, satellite, USGS topo — plus **overlays** for flood zones,
  contours and buildings.
- **Six label modes** for parcels: owner name, owner last name, street address, address number,
  parcel ID, or none.
- **Search** by owner name, address or parcel ID.
- **Measure tool** — tap points for distance, or enclose an area for area and perimeter, with
  automatic unit switching; copy the result to the clipboard.
- **Saved locations** with four pin colours, free-text notes and tags; **export as CSV**.
- **County Link** button that opens the county's own website for that parcel, and a **Navigate**
  button that hands off to the phone's navigation app.
- **Offline access** to parcel data, which is their main claim in rural areas.
- **Legal disclaimer:** their lines "are not... recently surveyed property lines and are not
  recommended to use for legal purposes. Counties will rely on deeds and plats of record."

**Why build rather than buy:** $99.99/year per user is cheap, and the honest answer is that for a
single agent LandGlide is cheaper than building anything. What it does not do is tie a parcel to
your own listings, your own farm-and-farm notes, the county's permit and sale history, or the
Happy Jack place names a client asks about. Building is worth it only if the app carries your
business — that is the decision, and it is yours, not the developer's.

Sources: landglide.com (home, pricing, FAQ pages), read 2026-11-21.

---

## 2. The data exists, it is free, and it is current

Coconino County publishes its parcel layer on ArcGIS Online. No key, no account, no fee, no
request form. Two services, same 78,595 parcels:

```
Parcels, geometry + site address
https://services1.arcgis.com/Rlvx5g8pKeK13apH/arcgis/rest/services/
  Coconino_County_Parcels_Open_Data/FeatureServer/0

Parcels, same geometry, plus owner name and owner mailing address
https://services1.arcgis.com/Rlvx5g8pKeK13apH/arcgis/rest/services/
  Coconino_County_Parcels_Public_View/FeatureServer/0
```

Note the org id: **`Rlvx5g8pKeK13apH`** — `Rlxv` 404s.

**Fields (tested):** `OBJECTID, APN, TYLERACCOUNTNUM, SITUS, SITUS_CITY, SITUS_ZIP`, plus on the
Public View `OWNERNAME, OWNERADDRESS, OWNERADDRESS_ADDRESS1/2, OWNERADDRESS_CITY,
OWNERADDRESS_STATE, OWNERADDRESS_ZIP`, and on both `Shape__Area, Shape__Length`.

**Verified behaviour (tested 2026-11-21):**

| What | Result |
|---|---|
| Parcel count | 78,595 in both services |
| Point query — "what parcel is at this GPS coordinate?" | 1 feature, sub-second, geometry returned as WGS84 rings |
| Envelope query — "parcels in this viewport" | 15 parcels in a 0.02° box, 4.4 KB of GeoJSON |
| 2,000 parcels, full geometry | 684 KB, **0.74 s** |
| 2,000 parcels, geometry simplified to ~30 m | 375 KB, **0.71 s** |
| 2,000 parcels, attributes only | 186 KB, 0.41 s |
| Max records per request | 2,000 |
| Output formats | JSON, GeoJSON, PBF |
| Native coordinate system | WKID 2223 (Arizona State Plane Central, US feet) |

**Acreage:** `Shape__Area` is in square feet; divide by 43,560. Checked against a known parcel
(APN `40327004C`): 212,301 ft² → 4.87 acres. ✅

**APN format:** eight digits, sometimes with a letter suffix — `40327004C`, not `403-27-004C`.
Any search box has to accept the dashed form and normalise it.

**Whole-county download is small.** Extrapolating the measured payloads: **~26 MB** for every
parcel in Coconino with full geometry, **~14 MB** simplified, **~7 MB** attributes only. That is
a download, not a project. It is the difference between an app that works under the pines on
Forest Road 82 and one that spins.

**The licence is published and it is a real constraint.** From the county's item description,
verbatim:

> Coconino County GIS gives no warranty, expressed or implied, as to the accuracy, reliability, or
> completeness of these data. This disclaimer applies both to the direct use of the data and any
> derivative products produced with the data. Any type of boundary, linear or point locations
> contained within this data or displayed within this product are approximate, and should not be
> used for authoritative or legal location purposes. [...] Per A.R.S. 37-178: A public agency that
> shares geospatial data of which it is the custodian is not liable for errors, inaccuracies or
> omissions and shall be held harmless from and against all damage, loss or liability arising from
> any use of geospatial data that is shared.

So: free to use, **must carry the disclaimer** — in the app, on the parcel detail sheet, and in
the store listing. Parcel lines are a convenience, never a legal boundary.

One caution the owner should decide, not the developer: the **Public View service carries owner
names and owner mailing addresses**. Arizona assessor records are public, but re-publishing them
inside a consumer app is a decision with privacy optics. Safe default: ship the Open Data service
(no owner names) and look up owner detail on demand from the Assessor, or restrict owner fields to
signed-in agent accounts.

---

## 3. What the app has to do

Six things, in priority order. Everything else is later.

1. **Open to my location**, on a satellite or street map, with parcel lines drawn over it.
2. **Tell me which parcel I am standing in** — APN, site address, acreage, owner — updating as I
   walk, without me tapping anything.
3. **Show my distance to the nearest boundary**, in feet. This is the feature that makes it usable
   with a client standing next to you: "we're about 40 feet inside the line."
4. **Tap any parcel** for its detail sheet, including acreage and the county link.
5. **Work with no signal**, at least for the Happy Jack area and preferably county-wide.
6. **Save a pin** with a note, so the walk is not lost.

Explicitly **not** in version one: listings, MLS, driving directions, measurement tools, CSV
export, team accounts, iOS and Android separately. LandGlide's feature list is the *reference*,
not the backlog.

---

## 4. How to build it — two options, one recommendation

### Option A — thin client, always online (2–3 weeks)

Map component + live queries to the county service as the user pans, and a point query each time
the GPS moves. Nothing is stored.

- **Good:** smallest build, no data pipeline, always current (the county updates the service).
- **Bad:** useless where Happy Jack actually is. You have walked those parcels; a dead app in a
  canyon is worse than no app.
- **Verdict:** ship it as the internal prototype to prove the map and the GPS logic, not as the
  product.

### Option B — offline county bundle (4–6 weeks) ← **recommended**

A build step (run once a month, or weekly) that pulls all 78,595 parcels from the county and
produces two files shipped inside the app:

- **`parcels.mbtiles`** — vector tile set of parcel polygons for drawing. ~14 MB simplified.
  Renders smoothly at every zoom, offline. (MBTiles is the format MapLibre reads offline out of the
  box; PMTiles is smaller and single-file but support in the React Native build is not guaranteed —
  verify in phase 1 before committing to it.)
- **`parcels.sqlite`** — one row per parcel: APN, situs, city, zip, acres, owner fields if
  allowed, bounding box, and the polygon as compact WKB. This answers "which parcel am I in?"
  and "distance to boundary" locally, in milliseconds, with no network.

At 78k parcels a bounding-box index (R-tree) fits comfortably in memory on a phone; point-in-
polygon only ever tests the handful of candidates near the GPS fix.

**Basemap is the only part that resists offline.** Satellite imagery for the whole county at
usable zoom is gigabytes. Two honest choices: (a) online basemap with offline parcel lines —
works because the lines are what matters and the imagery is a nicety; or (b) pre-cache imagery
for a defined operating area (Happy Jack and the subdivisions you actually work, roughly a
20 × 20 km box) at zoom 16–18, which is a few hundred MB. Start with (a).

**Accuracy expectation, stated once:** a phone's GPS is good to about 3–5 m in the open and much
worse under canopy, and the county's lines are themselves approximate. So the app is right to
tens of feet, not to inches. Never present a line as surveyed, and never let a client read the
app as a legal boundary. The disclaimer above is not decoration; it is the thing that keeps a
conversation about a fence from becoming a conversation about liability.

---

## 5. What to build it in

- **App:** React Native with Expo. One codebase, both stores, and it is the stack Replit can
  generate and run in a browser preview.
- **Map:** `@maplibre/maplibre-react-native` — it draws vector layers from a local MBTiles file
  with no network, and needs no per-map-view billing. (Mapbox and Google both charge per load and
  both want a key; the county data is free and the map layer should be too.)
- **Local data:** `expo-sqlite` for attributes; the tile file read from app storage.
- **Location:** `expo-location`, high-accuracy mode, watched continuously while the screen is on.
- **Boundary maths:** store each parcel's polygon; compute point-in-polygon and nearest-edge
  distance in JS. A `turf` point-to-line call per candidate is enough at this scale.
- **The refresh job:** a Node or Python script that pages the county service 2,000 rows at a
  time (**40 requests**, 0.35–0.40 s each — under 30 seconds total, tested), simplifies geometry,
  writes the PMTiles and SQLite, and reports the parcel count and the service's last-edit date.
  It must fail loudly if the count moves by more than a few percent — that is how you find out
  the county republished with a changed schema.

**Where Replit fits, and where it does not:** Replit can host the refresh job, the API if you ever
need one, and the Expo project itself, and it can give you a browser preview of the screens.
What it cannot do is put the app on a phone by itself — the installable build comes from **Expo
EAS** (`eas build`) or a local Android build. Confirm that in the first Replit session rather
than discovering it at the end.

**No backend is required for version one.** Everything is in the bundled files. A backend only
becomes necessary when pins and notes must sync between phones, and that can be a small API plus
a database later.

---

## 6. Build order

| Phase | Deliverable | Done when |
|---|---|---|
| 0 | Data probe script | Pulls all 78,595 parcels, prints count, byte size and last-edit date; two consecutive runs match |
| 1 | Map + GPS | Opens on the phone's location, satellite basemap, parcel lines from the bundled file |
| 2 | "Which parcel am I in" | APN, situs, acres, owner on screen, updating while walking; tested on three Happy Jack parcels with known boundaries |
| 3 | Distance to boundary | Feet to nearest edge, updating live; sanity-checked against a measured tape on one boundary |
| 4 | Tap for detail + county link | Detail sheet with disclaimer; links to the Assessor account page |
| 5 | Saved pins + notes | Local storage, survives restart |
| 6 | Refresh job | Monthly rebuild, count guard, publishable to Replit |

Phase 2 is the whole product. If phase 2 is not reliable under trees, nothing after it matters.

---

## 7. Copy-paste brief for Replit

> Build a React Native (Expo) mobile app for a real-estate agent working rural parcels in
> Coconino County, Arizona. The app shows the user's GPS position on a map with parcel boundaries
> drawn over it, and tells them which parcel they are standing in and how far they are from its
> nearest boundary.
>
> **Data source — Coconino County ArcGIS, public, no key:**
> `https://services1.arcgis.com/Rlvx5g8pKeK13apH/arcgis/rest/services/Coconino_County_Parcels_Open_Data/FeatureServer/0`
> and the same org's `Coconino_County_Parcels_Public_View/FeatureServer/0` for owner fields.
> 78,595 parcels. Query with `where=1=1`, `outSR=4326`, `f=geojson`, `maxAllowableOffset=0.0003`,
> page with `resultOffset` / `resultRecordCount=2000` (40 pages, no overlap, verified).
> divide by 43,560 for acres. APN is 8 digits with an optional letter suffix; accept dashed input
> and strip separators.
>
> **Ship offline.** A build script produces (a) an MBTiles vector tile set of parcel polygons and
> (b) an SQLite table of APN, situs, city, zip, acres, bbox and WKB polygon, both bundled in the
> app. Use `@maplibre/maplibre-react-native` for the map with that tile file as a local source,
> `expo-sqlite` for attributes, `expo-location` for a continuous high-accuracy watch. Compute
> point-in-polygon and nearest-edge distance locally; do not call a server at runtime.
>
> **Screens:** map with GPS dot and parcel lines; a bottom sheet for the current parcel showing
> APN, site address, acreage, owner and a link to the Coconino Assessor; a live "distance to
> boundary" readout in feet; tap any parcel for the same sheet; save a pin with a note.
>
> **Required:** show this disclaimer on the parcel sheet and in the store listing — "Parcel
> boundaries are approximate and are not a legal survey. Coconino County GIS gives no warranty as
> to accuracy. Per A.R.S. 37-178 the county is held harmless for any use of this data. Verify
> against deeds and plats of record." Never label a line "property line"; label it "parcel
> boundary (approx.)".
>
> **Constraints:** no backend in version one; no Mapbox or Google Maps keys; no MLS or listings;
> no measurement tool; no CSV export. Android first, iOS after.
