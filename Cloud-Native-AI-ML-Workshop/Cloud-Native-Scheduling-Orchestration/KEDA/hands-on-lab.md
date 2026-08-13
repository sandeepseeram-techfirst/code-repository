## Prerequisites

For the hands-on lab, use a local Kubernetes cluster.

Required:

- Docker
- `kind` OR `minikube`
- `kubectl`
- Helm 3
- A terminal with Bash
- Approximately 4 GB free RAM

KEDA requires Kubernetes 1.30 or newer according to the current deployment documentation.  

Recommended local stack:

```text
kind cluster
KEDA
RabbitMQ
Redis
Prometheus
Worker application
```

This lab uses RabbitMQ because it is simple, observable, and demonstrates queue-driven scaling clearly.

## Lab architecture

```text
+-------------+       +-------------+       +----------------+
|  Producer   | ----> |  RabbitMQ   | ----> | Worker Pods    |
| publish.py  |       | tasks queue |       | consumer app   |
+-------------+       +------+------+       +--------+-------+
                             |                       ^
                             | Queue depth           |
                             v                       |
                      +------+------+         +------+-------+
                      | KEDA Scaler | ------> | KEDA + HPA   |
                      +-------------+         +--------------+
```

The producer publishes messages. KEDA observes the RabbitMQ queue depth. As messages accumulate, KEDA scales the consumer Deployment. When the queue empties, KEDA scales it back down, potentially to zero.

## Step 1: Create a local cluster

```bash
kind create cluster --name keda-lab
kubectl cluster-info
kubectl get nodes
```

Expected output:

```text
NAME                       STATUS   ROLES           AGE   VERSION
keda-lab-control-plane     Ready    control-plane   1m    v1.3x.x
```

Purpose: this gives you an isolated, disposable Kubernetes environment for safe experimentation.
