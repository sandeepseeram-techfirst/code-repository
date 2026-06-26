# Apache HBase — Deep Dive

Apache HBase is an open-source, distributed, column-oriented NoSQL database modeled after Google Bigtable. It is designed for **massive tables**, **billions of rows**, and **low-latency random reads/writes**, while storing data durably on Hadoop HDFS or compatible distributed filesystems.

In one sentence: **HBase is a horizontally scalable key-value store with sparse, versioned, sorted rows—optimized for real-time operational access to very large datasets.**

***

## 1. The Problem HBase Solves

Traditional relational databases struggle when a workload has:

- Billions or trillions of rows.
- Very high write throughput, such as IoT events, clickstreams, or telemetry.
- Random point lookups by a known key.
- Sparse records, where different rows have different attributes.
- Need for linear horizontal scaling across commodity nodes.
- Need for strong consistency on individual row operations.

A typical RDBMS can handle structured data and complex joins well, but scaling writes and random access to petabyte scale often requires heavy sharding, denormalization, and operational complexity.

HBase solves this by:

- Automatically splitting large tables into **regions**.
- Distributing those regions across many **RegionServers**.
- Storing immutable files on distributed storage.
- Using a write-ahead log for durability.
- Providing fast row-key-based reads and writes.
- Supporting schema flexibility through dynamic column qualifiers.

It is **not** a general-purpose SQL database. It is best understood as a **distributed, sorted, persistent hash map** with powerful range-scan capabilities.

***

## 2. Core Data Model

HBase’s data model looks superficially like a table, but it behaves very differently from a relational table.

### Conceptual layout

```text
Table: user_events
Row Key: user123#2026-10-24T14:00:00Z

Column Family: events
  event:page_view    = homepage
  event:click        = signup_button

Column Family: profile
  profile:country    = IN
  profile:device     = mobile
```
### Key concepts

| Concept | Meaning |
|---|---|
| **Namespace** | Logical grouping of tables, similar to a database namespace. |
| **Table** | A collection of rows, distributed across the cluster. |
| **Row key** | The primary sorted identifier for a row. |
| **Column family** | A physical storage and configuration unit. |
| **Column qualifier** | A dynamic field inside a column family. |
| **Cell** | The value stored at a specific row, column family, qualifier, and timestamp. |
| **Timestamp/version** | Each cell can retain multiple historical versions. |
| **Region** | A contiguous range of row keys for one table. |
| **Store** | The on-disk representation of one column family within a region. |

### Important design implications

- **Rows are sorted lexicographically by row key.**
- **Column families must be defined when the table is created.**
- **Column qualifiers do not need to be predefined.**
- **Each cell is independently versioned by timestamp.**
- **Empty cells consume no storage**, making HBase suitable for sparse data.
- **Access is fastest when the row key is known or when scanning a narrow row-key range.**

A cell is effectively identified by:

```text
(row key, column family, column qualifier, timestamp) -> value
```

***

## 3. Architecture Overview

HBase follows a master-worker architecture.

```text
                 +----------------+
                 |    Clients     |
                 | Java/REST/Thrift|
                 +--------+-------+
                          |
                          v
             +------------------------+
             |       HBase Master      |
             | Metadata, DDL, balancing|
             +-----------+------------+
                         |
        +----------------+----------------+
        |                |                |
        v                v                v
+---------------+ +---------------+ +---------------+
| RegionServer  | | RegionServer  | | RegionServer  |
| Regions       | | Regions       | | Regions       |
| MemStore/WAL  | | MemStore/WAL  | | MemStore/WAL  |
+-------+-------+ +-------+-------+ +-------+-------+
        |                |                |
        +----------------+----------------+
                         |
                         v
              +----------------------+
              | HDFS / Cloud Storage |
              +----------------------+

        ZooKeeper provides coordination and failure detection.
```

### Main components

| Component | Responsibility |
|---|---|
| **Client** | Sends reads, writes, scans, and administrative operations. |
| **ZooKeeper** | Cluster coordination, leader election, region location discovery, failure detection. |
| **HMaster** | Coordinates DDL operations, region assignment, load balancing, and recovery. |
| **RegionServer** | Serves reads and writes for the regions assigned to it. |
| **Region** | A contiguous row-key range of a table. |
| **HDFS** | Durable storage for HFiles, WALs, and metadata. |
| **WAL** | Write-ahead log used to recover unflushed writes after failure. |
| **BlockCache** | Read cache for frequently accessed HFile blocks. |
| **MemStore** | In-memory write buffer before data is flushed to disk. |

***

## 4. How a Write Works

The write path is optimized for high throughput and durability.

```text
Client
  |
  | 1. Locate RegionServer
  v
RegionServer
  |
  | 2. Append to WAL
  |
  | 3. Write to MemStore
  |
  | 4. Acknowledge client
  |
  | 5. Flush MemStore to HFile when full
  v
HDFS
```

### Step-by-step

1. The client determines which RegionServer owns the target row key.
2. The client sends a `Put`, `Delete`, or batch mutation directly to that RegionServer.
3. The RegionServer appends the mutation to the **WAL**.
4. The mutation is written into the in-memory **MemStore** for the relevant column family.
5. Once the WAL and MemStore writes are complete, HBase acknowledges the write.
6. When the MemStore reaches a threshold, HBase flushes it into an immutable **HFile** on HDFS.
7. Over time, multiple HFiles accumulate and are merged through **compaction**.

### Why this is fast

- The WAL append is sequential.
- MemStore writes are in-memory.
- HFiles are immutable, avoiding expensive in-place updates.
- Writes to different row keys can be parallelized across RegionServers.

### Why this is durable

Even if a RegionServer crashes before flushing its MemStore, HBase can replay the WAL and recover committed writes.

***

## 5. How a Read Works

Reads are more complex than writes because HBase must combine several possible data sources.

```text
Client
  |
  | 1. Locate RegionServer
  v
RegionServer
  |
  | 2. Check BlockCache
  |
  | 3. Check MemStore
  |
  | 4. Read relevant HFiles
  |
  | 5. Merge versions and apply filters
  v
Client
```

### Read-time data sources

1. **BlockCache** — recently read HFile blocks.
2. **MemStore** — recent writes not yet flushed.
3. **HFiles** — immutable flushed files on HDFS.

HBase merges these sources by row key and timestamp, then returns the newest visible version according to the read consistency and version settings.

### Read optimization features

- **Bloom filters** reduce unnecessary HFile lookups.
- **Block cache** improves repeated-read latency.
- **Data block encoding** reduces storage and I/O.
- **Compression** reduces network and disk cost.
- **Short-circuit reads** can reduce HDFS network overhead where supported.
- **Region replicas** can provide timeline-consistent high-availability reads in suitable configurations.

***

