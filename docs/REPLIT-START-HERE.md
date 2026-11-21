# Starting this project in Replit

Two ways in. **A** is recommended — it gives Replit the whole repo so it can read the brief,
run the probe, and see the sample geometry without you copying anything.

---

## Path A — import the repo (recommended)

1. Replit → **Create** → **Import from GitHub**.
2. Paste: `https://github.com/offgrid1az/parcel-app`
3. Choose **React Native / Expo** if offered; otherwise pick a blank Node project — the repo is
   documentation and one Python script, so any template works and the app is generated next.
4. Open the Agent and paste the first prompt below.

## Path B — no repo access

In Replit, create a blank project and paste this, editing the URLs if you fork the repo:

> Fetch and read these first, then confirm you have them before writing any code:
> https://raw.githubusercontent.com/offgrid1az/parcel-app/main/docs/BRIEF-FOR-REPLIT.md
> https://raw.githubusercontent.com/offgrid1az/parcel-app/main/README.md
> https://raw.githubusercontent.com/offgrid1az/parcel-app/main/scripts/fetch_parcels.py
>
> Then summarise back to me: the county service URL, the parcel count, the two silent-failure
> traps, the licence requirement, and the recommended architecture. Do not start building until I
> confirm your summary.

---

## The first prompt (beginning of phase 1)

Paste this after the import. It is deliberately narrow — it asks for the map and the GPS dot
before anything else, because if that does not work under trees the rest does not matter.

> Read `docs/BRIEF-FOR-REPLIT.md` in this repo before writing anything, then build **phase 1 only**:
>
> A React Native (Expo) app that opens on the user's GPS position with parcel boundaries drawn
> over the map.
>
> - Map: `@maplibre/maplibre-react-native`. Open on the device location at zoom 16.
> - Parcels: use `data/sample-happy-jack.geojson` (744 real parcels) as the test layer. Style
>   parcel outlines in a high-contrast stroke with a translucent fill, and label nothing yet.
> - A visible "my location" dot, high-accuracy `expo-location` watch, updating continuously.
> - Do **not** add search, saved pins, measurement, listings, or a backend yet.
>
> Confirm the app runs in the browser preview and tell me what to install on the phone to test it.
> Then stop and wait for me.

## The second prompt (phase 2 — the actual product)

> Phase 2. Now answer "which parcel am I standing in?" and "how far to the boundary?" without any
> network call.
>
> - Bundle `data/sample-happy-jack.geojson` (later: the full county) into an SQLite table via
>   `expo-sqlite`: APN, situs, city, zip, acres, bbox, and the polygon.
> - On every GPS update, select candidates by bbox overlap and run point-in-polygon locally.
> - Show a bottom sheet for the current parcel: APN, site address, acreage as
>   `acres` from `Shape__Area ÷ 43560` (**not** measured from the drawn polygon), and the distance
>   in feet to the nearest boundary edge, updating live.
> - Label the layer "parcel boundary (approx.)" and put this on the sheet:
>   "Parcel boundaries are approximate and are not a legal survey. Coconino County GIS gives no
>   warranty as to accuracy. Per A.R.S. 37-178 the county is held harmless for any use of this
>   data. Verify against deeds and plats of record."
>
> Test it against three Happy Jack parcels whose corners are known. Show me the screen.

## The third prompt (phase 0/6 — the data pipeline)

> Write `scripts/build_bundle.py` that rebuilds the offline data from the live county service:
>
> - Page `Coconino_County_Parcels_Open_Data` 2,000 rows at a time with `resultOffset` and
>   `orderByFields=OBJECTID` (40 pages; `where=1=1` is mandatory or you get zero rows silently).
>   Request `outSR=4326` and `maxAllowableOffset=0.0003`.
> - Verify the pages are distinct (last APN of page N ≠ first APN of page N+1) and that the total
>   is 78,595 ± 1%. Fail loudly if it is not — that is how a schema change announces itself.
> - Write `parcels.mbtiles` for the map and `parcels.sqlite` for lookups.
> - Print the row count, the file sizes, and the service's last-edit date.

---

## What Replit cannot do for you

- **Installing on a phone.** Replit hosts the code and the preview; the installable Android build
  comes from **Expo EAS** (`eas build -p android --profile preview`) or a local build. Ask for the
  EAS setup in phase 1 and get a real APK on the phone early.
- **App store submission.** Separate, later, and it needs a Google Play account ($25 one-off).

## Checks before you call phase 2 done

- Stand on a parcel with a known corner: the app's line should sit within a few feet of the fence,
  and the "distance to boundary" readout should shrink to near zero as you reach it.
- Turn on airplane mode: everything except the basemap imagery should still work.
- Acreage on three parcels should match the county's published figures exactly, because it is the
  county's number, not a measurement.
