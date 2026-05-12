# Section 8.4 — Robustness Under Heterogeneous Cloud Nodes

> Drop-in subsection for the main paper, matching the prose style and
> length of Sections 8.1–8.3. Fig. 5 is a 2×2 grid with subfigures
> (a)–(d), matching the layout of Fig. 4.

---

## 8.4 Robustness Under Heterogeneous Cloud Nodes

Cloud nodes in a real deployment are hosted on machines that span a wide
range of resource levels, from small VPS instances with limited bandwidth
and storage to dedicated bare-metal servers with high throughput. To
verify that the ITFC incentive mechanism remains fair and
attack-resistant under such heterogeneity, this subsection introduces a
four-tier resource model and evaluates ITFC on the Holme-Kim power-law
cluster graph (Holme and Kim, "Growing scale-free networks with tunable
clustering," Physical Review E, 2002).

The Holme-Kim model generates networks by combining preferential
attachment with a triangle-formation step: after each new node attaches
to m existing nodes, an additional edge is formed to a neighbor of the
most recently chosen target with probability p. This process produces
both a scale-free degree distribution and tunable local clustering.
Measurements of the Bitcoin peer-to-peer network report an average
clustering coefficient of 0.068 on the mainnet and a network diameter
of 6 hops (Essaid and Ju, "Deep learning-based community detection
approach on Bitcoin network," Systems, 2022), with the Bitcoin protocol
specifying a default of 8 outbound connections per node (Bitcoin.org,
"P2P network guide," 2025) and approximately 22 000 reachable nodes
(Bitnodes, "Global Bitcoin nodes distribution," 2025). With m = 4 and
p = 0.12, the resulting graphs exhibit a clustering coefficient of
0.061 to 0.069, an average degree of approximately 8, and a diameter
of 5 to 6 hops, directly matching the measured Bitcoin mainnet
properties. The Doar topology of Section 8.1 (clustering 0.004 to
0.024) provides a complementary test with sparser local structure,
while the Watts-Strogatz topology of Section 8.2 exercises a narrow
degree distribution in contrast to the scale-free distribution of the
Holme-Kim model.

We assign each of the 2000 cloud nodes to one of four resource tiers
with population proportions 0.4, 0.3, 0.2, and 0.1, linearly spaced
so that the most constrained tier is the most common. The per-block
forwarding capacities of the four tiers are 250, 1000, 4000, and 16 000,
while mining power scales as 1×, 4×, 16×, and 64×. When a node's
forwarding work in a block exceeds its tier capacity C_i, both its relay
revenue and forwarding count are scaled by C_i / W_i, because the excess
forwards arrive after downstream peers have already received the
transaction via a faster route. The relay share is set to 50% of f0,
and the profit rate (u − f) / f0 is averaged over 5 random seeds.

Fig. 5(a) compares the per-tier profit rate across three topology
models: the Holme-Kim power-law cluster graph, the algorithm of Doar
("A better model for generating test networks," IEEE GLOBECOM, 1996)
used in Section 8.1, and the Watts-Strogatz small-world graph (Watts
and Strogatz, "Collective dynamics of 'small-world' networks," Nature,
1998) used in Section 8.2. All three topologies are generated with 2000
nodes, an average degree of approximately 8, and the same four-tier
heterogeneity model with proportions 0.4, 0.3, 0.2, and 0.1. The
grouped bars show the mean profit rate for each tier on each topology.
Within every tier, the three topologies produce closely matched profit
rates: for example, the proportion-0.4 tier yields −0.48 on
Holme-Kim, −0.48 on Doar, and −0.47 on Watts-Strogatz, while the
proportion-0.1 tier yields −0.21, −0.16, and −0.00, respectively. The
per-tier ordering is consistent across all three topologies, with
higher-capacity tiers achieving higher profit rates. This confirms that
the ITFC incentive structure is not sensitive to the choice of topology
model.

Fig. 5(b) shows the profit rate against the number of links per tier on
the Holme-Kim topology. Within every tier, the profit rate increases
monotonically in the number of links, preserving the key result of
Fig. 2(a). The curves separate by tier because a proportion-0.4 node
cannot deliver all the sufficient forwards its topological position would
entitle it to, so only the first 250 are credited. Algorithm 2 makes no
reference to any resource attribute; the separation is entirely due to
physical capacity ceilings. The per-tier mean unit revenues are 7.288,
7.351, 7.378, and 7.281 × 10⁻⁵ for proportions 0.4, 0.3, 0.2, and
0.1, respectively, all within 1.3% of each other. Algorithm 2 pays
every node the same rate per forward regardless of tier; the only
difference is how many forwards each node can physically deliver.

Fig. 5(c) confirms this by showing the sufficient forwarding times per
tier. Proportion-0.4 nodes saturate at their capacity of 250,
proportion-0.3 nodes at 1000, while proportion-0.1 nodes continue to
grow with degree. The local clustering of the Holme-Kim graph does
not alter the saturation pattern, because Algorithm 1 reduces the graph
to a BFS tree in which local triangles are pruned before incentive
allocation.

Fig. 5(d) shows the Sybil attack result with the adversary drawn from
each tier on a 300-node Holme-Kim substrate. In each of 3 seeds, one
adversary from every tier creates x ∈ {0, 5, 10, 20, 30, 50}
pseudonymous nodes forming a clique, with each pseudonymous transaction
paying 0.1 f0. Every curve stays at or below zero for all x, confirming
that the attack is unprofitable regardless of the adversary's resources.
The proportion-0.3 adversary suffers the steepest loss (−2.71 at
x = 50) because it falls from a higher honest baseline: at ≈300 honest
forwards per block, proportion-0.3 (capacity 1,000) earns full relay
revenue while proportion-0.4 (capacity 250) is already partially capped
at ≈83%. When 50 pseudonyms clique with the adversary, all pseudonym
traffic must route through it as the sole gateway, flooding its
forwarding count to ≈15,000; relay revenue collapses to ≈6.5% for
proportion-0.3 (drop ≈93.5%) versus ≈1.7% for proportion-0.4 (drop
≈81%). The proportion-0.1 adversary sees the smallest penalty (−1.46
at x = 50) because its 16,000-forward budget absorbs even the full
attack load with little saturation. Heterogeneity does not open a new
exploitable seam; capacity-bounded adversaries find the attack harder,
not easier.

We conclude that the fairness and attack-resistance guarantees of
Sections 8.1 and 8.2 extend to heterogeneous cloud node populations
under multiple network topologies, including the Holme-Kim model tuned
to match the measured clustering coefficient of the Bitcoin mainnet.
