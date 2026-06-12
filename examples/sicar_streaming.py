#!/usr/bin/env python3
"""
Streaming de Imoveis Geoespaciais (SICAR)
==========================================

Itera sobre os imoveis rurais com geometria de uma UF processando em
batches, sem acumular o GeoDataFrame completo em memoria.

Uso:
    python sicar_streaming.py
"""

from __future__ import annotations

import asyncio
import time

from agrobr.alt import sicar


async def main() -> None:
    inicio = time.perf_counter()
    total = 0

    async for gdf in sicar.imoveis_geo_stream("MG"):
        total += len(gdf)
        print(f"batch: {len(gdf)} imoveis | acumulado: {total}")

    elapsed = time.perf_counter() - inicio
    print(f"\ntotal: {total} imoveis em {elapsed:.1f}s")


if __name__ == "__main__":
    asyncio.run(main())
