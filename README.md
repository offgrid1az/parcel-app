# parcel-app

Research and starting materials for a field app that shows **which parcel you are standing on**
and **where its boundary runs**, using Coconino County's own free GIS parcel data — no vendor, no
per-county subscription.

Built for Happy Jack, Arizona. The county data covers all of Coconino (Flagstaff, Sedona,
Williams, Page, Grand Canyon), so the app is not limited to one community.

---

## Read this first

| File | What it is |
|---|---|
| [`docs/BRIEF-FOR-REPLIT.md`](docs/BRIEF-FOR-REPLIT.md) | The build brief: what LandGlide does and charges, the free county data, two architecture options with measured numbers, build order, and a copy-paste prompt for Replit. |
| [`docs/REPLIT-START-HERE.md`](docs/REPLIT-START-HERE.md) | Import instructions and the first prompt to give Replit Agent. |
| [`scripts/fetch_parcels.py`](scripts/fetch_parcels.py) | Working stdlib-only client for the county service. Three modes: `--probe`, `--bbox`, `--point`. Tested against the live service. |
| [`data/sample-happy-jack.geojson`](data/sample-happy-jack.geojson) | 744 real Happy Jack parcels, one subdivision cluster, ready to drop into a map as a test layer. |

## The short version

Coconino County publishes **78,595 parcels** on ArcGIS Online. No key, no account, no fee, no
request form. Verified live on 2026-11-21:

| Test | Result |
|---|---|
| Point → parcel ("which parcel am I in?") | 1 feature with polygon, sub-second |
| Envelope → parcels (map viewport) | 744 parcels in a 0.02° box, 214 KB GeoJSON |
| 2,000 parcels, full geometry | 684 KB in 0.74 s → county total **26 MB** |
| 2,000 parcels, simplified ~30 m | 375 KB in 0.71 s → county total **14 MB** |
| 2,000 parcels, attributes only | 131 KB → county total **5 MB** |
| Full rebuild | 40 paged requests, under 30 s |
| Acreage | `Shape__Area` is ft² → ÷ 43,560 (verified against a known parcel) |

**Why that matters:** the whole county's geometry is a normal-size download. The app can carry
every parcel offline and work under the pines where there is no signal — which is the entire
difference between a field tool and a demo.

## Endpoints

```
# geometry + site address (no owner names)
https://services1.arcgis.com/Rlvx5g8pKeK13apH/arcgis/rest/services/Coconino_County_Parcels_Open_Data/FeatureServer/0

# same geometry + OWNERNAME + owner mailing address
https://services1.arcgis.com/Rlvx5g8pKeK13apH/arcgis/rest/services/Coconino_County_Parcels_Public_View/FeatureServer/0
```

The org id is `Rlvx5g8pKeK13apH`. A plausible-looking variant (`Rlxv...`) returns a bare 404.
Copy the URL from the item metadata rather than retyping it.

## Two traps that fail silently

1. **`where=1=1` on every query.** Omitted, the service returns zero features with a 200 and no
   error — indistinguishable from "no parcels here".
2. **`inSR=4326` whenever you pass lat/lon.** The layer's native CRS is WKID 2223 (Arizona State
   Plane Central, US feet). Degrees without `inSR` are read as feet and the query returns nothing.

Both are cheap to get wrong and expensive to debug, because neither produces an error.

## Licence — carry it

> Coconino County GIS gives no warranty, expressed or implied, as to the accuracy, reliability, or
> completeness of these data. [...] Any type of boundary, linear or point locations contained
> within this data or displayed within this product are approximate, and should not be used for
> authoritative or legal location purposes. [...] Per A.R.S. 37-178: A public agency that shares
> geospatial data of which it is the custodian is not liable for errors, inaccuracies or omissions
> and shall be held harmless from and against all damage, loss or liability arising from any use of
> geospatial data that is shared.

Label lines **"parcel boundary (approx.)"**, never "property line". The disclaimer goes in the app,
on the parcel sheet, and in the store listing.

## Privacy note

The **Public View** service carries owner names and owner mailing addresses. Assessor records are
public in Arizona, but re-publishing them inside a consumer app has optics. Default position in
this repo: build on Open Data (no owner fields); gate owner detail to signed-in agent accounts, or
look it up on demand from the Assessor.

## Running the probe

```bash
python3 scripts/fetch_parcels.py --probe                              # count, timings, payload sizes
python3 scripts/fetch_parcels.py --point 34.64712,-111.10993          # 2663 Roundup Ln, 1.05 ac
python3 scripts/fetch_parcels.py --bbox -111.1164,34.6297,-111.0964,34.6497 --out out.geojson
python3 scripts/fetch_parcels.py --point 34.64712,-111.10993 --with-owner   # Public View service
```

No dependencies. Python 3.8+.

**Acreage from simplified geometry drifts.** The same parcel reads 1.05–1.07 acres depending on
whether the geometry was simplified for drawing. Use `Shape__Area ÷ 43560` for any acreage shown to
a client; the polygon is for the map, not the maths.

## Status

Research phase. No app code yet. The brief specifies React Native + Expo + MapLibre with a bundled
MBTiles tile set and SQLite attribute table, Android first, no backend in version one.
