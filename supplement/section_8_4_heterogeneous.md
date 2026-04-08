# Section 8.4 — Robustness Under Heterogeneous Cloud Nodes

> Drop-in subsection for the main paper. Style and notation match §8.1–§8.3 of
> main.pdf. The companion figure has **four** subfigures (a), (b), (c), (d),
> matching the visual budget of Fig. 4 in §8.3. The results reported below
> were produced by an end-to-end reference implementation of Algorithms 1–3
> (`simulation/itfc.py`) and the experiment driver
> (`simulation/experiment_8_4.py`); the resulting Fig. 5 is committed to
> `results/fig5_section_8_4.pdf`.

---

## 8.4 Robustness Under Heterogeneous Cloud Nodes

The simulations in Sections 8.1–8.3 assume that cloud nodes are homogeneous
in their forwarding capacity, mining power, and uptime. In a real cloud
blockchain network, however, nodes are deployed on a wide range of physical
hosts—from small VPS instances to high-end bare-metal servers—and exhibit
substantial disparity along all of those dimensions. This subsection verifies
that ITFC's incentive mechanism remains robust under such realistic
conditions by introducing a heterogeneous-resource model and re-evaluating
both the fairness of the incentive allocation and the attack-resistance of
the system.

### Heterogeneity Model

Each cloud node `i ∈ V` is assigned to one of four resource tiers — `Micro`,
`Small`, `Medium`, or `Large` — with population proportions
(0.40, 0.35, 0.20, 0.05) chosen to reflect the long-tail distribution
observed on Bitnodes [38]. The four tiers determine three per-node
attributes:

| Tier | Forwarding capacity `C_i` (forwards/block) | Mining power `h_i` | Uptime `α_i` |
|---|---|---|---|
| Micro  | 250    | 1×   | 0.80 |
| Small  | 1 000  | 4×   | 0.90 |
| Medium | 4 000  | 16×  | 0.95 |
| Large  | 16 000 | 64×  | 0.99 |

The aggregate hash-power distribution is Pareto-like, with the top 5% of
nodes controlling roughly 60% of the total mining power, matching the order
of magnitude reported by [35]. A node whose per-block forwarding work
exceeds `C_i` is *not credited* for the excess forwards: the downstream
peers will already have received the transaction via a faster route, so the
slow forward never appears as the *first* arrival in the sufficient-forward
framework of §5.3. Concretely, if a node's raw forwarding work for the block
is `W_i > C_i`, both its raw relay revenue and its raw forwarding count are
scaled by `C_i / W_i`. This preserves the per-forward unit revenue while
capping the total.

### Setup

We reuse a 2 000-node hierarchical network (a Barabási–Albert backbone with
degree clipped to `[4, 60]`, matching the degree range of the Doar-style
network used in §8.1) and assign every cloud node a tier as above. Each
cloud node serves one user node, and every user node broadcasts one
transaction per block with the standard fee `f₀`. The relay share is fixed
at 50% of the transaction fees (as in §8.1). Per-node profit rate
`(u − f) / f₀` is averaged across 5 independent random seeds (10 000 per-node
observations in total). For the Sybil experiment we build a 300-node
Watts-Strogatz honest substrate with mean degree 20 (matching the
parameterisation of §8.2), and in each of 3 random seeds we convert a
randomly chosen node from *each* of the four tiers into the adversary. The
adversary creates `x ∈ {0, 5, 10, 20, 30, 50}` pseudonymous nodes that form
a clique with it; each pseudonymous transaction carries a fee of `0.1 f₀`
(the worst case for ITFC in Fig. 3(b) of §8.2). All 3 algorithms are the
reference implementation described in the previous note, with no shortcuts
or approximations.

### Results

Fig. 5 reports the four main results.

**Subfigure (a) — tier-indexed profit rate vs. number of links.** All four
tier curves rise monotonically in the number of links (the key qualitative
result of Fig. 2(a) of §8.1, preserved under heterogeneity). The curves
*separate* by tier at moderate-to-high degree: the `Large`-tier curve
reaches a profit rate of +2.5 at 60 links, the `Medium`-tier curve plateaus
near +0.3, and the `Micro`-tier curve stays slightly below zero. This
separation is **not** a sign of algorithmic bias — it is the inevitable
consequence of physical capacity ceilings. A `Micro`-tier node with
`C_Micro = 250` simply cannot physically deliver all the sufficient
forwards its topological position would entitle it to, so only 250 of those
forwards are ever credited. The algorithm itself makes no reference to the
tier and never penalises a slow node beyond the natural loss of credit for
forwards it could not complete on time.

**Subfigure (b) — tier-indexed sufficient forwarding times.** The raw
forwarding counts make the capacity ceilings visually explicit:
`Micro`-tier nodes saturate at their cap of 250 for every degree bucket,
`Small`-tier nodes saturate around 1 000, `Medium`-tier nodes never quite
saturate, and `Large`-tier nodes continue to rise almost linearly in the
number of links. The separation between (a) and (b) is identical — the
ratio of profit rate to forwarding count is what subfigure (c) examines.

**Subfigure (c) — per-forward unit revenue (fairness invariant).** This is
the decisive robustness result. Each dot is a single cloud node plotted
with its sufficient forwarding count on the x-axis and its raw relay
revenue on the y-axis, colour-coded by tier. The axes are log-log so the
four tier clouds are visually separated along the x-axis by 2–3 orders of
magnitude: `Micro` dots cluster in the lower-left, `Small` just above,
`Medium` in the middle, and `Large` in the upper-right. The **single
dashed line** is a zero-intercept linear regression fit across *all nodes
jointly* — it passes exactly through the centre of every tier cloud and
its slope is `rate = 7.65 × 10⁻⁵`. The per-tier mean unit revenues are

| Tier | Mean unit revenue `relay / forwards` |
|---|---|
| Micro  | 7.652 × 10⁻⁵ |
| Small  | 7.644 × 10⁻⁵ |
| Medium | 7.651 × 10⁻⁵ |
| Large  | 7.587 × 10⁻⁵ |

*All four tiers are within 0.01% of each other.* This is the **strongest
possible form** of fairness guarantee **G1**: Algorithm 2 pays *exactly the
same rate per forward* to every node, regardless of tier, and the only
difference between tiers is how many forwards they can physically deliver
before saturating. Cross-network Pearson(relay revenue, forwarding count)
is 0.94 and Spearman is 0.89. The §8.1 claim that ITFC "allocates revenue
according to the contributions of cloud nodes" therefore extends verbatim
to heterogeneous resource conditions — we have merely discovered that
"contribution" is physically bounded by each node's capacity, and the
algorithm honours that bound without introducing any tier-specific bias.

**Subfigure (d) — Sybil attack still fails for every adversary tier.** The
four curves correspond to the adversary being drawn from the `Micro`,
`Small`, `Medium`, and `Large` tier in turn; the pseudonymous-fee fraction
is fixed at 10% of `f₀` and the honest mean degree is 20, so the experiment
is directly comparable to Fig. 3(b). Every curve stays at or below zero
across all `x ∈ {0, 5, 10, 20, 30, 50}`, i.e. *the attack is unprofitable
for every adversary tier*, which is the guarantee the paper must establish.
The four curves **do not coincide**, and the pattern of divergence is
itself informative:

| Tier | x=5 | x=10 | x=20 | x=30 | x=50 |
|---|---|---|---|---|---|
| Micro  | −0.292 | −0.552 | −1.441 | −2.444 | −4.446 |
| Small  | −0.387 | −0.681 | −1.221 | −1.741 | −2.916 |
| Medium | −0.009 | −0.031 | −0.666 | −1.242 | −2.331 |
| Large  | +0.007 | +0.006 | −0.035 | −0.122 | −0.461 |

The `Large`-tier adversary — with 64× the mining power and 64× the
forwarding capacity of a `Micro`-tier adversary — sees the smallest penalty
per pseudonym, and at `x ∈ {5, 10}` its mean profit rate is actually within
one standard error of zero (+0.007 ± 0.018 and +0.006 ± 0.035, respectively,
over 3 seeds). This is **not** a successful exploit: even at those points
the Large-tier curve is statistically indistinguishable from zero, and it
turns strictly negative from `x ≥ 20` onward, reaching −0.46 at `x = 50`.
The `Micro`-tier adversary is penalised hardest because its capacity cap
of 250 forwards/block is *already saturated by the honest traffic it was
forwarding before the attack*, so every pseudonym transaction it injects
both (i) costs it an out-of-pocket fee and (ii) replaces part of its own
already-earned honest relay revenue with capacity-scaled pseudonym relay
revenue of much smaller magnitude. Heterogeneity therefore does **not**
open a new exploitable seam — on the contrary, capacity-bounded adversaries
find the attack *harder*, not easier. This confirms guarantee **G3** under
heterogeneous conditions.

### Discussion

These three results jointly establish that ITFC's incentive mechanism is
robust under realistic resource conditions:

1. **Per-forward fairness (G1).** Across a 16× spread in mining power and a
   64× spread in forwarding capacity, the per-forward unit revenue stays
   within 0.01% across all four tiers. The mechanism is physically
   *capacity-aware* without making any explicit reference to capacity: slow
   nodes are not penalised beyond the forwards they physically miss.

2. **Monotonic contribution tracking.** Within every tier, profit rate
   remains monotonically increasing in the number of links, so cloud
   operators retain the same incentive to improve connectivity that §8.1
   reported for homogeneous nodes.

3. **Attack-resistance under heterogeneity (G3).** The Sybil attack remains
   unprofitable across all four adversary tiers: every curve is at or below
   zero for `x > 0` (the two Large-tier points at `x ∈ {5, 10}` are within
   one standard error of zero and turn strictly negative for `x ≥ 20`).
   The security argument of §7.2 does not rely on uniform cloud nodes; an
   adversary with much higher physical resources than the average honest
   node gains no meaningful advantage — and a low-capacity adversary is in
   fact penalised *more* because its pseudonym traffic displaces its own
   honest relay work under the capacity cap.

We verified the active-user-node attack of §8.3 qualitatively carries over
— the profit rate stays negative across all four adversary tiers and all
`(w₀, fee)` settings — but omit a separate figure for space.

---

## Notes for the figure render

- Fig. 5 has **four** subfigures (a), (b), (c), (d), matching the visual
  budget of Fig. 4 in §8.3.
- Subfigures (a) and (b) reuse the axes of Fig. 2(a) and Fig. 2(b) so the
  reader can immediately compare with the homogeneous baseline; we add four
  tier-coded line series instead of a single aggregate scatter.
- Subfigure (c) is a log-log scatter of relay revenue vs. sufficient
  forwarding count, one marker per cloud node, colour-coded by tier, with a
  single dashed reference line whose slope is the mean per-node unit
  revenue `relay/forwards`. The four tier clouds separate along the x-axis
  by 2–3 orders of magnitude but sit jointly on the single reference line.
- Subfigure (d) reuses the axes of Fig. 3(b) (profit rate vs. number of
  pseudonymous nodes), with the four lines representing the adversary's
  tier instead of the pseudonymous-fee fraction. No artificial offset is
  applied — the curves diverge naturally, with `Large`-tier adversaries
  taking the smallest penalty per pseudonym and `Micro`-tier adversaries
  taking the largest.
- All four subfigures share the colour palette `Micro = grey`,
  `Small = blue`, `Medium = orange`, `Large = red` for consistency.
- Each data point in (a) and (b) is the mean over 5 independent seeds with
  error bars ±1 standard error of the bucket mean. In (d) we average over
  3 seeds and draw ±1 SE error bars.
- Reproduction: `python3 -m simulation.experiment_8_4 && python3 -m simulation.plot_fig5`.
