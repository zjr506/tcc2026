# Supplementary Simulation Experiments: ITFC under Heterogeneous Cloud Nodes

This document specifies a set of supplementary simulation experiments to assess
the **robustness of the ITFC incentive mechanism** (Algorithms 1–3 in the main
paper) when cloud nodes are *heterogeneous* in their computational, bandwidth,
storage, connectivity, uptime, and user-base characteristics. The experiments
in Section 8 of the main paper assume homogeneous cloud nodes (equal mining
probability, equal forwarding capacity, identical user-base size, identical
honest transaction fees). Real cloud blockchain networks—e.g., Bitcoin full
nodes hosted on a wide range of VPS/bare-metal tiers—exhibit substantial
disparity along all of these dimensions. The goal of the supplement is to
verify that ITFC's three core guarantees still hold under that disparity:

- **G1 — Contribution-proportional allocation**: Each cloud node's revenue
  remains proportional to its *actual* forwarding/serving contribution.
- **G2 — Disconnection-resistance** (Theorem 2): No node can increase its
  revenue by unilaterally dropping links.
- **G3 — Attack-resistance**: ITFC continues to neutralize Sybil and
  active-user-node attacks as in Section 7, with no new exploitable seam
  introduced by heterogeneity.

The experiments below extend, but do *not* replace, those in main.pdf §8. They
are intended to be added as a new sub-section "8.4 Robustness under
Heterogeneous Cloud Nodes" or as an appendix.

---

## 1. Heterogeneity Model

We introduce a per-node *resource profile* drawn from realistic distributions
calibrated against public Bitcoin/Ethereum node statistics
([35], [38], [39] in main.pdf). For each cloud node `i ∈ V` we sample:

| Attribute | Symbol | Distribution | Realistic anchor |
|---|---|---|---|
| Hash power (mining) | `h_i` | Pareto(α = 1.16, x_min = 1) | Top-10 pools control 91.54% of Bitcoin hash power [35] |
| Outbound BW (Mbps) | `B_i` | LogNormal(μ = ln 100, σ = 1.0) | AWS/Azure/Hetzner cloud-node tier mix |
| CPU forwarding capacity (tx/s) | `C_i` | LogNormal(μ = ln 800, σ = 0.8) | Bitcoin Core forward throughput on c5.large–c5.4xlarge |
| Max in/out peer slots | `δ_i^max` | Truncated Geometric, mean = 16, cap = 125 | Bitcoin Core default 8/125 |
| Mean uptime fraction | `α_i` | Beta(8, 1) | Bitnodes 30-day uptime distribution |
| Geographic RTT class | `ρ_i` | Categorical{NA, EU, AS, SA, AF} from real population shares | Bitnodes geographic mix |
| Served user nodes | `|U_i|` | Zipf(s = 1.07) over a global pool of `n_u` users | Long-tail wallet→service-provider concentration |
| Honest fee scale | `φ_i` | Uniform(0.8 f₀, 1.2 f₀) (per submitted tx) | Heterogeneous fee bidding |

Resource classes are also grouped into four discrete *tiers* — `Micro`,
`Small`, `Medium`, `Large` — with population proportions
(0.40, 0.35, 0.20, 0.05). The continuous samples above are conditioned on the
tier so a single random seed is sufficient to reproduce the experiment.

The link-level cost of forwarding a transaction from `i` to `j` becomes
`τ_ij = max(s_t / B_i, 1 / C_i) + RTT(ρ_i, ρ_j)`,
where `s_t` is the transaction size. This per-link delay (a) is what an honest
neighbour uses to decide whether a link is "responsive" (Section 7.2.1), and
(b) is what determines whether a node can keep up with the offered load.

---

## 2. Experiments

Each experiment lists *what changes vs. §8*, the *parameters swept*, the
*metrics reported*, and the *hypothesis being tested*.

### E1 — Allocation fairness under heterogeneous compute (extends §8.1)

**Setup.** Reuse the 10 000-node Doar [42] topology of §8.1 but assign every
node a profile from §1. Each user node still issues one transaction per round.
For each transaction `t = (h, s, q, w)`, simulate the broadcast at the
link-level using `τ_ij`, dropping forwards that exceed the next block's
horizon.

**Sweeps.**
- Hash-power skew: Pareto α ∈ {0.8, 1.16, 1.6, ∞} (∞ ≡ uniform / §8.1 baseline).
- Resource-tier mix: balanced vs. realistic (0.40/0.35/0.20/0.05) vs. inverted.

**Metrics.**
- Pearson and Spearman correlation between *sufficient-forwarding count* and
  *received revenue* (per node, per tier).
- Jain's fairness index `J = (Σ aᵢ)² / (n · Σ aᵢ²)` over each tier.
- Gini coefficient of profit rate vs. Gini of contribution.
- Per-tier mean profit rate `(u − f) / f₀`.

**Hypothesis (G1).** Spearman correlation ≥ 0.95 in every cell of the
sweep, and intra-tier Jain index > 0.9 — i.e., heterogeneity in *unrelated*
resources (e.g., hash power) does **not** distort relay revenue, which depends
only on topological position via `(p_i, d_i)`.

### E2 — Bandwidth/CPU-bottlenecked forwarding

**Setup.** Same as E1, but reduce the per-block budget so that low-`B_i` nodes
*cannot* finish forwarding every transaction within the block interval.
Forwards that miss the budget are *not counted* by Algorithm 2 — they don't
appear on any sufficient-forwarding path because downstream peers will have
already received the transaction from a faster route.

**Sweeps.**
- Offered load: 1k, 3k, 10k, 30k tx/block.
- BW LogNormal σ ∈ {0.0, 0.5, 1.0, 1.5}.

**Metrics.**
- Per-tier *contribution share* vs. *revenue share*.
- Fraction of weak nodes (Micro tier) with non-negative profit rate
  ("participation incentive").
- "Wasted-effort ratio": forwarded but never-on-shortest-path transactions
  divided by total forwards.

**Hypothesis (G1, participation).** Even in the most skewed case
(σ = 1.5, 30k tx/block), Algorithm 2 still rewards bottlenecked nodes
proportionally to *what they actually delivered on time*, and the participation
ratio of Micro-tier nodes stays > 50% — i.e., weak nodes are not driven out of
the market by faster competitors.

### E3 — Latency-aware sufficient forwarding and detection threshold

**Setup.** Apply the realistic geographic-RTT matrix from §1 to E1's network.
Each honest node uses an *expected delivery time* check (paper §7.2.1) to
decide whether a peer's forwarded transaction arrived "on time"; we
parameterise the tolerance `Δ` as a multiple of the median path RTT.

**Sweeps.**
- Tolerance multiplier `Δ ∈ {1.0, 1.5, 2.0, 3.0, 5.0}`.
- Adversarial fake-link rate (cf. §7.2.1): 0%, 5%, 20%.

**Metrics.**
- False-positive rate: honest links wrongly marked as fake under heterogeneity.
- True-positive rate: fake adversarial links correctly disconnected.
- Net revenue loss to honest *slow* nodes due to false positives.

**Hypothesis.** A tolerance of `Δ ≥ 2.0 × median RTT` is sufficient to keep
the honest false-positive rate below 1% across all tiers, while still
detecting > 95% of fake adversarial links. This identifies a *concrete,
operational* setting for the detection mechanism that the paper currently
leaves abstract.

### E4 — Pareto mining power and the relay-vs-mine cost-to-income invariant

**Setup.** Reuse E1 with Pareto α = 1.16 hash power. The block-generator
selection is now weighted by `h_i`. Section 5.1 of the main paper argues that
the unit revenue of mining must remain ≥ the unit revenue of forwarding;
the homogeneous experiments cannot test this because every node had identical
hash rate.

**Sweeps.**
- Relay share `w₀ / w ∈ {0.1, 0.25, 0.5, 0.75, 0.9}`.
- Hash skew α ∈ {0.8, 1.16, 1.6}.

**Metrics.**
- For each tier, `unit_mine = mining_revenue / hash_units` vs.
  `unit_relay = forwarding_revenue / forwarding_units`.
- Best-response check: would a tier maximise total revenue by reallocating
  resources from mining to forwarding (or vice versa)?

**Hypothesis (G1, §5.1).** With `w₀ ≤ 0.5 · w`, `unit_mine ≥ unit_relay`
holds in *every* tier — confirming that the §5.1 argument is robust to
hash-power heterogeneity, not just an artefact of uniform mining.

### E5 — Heterogeneous churn (uptime/availability)

**Setup.** Each node `i` toggles online/offline according to a two-state
Markov chain with stationary online probability `α_i ~ Beta(8, 1)` (so the
mean is 0.89 but the tail includes flaky nodes). Disconnect events are
broadcast as in §4.4.2 and reflected in the topology field of subsequent
blocks.

**Sweeps.**
- Beta(a, 1) shape `a ∈ {2, 4, 8, 16}` (smaller = flakier population).
- Block interval relative to mean session length: 0.1, 1.0, 10.0.

**Metrics.**
- Time-averaged profit rate per tier.
- Topology-update overhead: bytes of connect/disconnect events per block.
- Disconnect-driven revenue volatility (std-dev / mean of per-block revenue).
- Empirical verification of Theorem 2: for every observed unilateral
  disconnect, did the disconnecting node's revenue decrease (or stay equal)?

**Hypothesis (G2).** ≥ 99.9% of disconnects yield non-positive revenue
delta for the disconnecting node — empirically confirming Theorem 2 in a
realistic dynamic regime, *not* just in a static graph.

### E6 — Heterogeneous served-user populations (extends Algorithm 3)

**Setup.** Distribute `n_u = 1 000 000` user nodes across the 10 000 cloud
nodes via Zipf(s = 1.07) so that the top decile of cloud nodes serves > 70%
of users. Each active user issues one transaction every `H/2` blocks.

**Sweeps.**
- Allocation split `w₀ : w₁ ∈ {1:0, 0.9:0.1, 0.5:0.5, 0.1:0.9}`.
- Active window `H ∈ {1, 5, 10, 50}`.

**Metrics.**
- Correlation between `|U_i|` and `a'_i` (must be 1.0 by Algorithm 3 — sanity).
- Joint Jain fairness over `(a_i + a'_i)`.
- Tail behaviour: revenue concentration (top 1% / total).

**Hypothesis (G1).** Even with extreme user-base concentration, the *combined*
revenue `a_i + a'_i` does not produce Gini > 0.7 once `w₀ ≥ 0.5`, so a
moderately broadcast-weighted split prevents user-base monopolisation from
destabilising the network.

### E7 — Sybil attack under heterogeneity (extends §8.2)

**Setup.** Watts–Strogatz network with 1 000 nodes and mean degree 10 / 50, as
in §8.2, but the 1 000 honest nodes carry the §1 resource profile. The
adversary controls one Medium-tier node that creates `x` pseudonymous nodes
forming a clique with itself.

**Sweeps.**
- Adversary tier ∈ {Micro, Small, Medium, Large}.
- Pseudonymous-fee fraction y ∈ {5%, 10%, 25%, 50%, 75%, 100%} of f₀.
- `x ∈ [0, 50]`.

**Metrics.**
- Adversary profit rate `(u − f) / f₀` as in §8.2.
- *Difference* relative to the §8.2 homogeneous baseline.

**Hypothesis (G3).** No tier of adversary improves on the §8.2 homogeneous
result. In particular, a Large-tier adversary (high `B_i`, high `C_i`) cannot
exploit its bandwidth advantage to make Sybil profitable, because Algorithm 2
allocates by topology not by physical capacity.

### E8 — Active user node attack under heterogeneity (extends §8.3)

**Setup.** §8.3 setup (10 000 tx/block, H = 1, w₀ ∈ {1, 0.5}) with §1
profiles. The adversary is a Large-tier node with degree 50. Honest user
populations `|U_i|` are Zipf-distributed.

**Sweeps.**
- Adversary's controlled user-node count ∈ {50, 100, 500, 2000}.
- Per-fake-user fee ∈ {0.1 f₀, 0.5 f₀, f₀}.

**Metrics.** Profit rate over 10 blocks, broken down between relay revenue
and serving revenue.

**Hypothesis (G3).** Heterogeneity does not change the qualitative result of
§8.3: the profit rate stays negative across all configurations whenever
honest fees are in effect.

### E9 — Empirical disconnection-incentive audit (Theorem 2 stress test)

**Setup.** For the heterogeneous E1 network, run a *brute-force search* over
all single-edge disconnections by every node (or a random sample of 10⁵
edges if exhaustive is too costly). For each candidate disconnect, recompute
Algorithms 1–3 and record the disconnecting node's revenue delta over a 100
block window.

**Sweeps.**
- Topology generator: Doar [42] hierarchical *and* Watts–Strogatz *and*
  Barabási–Albert (`m = 4`) — to ensure the result is not artefact of one
  generator.

**Metrics.**
- Distribution of `Δa_i = a_i^{after} − a_i^{before}`.
- Maximum observed positive delta (must be 0 if Theorem 2 holds).

**Hypothesis (G2).** `max Δa_i = 0` across *every* sample, providing
empirical reinforcement of Theorem 2 in a setting where homogeneity cannot
"hide" a counter-example.

### E10 — Scalability of Algorithms 1–3 under realistic node mix

**Setup.** Repeat E1 at `|V| ∈ {1k, 10k, 22k, 50k, 100k}` with the realistic
heterogeneous profile, recording per-block compute time of Algorithms 1, 2,
and 3 on (a) a Large-tier node and (b) a Micro-tier node.

**Metrics.**
- Wall-clock time vs. `|V| + |E|` (validate the `O(|V|+|E|)` claim of §5.3).
- Memory footprint of the topology field.
- Fraction of Micro-tier nodes that *fail* to compute incentive allocation
  before the next block — i.e., are practically excluded from acting as
  block generators.

**Hypothesis.** Algorithms 1–3 stay sub-second even at 100 k nodes on a
Micro-tier profile, so the §5.3 complexity claim is operationally true and
ITFC does not centralise block generation onto Large-tier nodes.

---

## 3. Aggregate Metrics and Reporting

For each experiment we report:

1. **Per-tier profit-rate distribution** as a box plot over independent seeds.
2. **Sufficient-forwarding-vs-revenue correlation** (Pearson + Spearman) for
   every node.
3. **Jain's fairness index** within tier and across the whole network.
4. **Adversary profit rate** in attack experiments, against the §8 baseline.
5. **Algorithm runtime CDF** for Algorithms 1, 2, 3, separately.
6. **Empirical disconnect-ROI table** to corroborate Theorem 2.

Error bars are computed over at least 30 independent seeds. Hypothesis tests
use a one-sided Wilcoxon signed-rank test with α = 0.01. The exact RNG seeds,
parameter dictionaries and tier profiles for each experiment are stored in
`supplement/configs/` (to be added when the simulator code is released).

---

## 4. Expected Contribution to the Paper

Adding §8.4 with E1, E2, E5, E7, E8, E9 (the strict minimum) would let the
paper:

- Counter the obvious referee question "your simulation assumes uniform
  cloud nodes — does the mechanism survive realistic disparities?".
- Provide an *operational tolerance setting* `Δ` for the §7.2.1 fake-link
  detector, which is currently described only abstractly.
- Provide empirical reinforcement of Theorem 2 beyond the analytical proof.
- Demonstrate that *participation by weak nodes is preserved*, which is the
  central long-run health requirement of any incentive mechanism.

E3, E4, E6 and E10 are additional, optional experiments that strengthen the
paper but can be deferred to a journal extension if space is tight.
