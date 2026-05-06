"""
Section 8.5 supplementary experiment: ITFC deployment performance overhead.

Two experiments, each producing multi-line data for Fig. 6:

  A — Algorithmic computation latency
      (a1) Per-tx latency vs. |V|: Algorithm 1 alone vs. Algorithms 1+2
      (a2) Block latency vs. tx_count for |V| in {500, 1000, 2000, 5000}

  B — Topological storage overhead
      (b1) Per-block storage (KB) vs. |V|: alloc / topology / total
      (b2) Cumulative blockchain size (MB) vs. blocks for four |V| values

Run:
    python3 -m simulation.experiment_8_5
"""

from __future__ import annotations

import json
import os
import time
from typing import List

import numpy as np
import networkx as nx

from simulation.itfc import graph_reduction, incentive_allocation, run_transaction


# ---------------------------------------------------------------------------
# Topology generator
# ---------------------------------------------------------------------------

def _to_adj(G: "nx.Graph", num_nodes: int) -> List[np.ndarray]:
    return [np.fromiter(G.neighbors(i), dtype=np.int64) for i in range(num_nodes)]


def make_doar_like(num_nodes: int, rng: np.random.Generator) -> List[np.ndarray]:
    G = nx.barabasi_albert_graph(num_nodes, m=4, seed=int(rng.integers(0, 2**31 - 1)))
    over = [v for v, d in G.degree() if d > 60]
    for v in over:
        nbrs = sorted(G.neighbors(v), key=lambda u: -G.degree(u))
        for u in nbrs:
            if G.degree(v) <= 60:
                break
            if G.degree(u) > 4:
                G.remove_edge(v, u)
    low = [v for v, d in G.degree() if d < 4]
    for v in low:
        while G.degree(v) < 4:
            u = int(rng.integers(0, num_nodes))
            if u != v and not G.has_edge(u, v):
                G.add_edge(u, v)
    return _to_adj(G, num_nodes)


def make_holme_kim(num_nodes: int, rng: np.random.Generator) -> List[np.ndarray]:
    """Holme-Kim power-law cluster graph (m=4, p=0.12).
    p=0.12 yields clustering ~0.068, matching Bitcoin mainnet (§8.4).
    """
    G = nx.powerlaw_cluster_graph(num_nodes, 4, 0.12,
                                   seed=int(rng.integers(0, 2**31 - 1)))
    return _to_adj(G, num_nodes)


def make_watts_strogatz(num_nodes: int, rng: np.random.Generator) -> List[np.ndarray]:
    """Watts-Strogatz small-world graph (k=8, p=0.1), as used in §8.2 and §8.4."""
    G = nx.watts_strogatz_graph(num_nodes, 8, 0.1,
                                seed=int(rng.integers(0, 2**31 - 1)))
    return _to_adj(G, num_nodes)


# ---------------------------------------------------------------------------
# Experiment A1 — Per-tx latency vs. |V|: Alg1+2 for three topologies
# ---------------------------------------------------------------------------

SIZES_A1 = [500, 1000, 2000, 5000, 10000, 20000]
W_PER_TX = 0.5
SAMPLE_TXS_A1 = 50  # transactions sampled per seed to keep runtime tractable


def _time_alg12(adj: List[np.ndarray], sources: List[int]) -> float:
    """Time Algorithms 1+2 (full incentive allocation) over all sources."""
    n = len(adj)
    t0 = time.perf_counter()
    for s in sources:
        E_src, _E_dst, D = graph_reduction(adj, s)
        incentive_allocation(n, E_src, D, W_PER_TX)
    return time.perf_counter() - t0


TOPOLOGY_GENERATORS = {
    "Doar": make_doar_like,
    "HK": make_holme_kim,
    "WS": make_watts_strogatz,
}


def experiment_a1_latency_vs_size() -> List[dict]:
    """Per-tx latency for the Alg 1+2 pipeline across network sizes,
    for Doar, Holme-Kim, and Watts-Strogatz topologies (same three as §8.4).

    Returns a list of dicts with keys:
      topology, num_nodes, mean_edges, alg12_ms, alg12_se_ms
    """
    results = []
    for topo_name, topo_fn in TOPOLOGY_GENERATORS.items():
        for num_nodes in SIZES_A1:
            print(f"  [A1] {topo_name}  |V|={num_nodes:>6}  sample_tx={SAMPLE_TXS_A1} ...", flush=True)
            alg12_times: List[float] = []
            edge_counts: List[int] = []
            for seed in range(3):
                rng = np.random.default_rng(seed * 37 + 5)
                adj = topo_fn(num_nodes, rng)
                edge_counts.append(sum(len(a) for a in adj) // 2)
                sample = rng.choice(num_nodes, size=SAMPLE_TXS_A1, replace=False).tolist()
                t12 = _time_alg12(adj, sample) / SAMPLE_TXS_A1 * 1000.0
                alg12_times.append(t12)
                print(f"      seed={seed}  alg1+2={t12:.3f} ms", flush=True)

            def _ms(lst: List[float]) -> tuple:
                m = float(np.mean(lst))
                s = float(np.std(lst, ddof=1) / np.sqrt(len(lst)))
                return round(m, 4), round(s, 4)

            a12m, a12s = _ms(alg12_times)
            results.append({
                "topology": topo_name,
                "num_nodes": num_nodes,
                "mean_edges": round(float(np.mean(edge_counts)), 1),
                "alg12_ms": a12m, "alg12_se_ms": a12s,
            })
            print(f"      -> alg1+2={a12m:.3f}±{a12s:.3f} ms", flush=True)
    return results


# ---------------------------------------------------------------------------
# Experiment A2 — Block latency vs. tx_count for multiple |V|
# ---------------------------------------------------------------------------

TX_COUNTS_A2 = [50, 100, 200, 500, 1000, 2000]
SIZES_A2 = [500, 1000, 2000, 5000]  # four lines in subplot (b)


def experiment_a2_latency_vs_txcount() -> List[dict]:
    """Block latency vs. tx_count for each |V| in SIZES_A2.

    Returns a list of dicts with keys: num_nodes, tx_count, block_latency_s.
    """
    results = []
    for num_nodes in SIZES_A2:
        print(f"  [A2] |V|={num_nodes} ...", flush=True)
        adjs: List[List[np.ndarray]] = []
        for seed in range(3):
            rng = np.random.default_rng(seed * 53 + 11 + num_nodes)
            adjs.append(make_doar_like(num_nodes, rng))

        rng_src = np.random.default_rng(99 + num_nodes)
        for tx_count in TX_COUNTS_A2:
            times: List[float] = []
            for seed in range(3):
                # Allow repetition so tx_count can exceed |V|.
                sources = rng_src.choice(
                    num_nodes, size=tx_count, replace=True
                ).tolist()
                t0 = time.perf_counter()
                for s in sources:
                    run_transaction(adjs[seed], source=s, w=W_PER_TX)
                times.append(time.perf_counter() - t0)
            mean_t = float(np.mean(times))
            results.append({"num_nodes": num_nodes, "tx_count": tx_count,
                            "block_latency_s": round(mean_t, 6)})
            print(f"      tx_count={tx_count:>5}  block={mean_t:.3f}s", flush=True)
    return results


# ---------------------------------------------------------------------------
# Experiment B — Storage overhead
# ---------------------------------------------------------------------------

BYTES_PER_ALLOC_RECORD = 28   # 20-byte address + 8-byte revenue (§6.4)
BYTES_PER_TOPO_EVENT = 41     # two 20-byte addresses + 1 type byte
CHURN_FRACTION = 0.005        # 0.5% of edges change per block

SIZES_B1 = [500, 1000, 2000, 5000, 10000, 22000, 50000]
BLOCKS_B2 = [1, 10, 50, 100, 500, 1000]
SIZES_B2 = [5000, 10000, 22000, 50000]  # four lines in subplot (d)


def _edges_for_ba(num_nodes: int) -> float:
    return 4.0 * (num_nodes - 4)


def _storage_per_block_kb(num_nodes: int) -> dict:
    ne = _edges_for_ba(num_nodes)
    alloc = num_nodes * BYTES_PER_ALLOC_RECORD / 1024.0
    topo = CHURN_FRACTION * ne * BYTES_PER_TOPO_EVENT / 1024.0
    return {"alloc_kb": alloc, "topology_kb_per_block": topo,
            "total_kb_per_block": alloc + topo}


def experiment_b_storage() -> dict:
    print("  [B1] storage per block vs. |V| ...", flush=True)
    vs_nodes = []
    for num_nodes in SIZES_B1:
        s = _storage_per_block_kb(num_nodes)
        vs_nodes.append({"num_nodes": num_nodes,
                         "alloc_kb": round(s["alloc_kb"], 4),
                         "topology_kb_per_block": round(s["topology_kb_per_block"], 4),
                         "total_kb_per_block": round(s["total_kb_per_block"], 4)})
        print(f"      |V|={num_nodes:>6}  alloc={s['alloc_kb']:.1f} KB  "
              f"topo={s['topology_kb_per_block']:.1f} KB  "
              f"total={s['total_kb_per_block']:.1f} KB", flush=True)

    print(f"  [B2] cumulative storage for |V| in {SIZES_B2} ...", flush=True)
    cumulative_by_size: List[dict] = []
    for num_nodes in SIZES_B2:
        total_kb = _storage_per_block_kb(num_nodes)["total_kb_per_block"]
        for nb in BLOCKS_B2:
            cumulative_by_size.append({
                "num_nodes": num_nodes,
                "num_blocks": nb,
                "cumulative_mb": round(total_kb * nb / 1024.0, 6),
            })
        print(f"      |V|={num_nodes}  per_block={total_kb:.1f} KB  "
              f"@1000blk={total_kb*1000/1024:.1f} MB", flush=True)

    return {"vs_nodes": vs_nodes, "cumulative": cumulative_by_size}


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main() -> None:
    out_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "results"))
    os.makedirs(out_dir, exist_ok=True)

    print("[experiment_8_5] A1: per-tx latency vs. |V| (Alg1 vs Alg1+2)", flush=True)
    t0 = time.perf_counter()
    latency_vs_size = experiment_a1_latency_vs_size()
    print(f"  -> done in {time.perf_counter()-t0:.1f}s", flush=True)
    with open(os.path.join(out_dir, "latency_vs_size.json"), "w") as fh:
        json.dump(latency_vs_size, fh, indent=2)

    print("[experiment_8_5] A2: block latency vs. tx_count, multi-|V|", flush=True)
    t0 = time.perf_counter()
    latency_vs_txcount = experiment_a2_latency_vs_txcount()
    print(f"  -> done in {time.perf_counter()-t0:.1f}s", flush=True)
    with open(os.path.join(out_dir, "latency_vs_txcount.json"), "w") as fh:
        json.dump(latency_vs_txcount, fh, indent=2)

    print("[experiment_8_5] B: storage overhead", flush=True)
    storage = experiment_b_storage()
    with open(os.path.join(out_dir, "storage.json"), "w") as fh:
        json.dump(storage, fh, indent=2)

    print("[experiment_8_5] all done.", flush=True)


if __name__ == "__main__":
    main()
