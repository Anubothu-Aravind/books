"""
ingest_geography.py

Ingests Bible Geography data from the openbibleinfo/Bible-Geocoding-Data repository on GitHub.
Sourced from:
  - https://raw.githubusercontent.com/openbibleinfo/Bible-Geocoding-Data/master/data/ancient.jsonl
  - https://raw.githubusercontent.com/openbibleinfo/Bible-Geocoding-Data/master/data/geometry.jsonl

Outputs:
  - geography/places.json
  - geography/regions_water.json
  - geography/metadata.json
"""

import os
import json
import urllib.request
import hashlib

base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
geography_dir = os.path.join(base_dir, "geography")
os.makedirs(geography_dir, exist_ok=True)

ANCIENT_URL = "https://raw.githubusercontent.com/openbibleinfo/Bible-Geocoding-Data/master/data/ancient.jsonl"
GEOMETRY_URL = "https://raw.githubusercontent.com/openbibleinfo/Bible-Geocoding-Data/master/data/geometry.jsonl"


def fetch_lines(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as r:
        return r.read().decode("utf-8").splitlines()


def extract_wikidata_id(linked_data):
    if not linked_data:
        return None
    # Look for any value containing Q-ID (e.g., {"id": "Q3743528"} or value like "Q1218")
    for key, val in linked_data.items():
        if isinstance(val, dict):
            qid = val.get("id") or val.get("wikidata_id") or val.get("url", "")
            if qid and isinstance(qid, str):
                # Search for Q followed by digits
                import re
                m = re.search(r"\b(Q\d+)\b", qid)
                if m:
                    return m.group(1)
        elif isinstance(val, str):
            import re
            m = re.search(r"\b(Q\d+)\b", val)
            if m:
                return m.group(1)
    return None


def main():
    print("=== INGESTING BIBLE GEOGRAPHY DATA ===")

    print(f"Downloading ancient geocoding data from: {ANCIENT_URL}")
    ancient_lines = fetch_lines(ANCIENT_URL)
    print(f"Loaded {len(ancient_lines)} ancient place records.")

    places = []
    regions_water = []

    # Keep track of IDs to avoid duplicates
    seen_ids = set()

    for line in ancient_lines:
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except Exception as e:
            print(f"Error parsing line: {e}")
            continue

        place_id = record.get("id")
        if not place_id or place_id in seen_ids:
            continue
        seen_ids.add(place_id)

        name = record.get("friendly_id")
        place_types = record.get("types", [])
        place_type = place_types[0] if place_types else "place"

        # Determine coordinates (lat/lon) from modern associations / resolutions
        lat = None
        lon = None
        confidence = "medium"

        modern_assocs = record.get("modern_associations") or []
        # If modern_assocs is a dict, convert it to a list of dicts (often it is a list, but let's check)
        if isinstance(modern_assocs, dict):
            modern_assocs = list(modern_assocs.values())

        if modern_assocs:
            # Sort by score if possible to get the highest-confidence association
            try:
                modern_assocs = sorted(
                    modern_assocs,
                    key=lambda x: x.get("score", {}).get("vote_total", 0) if isinstance(x.get("score"), dict) else 0,
                    reverse=True
                )
            except Exception:
                pass

            best_assoc = modern_assocs[0]
            # Try to get resolutions
            resolutions = best_assoc.get("resolutions") or []
            if resolutions:
                res = resolutions[0]
                lonlat = res.get("lonlat")
                if lonlat and "," in lonlat:
                    try:
                        lon_str, lat_str = lonlat.split(",")
                        lon = float(lon_str.strip())
                        lat = float(lat_str.strip())
                    except Exception:
                        pass
                
                # Check confidence from votes
                votes = best_assoc.get("votes", {})
                if isinstance(votes, dict):
                    tags = votes.get("tags", {})
                    if isinstance(tags, dict):
                        if tags.get("confidence_likely", 0) > tags.get("confidence_possible", 0):
                            confidence = "high"
                        elif tags.get("confidence_unlikely", 0) > tags.get("confidence_possible", 0):
                            confidence = "low"

        # Extract Wikidata ID
        wikidata_id = extract_wikidata_id(record.get("linked_data"))

        # Extract verses where this place occurs
        verses = []
        for v in record.get("verses", []):
            if isinstance(v, dict):
                usx_ref = v.get("usx")
                if usx_ref:
                    # e.g., "JDG 11:33"
                    verses.append(usx_ref)
                elif v.get("readable"):
                    verses.append(v.get("readable"))

        # Categorize: regions and large water bodies can go to regions_water, cities/settlements to places
        # common types: settlement, region, water, mountain, hill, valley, desert, etc.
        item = {
            "id": place_id,
            "name": name,
            "type": place_type,
            "wikidata_id": wikidata_id,
            "verses": sorted(list(set(verses)))
        }

        if lat is not None and lon is not None:
            item["lat"] = lat
            item["lon"] = lon

        if place_type in ["region", "water", "river", "sea", "lake", "stream", "ocean", "desert", "forest"]:
            item["confidence"] = confidence
            regions_water.append(item)
        else:
            item["confidence"] = confidence
            places.append(item)

    # Ingest geometry data (e.g. boundary polygons or lines for rivers/regions)
    print(f"Downloading geometry data from: {GEOMETRY_URL}")
    geometry_lines = fetch_lines(GEOMETRY_URL)
    print(f"Loaded {len(geometry_lines)} geometry definitions.")

    # Match geometry definitions back to regions/water and places
    geometry_by_name = {}
    for line in geometry_lines:
        if not line.strip():
            continue
        try:
            geom = json.loads(line)
        except Exception:
            continue
        name = geom.get("name")
        if name:
            geometry_by_name[name.lower()] = geom

    # Enrich regions_water and places with geometry metadata if available
    for r in regions_water:
        geom = geometry_by_name.get(r["name"].lower())
        if geom:
            r["geometry_type"] = geom.get("geometry")
            # If coordinates are in suggested/label_line, parse them
            suggested = geom.get("suggested", {})
            label_line = suggested.get("label_line") or suggested.get("label_line_horizontal")
            if label_line:
                r["label_line_coordinates"] = []
                for pt in label_line:
                    if "," in pt:
                        try:
                            lon_str, lat_str = pt.split(",")
                            r["label_line_coordinates"].append([float(lon_str), float(lat_str)])
                        except Exception:
                            pass

    # Save outputs
    places_file = os.path.join(geography_dir, "places.json")
    with open(places_file, "w", encoding="utf-8") as f:
        json.dump(places, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(places)} places to {places_file}")

    regions_water_file = os.path.join(geography_dir, "regions_water.json")
    with open(regions_water_file, "w", encoding="utf-8") as f:
        json.dump(regions_water, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(regions_water)} regions and water bodies to {regions_water_file}")

    # Generate metadata
    metadata_file = os.path.join(geography_dir, "metadata.json")
    
    # Calculate checksums
    def get_sha256(filepath):
        h = hashlib.sha256()
        with open(filepath, "rb") as f:
            while chunk := f.read(8192):
                h.update(chunk)
        return h.hexdigest()

    meta = {
        "dataset_name": "Bible Geography",
        "description": "Geographic locations, places, regions, mountains, and water bodies mentioned in the Bible.",
        "license": "Creative Commons Attribution 4.0 International (CC BY 4.0)",
        "source": "OpenBible.info Bible Geocoding Data (openbibleinfo/Bible-Geocoding-Data)",
        "source_urls": [ANCIENT_URL, GEOMETRY_URL],
        "download_date": urllib.request.urlopen(urllib.request.Request(ANCIENT_URL, method="HEAD")).info().get("Date") or "2026-08-16",
        "files": {
            "places.json": {
                "records_count": len(places),
                "sha256": get_sha256(places_file)
            },
            "regions_water.json": {
                "records_count": len(regions_water),
                "sha256": get_sha256(regions_water_file)
            }
        }
    }

    with open(metadata_file, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)
    print(f"Saved geography metadata to {metadata_file}")

    print("Geography data ingestion complete!\n")


if __name__ == "__main__":
    main()
