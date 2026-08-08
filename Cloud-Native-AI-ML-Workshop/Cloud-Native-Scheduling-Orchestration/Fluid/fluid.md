## Fluid 

**Fluid, elastic data abstraction and acceleration for BigData/AI applications in cloud.**

## Fluid on Kubernetes: Complete Hands-On Lab

**Fluid** is a Kubernetes-native *distributed dataset orchestrator and accelerator* for data-intensive workloads such as Spark, TensorFlow, PyTorch, Ray, and Flink. It lets a Kubernetes workload consume a remote dataset through a normal PVC, while Fluid transparently places and scales a distributed cache close to compute.  

It is particularly useful when a training job repeatedly reads the same large object-store, NFS, HDFS, or web-hosted dataset. Instead of every Pod paying the network and metadata cost of the source system, Fluid can cache data on cluster-local memory or SSD and schedule Pods near cached replicas.  