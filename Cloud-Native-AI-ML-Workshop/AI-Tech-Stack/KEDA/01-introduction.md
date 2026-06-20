# KEDA — Kubernetes Event-driven Autoscaling

**KEDA** is a lightweight Kubernetes add-on that scales workloads based on external events—such as Kafka lag, RabbitMQ queue depth, SQS messages, Prometheus metrics, or database queries. Its most distinctive capability is **scale-to-zero**: when there is no work, it can reduce a Deployment to zero pods and reactivate it when the next event arrives.

## In one sentence

KEDA turns Kubernetes autoscaling from “scale on CPU/memory” into “scale on the actual amount of work waiting to be done,” while working alongside—not replacing—the native Horizontal Pod Autoscaler (HPA).

## The problem it solves

Traditional Kubernetes autoscaling has a major limitation: HPA normally scales on CPU or memory. That works for request-serving apps, but it fails for asynchronous systems where the true load signal lives outside the pod.

Common failure modes KEDA addresses:

- A Kafka consumer has low CPU but a large consumer lag; CPU-based HPA does not scale it.
- A RabbitMQ/SQS worker is idle overnight but receives a burst at 09:00; fixed replicas waste capacity.
- A batch ingestion pipeline has no work for hours, yet keeps consuming cluster resources.
- A platform team needs one consistent autoscaling pattern across AWS, GCP, Azure, on-prem, Kafka, Redis, RabbitMQ, PostgreSQL, and custom APIs.
- Teams want to scale idle environments to zero without writing custom controllers or metrics adapters.

KEDA solves these by making the **event backlog, queue depth, stream lag, external metric, or query result** the scaling signal. 


## Core architecture

KEDA installs three main in-cluster components:

| Component | Responsibility |
|---|---|
| `keda-operator` | Watches KEDA custom resources, creates/manages HPAs, and handles the special zero-to-one and one-to-zero transitions. |
| `keda-metrics-apiserver` | Exposes external event metrics to Kubernetes through the Metrics API so HPA can use them for scaling above one replica. |
| `keda-admission-webhooks` | Validates `ScaledObject` and related resources when they are applied, catching invalid or conflicting configurations early. |

### Design principle

KEDA does not replace HPA. Instead, it extends HPA with external metrics:

- KEDA polls an event source through a **scaler**.
- The scaler returns a metric value, such as queue depth or consumer lag.
- KEDA’s metrics API server exposes that value to the Kubernetes API server.
- HPA reads the metric and calculates the desired replica count.
- For zero-to-one and one-to-zero, KEDA’s operator intervenes directly, because HPA cannot scale from zero without an existing pod to measure.  


### Scaling flow

```text
External system
  Kafka / RabbitMQ / SQS / Redis / Prometheus / DB
              |
              v
       KEDA scaler
              |
              v
    keda-metrics-apiserver
              |
              v
       Kubernetes API server
              |
              v
              HPA
              |
              v
        Deployment / StatefulSet
              |
              v
       ReplicaSet / Pods
```

There are two complementary scaling paths:

1. **Zero to one / one to zero:** handled directly by `keda-operator`.
2. **One to N / N to one:** handled by the HPA using metrics exposed by KEDA. 

## Key custom resources

KEDA is configured primarily through Kubernetes custom resources.

| Resource | Purpose |
|---|---|
| `ScaledObject` | Connects a long-running workload—Deployment, StatefulSet, or custom resource—to one or more event triggers. |
| `ScaledJob` | Creates Kubernetes Jobs in response to events, ideal for batch or one-shot workloads.  |
| `TriggerAuthentication` | Securely supplies credentials for event sources, such as Kubernetes Secrets, workload identity, or cloud-native authentication. |


### ScaledObject anatomy

A `ScaledObject` contains:

- `scaleTargetRef`: the workload to scale.
- `minReplicaCount`: minimum replicas, including `0`.
- `maxReplicaCount`: upper scaling bound.
- `triggers`: one or more event sources and thresholds.
- Optional `TriggerAuthentication` references for credentials.

Example concept:

```yaml
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: order-worker
spec:
  scaleTargetRef:
    name: order-worker
  minReplicaCount: 0
  maxReplicaCount: 20
  triggers:
    - type: rabbitmq
      metadata:
        queueName: orders
        mode: QueueLength
        value: "10"
```

This means: keep the worker at zero when the `orders` queue is empty, start one pod when work appears, and scale up as queue depth grows.

## Scalers: the integration layer

A **scaler** is the component that knows how to query a particular external system and translate its state into a scaling metric.

KEDA provides a large catalog of built-in scalers, including:

- Messaging: Kafka, RabbitMQ, NATS JetStream, Pulsar, Redis Streams, Solace, IBM MQ.
- Cloud queues and streams: AWS SQS, AWS Kinesis, GCP Pub/Sub, Azure Event Hubs, Azure Service Bus, Azure Storage Queue.
- Observability: Prometheus, Datadog, New Relic, Dynatrace, Loki, Elasticsearch.
- Databases: PostgreSQL, MySQL, MongoDB, Redis, Cassandra, ClickHouse.
- Scheduling and CI/CD: Cron, GitHub Actions runners, Azure Pipelines.
- Custom systems: External scaler and External Push scaler.  

This makes KEDA vendor-agnostic: the same Kubernetes platform can scale consumers for Kafka in one cluster, SQS in another, and Prometheus-backed inference services in a third.

## How scale-to-zero works

Scale-to-zero is KEDA’s differentiating feature.

1. The Deployment is scaled to zero because no events are pending.
2. KEDA continues polling the event source.
3. When the scaler reports activity, KEDA’s operator scales the Deployment from zero to one.
4. Once at least one pod exists, HPA takes over and can scale it further based on the external metric.
5. When the queue or stream becomes idle, KEDA scales the workload back to zero. 

This is especially valuable for:

- Development and staging environments.
- Nightly or intermittent batch workloads.
- Low-traffic event consumers.
- Cost-sensitive AI inference and data-processing workloads.
- Multi-tenant platforms where many workloads are idle most of the time.