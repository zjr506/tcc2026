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
scales. To assess how well the results generalise beyond the topology
used in Section 8.1, we repeat the latency measurements on a second
model: the Holme-Kim power-law cluster graph (Holme and Kim, "Growing
scale-free networks with tunable clustering," Physical Review E, 2002).
The Holme-Kim model extends preferential attachment with a
triangle-formation step that produces both a scale-free degree
distribution and significant local clustering, as we explain below.

We generate test networks using the algorithm of Doar ("A better model
for generating test networks," IEEE GLOBECOM, 1996), as in Section 8.1,
with the number of links per cloud node ranging from 4 to 60. For the
Holme-Kim networks we use m = 4 edges per new node and triangle-formation
probability p = 0.5. To measure per-transaction latency we sample 50
random source nodes from each generated graph, time Algorithm 1 (graph
reduction) alone and then Algorithms 1 and 2 together, and divide the
total by 50, averaged over 3 independent seeds. For the block latency
experiment we fix four network sizes and vary the number of transactions
per block from 50 to 2000. For the storage analysis we apply the encoding
of Section 6.4: each incentive allocation entry occupies 28 bytes (a
20-byte address and an 8-byte revenue value), and each topology change
event occupies 41 bytes (two addresses and a type byte). We model a churn
rate of 0.5% of all edges per block.

Fig. 6(a) shows the per-transaction latency for Algorithm 1 alone and for
Algorithms 1 and 2 combined, across network sizes from |V| = 500 to
20 000, for both the Doar and Holme-Kim topologies. All four curves grow
linearly, with fitted slopes of 5.47 × 10⁻³ ms per node for the Doar
combined pipeline and 5.50 × 10⁻³ ms per node for Holme-Kim, a
difference of less than 1%. The near-identical slopes confirm that the
O(|V| + |E|) bound is topology-agnostic: because Holme-Kim adds at most
O(|V|) triangles relative to Doar, the asymptotic complexity class is
unchanged. Algorithm 2 adds only a small constant fraction on top of
Algorithm 1 for both topologies, because the incentive computation
iterates over the same BFS edge set and requires no additional graph
traversal. At the Bitcoin reference scale of |V| = 22 000 the
extrapolated per-transaction latency is approximately 120 ms for both
topologies, well below the ten-minute block interval.

Fig. 6(b) shows the block processing latency as a function of the number
of transactions for four network sizes. All four curves are linear in the
number of transactions, confirming O(T) scaling in the transaction count
T. The curves are separated by |V|: the |V| = 500 line processes 2000
transactions in 4.6 s, while the |V| = 5000 line takes 52.8 s for the
same count, matching the linear-in-|V| scaling established in Fig. 6(a).
At Bitcoin's approximate rate of 2000 to 3000 transactions per block and
network scale |V| = 22 000, block generators have ample margin within the
ten-minute block interval.

Fig. 6(c) shows the per-block storage overhead versus network size.
Incentive allocation storage grows strictly linearly at 28 bytes per
node and dominates the total, while topology change storage remains below
40 KB even at |V| = 50 000. At |V| = 22 000 the model yields 601.6 KB
for incentive allocation, 17.6 KB for topology changes, and 619.2 KB in
total, within 0.5% of the Section 6.4 analytical estimate of 616 KB,
validating that estimate precisely.

Fig. 6(d) shows the cumulative ITFC-specific blockchain overhead over
time for four network sizes. At Bitcoin's rate of approximately 144
blocks per day, the |V| = 22 000 case accumulates roughly 87 MB per day,
while the |V| = 5000 case accumulates only 20 MB per day. We conclude
that the deployment performance overhead of ITFC is modest and well
within the storage and computation capacities of the cloud nodes
described in Section 3.

The topology comparison also allows us to assess the structural
properties of each model. According to Bitnodes ("Global Bitcoin nodes
distribution," 2025) the reachable Bitcoin network comprises roughly
22 000 nodes, and the Bitcoin protocol specifies a default of 8 outbound
connections per node (Bitcoin.org, "P2P network guide," 2025).
Measurements of the Bitcoin mainnet report an average clustering
coefficient of 0.068 and a network diameter of 6 hops (Essaid and Ju,
"Deep learning-based community detection approach on Bitcoin network,"
Systems, 2022). Our topology comparison experiment (measuring clustering
over seeds at |V| = 1 000 to 5 000) finds that the Doar topology yields
clustering of 0.004 to 0.024, while the Holme-Kim topology yields 0.21
to 0.24. The measured Bitcoin clustering (0.068) falls between the two
models, and both share a similar average degree (~8) and approximate
diameter of 5 to 6 hops, consistent with the measured values. The
Holme-Kim model provides a conservative test by overestimating
clustering relative to the real network: if the ITFC overhead is
acceptable under elevated clustering, it is also acceptable under the
lower clustering of the Bitcoin mainnet. The fact that both models
produce nearly identical latency slopes confirms that the O(|V|)
performance guarantee is not sensitive to the level of local clustering,
and the ITFC overhead figures reported above remain valid across the
range from Doar clustering (0.01) through Bitcoin clustering (0.07) to
Holme-Kim clustering (0.22).
