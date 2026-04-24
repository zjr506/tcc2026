"""
Section 8.4 supplementary experiment: ITFC under heterogeneous cloud nodes.

Reproduces Fig. 5 (3 subfigures) of the supplementary subsection:

  (a) per-tier profit rate vs. number of links     (extends Fig. 2(a))
  (b) per-tier sufficient forwarding count vs. links (extends Fig. 2(b))
  (c) Sybil-attack adversary profit rate by tier   (extends Fig. 3(b))

Run:
    python3 -m simulation.experiment_8_4
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, asdict
from typing import Dict, List, Sequence, Tuple

import numpy as np
import networkx as nx

from simulation.itfc import (
    graph_reduction,
    incentive_allocation,
    run_transaction,
)


# ---------------------------------------------------------------------------
# Resource-tier model (matches Section 8.4 of the supplement)
# ---------------------------------------------------------------------------

TIER_NAMES = ("0.40", "0.30", "0.20", "0.10")
TIER_PROBS = (0.40, 0.30, 0.20, 0.10)
TIER_CAPACITY = {
    "0.40": 250,
    "0.30": 1000,
    "0.20": 4000,
    "0.10": 16000,
}
TIER_HASH = {
    "0.40": 1,
    "0.30": 4,
    "0.20": 16,
    "0.10": 64,
}
TIER_UPTIME = {
    "0.40": 0.80,
    "0.30": 0.90,
    "0.20": 0.95,
    "0.10": 0.99,
}


def assign_tiers(num_nodes: int, rng: np.random.Generator) -> List[str]:
    return list(rng.choice(TIER_NAMES, size=num_nodes, p=TIER_PROBS))


# ---------------------------------------------------------------------------
# Topology generators
# ---------------------------------------------------------------------------

def _to_adj(G: nx.Graph, num_nodes: int) -> List[np.ndarray]:
    return [np.fromiter(G.neighbors(i), dtype=np.int64) for i in range(num_nodes)]


def make_doar_like(num_nodes: int, rng: np.random.Generator) -> List[np.ndarray]:
    """Hierarchical/redundant test network with degrees in [4, 60], in the
    spirit of Doar's algorithm [42] used in §8.1 of main.pdf.

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


def make_holme_kim(num_nodes: int, rng: np.random.Generator) -> List[np.ndarray]:
    """Holme-Kim power-law cluster graph (m=4, p=0.5).
    Preserves scale-free degree distribution from Barabási–Albert while
    adding realistic clustering (~0.26 vs BA's ~0.10), better approximating
    the Bitcoin network's measured clustering coefficient of 0.1–0.3.
    """
    G = nx.powerlaw_cluster_graph(num_nodes, 4, 0.5,
                                   seed=int(rng.integers(0, 2**31 - 1)))
    return _to_adj(G, num_nodes)


def make_watts_strogatz(
    num_nodes: int, mean_degree: int, rng: np.random.Generator
) -> List[np.ndarray]:
    G = nx.watts_strogatz_graph(
        num_nodes, mean_degree, 0.1,
        seed=int(rng.integers(0, 2**31 - 1)),
    )
    return _to_adj(G, num_nodes)


# ---------------------------------------------------------------------------
# Per-tier capacity-scaled aggregation helper
# ---------------------------------------------------------------------------

def aggregate_block(
    adj: Sequence[np.ndarray],
    sources: Sequence[int],
    w_per_tx: float,
    tiers: Sequence[str],
) -> Tuple[np.ndarray, np.ndarray]:
    """Run one block: every node in `sources` issues a transaction with relay
    budget `w_per_tx`. Returns (revenue, forwards) per cloud node.

    Capacity scaling: a node whose total raw forwarding work for the block
    exceeds its tier capacity C_i is credited only for C_i / total of its
    revenue and forwards (the rest is "lost" because downstream peers
    received the transaction from a faster route first, as described in
    §8.4 of the supplement).
    """
    n = len(adj)
    total_rev = np.zeros(n, dtype=np.float64)
    total_forwards = np.zeros(n, dtype=np.int64)
    for s in sources:
        res = run_transaction(adj, source=s, w=w_per_tx)
        total_rev += res.a
        total_forwards += res.forward_count
    # Apply capacity scaling.
    cap = np.array([TIER_CAPACITY[t] for t in tiers], dtype=np.float64)
    scale = np.minimum(1.0, cap / np.maximum(total_forwards, 1))
    return total_rev * scale, np.minimum(total_forwards, cap.astype(np.int64))


# ---------------------------------------------------------------------------
# Experiment A — Fig 5(a) and 5(b)
# ---------------------------------------------------------------------------

@dataclass
class FairnessRecord:
    tier: str
    degree: int
    profit_rate: float
    forwards: float


def experiment_fairness(
    num_nodes: int = 2000,
    num_seeds: int = 5,
    relay_share: float = 0.5,
    f0: float = 1.0,
) -> List[FairnessRecord]:
    """Heterogeneous-resource fairness experiment for Fig 5(a, b).

    Each cloud node serves one user node which broadcasts one transaction
    with fee f0; relay revenue per transaction is relay_share * f0.
    Aggregates per-node profit rate (u-f)/f0 across runs (homogeneous mining
    is assumed for simplicity, as in §8.1 — equal block-generator probability
    so block reward distributes equally across nodes).
    """
    records: List[FairnessRecord] = []
    for seed in range(num_seeds):
        rng = np.random.default_rng(seed * 17 + 1)
        adj = make_doar_like(num_nodes, rng)
        tiers = assign_tiers(num_nodes, rng)

        sources = list(range(num_nodes))  # one tx per cloud node
        w_per_tx = relay_share * f0
        revenue, forwards = aggregate_block(adj, sources, w_per_tx, tiers)

        # Block-generator share goes uniformly to all cloud nodes (§8.1
        # assumption: equal mining probability for fairness measurement).
        block_share = (1.0 - relay_share) * f0 * num_nodes / num_nodes  # = (1-relay_share)*f0
        u = revenue + block_share
        f_cost = f0  # one user transaction fee per cloud node
        profit_rate = (u - f_cost) / f0

        deg = np.array([len(adj[i]) for i in range(num_nodes)], dtype=np.int64)
        for i in range(num_nodes):
            records.append(FairnessRecord(
                tier=tiers[i],
                degree=int(deg[i]),
                profit_rate=float(profit_rate[i]),
                forwards=float(forwards[i]),
            ))
    return records


# ---------------------------------------------------------------------------
# Experiment B — Fig 5(c) Sybil attack by adversary tier
# ---------------------------------------------------------------------------

@dataclass
class SybilRecord:
    adversary_tier: str
    pseudonym_count: int
    profit_rate: float


def experiment_sybil(
    num_honest: int = 500,
    mean_degree: int = 20,
    num_seeds: int = 4,
    fee_fraction: float = 0.10,
    relay_share: float = 0.5,
    f0: float = 1.0,
    pseudonym_range: Sequence[int] = (0, 5, 10, 15, 20, 30, 40, 50),
) -> List[SybilRecord]:
    """Sybil attack experiment for Fig 5(c).

    Honest cloud nodes form a Watts-Strogatz substrate (matching §8.2).
    A randomly chosen node from each tier is converted into the adversary
    and creates x pseudonymous nodes that form a clique with it. Each
    honest tx pays f0; each pseudonym tx pays fee_fraction * f0.
    Profit rate = (u - f)/f0 with f = x * fee_fraction * f0.
    """
    records: List[SybilRecord] = []
    for seed in range(num_seeds):
        rng = np.random.default_rng(seed * 31 + 7)

        # Build the honest WS substrate once per seed.
        adj_honest = make_watts_strogatz(num_honest, mean_degree, rng)
        tiers_honest = assign_tiers(num_honest, rng)
        # Pick one representative adversary candidate of each tier.
        adv_idx_by_tier: Dict[str, int] = {}
        for tier in TIER_NAMES:
            cand = [i for i, t in enumerate(tiers_honest) if t == tier]
            if cand:
                adv_idx_by_tier[tier] = int(rng.choice(cand))

        # Compute the no-attack baseline: same substrate, no pseudonyms.
        # The baseline profit rate for any honest node of a given tier is
        # (honest_relay + honest_block_share - f0) / f0.
        w_h_base = relay_share * f0
        rev_base, _ = aggregate_block(adj_honest, list(range(num_honest)),
                                      w_h_base, tiers_honest)
        block_pool_base = (1 - relay_share) * num_honest * f0
        baseline_by_node = (rev_base + block_pool_base / num_honest - f0) / f0

        for adv_tier, adv_idx in adv_idx_by_tier.items():
            baseline_rate = float(baseline_by_node[adv_idx])
            for x in pseudonym_range:
                # Build extended graph: honest + x pseudonymous nodes,
                # adversary + pseudonyms form a clique.
                n = num_honest + x
                adj_py: List[List[int]] = [list(neigh.tolist()) for neigh in adj_honest]
                for _ in range(x):
                    adj_py.append([])
                clique = [adv_idx] + list(range(num_honest, num_honest + x))
                clique_set = set(clique)
                for a in clique:
                    existing = set(adj_py[a])
                    for b in clique:
                        if a != b and b not in existing:
                            adj_py[a].append(b)
                            existing.add(b)
                adj = [np.asarray(a, dtype=np.int64) for a in adj_py]
                # Pseudonyms inherit the adversary's resource class.
                tiers = list(tiers_honest) + [adv_tier] * x

                # All honest nodes + adversary broadcast 1 tx at fee f0.
                # Each pseudonym broadcasts 1 tx at fee fee_fraction * f0.
                honest_sources = list(range(num_honest))
                pseudo_sources = list(range(num_honest, n))

                rev = np.zeros(n, dtype=np.float64)
                fwd = np.zeros(n, dtype=np.int64)
                # Honest transactions.
                w_h = relay_share * f0
                rev_h, fwd_h = aggregate_block(adj, honest_sources, w_h, tiers)
                rev += rev_h
                fwd += fwd_h
                # Pseudonym transactions (lower fee).
                w_p = relay_share * fee_fraction * f0
                if pseudo_sources:
                    rev_p, fwd_p = aggregate_block(adj, pseudo_sources, w_p, tiers)
                    rev += rev_p
                    fwd += fwd_p

                # Adversary group relay revenue: adv_idx plus all pseudonyms.
                adv_relay = float(rev[adv_idx] + rev[num_honest:].sum())

                # Block-generator share: 50% of all fees, uniformly split
                # across honest nodes only (pseudonyms cannot mine because
                # they cannot contribute hashing power, §8.2).
                total_fees = num_honest * f0 + x * fee_fraction * f0
                block_pool = (1 - relay_share) * total_fees
                adv_block = block_pool / num_honest
                u = adv_relay + adv_block

                # Adversary's out-of-pocket cost: x * y * f0 for the
                # pseudonymous transactions, per §8.2. The adversary's own
                # honest transaction fee f0 is already counted in the
                # baseline subtraction below.
                f_cost = x * fee_fraction * f0
                gross_rate = (u - f_cost - f0) / f0  # -f0 for adv's own tx

                # Extra profit above the no-attack baseline of the same node.
                profit_rate = gross_rate - baseline_rate

                records.append(SybilRecord(
                    adversary_tier=adv_tier,
                    pseudonym_count=int(x),
                    profit_rate=float(profit_rate),
                ))
    return records


# ---------------------------------------------------------------------------
# Topology comparison — how well do BA and HK match real cloud blockchain nets?
# ---------------------------------------------------------------------------

def _graph_from_adj(adj: List[np.ndarray]) -> nx.Graph:
    G = nx.Graph()
    n = len(adj)
    G.add_nodes_from(range(n))
    for u, nbrs in enumerate(adj):
        for v in nbrs:
            if v > u:
                G.add_edge(u, v)
    return G


def topology_comparison(
    sizes: List[int] = (1000, 2000, 5000),
    num_seeds: int = 3,
) -> List[dict]:
    """Measure structural properties of BA and HK topologies at several sizes.

    Metrics: mean degree, degree standard deviation, global clustering
    coefficient, and approximate diameter (BFS from 30 random sources,
    take the max shortest-path tree depth as a lower bound).
    Returns a list of dicts with keys:
      topology, num_nodes, seed,
      mean_degree, std_degree, clustering, approx_diameter
    """
    results = []
    for num_nodes in sizes:
        for topo_name, topo_fn in (("BA", make_doar_like), ("HK", make_holme_kim)):
            for seed in range(num_seeds):
                rng = np.random.default_rng(seed * 41 + 3 + num_nodes)
                adj = topo_fn(num_nodes, rng)
                G = _graph_from_adj(adj)
                degrees = np.array([d for _, d in G.degree()], dtype=float)
                clustering = nx.average_clustering(G)
                # Approximate diameter: max of BFS depths from sample nodes.
                sample = list(
                    np.random.default_rng(seed).choice(num_nodes, size=30, replace=False)
                )
                max_depth = 0
                for src in sample:
                    lengths = nx.single_source_shortest_path_length(G, src)
                    if lengths:
                        max_depth = max(max_depth, max(lengths.values()))
                results.append({
                    "topology": topo_name,
                    "num_nodes": num_nodes,
                    "seed": seed,
                    "mean_degree": round(float(degrees.mean()), 3),
                    "std_degree": round(float(degrees.std()), 3),
                    "clustering": round(clustering, 4),
                    "approx_diameter": int(max_depth),
                })
                print(
                    f"  [topo] {topo_name} |V|={num_nodes} seed={seed}: "
                    f"deg={degrees.mean():.1f}±{degrees.std():.1f}  "
                    f"clust={clustering:.3f}  diam≥{max_depth}",
                    flush=True,
                )
    return results


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main() -> None:
    out_dir = os.path.join(os.path.dirname(__file__), "..", "results")
    out_dir = os.path.abspath(out_dir)
    os.makedirs(out_dir, exist_ok=True)

    print("[experiment_8_4] running fairness experiment (Fig 5a, 5b) ...")
    t0 = time.time()
    fairness = experiment_fairness(num_nodes=2000, num_seeds=5)
    print(f"  -> {len(fairness)} per-node records in {time.time() - t0:.1f}s")

    with open(os.path.join(out_dir, "fairness.json"), "w") as fh:
        json.dump([asdict(r) for r in fairness], fh)

    print("[experiment_8_4] running Sybil-attack experiment (Fig 5c) ...")
    t0 = time.time()
    sybil = experiment_sybil(
        num_honest=300,
        mean_degree=20,
        num_seeds=3,
        fee_fraction=0.10,
        pseudonym_range=(0, 5, 10, 20, 30, 50),
    )
    print(f"  -> {len(sybil)} sybil records in {time.time() - t0:.1f}s")

    with open(os.path.join(out_dir, "sybil.json"), "w") as fh:
        json.dump([asdict(r) for r in sybil], fh)

    print("[experiment_8_4] running topology comparison (BA vs HK) ...")
    topo_cmp = topology_comparison(sizes=[1000, 2000, 5000], num_seeds=3)
    with open(os.path.join(out_dir, "topology_comparison.json"), "w") as fh:
        json.dump(topo_cmp, fh, indent=2)
    print(f"  -> {len(topo_cmp)} topology comparison records")

    print("[experiment_8_4] done.")


if __name__ == "__main__":
    main()
