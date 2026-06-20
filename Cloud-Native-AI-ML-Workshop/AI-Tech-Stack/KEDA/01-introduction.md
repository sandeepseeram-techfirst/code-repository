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

