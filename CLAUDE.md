# CLAUDE.md — Repository Context for tcc2026

## Project Overview

This repository contains the simulation code, supplementary prose, and
figures for a paper on the ITFC (Incentive for Transaction Fee
Cooperation) blockchain system. The main paper is `main.pdf`. The
supplement adds two new subsections (§8.4 and §8.5) with experiments
on heterogeneous cloud nodes and deployment performance overhead.

## Repository Structure

```
main.pdf                          # Published paper (read-only reference)
simulation/
  itfc.py                         # Core ITFC algorithms (graph_reduction, incentive_allocation, run_transaction)
  experiment_8_4.py               # §8.4 experiments: fairness + Sybil under heterogeneous tiers
  experiment_8_5.py               # §8.5 experiments: latency, block processing, storage overhead
  plot_fig5.py                    # Renders Fig. 5 (2x2 grid) for §8.4
  plot_fig6.py                    # Renders Fig. 6 (2x2 grid) for §8.5
supplement/
  section_8_4_heterogeneous.md    # §8.4 prose (drop-in subsection for main paper)
  section_8_5_performance.md      # §8.5 prose (drop-in subsection for main paper)
  heterogeneous_cloud_experiments.md  # Early design notes (superseded by section_8_4)
results/
  fairness.json                   # 30,000 records (10k per topology: Doar, HK, WS)
  sybil.json                      # 144 records (72 per substrate: HK, WS)
  topology_comparison.json        # Clustering/degree/diameter for Doar, HK, WS
  latency_vs_size.json            # Per-tx latency vs |V| (Doar + HK)
  latency_vs_txcount.json         # Block latency vs tx count
  storage.json                    # Per-block storage overhead
  fig5_section_8_4.{pdf,png}      # Fig. 5 rendered output
  fig6_section_8_5.{pdf,png}      # Fig. 6 rendered output
```

## Key Technical Concepts

### ITFC System
- Algorithm 1: BFS graph reduction, O(|V|+|E|) per transaction
- Algorithm 2: Incentive allocation over the reduced BFS tree
- `run_transaction(adj, source, w)` in `itfc.py` runs both algorithms

### Topology Models (in experiment_8_4.py)
- **Doar** (`make_doar_like`): Barabási-Albert backbone with degree capped to [4, 60]. Used in main paper §8.1. Reference: Doar, IEEE GLOBECOM 1996 (ref [42] in main.pdf). Clustering: 0.004–0.024.
- **Holme-Kim** (`make_holme_kim`): `nx.powerlaw_cluster_graph(n, 4, 0.12)`. Scale-free + tunable clustering. p=0.12 yields clustering 0.061–0.069, directly matching Bitcoin mainnet (0.068). Diameter: 5–6.
- **Watts-Strogatz** (`make_watts_strogatz`): `nx.watts_strogatz_graph(n, k, 0.1)`. Used in main paper §8.2 (ref [43]). Narrow degree distribution.

### Four Resource Tiers (§8.4 heterogeneity model)
| Tier (proportion) | Capacity | Mining power |
|-------------------|----------|-------------|
| 0.40              | 250      | 1×          |
| 0.30              | 1,000    | 4×          |
| 0.20              | 4,000    | 16×         |
| 0.10              | 16,000   | 64×         |

When forwarding work exceeds tier capacity C_i, revenue and forwards are scaled by C_i / W_i.

### Bitcoin Network Measurements (verified)
- Mainnet clustering coefficient: **0.068** (Essaid and Ju, Systems MDPI, 2022)
- Mainnet diameter: **6 hops** (same source)
- ~22,000 reachable nodes (Bitnodes [38])
- Default 8 outbound connections (Bitcoin.org P2P guide [36])
- The Holme-Kim model (clustering 0.22) **overestimates** Bitcoin's clustering, providing a conservative test

## Fig. 5 Layout (§8.4)

| Subfig | Content | Legend labels |
|--------|---------|--------------|
| (a) | Per-tier profit rate by topology (grouped bar chart) | Holme-Kim, Doar, Watts-Strogatz |
| (b) | Per-tier profit rate vs links, Holme-Kim | 0.40, 0.30, 0.20, 0.10 |
| (c) | Per-tier forwarding count vs links, Holme-Kim | 0.40, 0.30, 0.20, 0.10 |
| (d) | Per-tier Sybil profit rate vs pseudonyms, Holme-Kim | 0.40, 0.30, 0.20, 0.10 |

Design rule: each subfigure uses exactly ONE label type (tier numbers OR topology names), never both.

## Fig. 6 Layout (§8.5)

| Subfig | Content |
|--------|---------|
| (a) | Per-tx latency vs |V|: Alg 1+2 on Doar, HK, WS (3 topologies matching §8.4) |
| (b) | Block processing latency vs tx count for multiple |V| |
| (c) | Per-block storage vs |V|: allocation, topology changes (+ ★ §6.4 total estimate) |
| (d) | Cumulative blockchain size vs blocks for multiple |V| |

## Running Experiments

```bash
# Run §8.4 experiments (fairness + Sybil + topology comparison)
python3 -m simulation.experiment_8_4
# Generates: results/fairness.json, results/sybil.json, results/topology_comparison.json

# Run §8.5 experiments (latency + storage)
python3 -m simulation.experiment_8_5
# Generates: results/latency_vs_size.json, latency_vs_txcount.json, storage.json

# Render figures
python3 -m simulation.plot_fig5   # -> results/fig5_section_8_4.{pdf,png}
python3 -m simulation.plot_fig6   # -> results/fig6_section_8_5.{pdf,png}
```

## Key Experiment Results

### Fairness (fairness.json, 30,000 records)
- Per-tier mean profit rates are similar across all 3 topologies (HK, Doar, WS)
- HK per-tier unit revenues: 7.288, 7.351, 7.378, 7.281 × 10⁻⁵ (within 1.3%)
- Doar per-tier unit revenues: 7.652, 7.659, 7.630, 7.613 × 10⁻⁵ (within 0.7%)

### Sybil (sybil.json, 144 records)
- All profit rates ≤ 0 for all tiers on both HK and WS substrates
- HK substrate: tier 0.30 at x=50: −2.71 (steepest); tier 0.10 at x=50: −1.46 (smallest)

### Performance (§8.5)
- Latency slopes: Doar 5.52, HK 5.60, WS 5.99 × 10⁻³ ms/node (max spread 9%; WS higher due to BFS cross-edge checks from high clustering)
- Storage at |V|=22,000: 619.2 KB/block (within 0.5% of §6.4 analytical estimate)

## References Used in Supplement

Only cite references that are verifiable. References already in main.pdf:
- [36] Bitcoin.org, "P2P network guide," 2025
- [38] Bitnodes, "Global Bitcoin nodes distribution," 2025
- [40] Delgado-Segura et al., "TxProbe," FC 2019
- [42] Doar, "A better model for generating test networks," IEEE GLOBECOM, 1996
- [43] Watts and Strogatz, "Collective dynamics of 'small-world' networks," Nature, 1998

New references added in supplement:
- Holme and Kim, "Growing scale-free networks with tunable clustering," Physical Review E, 2002
- Essaid and Ju, "Deep learning-based community detection approach on Bitcoin network," Systems (MDPI), 2022

**Do NOT cite** Franzoni et al. (ATOM, 2022) or Essaid et al. (Node-Probe, 2023) for clustering/diameter values — ATOM is about inference methodology (not measurements), and the Node-Probe group's measured clustering is 0.068, not 0.1–0.3.

## Style Rules

- Use full paper citations (author, title, venue, year), not numbered refs like [40]
- Keep compound-word hyphens (e.g., "power-law", "scale-free"); do not use em-dashes to connect sentences
- Do not say the Doar model is "bad" or "inferior"; frame HK as a complementary test with different clustering
- Each Fig. 5 subfigure uses ONE label type: either tier proportions or topology names
- The main paper calls its topology "algorithms in [42]" (Doar), never "Barabási-Albert"

## Git Branches

- `main`: primary branch, all work merged here — **active development branch**
- `claude/recover-previous-work-RusgC`: merged into main; retired
