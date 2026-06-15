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


## How It Works

### 1. Define features as code

Feature definitions live in a Git-managed Python repository. An entity identifies the lookup key; a feature view declares the source, schema, time-to-live, and whether the feature should be available online.

```python
from datetime import timedelta
from feast import Entity, FeatureView, Field, FileSource
from feast.types import Float32, Int64

customer = Entity(name="customer", join_keys=["customer_id"])

customer_stats_source = FileSource(
    name="customer_stats_source",
    path="data/customer_stats.parquet",
    timestamp_field="event_timestamp",
)

customer_stats = FeatureView(
    name="customer_stats",
    entities=[customer],
    ttl=timedelta(days=1),
    schema=[
        Field(name="daily_transactions", dtype=Int64),
        Field(name="lifetime_value", dtype=Float32),
    ],
    online=True,
    source=customer_stats_source,
)
```

This definition becomes the single contract for training, batch scoring, and online inference.

### 2. Register the feature catalog

Running `feast apply` parses the repository, validates definitions, writes metadata to the registry, and provisions the required online-store structures.

```bash
feast apply
```

The registry enables discovery, lineage, access control workflows, and consistent reuse across teams and services.

### 3. Generate training data

For model training, you provide an **entity dataframe**: entity keys plus the timestamp at which each label or training example occurred. Feast performs a point-in-time join to select only feature values known at or before each timestamp.

```python
from feast import FeatureStore

store = FeatureStore(repo_path="feature_repo")

training_df = store.get_historical_features(
    entity_df=training_entities,
    features=[
        "customer_stats:daily_transactions",
        "customer_stats:lifetime_value",
    ],
).to_df()
```

This avoids the classic leakage bug where a model is trained using a customer’s future transaction count.

### 4. Materialize features online

Batch features are not automatically available for real-time inference. **Materialization** reads recent historical feature values and writes the latest values into the online store.

```bash
feast materialize-incremental "$(date -u +'%Y-%m-%dT%H:%M:%S')"
```

In production, this is typically scheduled through Airflow, Dagster, Argo Workflows, Kubernetes CronJobs, or your existing orchestration platform.

### 5. Serve features for inference

At request time, the model service fetches the latest feature vector by entity key from the online store.

```python
features = store.get_online_features(
    features=[
        "customer_stats:daily_transactions",
        "customer_stats:lifetime_value",
    ],
    entity_rows=[{"customer_id": "C123"}],
).to_dict()
```

The result is passed directly into a model, rules engine, LLM application, or downstream decision service.

### 6. Push streaming updates

For event-driven features, Feast supports **push sources**. A streaming producer can push fresh feature values directly to the online store, and optionally to the offline store for future training.

Typical flow:

```text
Kafka / event stream
        |
        v
Stream processor / feature job
        |
        v
Feast push API
        |
   +----+----+
   v         v
Online      Offline
store       store
```

This enables features such as “transactions in the last 5 minutes” or “current cart value” to remain fresh without waiting for a batch materialization cycle.

## Real-World Use Cases

### Fraud detection

A payments platform can combine historical card behavior with real-time signals.

- **Offline features:** 30-day transaction count, average transaction amount, merchant-category history.
- **Online features:** Transaction count in the last five minutes, current device fingerprint risk, recent failed authorizations.
- **Outcome:** A low-latency model scores each authorization before the payment is approved.

Feast ensures the same feature definitions used to train the fraud model are available during live authorization decisions.

### Real-time recommendations

An e-commerce or content platform can personalize results using both long-term preferences and immediate behavior.

- **Offline features:** Purchase history, category affinity, lifetime value.
- **Online features:** Current cart contents, last viewed product, session click sequence.
- **Outcome:** A ranking service retrieves user and item vectors, scores candidates, and returns recommendations.

### Credit and risk scoring

A lender can maintain consistent borrower features across model development and production.

- **Offline features:** Repayment history, income band, delinquency counts, account age.
- **Online features:** Current outstanding balance, recent credit inquiries, account status.
- **Outcome:** Batch models score portfolios nightly, while real-time models support pre-qualification or application decisions.

### Customer segmentation

Marketing and growth teams can share standardized customer attributes.

- **Offline features:** Recency, frequency, monetary value, churn probability.
- **Online features:** Current subscription state, active campaign exposure, recent engagement.
- **Outcome:** Segment membership and campaign targeting use one governed feature catalog instead of divergent team-specific queries.

### LLM and RAG applications

Feast also supports vector retrieval for retrieval-augmented generation. You can store document chunks, embeddings, and metadata in an online vector-capable store, then retrieve relevant context using similarity search.

```python
documents = store.retrieve_online_documents(
    features=[
        "corpus:document_id",
        "corpus:chunk_id",
        "corpus:chunk_text",
        "corpus:chunk_embedding",
    ],
    query="What is the biggest city in the USA?",
).to_dict()
```

This makes Feast useful not only for classical ML models but also for LLM applications requiring governed, low-latency context retrieval.

## Production Design Considerations

| Concern | Practical approach |
|---|---|
| **Freshness** | Use streaming pushes for second/minute-level features; schedule materialization for hourly/daily batch features |
| **Latency** | Choose Redis, DynamoDB, ScyllaDB, or another low-latency online store based on access pattern and scale |
| **Backfills** | Use the offline store and historical retrieval; materialize only the required recent window online |
| **Feature ownership** | Assign each feature view an owning team through tags and repository CODEOWNERS |
| **Versioning** | Use `FeatureService` versions such as `fraud_model_v1`, `fraud_model_v2` |
| **Testing** | Validate schemas, null rates, freshness, and point-in-time joins in CI |
| **Deployment** | Run Feast SDK in model services or deploy the feature server for non-Python consumers |
| **Observability** | Monitor materialization lag, online read latency, missing feature rates, and registry deployment health |

## Hands-On Tutorial

This tutorial creates a local Feast project using Parquet as the offline source and SQLite as the online store. It is ideal for learning the workflow before connecting Snowflake, BigQuery, Spark, Redis, or another production backend.

### Prerequisites

- Python 3.9 or newer
- `pip`
- Basic familiarity with Pandas

### Step 1: Create an environment

```bash
python -m venv .venv
source .venv/bin/activate
```

On Windows:

```powershell
python -m venv .venv
.venv\Scripts\activate
```

### Step 2: Install Feast

```bash
pip install feast
```

### Step 3: Initialize a feature repository

```bash
feast init fraud_demo
cd fraud_demo/feature_repo
```

The generated repository includes:

```text
fraud_demo/
└── feature_repo/
    ├── data/
    ├── feature_definitions.py
    ├── feature_store.yaml
    └── test_workflow.py
```

### Step 4: Inspect the configuration

Open `feature_store.yaml`:

```yaml
project: fraud_demo
registry: data/registry.db
provider: local
online_store:
  type: sqlite
  path: data/online_store.db
entity_key_serialization_version: 3
```

For local development:

- `registry` stores feature metadata.
- `provider: local` uses local defaults.
- `online_store` uses SQLite.
- The offline store uses local Parquet files.

### Step 5: Define a customer feature

Replace or add the following in `feature_definitions.py`:

```python
from datetime import timedelta

from feast import Entity, FeatureView, Field, FileSource
from feast.types import Float32, Int64

customer = Entity(name="customer", join_keys=["customer_id"])

customer_stats_source = FileSource(
    name="customer_stats_source",
    path="data/customer_stats.parquet",
    timestamp_field="event_timestamp",
    created_timestamp_column="created",
)

customer_stats = FeatureView(
    name="customer_stats",
    entities=[customer],
    ttl=timedelta(days=1),
    schema=[
        Field(name="daily_transactions", dtype=Int64),
        Field(name="lifetime_value", dtype=Float32),
    ],
    online=True,
    source=customer_stats_source,
)
```

For the bundled demo data, retain the existing driver example if you want to run the workflow immediately without preparing your own Parquet dataset.

### Step 6: Register features

```bash
feast apply
```

Expected result:

```text
Created entity customer
Created feature view customer_stats
```

This registers metadata and creates the SQLite online-store table.

### Step 7: Generate a training dataset

Create `train.py`:

```python
from datetime import datetime

import pandas as pd
from feast import FeatureStore

entity_df = pd.DataFrame(
    {
        "customer_id": ["C123", "C456"],
        "event_timestamp": [
            datetime(2024, 1, 1, 12, 0, 0),
            datetime(2024, 1, 1, 13, 0, 0),
        ],
        "label_fraud": [0, 1],
    }
)

store = FeatureStore(repo_path=".")

training_df = store.get_historical_features(
    entity_df=entity_df,
    features=[
        "customer_stats:daily_transactions",
        "customer_stats:lifetime_value",
    ],
).to_df()

print(training_df)
```

Run it:

```bash
python train.py
```

Feast joins the feature history to each customer/timestamp pair using point-in-time logic.

### Step 8: Materialize features for online serving

```bash
feast materialize-incremental "$(date -u +'%Y-%m-%dT%H:%M:%S')"
```

This loads the latest feature values into SQLite so they can be served during inference.

### Step 9: Retrieve online features

Create `predict.py`:

```python
from feast import FeatureStore

store = FeatureStore(repo_path=".")

features = store.get_online_features(
    features=[
        "customer_stats:daily_transactions",
        "customer_stats:lifetime_value",
    ],
    entity_rows=[
        {"customer_id": "C123"},
        {"customer_id": "C456"},
    ],
).to_dict()

print(features)
```

Run it:

```bash
python predict.py
```

You should receive a dictionary containing the latest feature values for each customer.

### Step 10: Use a feature service

A `FeatureService` gives a model a stable, versioned feature contract.

```python
from feast import FeatureService

fraud_features_v1 = FeatureService(
    name="fraud_features_v1",
    features=[
        "customer_stats:daily_transactions",
        "customer_stats:lifetime_value",
    ],
)
```

Retrieve the entire service:

```python
feature_service = store.get_feature_service("fraud_features_v1")

features = store.get_online_features(
    features=feature_service,
    entity_rows=[{"customer_id": "C123"}],
).to_dict()

print(features)
```

This prevents an application from breaking when unrelated feature views change.

### Step 11: Explore the catalog

```bash
feast ui
```

Open:

```text
http://localhost:8888
```

The UI lets you inspect registered entities, feature views, schemas, data sources, and feature services.

## Minimal Production Pattern

For a Kubernetes-native deployment, a practical pattern is:

```text
Kafka -> Flink/Spark Streaming -> Feast push -> Redis
                                        |
                                        +--> Offline store

Airflow / Argo -> Feast materialization -> Redis

Model API -> Feast SDK / Feature Server -> Redis
```

- **Kafka:** Emits transaction, click, telemetry, or user events.
- **Stream processor:** Computes rolling aggregates and recent behavioral features.
- **Feast push:** Writes fresh values to online and optionally offline storage.
- **Orchestrator:** Runs scheduled batch materialization.
- **Model API:** Retrieves feature vectors with millisecond-level online reads.
- **Prometheus/Grafana:** Monitors freshness, latency, failures, and feature availability.

## When to Use Feast

Feast is a strong fit when you have multiple ML models, require consistent features across training and inference, need point-in-time correctness, or want to avoid coupling models directly to warehouse queries and application databases.

It is less necessary for a single small model with simple features, though it can still provide value as the ML platform grows. The main operational investment is managing feature freshness, materialization jobs, registry deployments, online-store capacity, and data-quality monitoring.