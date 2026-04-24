# Section 8.5 — Deployment Performance Overhead

> Drop-in subsection for the main paper, matching the prose style and
> length of Sections 8.1–8.4. Fig. 6 is a 2×2 grid with subfigures
> (a)–(d), matching the layout of Fig. 4 and Fig. 5.

---

## 8.5 Deployment Performance Overhead

Section 6.4 estimates the storage overhead of the incentive allocation
field at approximately 616 KB per block for a network of 22 000 cloud
nodes. Section 5.3 proves that the time complexity of Algorithms 1 and 2
is O(|V| + |E|) per transaction. This subsection substantiates both
claims quantitatively by measuring the computation latency of each
algorithmic stage and the storage overhead across a range of network
scales. To assess robustness to network topology, we repeat the latency
measurements on two graph models: the Barabási–Albert (BA) graph used in
Sections 8.1–8.4, and the Holme–Kim (HK) power-law cluster graph [40],
which adds triangle formation (probability p = 0.5) on top of preferential
attachment. The HK model better captures the clustering coefficient of
real cloud blockchain networks (0.1–0.3 [38]) while preserving the
scale-free degree distribution and diameter of BA.

We generate test networks with the same Barabási–Albert algorithm as in
Section 8.1, with the number of links per cloud node ranging from 4 to
60. The Holme–Kim networks use m = 4 and p = 0.5. To measure
per-transaction latency we sample 50 random source nodes from each
generated graph, time Algorithm 1 (graph reduction) alone and then
Algorithms 1 and 2 together, and divide the total by 50. We repeat each
measurement over 3 independent seeds. For the block latency experiment we
fix four network sizes and vary the number of transactions per block from
50 to 2000. For the storage analysis we apply the encoding of Section 6.4:
each incentive allocation entry occupies 28 bytes (a 20-byte address and
an 8-byte revenue value), and each topology change event occupies 41 bytes
(two addresses and a type byte). We model a churn rate of 0.5% of all
edges per block.

Fig. 6(a) shows the per-transaction latency for Algorithm 1 alone and for
Algorithms 1 and 2 combined, across network sizes from |V| = 500 to
20 000, separately for the BA and HK topologies. All four curves grow
linearly, with a fitted slope of 4.38 × 10⁻³ ms per node for BA and
4.59 × 10⁻³ ms per node for HK under the combined pipeline. The HK slope
is only 5% higher than BA, because the triangle formation step raises the
average edge count by at most 5% relative to pure preferential attachment
with the same m. Algorithm 2 adds only a small constant fraction on top
of Algorithm 1 for both topologies, because the incentive computation
iterates over the same edge set produced by the graph reduction and
requires no additional graph traversal. At the Bitcoin reference scale of
|V| = 22 000, the extrapolated per-transaction latency is approximately
96 ms for BA and 101 ms for HK, both well below the ten-minute block
interval.

Fig. 6(b) shows the block processing latency as a function of the number
of transactions for four network sizes. All four curves are linear in the
number of transactions, confirming O(T) scaling in the transaction count
T. The curves are separated by |V|: the |V| = 500 line processes 2000
transactions in 4.6 s, while the |V| = 5000 line takes 44.5 s for the
same count, matching the linear-in-|V| scaling established in Fig. 6(a).
At Bitcoin's approximate rate of 2000–3000 transactions per block and a
network scale of |V| = 22 000, block generators have ample margin within
the ten-minute block interval.

Fig. 6(c) shows the per-block storage overhead versus network size.
Incentive allocation storage grows strictly linearly at 28 bytes per
node and dominates the total, while topology change storage remains below
40 KB even at |V| = 50 000. At |V| = 22 000 the model yields 601.6 KB
for incentive allocation, 17.6 KB for topology changes, and 619.2 KB in
total — within 0.5% of the §6.4 analytical estimate of 616 KB, validating
that estimate precisely.

Fig. 6(d) shows the cumulative ITFC-specific blockchain overhead over
time for four network sizes. At Bitcoin's rate of approximately 144
blocks per day, the |V| = 22 000 case accumulates roughly 87 MB per day,
while the |V| = 5000 case accumulates only 20 MB per day. We conclude
that the deployment performance overhead of ITFC is modest and well
within the storage and computation capacities of the cloud nodes
described in Section 3.

Both topology models yield nearly identical O(|V|) scaling and closely
bracket the operating regime of real Bitcoin nodes. BA underestimates
clustering (0.004–0.023) relative to the empirically measured value
(0.1–0.3 [38]), while HK attains 0.21–0.24 across the same size range —
squarely within the real-network interval. Both models match the Bitcoin
network's small-world diameter of 5–7 hops [38, 39]. The near-identical
latency slopes confirm that the O(|V| + |E|) bound is topology-agnostic:
because HK adds at most O(|V|) triangles, the asymptotic complexity class
is unchanged and the constant factor increases by at most 5%.
