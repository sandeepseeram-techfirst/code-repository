# Feast: Technical Overview and Hands-On Guide

Feast is an open-source **feature store** that standardizes how ML/AI systems define, discover, compute, and serve features for both offline training and low-latency online inference. It decouples feature logic from storage and serving infrastructure, making it suitable for cloud-agnostic, Kubernetes-native ML platforms.

## What Feast Solves

Production ML commonly suffers from duplicated feature logic, unreliable point-in-time joins, training-serving skew, and slow or inconsistent online feature availability. Feast addresses these by treating features as version-controlled, reusable assets with explicit schemas, entities, data sources, and retrieval contracts.

- **Training-serving skew:** The same registered feature definitions are used for historical training retrieval and online inference.
- **Point-in-time correctness:** Historical feature retrieval joins feature data using event timestamps, preventing future values from leaking into training rows.
- **Feature reuse:** Teams can register and discover shared features instead of rebuilding similar transformations per model.
- **Infrastructure abstraction:** Feast connects to existing batch warehouses, streaming systems, and low-latency databases rather than replacing them.
- **Operational separation:** Data scientists define features; platform/SRE teams own the backing stores, orchestration, and serving reliability.

## Core Architecture

Feast is primarily a **control plane plus retrieval SDK**, not a monolithic data-processing engine. It coordinates metadata, offline data, and online data across pluggable backends.

```text
Feature definitions (Git)
          |
          v
      feast apply
          |
          v
      Feature Registry  <---- Feature catalog / metadata
          |
   +------+----------------------+
   |                             |
   v                             v
Offline Store                 Online Store
(warehouse/lakehouse)         (Redis, DynamoDB, etc.)
   |                             ^
   +---- materialization --------+
   |                             |
   v                             v
Training / batch scoring      Real-time inference
```

### Key concepts

| Concept | Purpose | Example |
|---|---|---|
| **Project** | Top-level namespace for features and resources | `fraud_detection` |
| **Entity** | Primary key used to retrieve features | `customer_id`, `driver_id`, `card_id` |
| **FeatureView** | Typed schema binding a data source to features | `customer_stats` with `daily_transactions`, `lifetime_value` |
| **Data source** | Where raw feature data originates | Parquet, BigQuery, Snowflake, Kafka push source |
| **FeatureService** | Versioned feature set consumed by a model | `fraud_model_v1` |
| **Registry** | Catalog of registered entities, views, and services | Local file, SQL-backed registry |
| **Offline store** | Historical data for training and batch scoring | Snowflake, BigQuery, Spark, PostgreSQL, DuckDB |
| **Online store** | Latest precomputed values for real-time reads | Redis, DynamoDB, Cassandra, PostgreSQL, SQLite |
| **On-demand FeatureView** | Request-time or derived transformation | `transaction_amount / account_balance` |

