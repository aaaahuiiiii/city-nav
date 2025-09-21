# 高德 Web 服务封装（REST）
# -*- coding: utf-8 -*-
# TravelBird-main/api/gaode_client.py
import os, aiohttp, math
from typing import List, Dict, Optional, Tuple

AMAP_KEY = os.getenv("AMAP_REST_KEY", "").strip()
BASE = "https://restapi.amap.com/v3"

class GaoDeClient:
    def __init__(self, key: Optional[str] = None):
        self.key = key or AMAP_KEY
        if not self.key:
            raise RuntimeError("缺少 AMAP_REST_KEY 环境变量")

    async def _get(self, path: str, params: Dict) -> Dict:
        params = dict(params or {})
        params["key"] = self.key
        url = f"{BASE}/{path}"
        async with aiohttp.ClientSession() as sess:
            async with sess.get(url, params=params, timeout=12) as r:
                r.raise_for_status()
                return await r.json()

    async def geocode(self, address: str, city: Optional[str] = None) -> Optional[Tuple[float,float]]:
        data = await self._get("geocode/geo", {"address": address, "city": city or ""})
        if data.get("status") != "1" or not data.get("geocodes"):
            return None
        loc = data["geocodes"][0]["location"]  # "lng,lat"
        lng, lat = map(float, loc.split(","))
        return (lng, lat)

    async def place_search(self, keywords: str, city: Optional[str]=None, page: int=1, size: int=10) -> List[Dict]:
        data = await self._get("place/text", {
            "keywords": keywords, "city": city or "", "page": page, "offset": size, "extensions":"all"
        })
        if data.get("status") != "1":
            return []
        pois = data.get("pois", []) or []
        out = []
        for p in pois:
            try:
                lng, lat = map(float, p["location"].split(","))
            except Exception:
                continue
            out.append({
                "name": p.get("name"), "addr": p.get("address"),
                "lng": lng, "lat": lat,
                "type": p.get("type"),
                "biz_ext": p.get("biz_ext", {}),
                "photos": p.get("photos", [])
            })
        return out

    async def driving_route(self, origin: Tuple[float,float], dest: Tuple[float,float], waypoints: List[Tuple[float,float]]=[]):
        def fmt(ll): return f"{ll[0]},{ll[1]}"
        params = {
            "origin": fmt(origin),
            "destination": fmt(dest),
            "extensions":"all",
            "strategy": "0",
            "show_fields": "cost,tmcs"
        }
        if waypoints:
            params["waypoints"] = "|".join(fmt(w) for w in waypoints)
        data = await self._get("direction/driving", params)
        return data if data.get("status") == "1" else None

def haversine(a: Tuple[float,float], b: Tuple[float,float]) -> float:
    R = 6371000.0
    (lng1, lat1), (lng2, lat2) = a, b
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = phi2 - phi1
    dl = math.radians(lng2 - lng1)
    h = (math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dl/2)**2)
    return 2*R*math.asin(math.sqrt(h))
