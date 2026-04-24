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
claims quantitatively by measuring the actual computation latency and
the storage overhead across a range of network scales.

We generate test networks with the same Barabási–Albert algorithm as in
Section 8.1, with the number of links per cloud node ranging from 4 to
60. We measure per-transaction computation latency by sampling 50 random
source nodes from each generated graph, timing the combined execution of
Algorithms 1 and 2 with a high-resolution clock, and dividing the total
time by 50. We repeat each measurement over 3 independent random seeds
and report the mean with ±1 standard error. We measure block processing
latency on a fixed 2 000-node network by varying the number of
transactions per block from 50 to 2 000 and timing the full block. For
the storage analysis we apply the encoding described in Section 6.4
directly: each incentive allocation entry occupies 28 bytes (a 20-byte
node address and an 8-byte revenue value), and each topology change event
occupies 41 bytes (two 20-byte addresses and a 1-byte event type). We
model a network churn rate of 0.5% of all edges changing per block.

Fig. 6(a) shows the per-transaction computation latency as a function of
network size |V|. The latency grows linearly from 2.7 ms at |V| = 500 to
97.4 ms at |V| = 20 000, with a fitted slope of 0.0048 ms per node. This
is consistent with the O(|V| + |E|) theoretical complexity: since the
Barabási–Albert graph has |E| ≈ 4|V|, the total work per transaction
scales linearly in |V|. At the Bitcoin reference scale of |V| = 22 000,
the extrapolated per-transaction latency is approximately 107 ms, well
below the ten-minute block interval. Block generators therefore have
ample time to run the incentive computation for all transactions in a
block without delaying block production.

Fig. 6(b) shows the block processing latency as a function of the number
of transactions in the block, with |V| = 2 000 held fixed. The latency
grows linearly from 0.44 s for 50 transactions to 18.2 s for 2 000
transactions, confirming that the total block overhead is O(T) in the
number of transactions T. A block containing 2 000 transactions at
Bitcoin scale would require roughly 10× more time due to the larger
network, giving an estimate of around 180 s, which is still well within
the ten-minute block interval.

Fig. 6(c) shows the per-block storage overhead as a function of network
size. The incentive allocation component grows linearly at 28 bytes per
node and dominates the total, while the topology change component
remains below 40 KB for all tested sizes. At |V| = 22 000 the model
predicts 601.6 KB for incentive allocation and 17.6 KB for topology
changes, giving a total of 619.2 KB per block. This agrees with the
analytical estimate of 616 KB in Section 6.4 to within 0.5%, validating
that estimate across a wide range of network sizes.

Fig. 6(d) shows how the cumulative ITFC overhead in the blockchain grows
with the number of blocks, for a fixed network of 22 000 nodes. The
overhead grows at 0.60 MB per block. At Bitcoin's approximate rate of
144 blocks per day, this corresponds to roughly 87 MB per day of
additional storage attributable to the incentive allocation and topology
fields. We conclude that the deployment performance overhead of ITFC is
modest and well within the capabilities of the cloud nodes described in
Section 3.
