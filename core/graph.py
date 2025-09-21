# 网格图与POI评分注入
# TravelBird-main/core/graph.py
from typing import Tuple, Dict, List
from dataclasses import dataclass, field
import math

Coord = Tuple[float, float]     # (lng, lat)
NodeId = Tuple[int, int]        # 网格索引

@dataclass
class Node:
    id: NodeId
    lnglat: Coord
    scenic: float = 0.0          # 出片指数（越大越好）
    quiet: float = 0.0           # 安静度（越大越好）
    traffic_penalty: float = 0.0 # 路况惩罚（越小越好）

@dataclass
class GridGraph:
    nodes: Dict[NodeId, Node] = field(default_factory=dict)
    neighbors: Dict[NodeId, List[NodeId]] = field(default_factory=dict)

    def add_node(self, n: Node):
        self.nodes[n.id] = n

    def add_edge_undirected(self, a: NodeId, b: NodeId):
        self.neighbors.setdefault(a, []).append(b)
        self.neighbors.setdefault(b, []).append(a)

def lerp(a: float, b: float, t: float) -> float: return a + (b-a)*t

def make_grid(start: Coord, end: Coord, n: int = 20) -> GridGraph:
    (lng1, lat1), (lng2, lat2) = start, end
    min_lng, max_lng = min(lng1, lng2), max(lng1, lng2)
    min_lat, max_lat = min(lat1, lat2), max(lat1, lat2)
    pad = 0.005  # 约500m缓冲
    min_lng -= pad; max_lng += pad; min_lat -= pad; max_lat += pad

    g = GridGraph()
    for i in range(n):
        for j in range(n):
            lng = lerp(min_lng, max_lng, i/(n-1))
            lat = lerp(min_lat, max_lat, j/(n-1))
            g.add_node(Node(id=(i,j), lnglat=(lng, lat)))
    dirs = [(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]
    for i in range(n):
        for j in range(n):
            for dx, dy in dirs:
                x, y = i+dx, j+dy
                if 0 <= x < n and 0 <= y < n:
                    g.add_edge_undirected((i,j), (x,y))
    return g

def inject_poi_scores(graph: GridGraph, pois: List[Dict], scenic_weight: float = 1.0, quiet_weight: float = 1.0):
    # 简化：有照片 → 出片更高；“公园/景点”提升出片；“咖啡/图书馆”更安静
    for p in pois:
        lng, lat = p["lng"], p["lat"]
        base_scenic = 0.6 + 0.4*min(1.0, len(p.get("photos", []))/3.0)
        base_quiet  = 0.5
        t = (p.get("type") or "")
        if "公园" in t or "景点" in t: base_scenic += 0.2
        if "咖啡" in t or "图书馆" in t: base_quiet  += 0.2

        for node in graph.nodes.values():
            d = haversine(node.lnglat, (lng, lat))
            influence = math.exp(-d/300.0)  # 300m 衰减
            node.scenic += scenic_weight * base_scenic * influence
            node.quiet  += quiet_weight  * base_quiet  * influence

def haversine(a: Coord, b: Coord) -> float:
    R = 6371000.0
    (lng1, lat1), (lng2, lat2) = a, b
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = phi2 - phi1
    dl = math.radians(lng2 - lng1)
    h = (math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dl/2)**2)
    return 2*R*math.asin(math.sqrt(h))
