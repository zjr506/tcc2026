"""
Render Fig. 6 (2x2 grid) for Section 8.5 from results of experiment_8_5.

  (a) Per-tx latency vs. |V|: Algorithm 1 vs. Algorithms 1+2  (+ linear fit)
  (b) Block processing latency vs. tx_count for |V| in {500,1000,2000,5000}
  (c) Per-block storage vs. |V|: alloc / topology / total  (+ §6.4 estimate)
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


# ---------------------------------------------------------------------------
# (a) Per-tx latency vs. |V|
# ---------------------------------------------------------------------------

def _plot_subfig_a(ax: plt.Axes, lv_size: List[dict]) -> None:
    from collections import defaultdict
    by_topo: dict = defaultdict(list)
    for r in lv_size:
        topo = r.get("topology", "BA")
        by_topo[topo].append(r)

    TOPO_STYLES = {
        "BA": {"alg1": ("#1f77b4", "o", "-"),  "alg12": ("#d62728", "s", "-")},
        "HK": {"alg1": ("#1f77b4", "^", "--"), "alg12": ("#d62728", "D", "--")},
    }

    for topo in ("BA", "HK"):
        records = sorted(by_topo[topo], key=lambda r: r["num_nodes"])
        xs = np.array([r["num_nodes"] for r in records], dtype=float)
        alg1 = np.array([r["alg1_ms"] for r in records], dtype=float)
        alg1_se = np.array([r["alg1_se_ms"] for r in records], dtype=float)
        alg12 = np.array([r["alg12_ms"] for r in records], dtype=float)
        alg12_se = np.array([r["alg12_se_ms"] for r in records], dtype=float)
        c1, m1, ls1 = TOPO_STYLES[topo]["alg1"]
        c12, m12, ls12 = TOPO_STYLES[topo]["alg12"]
        ax.errorbar(xs, alg1, yerr=alg1_se, marker=m1, markersize=5,
                    linewidth=1.4, capsize=2, linestyle=ls1, color=c1,
                    label=f"Alg 1 ({topo})")
        ax.errorbar(xs, alg12, yerr=alg12_se, marker=m12, markersize=5,
                    linewidth=1.4, capsize=2, linestyle=ls12, color=c12,
                    label=f"Alg 1+2 ({topo})")

    # Linear fit on BA Alg1+2 (reference line)
    ba_records = sorted(by_topo["BA"], key=lambda r: r["num_nodes"])
    xs_ba = np.array([r["num_nodes"] for r in ba_records], dtype=float)
    alg12_ba = np.array([r["alg12_ms"] for r in ba_records], dtype=float)
    slope = float(np.dot(xs_ba, alg12_ba) / np.dot(xs_ba, xs_ba))
    x_fit = np.linspace(xs_ba.min(), xs_ba.max(), 200)
    ax.plot(x_fit, slope * x_fit, linestyle=":", linewidth=1.0,
            color="gray", alpha=0.7,
            label=f"linear fit ({slope*1e3:.2f}×10⁻³ ms/node)")

    ax.set_xlabel(r"Network size $|V|$")
    ax.set_ylabel("Per-transaction latency (ms)")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=7.5, loc="upper left", framealpha=0.9)
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
    topo = np.array([r["topology_kb_per_block"] for r in vs_nodes], dtype=float)
    total = np.array([r["total_kb_per_block"] for r in vs_nodes], dtype=float)

    ax.plot(xs, alloc, marker="o", markersize=5, linewidth=1.4,
            color="#1f77b4", label="Incentive allocation")
    ax.plot(xs, topo, marker="^", markersize=5, linewidth=1.4,
            color="#ff7f0e", label="Topology changes")
    ax.plot(xs, total, marker="s", markersize=5, linewidth=1.4,
            color="#2ca02c", label="Total")
    ax.axhline(PAPER_ESTIMATE_KB, color="k", linewidth=1.0, linestyle="--",
               label=f"§6.4 estimate ({PAPER_ESTIMATE_KB:.0f} KB at |V|={PAPER_ESTIMATE_V:,})")

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
    by_v: dict = defaultdict(list)
    for r in storage["cumulative"]:
        by_v[r["num_nodes"]].append((r["num_blocks"], r["cumulative_mb"]))

    for num_nodes, pairs in sorted(by_v.items()):
        pairs.sort()
        xs = [p[0] for p in pairs]
        ys = [p[1] for p in pairs]
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
