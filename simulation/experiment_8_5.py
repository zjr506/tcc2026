"""
Section 8.5 supplementary experiment: ITFC deployment performance overhead.

Measures algorithmic computation latency and topological storage overhead,
validating the §6.4 storage estimate and providing empirical latency numbers.

Two experiments:
  A — Algorithmic computation latency
      (a1) Per-transaction and block latency vs. network size |V|
      (a2) Block latency vs. number of transactions per block (|V|=5000)
  B — Topological storage overhead
      (b1) Per-block storage (KB) vs. network size |V|
      (b2) Cumulative blockchain size (MB) vs. number of blocks (|V|=22000)

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

from simulation.itfc import run_transaction


# ---------------------------------------------------------------------------
# Topology generator (copied from experiment_8_4, not imported)
# ---------------------------------------------------------------------------

def _to_adj(G: "nx.Graph", num_nodes: int) -> List[np.ndarray]:
    return [np.fromiter(G.neighbors(i), dtype=np.int64) for i in range(num_nodes)]


def make_doar_like(num_nodes: int, rng: np.random.Generator) -> List[np.ndarray]:
    """Hierarchical/redundant test network with degrees in [4, 60], in the
    spirit of Doar's algorithm used in §8.1 of main.pdf.

    A Barabasi-Albert backbone provides the hierarchical, long-tailed
    degree distribution; we then cap the maximum degree at 60 by pruning
    edges between over-connected hubs, and floor the minimum at 4.
    """
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


# ---------------------------------------------------------------------------
# Experiment A1 — Latency vs. network size
# ---------------------------------------------------------------------------

SIZES_A1 = [500, 1000, 2000, 5000, 10000, 20000]
W_PER_TX = 0.5
# Sample this many transactions per run so per-tx timing is accurate but
# total experiment runtime stays under a few minutes for all |V| sizes.
SAMPLE_TXS_A1 = 50


def _run_block_timed(adj: List[np.ndarray], sources: List[int]) -> float:
    """Run run_transaction for every source and return total elapsed seconds."""
    t0 = time.perf_counter()
    for s in sources:
        run_transaction(adj, source=s, w=W_PER_TX)
    return time.perf_counter() - t0


def experiment_a1_latency_vs_size() -> List[dict]:
    """Measure per-transaction latency across network sizes.

    We sample SAMPLE_TXS_A1 random source nodes per seed and divide the
    total elapsed time by SAMPLE_TXS_A1 to obtain per-tx latency. This
    keeps total runtime tractable for large |V|. Three seeds per size.
    """
    results = []
    for num_nodes in SIZES_A1:
        num_seeds = 3
        print(
            f"  [A1] |V|={num_nodes:>6}  seeds={num_seeds}"
            f"  sample_tx={SAMPLE_TXS_A1} ...", flush=True
        )
        seed_per_tx: List[float] = []
        seed_edges: List[int] = []
        for seed in range(num_seeds):
            rng = np.random.default_rng(seed * 37 + 5)
            adj = make_doar_like(num_nodes, rng)
            num_edges = sum(len(a) for a in adj) // 2
            seed_edges.append(num_edges)
            sample = rng.choice(num_nodes, size=SAMPLE_TXS_A1, replace=False).tolist()
            elapsed = _run_block_timed(adj, sample)
            per_tx = elapsed / SAMPLE_TXS_A1 * 1000.0  # ms
            seed_per_tx.append(per_tx)
            print(f"      seed={seed}  |E|={num_edges}  per_tx={per_tx:.4f} ms", flush=True)

        mean_ms = float(np.mean(seed_per_tx))
        se_ms = float(np.std(seed_per_tx, ddof=1) / np.sqrt(num_seeds))
        mean_edges = float(np.mean(seed_edges))
        results.append({
            "num_nodes": num_nodes,
            "mean_edges": round(mean_edges, 1),
            "per_tx_latency_ms": round(mean_ms, 6),
            "per_tx_latency_se_ms": round(se_ms, 6),
        })
        print(f"      -> per_tx={mean_ms:.4f} ± {se_ms:.4f} ms", flush=True)
    return results


# ---------------------------------------------------------------------------
# Experiment A2 — Latency vs. tx count (|V|=5000 fixed)
# ---------------------------------------------------------------------------

TX_COUNTS_A2 = [50, 100, 200, 500, 1000, 2000]
FIXED_V_A2 = 2000


def experiment_a2_latency_vs_txcount() -> List[dict]:
    """Measure block latency as tx_count varies, with |V|=5000 fixed.

    Build one graph per seed and sample sources without replacement.
    Use 3 seeds.
    """
    print(f"  [A2] |V|={FIXED_V_A2} fixed, varying tx_count={TX_COUNTS_A2} ...", flush=True)
    num_seeds = 3
    # Build graphs once per seed.
    adjs: List[List[np.ndarray]] = []
    for seed in range(num_seeds):
        rng = np.random.default_rng(seed * 53 + 11)
        adjs.append(make_doar_like(FIXED_V_A2, rng))

    results = []
    rng_src = np.random.default_rng(99)
    for tx_count in TX_COUNTS_A2:
        times: List[float] = []
        for seed in range(num_seeds):
            adj = adjs[seed]
            # Sample tx_count distinct sources.
            sources = rng_src.choice(FIXED_V_A2, size=tx_count, replace=False).tolist()
            elapsed = _run_block_timed(adj, sources)
            times.append(elapsed)
        mean_t = float(np.mean(times))
        results.append({
            "tx_count": tx_count,
            "block_latency_s": round(mean_t, 6),
        })
        print(f"      tx_count={tx_count:>5}  block={mean_t:.4f}s", flush=True)
    return results


# ---------------------------------------------------------------------------
# Experiment B — Storage overhead
# ---------------------------------------------------------------------------

# §6.4: incentive allocation record = 20-byte address + 8-byte revenue = 28 bytes
BYTES_PER_ALLOC_RECORD = 28
# Topology event = two 20-byte addresses + 1 type byte = 41 bytes
BYTES_PER_TOPO_EVENT = 41
# Churn fraction per block: p=0.005 of total |E| edges change
CHURN_FRACTION = 0.005
# The paper's §6.4 reference estimate
PAPER_ESTIMATE_V = 22000
PAPER_ESTIMATE_KB = 616.0


def _edges_for_ba(num_nodes: int) -> float:
    """Expected number of undirected edges for BA(m=4): roughly m*(V-m) edges."""
    return 4.0 * (num_nodes - 4)


SIZES_B1 = [500, 1000, 2000, 5000, 10000, 22000, 50000]
BLOCKS_B2 = [1, 10, 50, 100, 500, 1000]
FIXED_V_B2 = 22000


def experiment_b_storage() -> dict:
    """Compute storage overhead analytically (no graph construction needed).

    Incentive allocation: |V| * 28 bytes per block.
    Topology change: p * |E| events per block * 41 bytes each.
    Uses |E| ≈ 4*(|V|-4) for Barabasi-Albert m=4 graph.
    """
    print("  [B1] storage vs. |V| ...", flush=True)
    vs_nodes = []
    for num_nodes in SIZES_B1:
        num_edges = _edges_for_ba(num_nodes)
        alloc_bytes = num_nodes * BYTES_PER_ALLOC_RECORD
        topo_events = CHURN_FRACTION * num_edges
        topo_bytes = topo_events * BYTES_PER_TOPO_EVENT
        alloc_kb = alloc_bytes / 1024.0
        topo_kb = topo_bytes / 1024.0
        total_kb = alloc_kb + topo_kb
        vs_nodes.append({
            "num_nodes": num_nodes,
            "alloc_kb": round(alloc_kb, 4),
            "topology_kb_per_block": round(topo_kb, 4),
            "total_kb_per_block": round(total_kb, 4),
        })
        print(
            f"      |V|={num_nodes:>6}  alloc={alloc_kb:.2f} KB  "
            f"topo={topo_kb:.2f} KB  total={total_kb:.2f} KB",
            flush=True,
        )

    print(f"  [B2] cumulative storage, |V|={FIXED_V_B2} ...", flush=True)
    # Per-block storage for |V|=22000.
    num_edges_22k = _edges_for_ba(FIXED_V_B2)
    alloc_per_block_kb = FIXED_V_B2 * BYTES_PER_ALLOC_RECORD / 1024.0
    topo_per_block_kb = (CHURN_FRACTION * num_edges_22k * BYTES_PER_TOPO_EVENT) / 1024.0
    total_per_block_kb = alloc_per_block_kb + topo_per_block_kb

    cumulative = []
    for num_blocks in BLOCKS_B2:
        cumulative_kb = total_per_block_kb * num_blocks
        cumulative_mb = cumulative_kb / 1024.0
        cumulative.append({
            "num_blocks": num_blocks,
            "cumulative_mb": round(cumulative_mb, 6),
        })
        print(
            f"      blocks={num_blocks:>5}  cumulative={cumulative_mb:.4f} MB",
            flush=True,
        )

    return {"vs_nodes": vs_nodes, "cumulative": cumulative}


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main() -> None:
    here = os.path.dirname(__file__)
    out_dir = os.path.abspath(os.path.join(here, "..", "results"))
    os.makedirs(out_dir, exist_ok=True)

    # --- Experiment A1: latency vs. size ---
    print("[experiment_8_5] Experiment A1: latency vs. network size", flush=True)
    t0 = time.perf_counter()
    latency_vs_size = experiment_a1_latency_vs_size()
    print(f"  -> A1 done in {time.perf_counter() - t0:.1f}s", flush=True)

    path_a1 = os.path.join(out_dir, "latency_vs_size.json")
    with open(path_a1, "w") as fh:
        json.dump(latency_vs_size, fh, indent=2)
    print(f"  -> saved {path_a1}", flush=True)

    # --- Experiment A2: latency vs. tx count ---
    print("[experiment_8_5] Experiment A2: latency vs. tx count (|V|=5000)", flush=True)
    t0 = time.perf_counter()
    latency_vs_txcount = experiment_a2_latency_vs_txcount()
    print(f"  -> A2 done in {time.perf_counter() - t0:.1f}s", flush=True)

    path_a2 = os.path.join(out_dir, "latency_vs_txcount.json")
    with open(path_a2, "w") as fh:
        json.dump(latency_vs_txcount, fh, indent=2)
    print(f"  -> saved {path_a2}", flush=True)

    # --- Experiment B: storage overhead ---
    print("[experiment_8_5] Experiment B: storage overhead", flush=True)
    t0 = time.perf_counter()
    storage = experiment_b_storage()
    print(f"  -> B done in {time.perf_counter() - t0:.3f}s", flush=True)

    path_b = os.path.join(out_dir, "storage.json")
    with open(path_b, "w") as fh:
        json.dump(storage, fh, indent=2)
    print(f"  -> saved {path_b}", flush=True)

    print("[experiment_8_5] all done.", flush=True)


if __name__ == "__main__":
    main()
