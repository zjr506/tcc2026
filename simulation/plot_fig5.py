"""
Render Fig. 5 (2x2 grid) for Section 8.4 of main.pdf from the raw
results produced by `python3 -m simulation.experiment_8_4`.

  (a) Per-tier profit rate by topology: Holme-Kim, Doar, Watts-Strogatz
  (b) Per-tier profit rate vs. number of links       — Holme-Kim
  (c) Per-tier sufficient forwarding count vs. links  — Holme-Kim
  (d) Per-tier Sybil-attack profit rate vs. pseudonyms — Holme-Kim

Subfigure (a) uses topology name labels (Holme-Kim, Doar, Watts-Strogatz).
Subfigures (b)-(d) use tier proportion labels (0.40, 0.30, 0.20, 0.10).

Run:
    python3 -m simulation.plot_fig5
"""

from __future__ import annotations

import json
import os
from collections import defaultdict
from typing import Dict, List, Tuple

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D

TIERS = ("0.40", "0.30", "0.20", "0.10")
TIER_COLORS = {
    "0.40": "#888888",
    "0.30": "#1f77b4",
    "0.20": "#ff7f0e",
    "0.10": "#d62728",
}
TIER_MARKERS = {"0.40": "o", "0.30": "s", "0.20": "^", "0.10": "D"}

TOPO_KEY_TO_LABEL = {"HK": "Holme-Kim", "Doar": "Doar", "WS": "Watts-Strogatz"}
TOPO_COLORS = {"Holme-Kim": "#1f77b4", "Doar": "#d62728", "Watts-Strogatz": "#2ca02c"}

DEGREE_BINS = [4, 8, 12, 16, 20, 25, 30, 35, 40, 45, 50, 55, 61]


def _bin_by_degree_per_tier(
    records: List[dict], key: str, bins: List[int],
) -> Dict[str, Tuple[np.ndarray, np.ndarray, np.ndarray]]:
    edges = np.array(bins, dtype=np.float64)
    centers = 0.5 * (edges[:-1] + edges[1:])
    out: Dict[str, Tuple[np.ndarray, np.ndarray, np.ndarray]] = {}
    for tier in TIERS:
        rows = [r for r in records if r["tier"] == tier]
        deg = np.array([r["degree"] for r in rows], dtype=np.float64)
        val = np.array([r[key] for r in rows], dtype=np.float64)
        means = np.full(len(centers), np.nan)
        sems = np.full(len(centers), np.nan)
        for b in range(len(centers)):
            mask = (deg >= edges[b]) & (deg < edges[b + 1])
            if mask.sum() >= 3:
                means[b] = val[mask].mean()
                sems[b] = val[mask].std(ddof=1) / np.sqrt(mask.sum())
        out[tier] = (centers, means, sems)
    return out


def _load(results_dir: str) -> Tuple[List[dict], List[dict]]:
    with open(os.path.join(results_dir, "fairness.json")) as fh:
        fairness = json.load(fh)
    with open(os.path.join(results_dir, "sybil.json")) as fh:
        sybil = json.load(fh)
    return fairness, sybil


# -----------------------------------------------------------------------
# (a) Per-tier profit rate by topology (grouped bar chart)
# -----------------------------------------------------------------------

def _plot_subfig_a(ax: plt.Axes, fairness: List[dict]) -> None:
    topo_order = ["HK", "Doar", "WS"]
    topo_labels = [TOPO_KEY_TO_LABEL[k] for k in topo_order]
    n_topo = len(topo_order)
    n_tier = len(TIERS)
    bar_width = 0.18
    x_pos = np.arange(n_tier)

    for i, topo_key in enumerate(topo_order):
        subset = [r for r in fairness if r.get("topology") == topo_key]
        if not subset:
            continue
        means = []
        sems = []
        for tier in TIERS:
            vals = [r["profit_rate"] for r in subset if r["tier"] == tier]
            means.append(np.mean(vals))
            sems.append(np.std(vals, ddof=1) / np.sqrt(len(vals))
                       if len(vals) > 1 else 0.0)
        offset = (i - (n_topo - 1) / 2) * bar_width
        label = topo_labels[i]
        ax.bar(x_pos + offset, means, bar_width, yerr=sems,
               color=TOPO_COLORS[label], capsize=3,
               edgecolor="white", label=label)

    ax.set_xticks(x_pos)
    ax.set_xticklabels(TIERS, fontsize=8)
    ax.set_xlabel("Tier (proportion)")
    ax.axhline(0, color="k", linewidth=0.5, linestyle=":")
    ax.set_ylabel("Profit Rate")
    ax.grid(alpha=0.3, axis="y")
    ax.legend(fontsize=7.5, loc="upper left", framealpha=0.9)
    ax.text(0.5, -0.23, "(a)", transform=ax.transAxes,
            ha="center", va="top", fontsize=10)


# -----------------------------------------------------------------------
# (b) Per-tier profit rate vs links — Holme-Kim only
# -----------------------------------------------------------------------

def _plot_subfig_b(ax: plt.Axes, fairness: List[dict]) -> None:
    subset = [r for r in fairness if r.get("topology", "HK") == "HK"]
    grouped = _bin_by_degree_per_tier(subset, "profit_rate", DEGREE_BINS)
    for tier in TIERS:
        x, y, se = grouped[tier]
        valid = ~np.isnan(y)
        ax.errorbar(
            x[valid], y[valid], yerr=se[valid],
            color=TIER_COLORS[tier], marker=TIER_MARKERS[tier],
            markersize=5, linewidth=1.4, capsize=2, label=tier,
        )

    ax.axhline(0, color="k", linewidth=0.5, linestyle=":")
    ax.set_xlabel("Number of Links")
    ax.set_ylabel("Profit Rate")
    ax.set_title("Holme-Kim", fontsize=9)
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8, loc="upper left", framealpha=0.9)
    ax.text(0.5, -0.23, "(b)", transform=ax.transAxes,
            ha="center", va="top", fontsize=10)


# -----------------------------------------------------------------------
# (c) Per-tier sufficient forwarding count vs links — Holme-Kim only
# -----------------------------------------------------------------------

def _plot_subfig_c(ax: plt.Axes, fairness: List[dict]) -> None:
    subset = [r for r in fairness if r.get("topology", "HK") == "HK"]
    grouped = _bin_by_degree_per_tier(subset, "forwards", DEGREE_BINS)
    for tier in TIERS:
        x, y, se = grouped[tier]
        valid = ~np.isnan(y)
        ax.errorbar(
            x[valid], y[valid] / 1e3, yerr=se[valid] / 1e3,
            color=TIER_COLORS[tier], marker=TIER_MARKERS[tier],
            markersize=5, linewidth=1.4, capsize=2, label=tier,
        )

    ax.set_xlabel("Number of Links")
    ax.set_ylabel(r"Sufficient Forwarding Times ($\times 10^3$)")
    ax.set_title("Holme-Kim", fontsize=9)
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8, loc="upper left", framealpha=0.9)
    ax.text(0.5, -0.23, "(c)", transform=ax.transAxes,
            ha="center", va="top", fontsize=10)


# -----------------------------------------------------------------------
# (d) Per-tier Sybil profit rate vs pseudonyms — Holme-Kim only
# -----------------------------------------------------------------------

def _plot_subfig_d(ax: plt.Axes, sybil: List[dict]) -> None:
    subset = [r for r in sybil if r.get("substrate", "HK") == "HK"]
    xs = sorted({r["pseudonym_count"] for r in subset})

    agg: Dict[Tuple[str, int], List[float]] = defaultdict(list)
    for r in subset:
        agg[(r["adversary_tier"], r["pseudonym_count"])].append(r["profit_rate"])

    for tier in TIERS:
        means = []
        sems = []
        for x in xs:
            vals = agg[(tier, x)]
            if vals:
                means.append(np.mean(vals))
                sems.append(np.std(vals, ddof=1) / np.sqrt(len(vals))
                           if len(vals) > 1 else 0.0)
            else:
                means.append(np.nan)
                sems.append(0.0)
        ax.errorbar(
            xs, np.array(means), yerr=sems,
            color=TIER_COLORS[tier], marker=TIER_MARKERS[tier],
            markersize=5, linewidth=1.4, capsize=2, label=tier,
        )

    ax.axhline(0, color="k", linewidth=0.5, linestyle=":")
    ax.set_xlabel("Number of Pseudonymous Nodes")
    ax.set_ylabel("Profit Rate")
    ax.set_title("Holme-Kim", fontsize=9)
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8, loc="lower left", framealpha=0.9)
    ax.text(0.5, -0.23, "(d)", transform=ax.transAxes,
            ha="center", va="top", fontsize=10)


# -----------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------

def main() -> None:
    here = os.path.dirname(__file__)
    results_dir = os.path.abspath(os.path.join(here, "..", "results"))
    fig_path_pdf = os.path.join(results_dir, "fig5_section_8_4.pdf")
    fig_path_png = os.path.join(results_dir, "fig5_section_8_4.png")

    fairness, sybil = _load(results_dir)

    fig, axes = plt.subplots(2, 2, figsize=(9.5, 7.4))
    _plot_subfig_a(axes[0, 0], fairness)
    _plot_subfig_b(axes[0, 1], fairness)
    _plot_subfig_c(axes[1, 0], fairness)
    _plot_subfig_d(axes[1, 1], sybil)
    fig.tight_layout()
    fig.savefig(fig_path_pdf, bbox_inches="tight")
    fig.savefig(fig_path_png, bbox_inches="tight", dpi=160)
    print(f"[plot_fig5] saved {fig_path_pdf}")
    print(f"[plot_fig5] saved {fig_path_png}")


if __name__ == "__main__":
    main()
