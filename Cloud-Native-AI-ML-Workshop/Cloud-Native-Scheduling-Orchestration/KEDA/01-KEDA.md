## KEDA (Kubernetes Event-driven Autoscaling)

KEDA (Kubernetes Event-driven Autoscaler) is a CNCF graduated, vendor-neutral Kubernetes add-on that scales workloads from **external events**—such as RabbitMQ queue depth, Kafka lag, Redis stream length, PostgreSQL query results, Prometheus metrics, or cloud queues—rather than only CPU/memory. It works alongside the native Kubernetes HPA and is especially valuable for bursty event-driven systems and **scale-to-zero** workloads.  

## What KEDA is?

KEDA converts an external event signal into a Kubernetes scaling decision.

- A producer emits work: messages, jobs, files, database rows, or metric values.
- KEDA polls the event source through a **scaler**.
- KEDA exposes that value to Kubernetes as an external metric.
- The Kubernetes HPA adjusts replicas above one; KEDA itself handles the zero-to-one and one-to-zero transitions.  

Think of KEDA as a translator: “There are 250 unprocessed RabbitMQ messages” becomes “run 8 worker pods.”

## Why it exists

The built-in HPA scales primarily on resource metrics such as CPU and memory. That is useful, but many production workloads do not correlate cleanly with CPU:

- A consumer may be idle at 2% CPU while a queue contains 50,000 messages.
- A batch worker may be I/O-bound and never trigger CPU scaling.
- A nightly pipeline may need to run only when files arrive.
- A low-traffic service may waste money running replicas overnight.

KEDA solves this by scaling on **work-to-do**, not merely resource pressure. It supports more than 70 built-in scalers across messaging systems, databases, cloud queues, monitoring systems, CI systems, and custom APIs.

## Architecture

```text
                 +---------------------+
                 |   Event source      |
                 | RabbitMQ / Kafka    |
                 | Redis / PostgreSQL  |
                 | Prometheus / SQS    |
                 +----------+----------+
                            |
                            | Polls metrics
                            v
        +-------------------+-------------------+
        |              KEDA operator            |
        | - Watches ScaledObject / ScaledJob    |
        | - Creates/manages HPA                 |
        | - Handles 0 <-> 1 replicas            |
        +-------------------+-------------------+
                            |
                            | External metrics
                            v
        +-------------------+-------------------+
        |       keda-metrics-apiserver          |
        | Exposes event metrics to K8s API      |
        +-------------------+-------------------+
                            |
                            v
        +-------------------+-------------------+
        |        Kubernetes HPA controller      |
        | Calculates desired replicas 1 -> N    |
        +-------------------+-------------------+
                            |
                            v
        +-------------------+-------------------+
        | Deployment / StatefulSet / Custom CRD |
        | ReplicaSet creates/terminates pods    |
        +---------------------------------------+
```

### Core components

| Component | Purpose |
|---|---|
| `keda-operator` | Watches `ScaledObject` and `ScaledJob` resources, creates HPAs, and performs zero-to-one and one-to-zero scaling.   |
| `keda-metrics-apiserver` | Serves external metrics from event sources to the Kubernetes API server so the HPA can consume them.    |
| `keda-admission-webhooks` | Validates KEDA resources when applied, catching mistakes such as conflicting `ScaledObjects` targeting the same workload.   |
| `ScaledObject` | Binds a Deployment, StatefulSet, or custom scalable resource to one or more event triggers.   |
| `ScaledJob` | Creates Kubernetes Jobs in response to events, intended for batch processing.    |
| `TriggerAuthentication` | Securely supplies credentials or identity configuration to scalers.    |
| Scaler | A pluggable integration that knows how to query a particular event source.   |

### Scaling behavior

KEDA uses two paths:

1. **Zero to one / one to zero:** handled directly by the KEDA operator. This enables scale-to-zero.
2. **One to N / N to one:** delegated to the Kubernetes HPA, which reads external metrics from KEDA’s metrics API server.  

Important limitation: CPU and memory triggers cannot scale from zero because no running pod means no CPU or memory metric exists. 



