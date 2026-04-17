"""
Render Fig. 5 (four subfigures) for Section 8.4 of main.pdf from the raw
results produced by `python3 -m simulation.experiment_8_4`.

Layout (1x4 row, matching the horizontal-row style of Fig. 2 in §8.1):

  (a) profit rate per tier vs. number of links
  (b) sufficient forwarding times per tier vs. number of links
  (c) per-forward unit revenue: relay revenue vs. forwarding count, one
      point per node, colour-coded by tier, single regression line showing
      the tier-blind rate (fairness invariant)
  (d) Sybil attack adversary profit rate by adversary tier
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

TIERS = ("0.40", "0.30", "0.20", "0.10")
TIER_COLORS = {
    "0.40": "#888888",
    "0.30": "#1f77b4",
    "0.20": "#ff7f0e",
    "0.10": "#d62728",
}
TIER_MARKERS = {"0.40": "o", "0.30": "s", "0.20": "^", "0.10": "D"}


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
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8, loc="upper left", framealpha=0.9)
    ax.text(0.5, -0.23, "(a)", transform=ax.transAxes,
            ha="center", va="top", fontsize=10)


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
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8, loc="upper left", framealpha=0.9)
    ax.text(0.5, -0.23, "(b)", transform=ax.transAxes,
            ha="center", va="top", fontsize=10)


def _plot_subfig_c(ax: plt.Axes, fairness: List[dict]) -> None:
    """Per-forward unit-revenue scatter: relay_revenue vs. forwards, one
    point per node, colour-coded by tier. A single regression line fit to
    all nodes jointly shows that every tier sits on the same line — i.e.
    Algorithm 2 pays the same rate per forward regardless of tier.

    Note: relay_revenue = profit_rate + 0.5, because profit_rate =
    (relay_rev + block_share - cost)/f0 = relay_rev + 0.5 - 1.0 = relay_rev - 0.5.
    """
    pr = np.array([r["profit_rate"] for r in fairness], dtype=np.float64)
    fw = np.array([r["forwards"] for r in fairness], dtype=np.float64)
    tier_arr = np.array([r["tier"] for r in fairness])
    relay = pr + 0.5
    # Drop zero-forward nodes (no contribution → outside the fairness claim).
    valid = fw > 0
    pr, fw, tier_arr, relay = pr[valid], fw[valid], tier_arr[valid], relay[valid]

    # Keep only points with non-trivial relay revenue so log-log is defined.
    pos = relay > 1e-12
    fw, relay, tier_arr = fw[pos], relay[pos], tier_arr[pos]

    # Subsample each tier for visual clarity (the data set has ~10k nodes).
    rng = np.random.default_rng(0)
    max_per_tier = 500
    for tier in TIERS:
        m = tier_arr == tier
        idx = np.nonzero(m)[0]
        if len(idx) > max_per_tier:
            idx = rng.choice(idx, size=max_per_tier, replace=False)
        ax.scatter(
            fw[idx], relay[idx],
            s=12, alpha=0.55,
            color=TIER_COLORS[tier], marker=TIER_MARKERS[tier],
            label=tier, edgecolors="none",
        )

    # Reference line = mean per-node unit revenue (relay/forwards).
    # This is the quantity whose per-tier value is reported in the supplement
    # text (all tiers within 0.01%). A zero-intercept OLS slope would be
    # biased upward by the Large-tier outliers — we want the tier-blind rate
    # that the *typical node* experiences, not a forwarding-count-weighted
    # average that privileges a few high-capacity nodes.
    slope = float((relay / fw).mean())
    x_line = np.logspace(np.log10(fw.min()), np.log10(fw.max()), 100)
    ax.plot(
        x_line, slope * x_line,
        color="black", linewidth=1.3, linestyle="--",
        label=f"rate = {slope * 1e5:.2f}×10⁻⁵",
    )
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Sufficient Forwarding Times")
    ax.set_ylabel("Relay Revenue")
    ax.grid(alpha=0.3, which="both")
    ax.legend(fontsize=7, loc="lower right", framealpha=0.9, markerscale=1.6)
    ax.text(0.5, -0.23, "(c)", transform=ax.transAxes,
            ha="center", va="top", fontsize=10)


def _plot_subfig_d(ax: plt.Axes, sybil: List[dict]) -> None:
    agg: Dict[Tuple[str, int], List[float]] = defaultdict(list)
    for r in sybil:
        agg[(r["adversary_tier"], r["pseudonym_count"])].append(r["profit_rate"])

    xs = sorted({r["pseudonym_count"] for r in sybil})
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
            label=tier,
            color=TIER_COLORS[tier], marker=TIER_MARKERS[tier],
            markersize=5, linewidth=1.3, capsize=2,
        )
    ax.axhline(0, color="k", linewidth=0.5, linestyle=":")
    ax.set_xlabel("Number of Pseudonymous Nodes")
    ax.set_ylabel("Profit Rate")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8, loc="lower left", framealpha=0.9)
    ax.text(0.5, -0.23, "(d)", transform=ax.transAxes,
            ha="center", va="top", fontsize=10)


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
