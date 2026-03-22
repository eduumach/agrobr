"""Enrich _municipios_ibge.json with centroid coordinates from IBGE Malhas API.

One-time script. Fetches centroids for all 5570+ municipalities from
servicodados.ibge.gov.br/api/v3/malhas/municipios and merges into the
existing JSON file, adding [lat, lon] to each entry.

Usage:
    python scripts/enrich_municipios_centroids.py
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import httpx

MUNICIPIOS_JSON = Path(__file__).parent.parent / "agrobr" / "normalize" / "_municipios_ibge.json"
IBGE_METADADOS_URL = "https://servicodados.ibge.gov.br/api/v3/malhas/paises/BR/metadados"
TIMEOUT = 30.0


def fetch_centroids() -> dict[int, tuple[float, float]]:
    params = {"intrarregiao": "municipio"}
    with httpx.Client(timeout=TIMEOUT) as client:
        resp = client.get(IBGE_METADADOS_URL, params=params)
        resp.raise_for_status()
        data = resp.json()

    centroids: dict[int, tuple[float, float]] = {}
    for item in data:
        code = int(item["id"])
        centroid = item.get("centroide", {})
        lat = centroid.get("latitude")
        lon = centroid.get("longitude")
        if lat is not None and lon is not None:
            centroids[code] = (round(float(lat), 4), round(float(lon), 4))
    return centroids


def enrich() -> None:
    print(f"Loading {MUNICIPIOS_JSON} ...")
    with MUNICIPIOS_JSON.open(encoding="utf-8") as f:
        municipios: list[list[Any]] = json.load(f)

    print(f"  {len(municipios)} municipalities loaded")

    print("Fetching centroids from IBGE Malhas API ...")
    t0 = time.perf_counter()
    centroids = fetch_centroids()
    elapsed = time.perf_counter() - t0
    print(f"  {len(centroids)} centroids fetched in {elapsed:.1f}s")

    matched = 0
    missing = []
    for entry in municipios:
        code = entry[0]
        coords = centroids.get(code)
        if coords:
            if len(entry) == 3:
                entry.extend([coords[0], coords[1]])
            else:
                entry[3] = coords[0]
                entry[4] = coords[1]
            matched += 1
        else:
            missing.append((code, entry[1], entry[2]))

    print(f"  Matched: {matched}")
    if missing:
        print(f"  Missing centroids ({len(missing)}):")
        for code, name, uf in missing:
            print(f"    {code} {name}/{uf}")

    with MUNICIPIOS_JSON.open("w", encoding="utf-8") as f:
        json.dump(municipios, f, ensure_ascii=False, separators=(",", ":"))

    size_kb = MUNICIPIOS_JSON.stat().st_size / 1024
    print(f"\nSaved {MUNICIPIOS_JSON} ({size_kb:.0f} KB)")


if __name__ == "__main__":
    enrich()
