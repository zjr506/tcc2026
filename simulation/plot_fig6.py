"""
Render Fig. 6 (four subfigures) for Section 8.5 of main.pdf from the raw
results produced by `python3 -m simulation.experiment_8_5`.

Layout (2x2 grid, matching the visual style of Fig. 5 / plot_fig5.py):

  (a) Per-transaction latency (ms) vs. |V|  — actual measurements + linear fit
  (b) Block processing latency (s)  vs. tx_count  — for |V|=5000
  (c) Per-block storage (KB)        vs. |V|  — incentive alloc + topology lines
  (d) Cumulative blockchain size (MB) vs. number of blocks  — for |V|=22000

Run:
    python3 -m simulation.plot_fig6
"""

from __future__ import annotations

import json
import os
from typing import List

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


# §6.4 paper reference estimate
PAPER_ESTIMATE_V = 22000
PAPER_ESTIMATE_KB = 616.0


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def _load(results_dir: str) -> tuple:
    with open(os.path.join(results_dir, "latency_vs_size.json")) as fh:
        latency_vs_size: List[dict] = json.load(fh)
    with open(os.path.join(results_dir, "latency_vs_txcount.json")) as fh:
        latency_vs_txcount: List[dict] = json.load(fh)
    with open(os.path.join(results_dir, "storage.json")) as fh:
        storage: dict = json.load(fh)
    return latency_vs_size, latency_vs_txcount, storage


# ---------------------------------------------------------------------------
# Subfigure (a): per-transaction latency vs. |V|
# ---------------------------------------------------------------------------

def _plot_subfig_a(ax: plt.Axes, latency_vs_size: List[dict]) -> None:
    """Per-transaction latency (ms) vs. |V|, with linear reference fit."""
    xs = np.array([r["num_nodes"] for r in latency_vs_size], dtype=np.float64)
    ys = np.array([r["per_tx_latency_ms"] for r in latency_vs_size], dtype=np.float64)
    ses = np.array(
        [r.get("per_tx_latency_se_ms", 0.0) for r in latency_vs_size],
        dtype=np.float64,
    )

    # Plot mean ± 1 SE error bars across seeds.
    ax.errorbar(
        xs, ys, yerr=ses,
        marker="o", markersize=5, linewidth=1.5,
        color="#1f77b4", label="measured",
        capsize=3, elinewidth=1.0,
    )

    # Linear fit: y = slope * x  (forced through origin for the reference line)
    slope = float(np.dot(xs, ys) / np.dot(xs, xs))
    x_fit = np.linspace(xs.min(), xs.max(), 200)
    ax.plot(
        x_fit, slope * x_fit,
        linestyle="--", linewidth=1.2, color="#d62728",
        label=f"linear fit (slope={slope:.4f} ms/node)",
    )

    ax.set_xlabel(r"Network size $|V|$")
    ax.set_ylabel("Per-transaction latency (ms)")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8, loc="upper left", framealpha=0.9)
    ax.text(0.5, -0.23, "(a)", transform=ax.transAxes,
            ha="center", va="top", fontsize=10)


# ---------------------------------------------------------------------------
# Subfigure (b): block latency vs. tx count
# ---------------------------------------------------------------------------

def _plot_subfig_b(ax: plt.Axes, latency_vs_txcount: List[dict]) -> None:
    """Block processing latency (s) vs. number of transactions, |V|=5000."""
    xs = np.array([r["tx_count"] for r in latency_vs_txcount], dtype=np.float64)
    ys = np.array([r["block_latency_s"] for r in latency_vs_txcount], dtype=np.float64)

    ax.plot(
        xs, ys,
        marker="s", markersize=5, linewidth=1.5,
        color="#ff7f0e", label=r"$|V|=2000$",
    )

    ax.set_xlabel("Transactions per block")
    ax.set_ylabel("Block processing latency (s)")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8, loc="upper left", framealpha=0.9)
    ax.text(0.5, -0.23, "(b)", transform=ax.transAxes,
            ha="center", va="top", fontsize=10)


# ---------------------------------------------------------------------------
# Subfigure (c): per-block storage vs. |V|
# ---------------------------------------------------------------------------

def _plot_subfig_c(ax: plt.Axes, storage: dict) -> None:
    """Per-block storage (KB) vs. |V|: incentive allocation + topology change."""
    vs_nodes: List[dict] = storage["vs_nodes"]
    xs = np.array([r["num_nodes"] for r in vs_nodes], dtype=np.float64)
    alloc_kb = np.array([r["alloc_kb"] for r in vs_nodes], dtype=np.float64)
    topo_kb = np.array([r["topology_kb_per_block"] for r in vs_nodes], dtype=np.float64)

    ax.plot(
        xs, alloc_kb,
        marker="o", markersize=5, linewidth=1.5,
        color="#1f77b4", label="Incentive allocation",
    )
    ax.plot(
        xs, topo_kb,
        marker="^", markersize=5, linewidth=1.5,
        color="#ff7f0e", label="Topology changes",
    )

    # §6.4 reference estimate: 616 KB at |V|=22000.
    ax.axhline(
        PAPER_ESTIMATE_KB, color="k", linewidth=1.0, linestyle="--",
        label=f"§6.4 estimate ({PAPER_ESTIMATE_KB:.0f} KB at |V|={PAPER_ESTIMATE_V:,})",
    )

    ax.set_xlabel(r"Network size $|V|$")
    ax.set_ylabel("Storage per block (KB)")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8, loc="upper left", framealpha=0.9)
    ax.text(0.5, -0.23, "(c)", transform=ax.transAxes,
            ha="center", va="top", fontsize=10)


# ---------------------------------------------------------------------------
# Subfigure (d): cumulative blockchain size vs. number of blocks
# ---------------------------------------------------------------------------

def _plot_subfig_d(ax: plt.Axes, storage: dict) -> None:
    """Cumulative blockchain size (MB) vs. number of blocks, |V|=22000."""
    cumulative: List[dict] = storage["cumulative"]
    xs = np.array([r["num_blocks"] for r in cumulative], dtype=np.float64)
    ys = np.array([r["cumulative_mb"] for r in cumulative], dtype=np.float64)

    ax.plot(
        xs, ys,
        marker="D", markersize=5, linewidth=1.5,
        color="#2ca02c", label=r"$|V|=22{,}000$",
    )

    ax.set_xlabel("Number of blocks")
    ax.set_ylabel("Cumulative blockchain size (MB)")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8, loc="upper left", framealpha=0.9)
    ax.text(0.5, -0.23, "(d)", transform=ax.transAxes,
            ha="center", va="top", fontsize=10)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main() -> None:
    here = os.path.dirname(__file__)
    results_dir = os.path.abspath(os.path.join(here, "..", "results"))
    fig_path_pdf = os.path.join(results_dir, "fig6_section_8_5.pdf")
    fig_path_png = os.path.join(results_dir, "fig6_section_8_5.png")

    latency_vs_size, latency_vs_txcount, storage = _load(results_dir)

    fig, axes = plt.subplots(2, 2, figsize=(9.5, 7.4))
    _plot_subfig_a(axes[0, 0], latency_vs_size)
    _plot_subfig_b(axes[0, 1], latency_vs_txcount)
    _plot_subfig_c(axes[1, 0], storage)
    _plot_subfig_d(axes[1, 1], storage)
    fig.tight_layout()
    fig.savefig(fig_path_pdf, bbox_inches="tight")
    fig.savefig(fig_path_png, bbox_inches="tight", dpi=160)
    print(f"[plot_fig6] saved {fig_path_pdf}")
    print(f"[plot_fig6] saved {fig_path_png}")


if __name__ == "__main__":
    main()
