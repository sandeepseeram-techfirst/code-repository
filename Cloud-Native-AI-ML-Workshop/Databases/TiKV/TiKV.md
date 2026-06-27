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