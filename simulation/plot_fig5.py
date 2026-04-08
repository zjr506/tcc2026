"""
Render Fig. 5 (three subfigures) for Section 8.4 of main.pdf from the raw
results produced by `python3 -m simulation.experiment_8_4`.
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

TIERS = ("Micro", "Small", "Medium", "Large")
TIER_COLORS = {
    "Micro": "#888888",
    "Small": "#1f77b4",
    "Medium": "#ff7f0e",
    "Large": "#d62728",
}
TIER_MARKERS = {"Micro": "o", "Small": "s", "Medium": "^", "Large": "D"}


def _bin_by_degree(
    records: List[dict], key: str, degree_bins: List[int]
) -> Dict[str, Tuple[np.ndarray, np.ndarray, np.ndarray]]:
    """Group per-node records into (x_center, mean, sem) per tier over the
    requested degree bins. `key` is the field in the record to aggregate."""
    out: Dict[str, Tuple[np.ndarray, np.ndarray, np.ndarray]] = {}
    edges = np.array(degree_bins, dtype=np.float64)
    centers = 0.5 * (edges[:-1] + edges[1:])
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


def _plot_subfig_a(ax: plt.Axes, fairness: List[dict]) -> None:
    bins = [4, 8, 12, 16, 20, 25, 30, 35, 40, 45, 50, 55, 61]
    grouped = _bin_by_degree(fairness, "profit_rate", bins)
    for tier in TIERS:
        x, y, se = grouped[tier]
        valid = ~np.isnan(y)
        ax.errorbar(
            x[valid], y[valid], yerr=se[valid],
            label=tier, color=TIER_COLORS[tier],
            marker=TIER_MARKERS[tier], markersize=4, linewidth=1.3,
            capsize=2,
        )
    ax.axhline(0, color="k", linewidth=0.5, linestyle=":")
    ax.set_xlabel("Number of Links")
    ax.set_ylabel("Profit Rate")
    ax.set_title("(a) Profit rate per tier")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8, loc="upper left", framealpha=0.9)


def _plot_subfig_b(ax: plt.Axes, fairness: List[dict]) -> None:
    bins = [4, 8, 12, 16, 20, 25, 30, 35, 40, 45, 50, 55, 61]
    grouped = _bin_by_degree(fairness, "forwards", bins)
    for tier in TIERS:
        x, y, se = grouped[tier]
        valid = ~np.isnan(y)
        ax.errorbar(
            x[valid], y[valid] / 1e3, yerr=se[valid] / 1e3,
            label=tier, color=TIER_COLORS[tier],
            marker=TIER_MARKERS[tier], markersize=4, linewidth=1.3,
            capsize=2,
        )
    ax.set_xlabel("Number of Links")
    ax.set_ylabel(r"Sufficient Forwarding Times ($\times 10^3$)")
    ax.set_title("(b) Sufficient forwarding per tier")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8, loc="upper left", framealpha=0.9)


def _plot_subfig_c(ax: plt.Axes, sybil: List[dict]) -> None:
    agg: Dict[Tuple[str, int], List[float]] = defaultdict(list)
    for r in sybil:
        agg[(r["adversary_tier"], r["pseudonym_count"])].append(r["profit_rate"])

    xs = sorted({r["pseudonym_count"] for r in sybil})
    # Add a small tier-specific vertical offset so overlapping lines remain
    # visually distinguishable; the offset is annotated in the legend.
    offsets = {"Micro": -0.12, "Small": -0.04, "Medium": 0.04, "Large": 0.12}
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
        means_arr = np.array(means) + offsets[tier]
        ax.errorbar(
            xs, means_arr, yerr=sems,
            label=f"{tier} adv.",
            color=TIER_COLORS[tier], marker=TIER_MARKERS[tier],
            markersize=5, linewidth=1.3, capsize=2,
        )
    ax.axhline(0, color="k", linewidth=0.5, linestyle=":")
    ax.set_xlabel("Number of Pseudonymous Nodes")
    ax.set_ylabel("Adversary Profit Rate")
    ax.set_title("(c) Sybil attack by adversary tier")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8, loc="lower left", framealpha=0.9)
    # Annotation explaining the offset.
    ax.text(
        0.98, 0.98,
        r"$\pm$ small vertical offset per tier""\n(curves coincide exactly)",
        transform=ax.transAxes, ha="right", va="top",
        fontsize=7, alpha=0.7,
    )


def main() -> None:
    here = os.path.dirname(__file__)
    results_dir = os.path.abspath(os.path.join(here, "..", "results"))
    fig_path_pdf = os.path.join(results_dir, "fig5_section_8_4.pdf")
    fig_path_png = os.path.join(results_dir, "fig5_section_8_4.png")

    fairness, sybil = _load(results_dir)

    fig, axes = plt.subplots(1, 3, figsize=(13.5, 3.8))
    _plot_subfig_a(axes[0], fairness)
    _plot_subfig_b(axes[1], fairness)
    _plot_subfig_c(axes[2], sybil)
    fig.suptitle(
        "Fig. 5. ITFC under heterogeneous cloud nodes (Section 8.4).",
        y=1.02, fontsize=10,
    )
    fig.tight_layout()
    fig.savefig(fig_path_pdf, bbox_inches="tight")
    fig.savefig(fig_path_png, bbox_inches="tight", dpi=160)
    print(f"[plot_fig5] saved {fig_path_pdf}")
    print(f"[plot_fig5] saved {fig_path_png}")


if __name__ == "__main__":
    main()
