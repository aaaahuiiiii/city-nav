# aiohttp路由（/api/geocode /api/places /api/plan_moa /api/plan_drive）
# TravelBird-main/routes/planner_routes.py
from aiohttp import web
from typing import List, Tuple, Dict
import os
from api.gaode_client import GaoDeClient, haversine
from core.graph import make_grid, inject_poi_scores
from core.moa_star import moa_star, Weights

DEFAULT_CITY = os.getenv("DEFAULT_CITY", "昆明")

def path_nodes_to_coords(graph, path):
    return [graph.nodes[nid].lnglat for nid in path]

async def geocode(request: web.Request):
    body = await request.json()
    q = (body.get("q") or "").strip()
    city = (body.get("city") or DEFAULT_CITY).strip()
    cli = GaoDeClient()
    ll = await cli.geocode(q, city)
    return web.json_response({"ok": bool(ll), "lnglat": ll, "city": city})

async def places(request: web.Request):
    body = await request.json()
    kw = (body.get("keywords") or "").strip()
    city = (body.get("city") or DEFAULT_CITY).strip()
    size = int(body.get("size", 10))
    cli = GaoDeClient()
    pois = await cli.place_search(kw, city, page=1, size=size)
    return web.json_response({"ok": True, "pois": pois})

async def plan_moa(request: web.Request):
    """
    body:
      { start: {lng,lat}, end: {lng,lat},
        scenic_kw?: "咖啡馆", quiet_kw?: "公园",
        weights?: { w_dist, w_time, w_scenic, w_quiet },
        grid_n?: 24 }
    """
    body = await request.json()
    start = (float(body["start"]["lng"]), float(body["start"]["lat"]))
    end   = (float(body["end"]["lng"]),   float(body["end"]["lat"]))
    grid_n = int(body.get("grid_n", 24))

    w = body.get("weights", {}) or {}
    ws = Weights(
        w_dist=float(w.get("w_dist", 1.0)),
        w_time=float(w.get("w_time", 0.0)),
        w_scenic=float(w.get("w_scenic", 0.0)),
        w_quiet=float(w.get("w_quiet", 0.0)),
    )

    cli = GaoDeClient()
    graph = make_grid(start, end, n=grid_n)

    scenic_kw = (body.get("scenic_kw") or "").strip()
    quiet_kw  = (body.get("quiet_kw")  or "").strip()
    pois = []
    if scenic_kw:
        pois += (await cli.place_search(scenic_kw, city=DEFAULT_CITY, size=15))
    if quiet_kw:
        pois += (await cli.place_search(quiet_kw,  city=DEFAULT_CITY, size=15))
    inject_poi_scores(graph, pois, scenic_weight=1.0, quiet_weight=1.0)

    def nearest_id(lnglat):
        best, bestd = None, 1e18
        for nid, node in graph.nodes.items():
            d = haversine(node.lnglat, lnglat)
            if d < bestd: best, bestd = nid, d
        return best

    s_id, e_id = nearest_id(start), nearest_id(end)
    path = moa_star(graph, s_id, e_id, ws, coord_of=lambda nid: graph.nodes[nid].lnglat)
    if not path:
        return web.json_response({"ok": False, "error": "未找到路径"})

    coords = path_nodes_to_coords(graph, path)
    return web.json_response({"ok": True, "polyline": coords, "grid_n": grid_n, "weights": ws.__dict__})

async def plan_drive(request: web.Request):
    body = await request.json()
    start = (float(body["start"]["lng"]), float(body["start"]["lat"]))
    end   = (float(body["end"]["lng"]),   float(body["end"]["lat"]))
    waypoints = [(float(p["lng"]), float(p["lat"])) for p in body.get("waypoints", [])]
    cli = GaoDeClient()
    data = await cli.driving_route(start, end, waypoints)
    return web.json_response({"ok": bool(data), "data": data})

def setup_routes(app: web.Application):
    app.router.add_post("/api/geocode", geocode)
    app.router.add_post("/api/places",  places)
    app.router.add_post("/api/plan_moa", plan_moa)
    app.router.add_post("/api/plan_drive", plan_drive)
