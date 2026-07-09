## Summary

Covers four foundational distributed-systems concepts: **quorum**, **thundering herd**, and **message delivery guarantees**. Together, they illustrate how distributed systems balance consistency, availability, performance, and correctness under partial failure.

## Key technical insights

- **Quorum controls consistency in replication.** With \(N\) replicas, requiring \(R + W > N\) ensures every read quorum overlaps with every write quorum, allowing readers to detect or retrieve the latest committed value.

- **Quorum is tunable, not free.** Larger read or write quorums improve consistency and durability but reduce availability and increase latency; smaller quorums improve responsiveness at the cost of stale reads or conflict risk.

- **Quorum alone does not provide linearizability.** Systems still need versioning, timestamps, vector clocks, or explicit conflict-resolution rules to determine which value is authoritative when concurrent writes occur.

- **Majority quorums enable failure tolerance.** With \(N = 2f + 1\), the system can tolerate \(f\) replica failures while still forming a majority.

- **Thundering herd is correlated load.** Many clients simultaneously perform the same expensive operation—often after a cache expiry, restart, retry, or broadcast—overloading a database, origin service, or downstream dependency.

- **Prevent duplicate expensive work.** Use request coalescing/single-flight, distributed locks, stale-while-revalidate, TTL jitter, early refresh, and rate limiting so one request rebuilds a value while others reuse or wait for it.

- **Retry storms need jitter.** Exponential backoff without jitter can synchronize client retries and recreate a thundering herd after a transient outage.

- **At-least-once is the practical default.** It prevents silent message loss but can deliver duplicates, so consumers must be idempotent through deduplication keys, upserts, conditional writes, or naturally idempotent operations.

- **Exactly-once is usually end-to-end, not broker-only.** A messaging system may provide transactional or idempotent processing internally, but guarantees break if writes reach an external system that cannot participate in the same transactional boundary.

- **Choose guarantees by failure impact.** Use at-most-once for tolerable loss, at-least-once plus idempotency for critical events, and effectively exactly-once only when the full processing path can enforce transactional or idempotent semantics.

## Practical takeaway

Design distributed systems around explicit failure assumptions: use quorums to bound consistency, eliminate correlated work to prevent herd effects, and build idempotent consumers so redelivery is safe. The strongest production pattern is often **at-least-once delivery with idempotent processing**, rather than relying on a broker label alone.