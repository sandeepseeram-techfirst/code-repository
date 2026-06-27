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

## Storage Engine: RocksDB

Under each TiKV node is RocksDB, an embedded LSM-tree key-value store.

The write path is roughly:

```text
Write -> WAL -> MemTable -> SST files
```

- **Write-Ahead Log (WAL):** Ensures durability before an operation is acknowledged.
- **MemTable:** An in-memory sorted structure that absorbs recent writes.
- **SST files:** Immutable on-disk sorted files created when the MemTable fills.
- **Compaction:** Background process that merges SST files, removes obsolete versions, and controls read amplification.

RocksDB is chosen because it provides high write throughput, efficient range scans, compression, and mature crash-recovery behavior.

## MVCC and Transactions

TiKV uses **Multi-Version Concurrency Control (MVCC)**. Instead of overwriting a value immediately, it stores multiple versions of a key associated with timestamps.

Conceptually:

```text
key=user:1001
  version @ t=105 -> value_v3
  version @ t=101 -> value_v2
  version @ t=97  -> value_v1
```

This allows readers to see a consistent snapshot without blocking writers.





### TxnKV Transaction Flow

A simplified optimistic transaction works like this:

1. **Begin:** The client obtains a timestamp from PD, called `start_ts`.
2. **Read:** Reads see a consistent snapshot as of `start_ts`.
3. **Buffer writes:** Writes are held locally in the client transaction buffer.
4. **Commit:** The client requests a commit timestamp from PD, called `commit_ts`.
5. **Primary key lock:** TiKV writes a lock for the transaction’s primary key.
6. **Secondary key locks:** It writes locks for other modified keys.
7. **Commit records:** Once the primary key is committed, secondary keys are committed.
8. **Cleanup:** Locks are removed after commit or rollback.

This is similar in spirit to Percolator-style distributed transactions and enables ACID semantics across keys stored on different TiKV nodes.

### Example Transaction

```text
BEGIN

GET account:alice   -> 100
GET account:bob     -> 50

PUT account:alice   -> 80
PUT account:bob     -> 70

COMMIT
```

Even if `account:alice` and `account:bob` reside in different regions on different TiKV nodes, TiKV ensures either both updates become visible or neither does.

## RawKV vs TxnKV

| Aspect | RawKV | TxnKV |
|---|---|---|
| Operation style | Direct `put`, `get`, `delete`, `scan` | Transactional reads and writes |
| Transactions | No built-in multi-key ACID transactions | Yes |
| Latency | Lower overhead | Higher overhead due to locking and timestamps |
| Use case | Caching, metadata, feature storage, queues | Financial ledgers, inventory, coordination state |
| Consistency | Configurable | Strong, ACID-compliant |
| Complexity | Simpler | More complex |

Use **RawKV** when you need speed and simple access patterns. Use **TxnKV** when multiple keys must change atomically.

## Coprocessors

TiKV includes a coprocessor framework that allows computation to be pushed down to storage nodes.

Instead of transferring millions of rows to an application and filtering them there, a caller can ask TiKV to perform part of the work locally.

For example, TiDB can push down parts of SQL execution—filters, aggregations, and some expressions—to TiKV. This reduces network transfer and improves query performance.

```text
Without pushdown:
TiKV -> transfer many rows -> TiDB filters/aggregates

With pushdown:
TiKV filters/aggregates locally -> smaller result -> TiDB
```

## How a Read Works

```text
1. Client wants key K.
2. Client asks PD for the region containing K.
3. PD returns region metadata and leader location.
4. Client sends read to region leader.
5. Leader reads from RocksDB/MVCC version store.
6. Leader returns value to client.
```

For transactional reads, the client uses its `start_ts` to select the correct visible version of the key.

## How a Write Works

```text
1. Client sends write for key K.
2. Client locates the region leader via PD.
3. Leader appends the operation to its Raft log.
4. Leader replicates the log entry to followers.
5. A majority persists the entry.
6. Leader commits and applies the write to RocksDB.
7. Client receives acknowledgment.
```

For TxnKV, this is preceded and followed by transaction metadata operations: acquiring locks, obtaining timestamps, and writing commit records.

## Scaling and Rebalancing

TiKV scales horizontally through PD-driven scheduling.

When a new TiKV node joins:

1. PD detects the new node.
2. PD identifies overloaded or under-replicated regions.
3. PD moves replicas or leader roles to the new node.
4. Raft handles safe replica addition and removal.
5. Traffic gradually shifts to the new node.

This lets the cluster grow from gigabytes to hundreds of terabytes or more without requiring application-level resharding.

## Failure Handling

| Failure | TiKV behavior |
|---|---|
| One TiKV replica fails | Raft quorum continues; PD schedules a replacement replica |
| Region leader fails | A follower is elected as the new leader |
| Entire TiKV node fails | Its regions’ remaining replicas continue serving; replacements are created elsewhere |
| PD node fails | PD cluster continues if quorum remains |
| Network partition | Minority side cannot commit; majority side remains available |

The key principle is that availability depends on maintaining a Raft majority for each affected region.

## Real-World Problems and Use Cases

### 1. Storage Layer for Distributed SQL

TiKV was originally built as the storage layer for **TiDB**, a MySQL-compatible distributed SQL database.

TiDB handles SQL parsing, optimization, and query execution; TiKV stores rows and indexes.

```text
Application
   |
 TiDB: SQL layer
   |
 TiKV: distributed transactional KV storage
```

This supports HTAP-style systems where operational transactions and analytical queries need to coexist.

### 2. Object Storage Metadata

Object stores need to track billions or trillions of objects: names, buckets, permissions, versions, ownership, and lifecycle state.

TiKV is suitable because it provides:

- Low-latency point lookups.
- Sorted range scans.
- Horizontal scalability.
- Strong consistency for metadata updates.

### 3. Online Feature Store

Machine learning systems often serve features at inference time with strict latency requirements.

TiKV can store feature vectors and entity attributes keyed by user ID, device ID, session ID, or item ID.

Example:

```text
feature:user:123:click_rate_7d -> 0.183
feature:user:123:purchase_count -> 12
feature:item:987:embedding -> [...]
```

It supports high-throughput reads for online inference and transactional updates during feature backfills.

### 4. Recommendation Systems

Recommendation services need fast access to user profiles, item metadata, interaction histories, embeddings, and model-serving features.

TiKV can store:

- User interaction histories.
- Item catalogs.
- Real-time counters.
- Candidate retrieval metadata.
- Personalization features.

Its range scans are useful for retrieving recent events or ordered item data.

### 5. Distributed Cache and Redis-Compatible Services

Projects such as Tidis and Titan use TiKV as a durable storage layer behind Redis-compatible APIs.

This provides a useful combination:

- Redis-like data structures and protocol familiarity.
- TiKV durability, replication, and scale.
- Persistence beyond an in-memory cache.

### 6. Distributed File System Metadata

JuiceFS uses TiKV as a metadata engine alongside object storage for file data.

A typical split is:

```text
TiKV: file metadata, directories, inodes, permissions
S3-compatible object store: actual file contents
```

TiKV is well suited because filesystem metadata requires frequent small reads and writes, consistent updates, and range scans.

### 7. Multi-Tenant Platform State

Platform engineering systems can use TiKV for:

- Tenant configuration.
- Service discovery metadata.
- Rate-limit counters.
- Quota tracking.
- Workflow state.
- Distributed locks and coordination data.

TxnKV is especially useful when a workflow must update several related records atomically.

## Design Insights

### Sorted Data Is a Superpower

Because keys are sorted, TiKV naturally supports:

- Prefix scans.
- Range queries.
- Ordered iteration.
- Efficient locality for related keys.
- Dynamic splitting of hot or large ranges.

Design keys so related data shares a prefix:

```text
tenant:{tenant_id}:user:{user_id}:profile
tenant:{tenant_id}:user:{user_id}:orders
tenant:{tenant_id}:user:{user_id}:events
```

### Regions Enable Elasticity

Dynamic region splitting and movement allow TiKV to adapt to data growth and changing access patterns. This is more flexible than static hash sharding.

### Raft Provides Strong Durability

Raft ensures that a committed write is replicated to a quorum. This is stronger than asynchronous primary-replica replication, where a primary failure can lose recently acknowledged writes.

### PD Separates Control Plane and Data Plane

TiKV nodes focus on storing and serving data. PD focuses on topology, scheduling, timestamps, and cluster health.

This separation keeps the data path efficient while allowing sophisticated global optimization in the control plane.

### Local Storage Avoids Distributed File System Dependencies

Each TiKV node uses its own local disk through RocksDB. This reduces operational complexity and avoids making every write depend on a network file system.

### Pushdown Reduces Network Cost

The coprocessor model follows a classic distributed-systems principle: move computation to data when possible, rather than moving large volumes of data to computation.

## Simplified Mental Model

```text
TiKV = Distributed Raft-replicated RocksDB
     + Dynamic range sharding
     + PD-based scheduling
     + MVCC
     + Distributed transactions
     + gRPC APIs
     + Pushdown computation
```

If you remember only one thing: **TiKV turns a fast local key-value engine into a scalable, fault-tolerant, transactional distributed storage layer.**

## Hands-On Tutorial

This tutorial demonstrates TiKV concepts using Docker Compose and the Python client. It uses a minimal local cluster suitable for learning, not production.

### Prerequisites

Install:

- Docker
- Docker Compose
- Python 3.9+
- `pip`

### Step 1: Create a Project Directory

```bash
mkdir tikv-lab
cd tikv-lab
```

### Step 2: Create a Docker Compose File

Create `docker-compose.yml`:

```yaml
version: "3.8"

services:
  pd:
    image: pingcap/pd:v7.1.0
    command:
      - --name=pd
      - --client-urls=http://0.0.0.0:2379
      - --peer-urls=http://0.0.0.0:2380
      - --advertise-client-urls=http://pd:2379
      - --advertise-peer-urls=http://pd:2380
      - --initial-cluster=pd=http://pd:2380
    ports:
      - "2379:2379"
    networks:
      - tikvnet

  tikv:
    image: pingcap/tikv:v7.1.0
    command:
      - --addr=0.0.0.0:20160
      - --advertise-addr=tikv:20160
      - --pd=pd:2379
    depends_on:
      - pd
    ports:
      - "20160:20160"
    networks:
      - tikvnet

networks:
  tikvnet:
    driver: bridge
```

This starts one PD and one TiKV node. A real production deployment should use at least 3 TiKV nodes and 3 PD nodes.

### Step 3: Start the Cluster

```bash
docker compose up -d
```

Check status:

```bash
docker compose ps
docker compose logs -f pd
docker compose logs -f tikv
```

PD listens on port `2379`; TiKV listens on port `20160`.

### Step 4: Install the Python Client

```bash
python -m venv .venv
source .venv/bin/activate

pip install tikv-client
```

If the client package is unavailable in your environment, use the TiKV Java, Go, Rust, or C++ client instead. The concepts remain identical.

### Step 5: Create a RawKV Python Script

Create `rawkv_demo.py`:

```python
from tikv_client import RawClient

client = RawClient.connect("127.0.0.1:2379")

# Put key-value pairs
client.put(b"user:1001:name", b"Alice")
client.put(b"user:1001:plan", b"pro")
client.put(b"user:1002:name", b"Bob")
client.put(b"user:1002:plan", b"free")

# Get one value
name = client.get(b"user:1001:name")
print("Alice:", name)

# Scan a key prefix
pairs = client.scan(b"user:1001:", b"user:1002:")
for key, value in pairs:
    print(key.decode(), "=", value.decode())

# Delete a key
client.delete(b"user:1002:plan")

print("After delete:", client.get(b"user:1002:plan"))
```

Run it:

```bash
python rawkv_demo.py
```

Expected output:

```text
Alice: b'Alice'
user:1001:name = Alice
user:1001:plan = pro
After delete: None
```

### What This Demonstrates

- `put` writes a key-value pair.
- `get` performs a point lookup.
- `scan` reads an ordered key range.
- `delete` removes a key.
- Prefix-based keys enable efficient range scans.

### Step 6: Create a Transactional Script

Create `txnkv_demo.py`:

```python
from tikv_client import TransactionClient

client = TransactionClient.connect("127.0.0.1:2379")

# Initial balances
with client.begin() as txn:
    txn.set(b"account:alice", b"100")
    txn.set(b"account:bob", b"50")
    txn.commit()

# Transfer 30 units from Alice to Bob atomically
with client.begin() as txn:
    alice = int(txn.get(b"account:alice"))
    bob = int(txn.get(b"account:bob"))

    if alice < 30:
        raise ValueError("Insufficient balance")

    txn.set(b"account:alice", str(alice - 30).encode())
    txn.set(b"account:bob", str(bob + 30).encode())
    txn.commit()

with client.begin() as txn:
    print("Alice:", txn.get(b"account:alice"))
    print("Bob:", txn.get(b"account:bob"))
```

Run it:

```bash
python txnkv_demo.py
```

Expected output:

```text
Alice: b'70'
Bob: b'80'
```

### What This Demonstrates

- Two keys are updated together.
- If the process fails before `commit()`, neither update is applied.
- This models a basic double-entry ledger or inventory transfer.

### Step 7: Inspect the Cluster

Use PD’s HTTP API to inspect cluster state:

```bash
curl -s http://127.0.0.1:2379/pd/api/v1/stores | jq
```

You should see the TiKV store, its capacity, and its status.

To inspect regions:

```bash
curl -s http://127.0.0.1:2379/pd/api/v1/regions | jq
```

As you insert more data, PD will report regions, leaders, and replica placement.

### Step 8: Observe Range Scanning

Add a script that creates related keys:

```python
from tikv_client import RawClient

client = RawClient.connect("127.0.0.1:2379")

for i in range(10):
    key = f"user:1001:event:{i:04d}".encode()
    value = f"event-{i}".encode()
    client.put(key, value)

events = client.scan(
    b"user:1001:event:",
    b"user:1001:event:\xff"
)

for key, value in events:
    print(key.decode(), "=", value.decode())
```

Run:

```bash
python events_demo.py
```

This illustrates why key design matters: all events for user `1001` are adjacent in sorted-key order, so they can be scanned efficiently.

## Production Design Checklist

When deploying TiKV for real workloads:

- Deploy at least **3 TiKV nodes** for replica fault tolerance.
- Deploy **3 or 5 PD nodes** for control-plane high availability.
- Use local NVMe or high-performance SSD storage.
- Separate PD, TiKV, and application workloads where possible.
- Monitor Raft latency, region health, disk usage, compaction, and PD scheduling.
- Design keys to avoid monotonically increasing hotspots, such as timestamps alone.
- Prefer prefix-based keys for related records.
- Use RawKV for high-throughput simple access.
- Use TxnKV when multi-key atomicity is required.
- Set appropriate region size, replication factor, and compaction settings.
- Test node failure, disk failure, network partition, and rolling upgrade scenarios.

## When to Choose TiKV

Choose TiKV when you need:

- A scalable distributed key-value store.
- Strongly consistent replication.
- ACID transactions across distributed data.
- Low-latency online reads and writes.
- A foundation for a custom database, metadata service, feature store, or filesystem.

Choose something else when:

- You only need an ephemeral cache; Redis or Memcached may be simpler.
- You need document queries and flexible schemas; MongoDB or Couchbase may fit better.
- You need full SQL analytics; a columnar warehouse or query engine may be more appropriate.
- You need a single-node embedded store; RocksDB alone may be sufficient.

## Key Takeaways

- TiKV is a distributed, transactional, Raft-replicated key-value database.
- It combines RocksDB storage, Raft consensus, dynamic regions, MVCC, and PD-based scheduling.
- RawKV is optimized for simple high-performance access; TxnKV adds distributed ACID transactions.
- Its architecture is especially strong for large-scale metadata, feature serving, recommendation, object-storage, and database storage workloads.
- The most important design skill is key modeling: use sorted, prefixed keys to exploit TiKV’s range-scan and region-sharding strengths.