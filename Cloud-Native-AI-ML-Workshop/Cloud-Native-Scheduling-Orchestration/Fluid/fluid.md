## Fluid 

**Fluid, elastic data abstraction and acceleration for BigData/AI applications in cloud.**

## Fluid on Kubernetes: Complete Hands-On Lab

**Fluid** is a Kubernetes-native *distributed dataset orchestrator and accelerator* for data-intensive workloads such as Spark, TensorFlow, PyTorch, Ray, and Flink. It lets a Kubernetes workload consume a remote dataset through a normal PVC, while Fluid transparently places and scales a distributed cache close to compute.  

It is particularly useful when a training job repeatedly reads the same large object-store, NFS, HDFS, or web-hosted dataset. Instead of every Pod paying the network and metadata cost of the source system, Fluid can cache data on cluster-local memory or SSD and schedule Pods near cached replicas.

## Why Fluid exists

Kubernetes is excellent at orchestrating compute, but it does not natively understand *datasets* as first-class resources. A Pod can mount a PVC, but Kubernetes does not know:

- Which Pods share the same dataset.
- How much of the dataset is hot.
- Whether a cache should be pre-warmed before training starts.
- Where cache replicas live.
- Whether a Pod should be scheduled near a cache replica.
- How to elastically grow or shrink cache capacity.

Fluid addresses this by introducing Kubernetes custom resources for datasets and cache runtimes. Its three headline capabilities are dataset abstraction, data acceleration through distributed caching, and data-aware scheduling.

### The core idea

```text
Traditional Kubernetes:

Training Pods ──> Object Store / NFS / HDFS
                  repeated remote reads
                  high latency, egress cost, metadata pressure

With Fluid:

Training Pods ──> Fluid PVC ──> Distributed cache
                                   │
                                   └──> Remote source
                                        only first/cold reads
```

Fluid does **not** replace your storage system. It sits in front of it as a cache and access layer, commonly backed by Alluxio. The remote system remains the source of truth.

 
## Architecture and components

Fluid is a Kubernetes controller-based system with a CSI integration.

```text
                         Kubernetes Control Plane
 ┌───────────────────────────────────────────────────────────────┐
 │                                                               │
 │  Dataset CRD          Runtime CRD           DataLoad CRD      │
 │  (logical data)       (cache deployment)    (warmup policy)   │
 │         │                    │                     │          │
 │         └──────────┬─────────┴──────────┬──────────┘          │
 │                    ▼                    ▼                     │
 │          Dataset Controller        Runtime Controller         │
 │                    │                    │                     │
 │                    └────────┬───────────┘                     │
 │                             ▼                                 │
 │                 Creates StatefulSets, Services,               │
 │                 PV/PVC, ConfigMaps, cache resources           │
 └───────────────────────────────────────────────────────────────┘
                              │
                              ▼
 ┌───────────────────────────────────────────────────────────────┐
 │                        Worker Nodes                           │
 │                                                               │
 │  App Pod ──> CSI Node Plugin ──> FUSE mount ──> Cache Worker  │
 │                                                               │
 │  Cache Worker(s) ──> Remote UFS: S3, OSS, HDFS, NFS, Web      │
 └───────────────────────────────────────────────────────────────┘
```

### Main concepts

| Component | Purpose | Simple explanation |
|---|---|---|
| `Dataset` | Declares the data source and logical dataset | “Here is the data I want Kubernetes workloads to use.” |
| Runtime, e.g. `AlluxioRuntime` | Declares how to run the cache engine | “Run an Alluxio cache for this dataset with these resources.” |
| Cache workers | Store cached blocks | “Keep hot data close to compute.” |
| FUSE client | Presents cache as a POSIX-like filesystem | “Let a container read data as if it were local.” |
| CSI node plugin | Connects Kubernetes volume mounting to Fluid | “Make the dataset mountable as a PVC.” |
| `DataLoad` | Triggers preloading | “Warm the cache before the job starts.” |
| PV/PVC | Kubernetes-native workload interface | “Workloads use a familiar volume interface.” |

Fluid’s `Dataset` is the logical abstraction; the `Runtime` implements lifecycle, isolation, versioning, and acceleration behind a common interface. Fluid currently documents Alluxio as a cache runtime in its core examples, while its design supports pluggable runtimes.  