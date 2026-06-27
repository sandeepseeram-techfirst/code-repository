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