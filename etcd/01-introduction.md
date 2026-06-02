## etcd 

A distributed, reliable key-value store for the most critical data of a distributed system. 

etcd is a strongly consistent, distributed key-value store that provides a reliable way to store data that needs to be accessed by a distributed system or cluster of machines. It gracefully handles leader elections during network partitions and can tolerate machine failure, even in the leader node.

* It is most famous as the primary brain and source of truth for Kubernetes, which stores all cluster state, pod specs, secrets, and deployment configurations directly in etcd.

**Core Characteristics**

1. Strong Consistency: It prioritizes consistency over availability (CP system under the CAP theorem), ensuring clients never read stale configurations.

2. Distributed & Fault-Tolerant: Runs across a multi-node cluster, tolerating machine crashes without data corruption or downtime (as long as a quorum is preserved).

3. HTTP/gRPC API: Clients communicate via a lightweight gRPC API with full support for transactions, leases, and watches.

4. Watch Mechanism: Clients can "watch" specific keys or directory prefixes; etcd pushes real-time event notifications when a value updates, eliminating polling.


