# TiKV Deep Dive

TiKV is an open-source, distributed, transactional key-value database designed to store very large datasets with low, stable latency. It provides both simple `get/put` access and ACID-compliant distributed transactions, making it useful either directly or as the storage engine beneath higher-level systems such as TiDB, JuiceFS, and Redis-compatible services.

Think of TiKV as a **distributed, replicated, transactional version of RocksDB**: it takes a local embedded key-value engine and adds sharding, replication, consensus, scheduling, and distributed transactions.

## What TiKV Is

TiKV is a CNCF Graduated project written primarily in Rust. It stores data as key-value pairs and exposes two main APIs:

| API | Purpose | Typical guarantees |
|---|---|---|
| **RawKV** | Simple key-value operations such as `put`, `get`, `delete`, `scan` | Tunable consistency/performance trade-off |
| **TxnKV** | Transactional operations with snapshot isolation and commit/rollback semantics | ACID-compliant distributed transactions |

It is designed for online serving systems that need predictable performance at scale: metadata stores, feature stores, recommendation systems, object-storage metadata, and database storage layers.

## Core Problems It Solves

TiKV addresses several common failures of traditional databases and ad hoc sharded systems:

- **Horizontal scaling:** Add TiKV nodes to increase capacity and throughput instead of vertically scaling one database server.
- **Data durability:** Replicate every data range across multiple nodes using Raft consensus.
- **Automatic failure recovery:** If a replica or node fails, remaining replicas continue serving and the cluster replaces missing replicas.
- **Cross-node transactions:** Unlike many proxy-based sharding approaches, TxnKV supports ACID transactions that span multiple keys and TiKV nodes.
- **Operational simplicity:** It does not require an external distributed file system; each TiKV node uses local storage.
- **Stable latency:** Data is partitioned into small regions, and requests are routed directly to the node responsible for the relevant key range.

## High-Level Architecture

A TiKV cluster has two major server roles:

```text
              +----------------+
              |   Client/App   |
              +--------+-------+
                       |
                    gRPC
                       |
        +--------------+--------------+
        |                             |
+-------v-------+             +-------v-------+
| Placement     |             | TiKV Nodes    |
| Driver (PD)   |<----------->| Region leaders|
| Metadata,     |             | Raft groups   |
| scheduling,   |             | RocksDB       |
| TS allocation |             +---------------+
+---------------+
```

### 1. TiKV Nodes

TiKV nodes store the actual data. Each node runs:

- A **RocksDB instance** for durable local key-value storage.
- One or more **Raft groups**, each responsible for replicating a data range.
- A **gRPC server** for client and inter-node communication.
- A **coprocessor framework** that can execute pushed-down computation near the data.

### 2. Placement Driver (PD)

PD is the cluster brain. It does not store user data; it stores and manages cluster metadata. Its main responsibilities are:

- Tracking which TiKV node stores which data region.
- Assigning region leaders.
- Balancing load, disk usage, and replica distribution.
- Detecting failures and scheduling replica movement.
- Allocating globally ordered timestamps for transactional workloads.

PD itself is typically deployed as a small cluster of 3 or 5 nodes for high availability.


### 3. Clients

Applications use a TiKV client library or connect through an upper-layer system. Clients communicate with PD and TiKV over gRPC. A client typically asks PD where a key lives, then sends the read or write directly to the appropriate TiKV region leader.


## Data Model

TiKV stores ordered key-value pairs:

```text
key -> value
```

Keys are byte arrays and are sorted lexicographically. This ordering enables efficient range scans, prefix scans, and iteration.

Example:

```text
user:1001:profile -> {"name":"Alice"}
user:1001:orders  -> [...]
user:1002:profile -> {"name":"Bob"}
```

A scan over the prefix `user:1001:` can efficiently retrieve all data associated with user `1001`.


## Regions and Sharding

TiKV does not shard by entire tables or fixed hash buckets. It splits the keyspace into contiguous, sorted key ranges called **Regions**.

```text
Region 1: [ "", "user:5000" )
Region 2: [ "user:5000", "user:9000" )
Region 3: [ "user:9000", "" )
```

Each region:

- Has a start key and end key.
- Contains a bounded amount of data.
- Is replicated across multiple TiKV nodes, commonly 3 replicas.
- Forms one Raft group.
- Has one elected **leader** that handles reads and writes for that range.

When a region grows beyond a configured size threshold, TiKV splits it. When regions become too small or unevenly distributed, TiKV can merge or move them.

This design avoids hotspots better than fixed sharding because the system can continuously rebalance ranges as data grows.

## Raft Replication and Consistency

Each Region is replicated by a **Raft group**. Raft is a consensus protocol that ensures replicas agree on the same sequence of changes.

A simplified write flow:

```text
Client
  |
  | 1. Write request
  v
Region Leader
  |
  | 2. Append log entry locally
  | 3. Replicate log to follower replicas
  v
Raft Quorum
  |
  | 4. Majority acknowledges entry
  v
Leader commits and applies write to RocksDB
  |
  v
Client receives success
```

For a typical 3-replica region:

- The leader accepts the write.
- It replicates the Raft log entry to two followers.
- Once a majority, meaning at least 2 of 3 replicas, has persisted the entry, the write is committed.
- The leader applies the change to its local RocksDB store.
- Followers eventually apply the same change.

This provides durability and consistency even if one replica fails, assuming the remaining replicas form a quorum.

