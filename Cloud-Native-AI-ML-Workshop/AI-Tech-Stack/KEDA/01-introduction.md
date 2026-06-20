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