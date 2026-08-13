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

## Step 2: Install KEDA

```bash
helm repo add kedacore https://kedacore.github.io/charts
helm repo update

helm install keda kedacore/keda \
  --namespace keda \
  --create-namespace
```

This is the recommended flexible installation method: Helm manages the KEDA components, CRDs, RBAC, and upgrade lifecycle.  

Verify installation:

```bash
kubectl get pods -n keda
kubectl get crd | grep keda
```

Expected output:

```text
NAME                                      READY   STATUS    RESTARTS   AGE
keda-operator-xxxxxxxxxx-xxxxx            1/1     Running   0          1m
keda-admission-webhooks-xxxxxxxx-xxxxx    1/1     Running   0          1m
```

You should see CRDs including:

```text
scaledobjects.keda.sh
scaledjobs.keda.sh
triggerauthentications.keda.sh
```

Purpose: confirm that the operator, webhook, and custom resource definitions are installed before creating workload integrations.

## Step 3: Install RabbitMQ

Create `rabbitmq.yaml`:

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: rabbitmq
  namespace: default
spec:
  serviceName: rabbitmq
  replicas: 1
  selector:
    matchLabels:
      app: rabbitmq
  template:
    metadata:
      labels:
        app: rabbitmq
    spec:
      containers:
        - name: rabbitmq
          image: rabbitmq:3.13-management
          ports:
            - containerPort: 5672
              name: amqp
            - containerPort: 15672
              name: management
          env:
            - name: RABBITMQ_DEFAULT_USER
              value: "keda"
            - name: RABBITMQ_DEFAULT_PASS
              value: "keda-password"
          readinessProbe:
            tcpSocket:
              port: 5672
            initialDelaySeconds: 10
            periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: rabbitmq
  namespace: default
spec:
  selector:
    app: rabbitmq
  ports:
    - name: amqp
      port: 5672
      targetPort: 5672
    - name: management
      port: 15672
      targetPort: 15672
```

Apply it:

```bash
kubectl apply -f rabbitmq.yaml
kubectl rollout status statefulset/rabbitmq
```

Expected output:

```text
statefulset rolling update complete 1 pods...
```

Purpose: RabbitMQ acts as the external event source. In production, use a managed broker or a highly available RabbitMQ cluster; this single-instance setup is for learning only.

