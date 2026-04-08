"""
Reference implementation of the ITFC incentive-allocation algorithms from
main.pdf (TCC 2026 submission):

  - Algorithm 1: Graph Reduction (BFS, keeps links on any shortest path
                 from the source s).
  - Algorithm 2: Incentive Allocation (per-level multipliers r_n and
                 per-node shares proportional to p_i / g_{d_i}).
  - Algorithm 3: Incentive Allocation for Serving User Nodes.

Notation follows Table 1 of the paper exactly. The helper `run_transaction`
composes Algorithms 1 and 2 into the per-transaction pipeline of Section 5
of the paper.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import List, Sequence, Tuple

import numpy as np

INF = np.iinfo(np.int32).max  # sentinel for "unreachable"


# ---------------------------------------------------------------------------
# Algorithm 1 — Graph Reduction
# ---------------------------------------------------------------------------

def graph_reduction(
    adj: Sequence[np.ndarray], s: int
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Algorithm 1: Graph Reduction via BFS.

    Parameters
    ----------
    adj : list whose i-th element is a numpy int array of neighbours of
          cloud node i.
    s   : index of the source cloud node (the cloud node that serves the
          payer h and initiates broadcasting of the transaction).

    Returns
    -------
    E_prime_src : int array of tail endpoints of each link in E' (sorted
                  by source), so that the k-th link is (E_prime_src[k], E_prime_dst[k]).
    E_prime_dst : int array of head endpoints of each link in E'.
    D           : int array of length |V|, D[i] = d_i (BFS level), with
                  unreachable nodes equal to INF.
    """
    n = len(adj)
    D = np.full(n, INF, dtype=np.int64)
    D[s] = 0
    Q: deque[int] = deque([s])
    # BFS
    while Q:
        i = Q.popleft()
        nbrs = adj[i]
        for j in nbrs:
            if D[j] == INF:
                D[j] = D[i] + 1
                Q.append(int(j))
    # Collect E' = { (i, j) : d_j = d_i + 1 } using numpy where possible.
    src_list: List[np.ndarray] = []
    dst_list: List[np.ndarray] = []
    for i in range(n):
        if D[i] == INF:
            continue
        nbrs = adj[i]
        if len(nbrs) == 0:
            continue
        d_nbrs = D[nbrs]
        mask = d_nbrs == D[i] + 1
        if mask.any():
            keep = nbrs[mask]
            src_list.append(np.full(keep.shape, i, dtype=np.int64))
            dst_list.append(keep.astype(np.int64))
    if src_list:
        E_src = np.concatenate(src_list)
        E_dst = np.concatenate(dst_list)
    else:
        E_src = np.zeros(0, dtype=np.int64)
        E_dst = np.zeros(0, dtype=np.int64)
    return E_src, E_dst, D


# ---------------------------------------------------------------------------
# Algorithm 2 — Incentive Allocation
# ---------------------------------------------------------------------------

def incentive_allocation(
    num_nodes: int,
    E_prime_src: np.ndarray,
    D: np.ndarray,
    w: float,
) -> Tuple[np.ndarray, np.ndarray]:
    """Algorithm 2: Incentive Allocation.

    Computes a_i = (p_i * r_{d_i} * w) / (g_{d_i} * S) as in the paper.

    Returns
    -------
    a : numpy array of length |V| with a_i the revenue allocated to node i.
    p : numpy int array of length |V| with p_i the outdegree of i in (V, E').
    """
    n = num_nodes
    # Line 3–5: compute outdegree p_i in E'.
    p = np.bincount(E_prime_src, minlength=n).astype(np.int64)
    # Line 6–9: compute c_{d_i} and g_{d_i}.
    reachable = D != INF
    if not reachable.any():
        return np.zeros(n, dtype=np.float64), p
    max_lvl = int(D[reachable].max())
    size = max_lvl + 2
    c = np.bincount(D[reachable], minlength=size).astype(np.int64)
    # g[level] = sum of p_i over nodes with that level.
    g = np.zeros(size, dtype=np.int64)
    np.add.at(g, D[reachable], p[reachable])

    # Line 10: find maximum level M with c_M != 0.
    nonzero_levels = np.nonzero(c)[0]
    M = int(nonzero_levels.max())
    if M < 2:
        # No intermediate relay levels: nothing to allocate.
        return np.zeros(n, dtype=np.float64), p

    # Line 11–14: compute r_n for n in [1, M-1] downward.
    r = np.zeros(size, dtype=np.float64)
    r[M - 1] = 1.0
    for lvl in range(M - 2, 0, -1):
        r[lvl] = r[lvl + 1] * ((c[lvl] - 1) * c[lvl + 1] + 1) / 2.0

    # S = sum of the level multipliers (paper §5.3 narrative text).
    S = float(r[1:M].sum())
    if S <= 0.0:
        return np.zeros(n, dtype=np.float64), p

    # Line 16–18: per-node revenue.
    a = np.zeros(n, dtype=np.float64)
    # Only intermediate levels (1 .. M-1) earn relay revenue.
    mask = reachable & (D >= 1) & (D < M) & (p > 0)
    if mask.any():
        di = D[mask]
        a[mask] = (p[mask] * r[di] * w) / (g[di] * S)
    return a, p


# ---------------------------------------------------------------------------
# Algorithm 3 — Incentive Allocation for Serving User Nodes
# ---------------------------------------------------------------------------

def serving_allocation(
    num_nodes: int,
    U_sizes: Sequence[int],
    w1: float,
) -> np.ndarray:
    """Algorithm 3: distribute w1 proportionally to the number of active
    user nodes served by each cloud node."""
    U = np.asarray(U_sizes, dtype=np.float64)
    total = float(U.sum())
    if total == 0.0:
        return np.zeros(num_nodes, dtype=np.float64)
    return w1 * U / total


# ---------------------------------------------------------------------------
# Convenience wrapper for a single transaction
# ---------------------------------------------------------------------------

@dataclass
class TxResult:
    source: int
    a: np.ndarray                 # a_i from Algorithm 2
    forward_count: np.ndarray     # p_i in E' (forwarding work on this tx)


def run_transaction(
    adj: Sequence[np.ndarray],
    source: int,
    w: float,
) -> TxResult:
    E_src, _E_dst, D = graph_reduction(adj, source)
    a, p = incentive_allocation(len(adj), E_src, D, w)
    return TxResult(source=source, a=a, forward_count=p)
