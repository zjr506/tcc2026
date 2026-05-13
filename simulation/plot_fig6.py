"""
Render Fig. 6 (2x2 grid) for Section 8.5 from results of experiment_8_5.

  (a) Per-node latency rate vs. |V|: Alg 1+2 for Doar, HK, WS
      (flat lines confirm O(|V|) scaling; topology separation visible)
  (b) Block processing latency vs. tx_count for |V| in {500,1000,2000,5000}
  (c) Per-block storage vs. |V|: allocation / topology changes / total / Section 6.4 allocation estimate
  (d) Cumulative blockchain size vs. blocks for four |V| values

Run:
    python3 -m simulation.plot_fig6
"""

from __future__ import annotations

import json
import os
from collections import defaultdict
from typing import List

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

PAPER_ESTIMATE_V = 22000
PAPER_ESTIMATE_KB = 616.0

SIZE_COLORS = {
    500: "#888888",
    1000: "#1f77b4",
    2000: "#ff7f0e",
    5000: "#d62728",
    10000: "#9467bd",
    22000: "#2ca02c",
    50000: "#8c564b",
}
SIZE_MARKERS = {500: "o", 1000: "s", 2000: "^", 5000: "D",
                10000: "v", 22000: "P", 50000: "X"}


def _load(results_dir: str) -> tuple:
    with open(os.path.join(results_dir, "latency_vs_size.json")) as fh:
        lv_size: List[dict] = json.load(fh)
    with open(os.path.join(results_dir, "latency_vs_txcount.json")) as fh:
        lv_tx: List[dict] = json.load(fh)
    with open(os.path.join(results_dir, "storage.json")) as fh:
        storage: dict = json.load(fh)
    return lv_size, lv_tx, storage


# Topology color/marker scheme consistent with Fig. 5 (Section 8.4)
TOPO_COLOR = {"HK": "#1f77b4", "Doar": "#d62728", "WS": "#2ca02c"}
TOPO_MARKER = {"HK": "o", "Doar": "s", "WS": "^"}
TOPO_LABEL = {"HK": "Holme-Kim", "Doar": "Doar", "WS": "Watts-Strogatz"}


# ---------------------------------------------------------------------------
# (a) Per-node latency rate vs. |V|: Alg 1+2 for three topologies
#     Y = latency_ms / num_nodes  (units: 10^-3 ms/node)
#     Flat lines confirm O(|V|) scaling; topology differences are visible.
# ---------------------------------------------------------------------------

def _plot_subfig_a(ax: plt.Axes, lv_size: List[dict]) -> None:
    by_topo: dict = defaultdict(list)
    for r in lv_size:
        by_topo[r.get("topology", "Doar")].append(r)

    for topo in ("Doar", "HK", "WS"):
        records = sorted(by_topo.get(topo, []), key=lambda r: r["num_nodes"])
        if not records:
            continue
        xs = np.array([r["num_nodes"] for r in records], dtype=float)
        ys_ms = np.array([r["alg12_ms"] for r in records], dtype=float)
        rate = ys_ms / xs * 1e3          # x10^-3 ms/node, for plotting
        rate_se = np.array([r["alg12_se_ms"] for r in records], dtype=float) / xs * 1e3
        # OLS slope through origin - matches the value cited in prose
        ols_slope = float(np.dot(xs, ys_ms) / np.dot(xs, xs)) * 1e3
        ax.errorbar(xs, rate, yerr=rate_se,
                    marker=TOPO_MARKER[topo], markersize=5,
                    linewidth=1.4, capsize=2, linestyle="-",
                    color=TOPO_COLOR[topo],
                    label=f"{TOPO_LABEL[topo]} ({ols_slope:.2f})")

    ax.set_xlabel(r"Network size $|V|$")
    ax.set_ylabel(r"Latency rate (10$^{-3}$ ms/node)")
    ax.set_xticks([500, 2000, 5000, 10000, 20000])
    ax.set_xticklabels(["500", "2k", "5k", "10k", "20k"])
    ax.grid(alpha=0.3)
    ax.legend(fontsize=7.5, loc="upper right", framealpha=0.9,
              title="Topology (rate x10^-3 ms/node)", title_fontsize=7)
    ax.text(0.5, -0.23, "(a)", transform=ax.transAxes,
            ha="center", va="top", fontsize=10)


# ---------------------------------------------------------------------------
# (b) Block latency vs. tx_count for multiple |V|
# ---------------------------------------------------------------------------

def _plot_subfig_b(ax: plt.Axes, lv_tx: List[dict]) -> None:
    by_v: dict = defaultdict(list)
    for r in lv_tx:
        by_v[r["num_nodes"]].append((r["tx_count"], r["block_latency_s"]))

    for num_nodes, pairs in sorted(by_v.items()):
        pairs.sort()
        xs = [p[0] for p in pairs]
        ys = [p[1] for p in pairs]
        ax.plot(xs, ys,
                marker=SIZE_MARKERS.get(num_nodes, "o"), markersize=5,
                linewidth=1.4, color=SIZE_COLORS.get(num_nodes, "k"),
                label=f"|V|={num_nodes:,}")

    ax.set_xlabel("Transactions per block")
    ax.set_ylabel("Block processing latency (s)")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8, loc="upper left", framealpha=0.9)
    ax.text(0.5, -0.23, "(b)", transform=ax.transAxes,
            ha="center", va="top", fontsize=10)


# ---------------------------------------------------------------------------
# (c) Per-block storage vs. |V|
# ---------------------------------------------------------------------------

def _plot_subfig_c(ax: plt.Axes, storage: dict) -> None:
    vs_nodes: List[dict] = storage["vs_nodes"]
    xs = np.array([r["num_nodes"] for r in vs_nodes], dtype=float)
    alloc = np.array([r["alloc_kb"] for r in vs_nodes], dtype=float)
    topo_chg = np.array([r["topology_kb_per_block"] for r in vs_nodes], dtype=float)
    total = np.array([r["total_kb_per_block"] for r in vs_nodes], dtype=float)

    ax.plot(xs, alloc, marker="o", markersize=5, linewidth=1.4,
            color="#1f77b4", label="Incentive allocation")
    ax.plot(xs, topo_chg, marker="^", markersize=5, linewidth=1.4,
            color="#ff7f0e", label="Topology changes")
    ax.plot(xs, total, marker="D", markersize=4, linewidth=1.4,
            color="#9467bd", label="Total")

    # Section 6.4 estimates the allocation field only. Use the same decimal KB
    # convention here so the dashed line is directly comparable to alloc_kb.
    x_est = np.array([xs.min(), xs.max()])
    slope_est = PAPER_ESTIMATE_KB / PAPER_ESTIMATE_V
    ax.plot(x_est, slope_est * x_est, linestyle="--", linewidth=1.4,
            color="#2ca02c",
            label=f"Section 6.4 allocation estimate ({PAPER_ESTIMATE_KB:.0f} KB at |V|={PAPER_ESTIMATE_V:,})")

    ax.set_xlabel(r"Network size $|V|$")
    ax.set_ylabel("Storage per block (KB)")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=7.5, loc="upper left", framealpha=0.9)
    ax.text(0.5, -0.23, "(c)", transform=ax.transAxes,
            ha="center", va="top", fontsize=10)


# ---------------------------------------------------------------------------
# (d) Cumulative blockchain size vs. blocks, multiple |V|
# ---------------------------------------------------------------------------

def _plot_subfig_d(ax: plt.Axes, storage: dict) -> None:
    # Compute cumulative on the fly from vs_nodes so (d) uses the same
    # |V| range as (b): [500, 1000, 2000, 5000].
    SIZES_D = [500, 1000, 2000, 5000]
    BLOCKS = [1, 10, 50, 100, 500, 1000]
    kb_per_block = {r["num_nodes"]: r["total_kb_per_block"]
                    for r in storage["vs_nodes"]}

    for num_nodes in SIZES_D:
        if num_nodes not in kb_per_block:
            continue
        kb = kb_per_block[num_nodes]
        xs = BLOCKS
        ys = [kb * nb / 1000.0 for nb in BLOCKS]
        ax.plot(xs, ys,
                marker=SIZE_MARKERS.get(num_nodes, "o"), markersize=5,
                linewidth=1.4, color=SIZE_COLORS.get(num_nodes, "k"),
                label=f"|V|={num_nodes:,}")

    ax.set_xlabel("Number of blocks")
    ax.set_ylabel("Cumulative blockchain size (MB)")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8, loc="upper left", framealpha=0.9)
    ax.text(0.5, -0.23, "(d)", transform=ax.transAxes,
            ha="center", va="top", fontsize=10)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    here = os.path.dirname(__file__)
    results_dir = os.path.abspath(os.path.join(here, "..", "results"))
    fig_path_pdf = os.path.join(results_dir, "fig6_section_8_5.pdf")
    fig_path_png = os.path.join(results_dir, "fig6_section_8_5.png")

    lv_size, lv_tx, storage = _load(results_dir)

    fig, axes = plt.subplots(2, 2, figsize=(9.5, 7.4))
    _plot_subfig_a(axes[0, 0], lv_size)
    _plot_subfig_b(axes[0, 1], lv_tx)
    _plot_subfig_c(axes[1, 0], storage)
    _plot_subfig_d(axes[1, 1], storage)
    fig.tight_layout()
    fig.savefig(fig_path_pdf, bbox_inches="tight")
    fig.savefig(fig_path_png, bbox_inches="tight", dpi=160)
    print(f"[plot_fig6] saved {fig_path_pdf}")
    print(f"[plot_fig6] saved {fig_path_png}")


if __name__ == "__main__":
    main()
