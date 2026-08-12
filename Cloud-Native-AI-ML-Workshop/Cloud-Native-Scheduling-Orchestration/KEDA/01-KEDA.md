## KEDA (Kubernetes Event-driven Autoscaling)

KEDA (Kubernetes Event-driven Autoscaler) is a CNCF graduated, vendor-neutral Kubernetes add-on that scales workloads from **external events**—such as RabbitMQ queue depth, Kafka lag, Redis stream length, PostgreSQL query results, Prometheus metrics, or cloud queues—rather than only CPU/memory. It works alongside the native Kubernetes HPA and is especially valuable for bursty event-driven systems and **scale-to-zero** workloads.  

## What KEDA is?

KEDA converts an external event signal into a Kubernetes scaling decision.

- A producer emits work: messages, jobs, files, database rows, or metric values.
- KEDA polls the event source through a **scaler**.
- KEDA exposes that value to Kubernetes as an external metric.
- The Kubernetes HPA adjusts replicas above one; KEDA itself handles the zero-to-one and one-to-zero transitions.  

Think of KEDA as a translator: “There are 250 unprocessed RabbitMQ messages” becomes “run 8 worker pods.”
