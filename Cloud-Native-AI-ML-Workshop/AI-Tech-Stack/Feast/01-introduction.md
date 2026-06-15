# Feast: Technical Overview and Hands-On Guide

Feast is an open-source **feature store** that standardizes how ML/AI systems define, discover, compute, and serve features for both offline training and low-latency online inference. It decouples feature logic from storage and serving infrastructure, making it suitable for cloud-agnostic, Kubernetes-native ML platforms.

### What Feast Solves

Production ML commonly suffers from duplicated feature logic, unreliable point-in-time joins, training-serving skew, and slow or inconsistent online feature availability. 

**Feast addresses these by treating features as version-controlled, reusable assets with explicit schemas, entities, data sources, and retrieval contracts.**

**Training-serving skew:** The same registered feature definitions are used for historical training retrieval and online inference.

**Point-in-time correctness:** Historical feature retrieval joins feature data using event timestamps, preventing future values from leaking into training rows.

**Feature reuse:** Teams can register and discover shared features instead of rebuilding similar transformations per model.

**Infrastructure abstraction:** Feast connects to existing batch warehouses, streaming systems, and low-latency databases rather than replacing them.

**Operational separation:** Data scientists define features; platform/SRE teams own the backing stores, orchestration, and serving reliability.