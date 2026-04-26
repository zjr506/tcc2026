"""
Render Fig. 5 (four subfigures) for Section 8.4 of main.pdf from the raw
results produced by `python3 -m simulation.experiment_8_4`.

Both the Holme-Kim (HK, solid lines) and Doar (dashed lines) topologies
are shown in (a)-(c); both the Holme-Kim and Watts-Strogatz (WS) Sybil
substrates are shown in (d).
"""

from __future__ import annotations

import json
import os
from collections import defaultdict
from typing import Dict, List, Tuple

import numpy as np
import matplotlib
from matplotlib.lines import Line2D

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

TOPO_STYLE = {"HK": "-", "Doar": "--"}
SUBSTRATE_STYLE = {"HK": "-", "WS": "--"}


def _bin_by_degree(
    records: List[dict], key: str, degree_bins: List[int]
) -> Dict[str, Tuple[np.ndarray, np.ndarray, np.ndarray]]:
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


def _topology_legend(ax: plt.Axes, label_a: str, label_b: str) -> None:
    """Add a compact two-entry style legend (solid/dashed) as a second legend."""
    handles = [
        Line2D([0], [0], color="k", linestyle="-", linewidth=1.3, label=label_a),
        Line2D([0], [0], color="k", linestyle="--", linewidth=1.3, label=label_b),
    ]
    ax.legend(handles=handles, fontsize=7.5, loc="lower right", framealpha=0.9)


def _plot_subfig_a(ax: plt.Axes, fairness: List[dict]) -> None:
    bins = [4, 8, 12, 16, 20, 25, 30, 35, 40, 45, 50, 55, 61]
    topos = sorted({r.get("topology", "HK") for r in fairness})
    # First pass: plot, collecting handles for tier legend
    tier_handles = {}
    for topo in ("HK", "Doar"):
        subset = [r for r in fairness if r.get("topology", "HK") == topo]
        if not subset:
            continue
        ls = TOPO_STYLE[topo]
        grouped = _bin_by_degree(subset, "profit_rate", bins)
        for tier in TIERS:
            x, y, se = grouped[tier]
            valid = ~np.isnan(y)
            h = ax.errorbar(
                x[valid], y[valid], yerr=se[valid],
                color=TIER_COLORS[tier], marker=TIER_MARKERS[tier],
                linestyle=ls, markersize=4, linewidth=1.3, capsize=2,
            )
            if tier not in tier_handles:
                tier_handles[tier] = h

    ax.axhline(0, color="k", linewidth=0.5, linestyle=":")
    ax.set_xlabel("Number of Links")
    ax.set_ylabel("Profit Rate")
    ax.grid(alpha=0.3)
    # Tier colour legend
    tier_leg_handles = [
        Line2D([0], [0], color=TIER_COLORS[t], marker=TIER_MARKERS[t],
               markersize=4, linewidth=1.3, label=t) for t in TIERS
    ] + [
        Line2D([0], [0], color="k", linestyle="-", linewidth=1.2, label="Holme-Kim"),
        Line2D([0], [0], color="k", linestyle="--", linewidth=1.2, label="Doar"),
    ]
    ax.legend(handles=tier_leg_handles, fontsize=7.5, loc="upper left",
              framealpha=0.9, ncol=1)
    ax.text(0.5, -0.23, "(a)", transform=ax.transAxes,
            ha="center", va="top", fontsize=10)


def _plot_subfig_b(ax: plt.Axes, fairness: List[dict]) -> None:
    bins = [4, 8, 12, 16, 20, 25, 30, 35, 40, 45, 50, 55, 61]
    for topo in ("HK", "Doar"):
        subset = [r for r in fairness if r.get("topology", "HK") == topo]
        if not subset:
            continue
        ls = TOPO_STYLE[topo]
        grouped = _bin_by_degree(subset, "forwards", bins)
        for tier in TIERS:
            x, y, se = grouped[tier]
            valid = ~np.isnan(y)
            ax.errorbar(
                x[valid], y[valid] / 1e3, yerr=se[valid] / 1e3,
                color=TIER_COLORS[tier], marker=TIER_MARKERS[tier],
                linestyle=ls, markersize=4, linewidth=1.3, capsize=2,
            )

    ax.set_xlabel("Number of Links")
    ax.set_ylabel(r"Sufficient Forwarding Times ($\times 10^3$)")
    ax.grid(alpha=0.3)
    tier_leg_handles = [
        Line2D([0], [0], color=TIER_COLORS[t], marker=TIER_MARKERS[t],
               markersize=4, linewidth=1.3, label=t) for t in TIERS
    ] + [
        Line2D([0], [0], color="k", linestyle="-", linewidth=1.2, label="Holme-Kim"),
        Line2D([0], [0], color="k", linestyle="--", linewidth=1.2, label="Doar"),
    ]
    ax.legend(handles=tier_leg_handles, fontsize=7.5, loc="upper left",
              framealpha=0.9)
    ax.text(0.5, -0.23, "(b)", transform=ax.transAxes,
            ha="center", va="top", fontsize=10)


def _plot_subfig_c(ax: plt.Axes, fairness: List[dict]) -> None:
    rng = np.random.default_rng(0)
    max_per_tier = 350
    slope_all: List[float] = []

    topo_marker_fill = {"HK": True, "Doar": False}

    for topo in ("HK", "Doar"):
        subset = [r for r in fairness if r.get("topology", "HK") == topo]
        if not subset:
            continue
        pr = np.array([r["profit_rate"] for r in subset], dtype=np.float64)
        fw = np.array([r["forwards"] for r in subset], dtype=np.float64)
        tier_arr = np.array([r["tier"] for r in subset])
        relay = pr + 0.5
        valid = (fw > 0) & (relay > 1e-12)
        fw, relay, tier_arr = fw[valid], relay[valid], tier_arr[valid]
        slope_all.extend((relay / fw).tolist())

        filled = topo_marker_fill[topo]
        alpha = 0.60 if filled else 0.40
        for tier in TIERS:
            m = tier_arr == tier
            idx = np.nonzero(m)[0]
            if len(idx) > max_per_tier:
                idx = rng.choice(idx, size=max_per_tier, replace=False)
            ax.scatter(
                fw[idx], relay[idx],
                s=10, alpha=alpha,
                color=TIER_COLORS[tier],
                marker=TIER_MARKERS[tier],
                edgecolors=TIER_COLORS[tier] if not filled else "none",
                facecolors=TIER_COLORS[tier] if filled else "none",
            )

    slope = float(np.mean(slope_all))
    fw_all = np.array([r["forwards"] for r in fairness
                       if r["forwards"] > 0], dtype=float)
    x_line = np.logspace(np.log10(fw_all.min()), np.log10(fw_all.max()), 100)
    ax.plot(x_line, slope * x_line, color="black", linewidth=1.3, linestyle="--",
            label=f"rate = {slope * 1e5:.2f}×10⁻⁵")

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Sufficient Forwarding Times")
    ax.set_ylabel("Relay Revenue")
    ax.grid(alpha=0.3, which="both")

    tier_leg = [
        Line2D([0], [0], color=TIER_COLORS[t], marker=TIER_MARKERS[t],
               markersize=4, linewidth=0, label=t) for t in TIERS
    ] + [
        Line2D([0], [0], color="k", linestyle="-", markersize=5,
               marker="o", label="Holme-Kim"),
        Line2D([0], [0], color="k", linestyle="-", markersize=5,
               marker="o", markerfacecolor="none", label="Doar"),
        Line2D([0], [0], color="black", linewidth=1.3, linestyle="--",
               label=f"rate = {slope * 1e5:.2f}×10⁻⁵"),
    ]
    ax.legend(handles=tier_leg, fontsize=7, loc="lower right",
              framealpha=0.9, markerscale=1.4)
    ax.text(0.5, -0.23, "(c)", transform=ax.transAxes,
            ha="center", va="top", fontsize=10)


def _plot_subfig_d(ax: plt.Axes, sybil: List[dict]) -> None:
    xs = sorted({r["pseudonym_count"] for r in sybil})
    substrates = sorted({r.get("substrate", "HK") for r in sybil})

    for substrate in ("HK", "WS"):
        subset = [r for r in sybil if r.get("substrate", "HK") == substrate]
        if not subset:
            continue
        ls = SUBSTRATE_STYLE[substrate]
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
                linestyle=ls, markersize=5, linewidth=1.3, capsize=2,
            )

    ax.axhline(0, color="k", linewidth=0.5, linestyle=":")
    ax.set_xlabel("Number of Pseudonymous Nodes")
    ax.set_ylabel("Profit Rate")
    ax.grid(alpha=0.3)
    leg_handles = [
        Line2D([0], [0], color=TIER_COLORS[t], marker=TIER_MARKERS[t],
               markersize=4, linewidth=1.3, label=t) for t in TIERS
    ] + [
        Line2D([0], [0], color="k", linestyle="-", linewidth=1.2, label="Holme-Kim"),
        Line2D([0], [0], color="k", linestyle="--", linewidth=1.2, label="Watts-Strogatz"),
    ]
    ax.legend(handles=leg_handles, fontsize=7.5, loc="lower left", framealpha=0.9)
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
