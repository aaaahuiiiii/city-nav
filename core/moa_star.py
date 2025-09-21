# 多目标A*（加权标量化）
# TravelBird-main/core/moa_star.py
from typing import Dict, Tuple, List, Optional
from dataclasses import dataclass
import heapq
from .graph import GridGraph, NodeId, haversine

@dataclass
class Weights:
    w_dist: float = 1.0    # 距离（越小越好）
    w_time: float = 0.0    # 时间/路况惩罚（越小越好）
    w_scenic: float = 0.0  # 出片（越大越好 → 转为负代价）
    w_quiet: float = 0.0   # 安静（越大越好 → 转为负代价）

def normalize(x: float, lo: float, hi: float) -> float:
    if hi <= lo: return 0.0
    return (x - lo) / (hi - lo)

def reconstruct(came: Dict[NodeId, NodeId], cur: NodeId) -> List[NodeId]:
    path = [cur]
    while cur in came:
        cur = came[cur]
        path.append(cur)
    path.reverse()
    return path

def moa_star(graph: GridGraph, start: NodeId, goal: NodeId, weights: Weights, coord_of) -> Optional[List[NodeId]]:
    # 估计邻边距离范围
    dists = []
    for u, nbrs in graph.neighbors.items():
        for v in nbrs:
            dists.append(haversine(coord_of(u), coord_of(v)))
    d_lo, d_hi = (min(dists), max(dists)) if dists else (1.0, 1.0)

    s_vals = [n.scenic for n in graph.nodes.values()]
    q_vals = [n.quiet  for n in graph.nodes.values()]
    s_lo, s_hi = (min(s_vals), max(s_vals)) if s_vals else (0.0, 1.0)
    q_lo, q_hi = (min(q_vals), max(q_vals)) if q_vals else (0.0, 1.0)

    openq: List[Tuple[float, NodeId]] = []
    heapq.heappush(openq, (0.0, start))
    came: Dict[NodeId, NodeId] = {}
    g_cost: Dict[NodeId, float] = {start: 0.0}

    def h(n: NodeId) -> float:
        # admissible 启发：终点直线距离 / d_hi
        return haversine(coord_of(n), coord_of(goal)) / max(d_hi, 1e-6)

    while openq:
        _, cur = heapq.heappop(openq)
        if cur == goal:
            return reconstruct(came, cur)

        for nxt in graph.neighbors.get(cur, []):
            d = haversine(coord_of(cur), coord_of(nxt))
            nd = normalize(d, d_lo, d_hi)

            node = graph.nodes[nxt]
            # scenic/quiet 要“最大化” → 代价里取 (1 - 归一化值)
            ns = 1.0 - normalize(node.scenic, s_lo, s_hi)
            nq = 1.0 - normalize(node.quiet,  q_lo, q_hi)

            edge_penalty = (graph.nodes[cur].traffic_penalty + node.traffic_penalty) * 0.5
            nt = normalize(edge_penalty, 0.0, 1.0)

            edge_cost = (weights.w_dist*nd +
                         weights.w_time*nt +
                         weights.w_scenic*ns +
                         weights.w_quiet*nq)

            tentative = g_cost[cur] + edge_cost
            if tentative < g_cost.get(nxt, float("inf")):
                came[nxt] = cur
                g_cost[nxt] = tentative
                f = tentative + h(nxt) * 0.3  # 启发比例可调
                heapq.heappush(openq, (f, nxt))
    return None
