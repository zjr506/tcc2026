# Section 8.4 — Robustness Under Heterogeneous Cloud Nodes

> Drop-in subsection for the main paper, matching the prose style and
> length of Sections 8.1–8.3. Fig. 5 is a 2×2 grid with subfigures
> (a)–(d), matching the layout of Fig. 4.

---

## 8.4 Robustness Under Heterogeneous Cloud Nodes

The simulations in Sections 8.1–8.3 assume that cloud nodes are
homogeneous in their forwarding capacity and mining power. In practice,
cloud nodes are deployed on hosts ranging from small VPS instances to
bare-metal servers. To verify that the incentive mechanism remains robust
under such conditions, we assign each cloud node to one of four resource
tiers with population proportions 0.40, 0.30, 0.20, and 0.10, linearly
spaced so that the most constrained tier is the most common. The
per-block forwarding capacities of the four tiers are 250, 1000, 4000,
and 16 000, while mining power scales as 1×, 4×, 16×, and 64×. When a
node's forwarding work exceeds its tier capacity C_i, both its relay
revenue and forwarding count are scaled by C_i / W_i, because the excess
forwards arrive after downstream peers have already received the
transaction via a faster route.

We generate a 2000-node network with the same algorithm as in Section 8.1
(Doar, "A better model for generating test networks," IEEE GLOBECOM,
1996), assign tiers as above, and set the relay share to 50% of f0. The
profit rate (u − f ) / f0 is averaged over 5 random seeds. For the Sybil
experiment we use a 300-node Watts–Strogatz substrate (Watts and Strogatz,
"Collective dynamics of 'small-world' networks," Nature, 1998) with mean
degree 20, matching Section 8.2. In each of 3 seeds we select one
adversary from every tier, who creates x ∈ {0, 5, 10, 20, 30, 50}
pseudonymous nodes forming a clique; each pseudonymous transaction pays
0.1 f0.

Fig. 5(a) shows the profit rate against the number of links per tier.
Within every tier, the profit rate increases monotonically in the number
of links, preserving the key result of Fig. 2(a). The curves separate
by tier because a proportion-0.40 node cannot deliver all the sufficient
forwards its topological position would entitle it to, so only the first
250 are credited. Algorithm 2 makes no reference to any resource
attribute; the separation is entirely due to physical capacity ceilings.
Fig. 5(b) confirms this by showing the sufficient forwarding times per
tier: proportion-0.40 nodes saturate at 250, proportion-0.30 nodes at
1000, while proportion-0.10 nodes continue to grow with degree.

Fig. 5(c) verifies the per-forward fairness directly. Each point is a
single cloud node plotted with its sufficient forwarding count against
its relay revenue on a logarithmic scale. A single reference line with
slope 7.65 × 10⁻⁵ passes through the centre of every tier cloud. The
per-tier mean unit revenues are 7.652, 7.659, 7.630, and 7.613 × 10⁻⁵
for proportions 0.40, 0.30, 0.20, and 0.10, respectively — all within
0.6% of each other. The cross-network Pearson correlation is 0.95 and
the Spearman correlation is 0.90. Algorithm 2 pays every node the same
rate per forward regardless of tier; the only difference is how many
forwards each node can physically deliver.

Fig. 5(d) shows the Sybil attack result with the adversary drawn from
each tier. Every curve stays at or below zero for all x, confirming that
the attack is unprofitable regardless of the adversary's resources. The
proportion-0.40 adversary suffers the steepest loss (−4.45 at x = 50)
because its capacity is already saturated by honest traffic, so
pseudonymous transactions displace its own relay revenue. The
proportion-0.10 adversary sees the smallest penalty, with its profit
rate near zero at x ∈ {5, 10} and strictly negative from x ≥ 20 onward.
Heterogeneity does not open a new exploitable seam; capacity-bounded
adversaries find the attack harder, not easier.

We conclude that the fairness and attack-resistance guarantees of
Sections 8.1 and 8.2 extend to heterogeneous cloud node populations.
We have also verified that the active user node attack of Section 8.3
remains unprofitable under the same heterogeneity model but omit a
separate figure for space.

To assess how well the test topology approximates real cloud blockchain
networks, we replicate the fairness experiment on a second model: the
Holme–Kim power-law cluster graph (Holme and Kim, "Growing scale-free
networks with tunable clustering," Physical Review E, 2002) with the same
m = 4 edges per new node and triangle formation probability p = 0.5. Real
Bitcoin network measurements (Franzoni et al., "ATOM: Active topology
monitoring for the Bitcoin peer-to-peer network," Peer-to-Peer Networking
and Applications, 2022; Essaid et al., "Characterizing the Bitcoin network
topology with node-probe," International Journal of Network Management,
2023) report a clustering coefficient of 0.1–0.3 and a diameter of 5–7
hops. Our topology comparison shows that the Doar model yields clustering
of 0.004–0.024 — well below the real-network range — whereas the
Holme–Kim model achieves 0.21–0.24 across |V| = 1 000–5 000, placing it
squarely within 0.1–0.3. Both models share a similar average degree (~8)
and diameter of 5–6 hops. Under the Holme–Kim topology the per-tier unit
revenues remain within 0.7% of the Doar values, and the Sybil profit
rates remain at or below zero for all pseudonym counts and all tiers.
This insensitivity to clustering arises because Algorithm 2 operates on
a BFS tree rooted at the transaction source: the additional triangles
introduced by Holme–Kim are pruned during graph reduction and do not
create new incentive pathways. The heterogeneity results reported in this
section therefore hold across the realistic range of clustered scale-free
topologies that characterise real cloud blockchain deployments.
