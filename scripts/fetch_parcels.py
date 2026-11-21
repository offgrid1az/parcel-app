#!/usr/bin/env python3
"""Fetch Coconino County parcels from the county's public ArcGIS service.

No dependencies beyond the standard library. No API key. No rate limit has been observed.

Three jobs, all verified against the live service on 2026-11-21:

    # 1. how big is the whole county, and what does it cost to pull it?
    python3 fetch_parcels.py --probe

    # 2. a sample viewport, saved as GeoJSON (what the map layer consumes)
    #    this box is a real Happy Jack subdivision cluster: 744 parcels
    python3 fetch_parcels.py --bbox -111.1164,34.6297,-111.0964,34.6497 --out data/sample.geojson

    # 3. "which parcel am I standing in?" — pass a GPS fix (lat,lon)
    python3 fetch_parcels.py --point 34.64712,-111.10993   # 2663 Roundup Ln, 1.07 ac

The service defaults to Open Data (no owner names). Pass --with-owner to use the Public View
service, which carries OWNERNAME and the owner mailing address — that is a privacy decision for
the site owner, not a technical one.
"""

import argparse
import json
import math
import os
import time
import urllib.parse
import urllib.request

ORG = "Rlvx5g8pKeK13apH"  # CoconinoCountyGIS. Rlxv 404s.
BASE = f"https://services1.arcgis.com/{ORG}/arcgis/rest/services"
SERVICES = {
    "open": "Coconino_County_Parcels_Open_Data",
    "owner": "Coconino_County_Parcels_Public_View",
}
FIELDS = {
    "open": "APN,SITUS,SITUS_CITY,SITUS_ZIP,Shape__Area",
    "owner": "APN,SITUS,SITUS_CITY,SITUS_ZIP,Shape__Area,OWNERNAME,OWNERADDRESS_CITY,OWNERADDRESS_STATE",
}
SQFT_PER_ACRE = 43560.0
M2_PER_ACRE = 4046.8564224


def ring_acres(ring: list) -> float:
    """Area of a WGS84 ring in acres.

    ArcGIS's GeoJSON output does not carry Shape__Area, so this projects the ring to a local
    planar frame at its own latitude (equirectangular) and uses the shoelace formula. For parcel-
    sized shapes that is within a fraction of a percent, and it needs no dependency.
    """
    if len(ring) < 3:
        return 0.0
    lat0 = sum(p[1] for p in ring) / len(ring)
    mx, my = 111320.0 * math.cos(math.radians(lat0)), 110540.0
    pts = [(p[0] * mx, p[1] * my) for p in ring]
    s = 0.0
    for i in range(len(pts)):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % len(pts)]
        s += x1 * y2 - x2 * y1
    return abs(s) / 2.0 / M2_PER_ACRE


def query(service: str, **params) -> dict:
    """One ArcGIS query. where=1=1 is required or the service returns zero features silently.

    Uses f=json, not f=geojson: an envelope passed to the GeoJSON output format returns zero
    features with a clean 200. The native format also carries Shape__Area, which is the county's
    own acreage figure.
    """
    params.setdefault("where", "1=1")
    params.setdefault("f", "json")
    url = f"{BASE}/{SERVICES[service]}/FeatureServer/0/query?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=180) as r:
        return json.loads(r.read().decode("utf8"))


def to_geojson(esri: dict) -> dict:
    """ArcGIS JSON -> a GeoJSON FeatureCollection with an `acres` property on every feature."""
    feats = []
    for f in esri.get("features", []):
        attrs = dict(f.get("attributes", {}))
        rings = (f.get("geometry") or {}).get("rings") or []
        attrs["acres"] = round((attrs.get("Shape__Area") or 0) / SQFT_PER_ACRE, 2) if attrs.get("Shape__Area") \
            else round(ring_acres(rings[0]), 2) if rings else 0.0
        feat = {"type": "Feature", "properties": attrs}
        if rings:
            feat["geometry"] = {"type": "Polygon", "coordinates": rings}
        feats.append(feat)
    return {"type": "FeatureCollection", "features": feats}


def count(service: str) -> int:
    return query(service, returnCountOnly="true", f="json", returnGeometry="false")["count"]


def point_lookup(lat: float, lon: float, service: str = "open") -> None:
    """GPS fix -> the parcel containing it. Zero hits means a wrong parameter, not a missing parcel."""
    data = query(
        service,
        geometry=f"{lon},{lat}",
        geometryType="esriGeometryPoint",
        inSR="4326",
        outSR="4326",
        spatialRel="esriSpatialRelIntersects",
        outFields=FIELDS[service],
        returnGeometry="true",
    )
    feats = to_geojson(data)["features"]
    if not feats:
        print(f"No parcel at {lat},{lon}. Check the coordinate order (lat,lon) and the service.")
        return
    for f in feats:
        p = f["properties"]
        print(f"APN {p['APN']} | {p.get('SITUS') or '(no site address)'} | {p['acres']:.2f} ac")
        if p.get("OWNERNAME"):
            print(f"  owner: {p['OWNERNAME']}")
        print(f"  boundary: {len(f['geometry']['coordinates'][0])} vertices, EPSG:4326")


def bbox_fetch(bbox: str, service: str, out: str) -> None:
    xmin, ymin, xmax, ymax = (float(v) for v in bbox.split(","))
    data = query(
        service,
        geometry=f"{xmin},{ymin},{xmax},{ymax}",
        geometryType="esriGeometryEnvelope",
        inSR="4326",
        outSR="4326",
        spatialRel="esriSpatialRelIntersects",
        outFields=FIELDS[service],
        returnGeometry="true",
        maxAllowableOffset="0.0003",
    )
    data = to_geojson(data)
    directory = os.path.dirname(out)
    if directory:
        os.makedirs(directory, exist_ok=True)
    payload = json.dumps(data, separators=(",", ":"))
    with open(out, "w", encoding="utf8") as fh:
        fh.write(payload)
    print(f"{len(data.get('features', []))} parcels -> {out} ({len(payload) / 1024:.0f} KB)")


def probe(service: str) -> None:
    """Measure the payload three ways, then extrapolate to the whole county."""
    total = count(service)
    full = count(service)  # cheap sanity that the count is stable between two calls
    print(f"parcels: {total} (re-read: {full})  service={service}")
    if total != full:
        print("  WARNING: count moved between two calls — the county may be mid-republish")

    shapes = [
        ("full geometry", {"returnGeometry": "true", "maxAllowableOffset": ""}),
        ("simplified ~30m", {"returnGeometry": "true", "maxAllowableOffset": "0.0003"}),
        ("attributes only", {"returnGeometry": "false"}),
    ]
    for label, extra in shapes:
        params = {
            "outFields": "APN",
            "outSR": "4326",
            "resultOffset": "0",
            "resultRecordCount": "2000",
            "orderByFields": "OBJECTID",
        }
        params.update({k: v for k, v in extra.items() if v})
        started = time.time()
        url = (
            f"{BASE}/{SERVICES[service]}/FeatureServer/0/query?"
            + urllib.parse.urlencode(dict(params, where="1=1", f="geojson"))
        )
        with urllib.request.urlopen(url, timeout=180) as r:
            body = r.read()
        elapsed = time.time() - started
        n = len(json.loads(body.decode("utf8")).get("features", []))
        per_page = len(body) / max(n, 1)
        print(
            f"  {label:16s} {len(body) / 1024:7.0f} KB in {elapsed:4.2f}s "
            f"({n} features) -> county total ~{per_page * total / 1048576:6.1f} MB"
        )

    pages = -(-total // 2000)
    print(f"  rebuild cost: {pages} paged requests")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--probe", action="store_true", help="count, timing and payload for the whole county")
    ap.add_argument("--bbox", help="xmin,ymin,xmax,ymax in WGS84")
    ap.add_argument("--point", help="lat,lon — which parcel contains this GPS fix")
    ap.add_argument("--out", default="parcels.geojson")
    ap.add_argument("--with-owner", action="store_true", help="use the Public View service (owner fields)")
    args = ap.parse_args()

    service = "owner" if args.with_owner else "open"
    if args.point:
        lat, lon = (float(v) for v in args.point.split(","))
        point_lookup(lat, lon, service)
    elif args.bbox:
        bbox_fetch(args.bbox, service, args.out)
    elif args.probe:
        probe(service)
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
