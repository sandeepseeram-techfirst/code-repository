A **quorum** is the minimum number of replicas in a distributed system that must agree before a read or write is considered successful. It lets a replicated system remain consistent and make progress despite some node or network failures.

## Core idea

For a system with \(N\) replicas, you configure:

- **Write quorum** \(W\): replicas that must acknowledge a write.
- **Read quorum** \(R\): replicas contacted to satisfy a read.

To guarantee that a read sees the latest committed write, require:

\[
R + W > N
\]

This ensures the read set and write set overlap in at least one replica, so the reader can detect or obtain the most recent value.

## Example

With \(N = 5\) replicas, a common configuration is \(W = 3\) and \(R = 3\):

- A write succeeds only after 3 of 5 replicas acknowledge it.
- A read queries 3 of 5 replicas.
- Because \(3 + 3 = 6 > 5\), every read quorum overlaps with every write quorum.

If only 2 replicas are reachable, the system cannot form a quorum and must reject writes—or serve stale/degraded reads, depending on its consistency policy.

## Why it matters

| Configuration | Effect |
|---|---|
| Higher \(W\) | Stronger write durability and consistency, but writes become slower and less available |
| Higher \(R\) | Stronger read consistency, but reads become slower and less available |
| Lower \(R + W\) | Better latency and availability, but higher risk of stale reads or conflicts |

A quorum is therefore a **tunable consistency–availability trade-off**, not a free consistency guarantee.

## Important nuances

- **Quorum does not automatically mean linearizability.** The system still needs versioning, timestamps, vector clocks, or conflict resolution to determine which overlapping value is newest.
- **It does not eliminate conflicts.** If concurrent writes reach different replicas, a quorum can detect the conflict but still needs a resolution rule, such as last-write-wins, application-level merge, or CRDT semantics.
- **It is common in replicated storage systems.** Examples include Dynamo-style key-value stores, Cassandra, and Raft-based systems, though Raft uses quorum primarily for leader election and log replication.
- **Failure tolerance follows from the majority rule.** With \(N = 2f + 1\), the system can tolerate \(f\) failed replicas while retaining a majority quorum.

## Practical takeaway

Use quorums when you need replicated data to survive partial failures while bounding inconsistency. For strict correctness, pair a quorum with explicit versioning and conflict-resolution rules; for availability-first systems, accept eventual consistency and design reconciliation carefully.