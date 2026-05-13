# Section 8.5 - Deployment Performance Overhead

> Drop-in subsection for the main paper, matching the prose style and
> length of Sections 8.1-8.4. Fig. 6 is a 2x2 grid with subfigures
> (a)-(d), matching the layout of Fig. 4 and Fig. 5.

---

## 8.5 Deployment Performance Overhead

Section 6.4 estimates the storage overhead of the incentive allocation
field at approximately 616 KB per block for a network of 22 000 cloud
nodes. Section 5.3 proves that the time complexity of Algorithms 1 and 2
is O(|V| + |E|) per transaction. This subsection substantiates both
claims quantitatively by measuring the computation latency of the full
Algorithms 1 and 2 pipeline and the storage overhead across a range of
network scales. To confirm that the results hold across different network
structures, we run the latency measurements on the same three topologies
used in Section 8.4: the algorithm of Doar ("A better model for
generating test networks," IEEE GLOBECOM, 1996), the Holme-Kim
power-law cluster graph (Holme and Kim, "Growing scale-free networks
with tunable clustering," Physical Review E, 2002), and the
Watts-Strogatz small-world graph (Watts and Strogatz, "Collective
dynamics of 'small-world' networks," Nature, 1998).

We generate networks with the same parameters as Section 8.4: 2000
cloud nodes, an average degree of approximately 8, m = 4 for both the
Doar and Holme-Kim models, Holme-Kim triangle-formation probability
p = 0.12 (clustering 0.061 to 0.069, matching the Bitcoin mainnet), and
Watts-Strogatz rewiring probability 0.1. To measure per-transaction
latency we sample 50 random source nodes from each generated graph, time
Algorithms 1 and 2 together, and divide the total by 50, averaged over
3 independent seeds. For the block latency experiment we fix four network
sizes and vary the number of transactions per block from 50 to 2000,
using the Doar topology. For the storage analysis we apply the encoding
of Section 6.4: each incentive allocation entry occupies 28 bytes (a
20-byte address and an 8-byte revenue value), and each topology change
event occupies 41 bytes (two addresses and a type byte). We model a churn
rate of 0.5% of all edges per block.

Fig. 6(a) plots the per-node latency rate - the per-transaction latency
of the full Algorithms 1 and 2 pipeline divided by |V| - across network
sizes from |V| = 500 to 20 000 for the three topologies. A flat
horizontal band for each topology directly confirms O(|V|) scaling: if
processing time were super-linear in |V|, the rate would rise with |V|.
The three bands are clearly separated. The fitted per-node rates are
5.52 x 10^-3 ms per node for Doar, 5.60 x 10^-3 ms per node for
Holme-Kim, and 5.99 x 10^-3 ms per node for Watts-Strogatz, a maximum
spread of 9%. The Watts-Strogatz rate is slightly higher because its
uniformly distributed degree sequence and high local clustering (0.47)
generate more BFS cross-edge checks per transaction during the graph
reduction of Algorithm 1. Algorithm 2 adds negligible overhead on top of
Algorithm 1 for all three topologies, because the incentive computation
iterates over the same BFS edge set and requires no additional graph
traversal. At the Bitcoin reference scale of |V| = 22 000 the
extrapolated per-transaction latency is approximately 121 ms for Doar,
123 ms for Holme-Kim, and 132 ms for Watts-Strogatz, all well below the
ten-minute block interval.

Fig. 6(b) shows the block processing latency as a function of the number
of transactions for four network sizes on the Doar topology. All four
curves are linear in the number of transactions, confirming O(T) scaling
in the transaction count T. The curves are separated by |V|: the
|V| = 500 line processes 2000 transactions in 4.6 s, while the
|V| = 5000 line takes 52.8 s for the same count, matching the
linear-in-|V| scaling established in Fig. 6(a). At Bitcoin's approximate
rate of 2000 to 3000 transactions per block and network scale
|V| = 22 000, block generators have ample margin within the ten-minute
block interval.

Fig. 6(c) shows the per-block storage overhead versus network size.
Incentive allocation grows at 28 bytes per node and dominates the total,
while topology change storage grows much more slowly, reaching about
41 KB even at |V| = 50 000. The dashed line shows the Section 6.4
analytical estimate for the incentive allocation field, extrapolated as a
linear function of |V| with slope 616 KB / 22 000 nodes. Using the same
decimal-KB convention as Section 6.4, this line coincides with the
simulated allocation component: at |V| = 22 000, the allocation field is
616.0 KB, topology changes add 18.0 KB, and the total is 634.0 KB. Thus
topology churn adds only 2.9% over the allocation-field estimate at the
Bitcoin-scale reference point.

Fig. 6(d) shows the cumulative ITFC-specific blockchain overhead over
time for the same four network sizes as Fig. 6(b). At Bitcoin's rate of
approximately 144 blocks per day, the |V| = 5000 case accumulates
roughly 20 MB per day, while the |V| = 500 case accumulates less than
2 MB per day. We conclude
that the deployment performance overhead of ITFC is modest and well
within the storage and computation capacities of the cloud nodes
described in Section 3.

The topology comparison confirms that the O(|V| + |E|) performance bound
holds across all three network models, which span a wide range of
structural properties as documented in Section 8.4: Doar (clustering
0.004 to 0.024), Holme-Kim with m = 4, p = 0.12 (clustering 0.061 to
0.069, directly matching the measured Bitcoin mainnet clustering of 0.068
reported by Essaid and Ju, "Deep learning-based community detection
approach on Bitcoin network," Systems, 2022), and Watts-Strogatz
(clustering 0.47 to 0.48). The per-transaction slopes are within 9% of
one another; the Watts-Strogatz slope is slightly elevated because its
high clustering generates more cross-edge checks during Algorithm 1, but
the O(|V|) class of the bound is unchanged. The ITFC overhead figures
reported above are therefore valid across all three network structures and
across the full range of local clustering observed in practice.
