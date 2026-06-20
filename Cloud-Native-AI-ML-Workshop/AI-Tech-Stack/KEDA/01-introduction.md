# KEDA — Kubernetes Event-driven Autoscaling

**KEDA** is a lightweight Kubernetes add-on that scales workloads based on external events—such as Kafka lag, RabbitMQ queue depth, SQS messages, Prometheus metrics, or database queries. Its most distinctive capability is **scale-to-zero**: when there is no work, it can reduce a Deployment to zero pods and reactivate it when the next event arrives.

## In one sentence

KEDA turns Kubernetes autoscaling from “scale on CPU/memory” into “scale on the actual amount of work waiting to be done,” while working alongside—not replacing—the native Horizontal Pod Autoscaler (HPA).