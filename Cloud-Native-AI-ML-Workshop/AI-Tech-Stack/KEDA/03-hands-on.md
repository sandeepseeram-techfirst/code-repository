 
## Hands-on tutorial: Scale a worker with Redis

This tutorial demonstrates KEDA’s core behavior: scale a Redis-backed worker from zero to multiple replicas as messages arrive.

### Prerequisites

You need:

- A Kubernetes cluster: Kind, Minikube, k3s, MicroK8s, or a managed cluster.
- `kubectl` configured against the cluster.
- Helm 3.
- Redis accessible from the cluster.

For a local test, you can run Redis in-cluster.

### Step 1: Install KEDA

Add the KEDA Helm repository:

```bash
helm repo add kedacore https://kedacore.github.io/charts
helm repo update
```

Install KEDA:

```bash
helm install keda kedacore/keda \
  --namespace keda \
  --create-namespace
```

Verify installation:

```bash
kubectl get pods -n keda
```

You should see KEDA operator, metrics API server, and webhook-related pods running. KEDA requires Kubernetes 1.30 or newer.  

### Step 2: Create a namespace

```bash
kubectl create namespace keda-demo
kubectl config set-context --current --namespace=keda-demo
```

### Step 3: Deploy Redis

Create `redis.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
        - name: redis
          image: redis:7-alpine
          ports:
            - containerPort: 6379
--- 
apiVersion: v1
kind: Service
metadata:
  name: redis
spec:
  selector:
    app: redis
  ports:
    - port: 6379
      targetPort: 6379
```

Apply it:

```bash
kubectl apply -f redis.yaml
```

### Step 4: Deploy a worker

Create a simple worker that consumes items from a Redis list.

Create `worker.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis-worker
spec:
  replicas: 0
  selector:
    matchLabels:
      app: redis-worker
  template:
    metadata:
      labels:
        app: redis-worker
    spec:
      containers:
        - name: worker
          image: busybox:1.36
          command:
            - sh
            - -c
            - |
              while true; do
                ITEM=$(redis-cli -h redis -r 100 BLPOP jobs 5)
                if [ "$ITEM" != "(nil)" ]; then
                  echo "Processing: $ITEM"
                  sleep 2
                fi
              done
```

Apply it:

```bash
kubectl apply -f worker.yaml
```

The Deployment starts with `replicas: 0`; KEDA will activate it when Redis contains pending jobs.

### Step 5: Create the ScaledObject

Create `scaledobject.yaml`:

```yaml
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: redis-worker-scaler
spec:
  scaleTargetRef:
    name: redis-worker
  minReplicaCount: 0
  maxReplicaCount: 5
  pollingInterval: 5
  cooldownPeriod: 30
  triggers:
    - type: redis
      metadata:
        address: redis.keda-demo.svc.cluster.local:6379
        listName: jobs
        listLength: "1"
```

This configuration means:

- Poll Redis every 5 seconds.
- Start scaling when the `jobs` list has at least one item.
- Allow up to 5 worker replicas.
- Return to zero after 30 seconds of inactivity.

Apply it:

```bash
kubectl apply -f scaledobject.yaml
```

### Step 6: Verify initial scale-to-zero

Check the worker:

```bash
kubectl get deployment redis-worker
```

Expected output should show:

```text
READY   UP-TO-DATE   AVAILABLE
0/0      0            0
```

Check the KEDA-managed HPA:

```bash
kubectl get hpa
```

KEDA creates and manages an HPA for the `redis-worker` Deployment.  

### Step 7: Add work to Redis

Run a temporary Redis client:

```bash
kubectl run redis-client --rm -it \
  --image=redis:7-alpine \
  --restart=Never \
  -- redis-cli -h redis
```

Inside the client, add 20 jobs:

```text
RPUSH jobs job-1 job-2 job-3 job-4 job-5 job-6 job-7 job-8 job-9 job-10 job-11 job-12 job-13 job-14 job-15 job-16 job-17 job-18 job-19 job-20
EXIT
```

Alternatively, run a one-shot command:

```bash
kubectl run redis-producer --rm -it \
  --image=redis:7-alpine \
  --restart=Never \
  -- redis-cli -h redis RPUSH jobs job-1 job-2 job-3 job-4 job-5
```

### Step 8: Watch KEDA scale up

In another terminal:

```bash
kubectl get pods -w
```

You should see:

1. KEDA activates the Deployment from zero to one.
2. HPA scales it further as the Redis list remains above the threshold.
3. As jobs are consumed, the list length decreases.
4. KEDA eventually scales the Deployment back to zero after the cooldown period.

Check current state:

```bash
kubectl get deployment redis-worker
kubectl get pods
kubectl get hpa
```

### Step 9: Inspect KEDA resources

Check the `ScaledObject`:

```bash
kubectl get scaledobject
kubectl describe scaledobject redis-worker-scaler
```

Look for:

- Active trigger status.
- Current external metric value.
- Target Deployment.
- HPA ownership.
- Any authentication or connectivity errors.

### Step 10: Clean up

```bash
kubectl delete scaledobject redis-worker-scaler
kubectl delete deployment redis-worker
kubectl delete deployment redis
kubectl delete service redis
kubectl delete namespace keda-demo
```

If needed, remove KEDA itself:

```bash
helm uninstall keda --namespace keda
kubectl delete namespace keda
```

## Hands-on tutorial: Scale Kafka consumers

For a production-style event platform, the pattern is similar but uses Kafka consumer lag.

### Example ScaledObject

```yaml
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: kafka-consumer-scaler
spec:
  scaleTargetRef:
    name: kafka-consumer
  minReplicaCount: 0
  maxReplicaCount: 12
  pollingInterval: 10
  triggers:
    - type: kafka
      metadata:
        bootstrapServers: kafka-bootstrap.kafka.svc.cluster.local:9092
        consumerGroup: order-processor
        topic: orders
        lagThreshold: "100"
        offsetResetPolicy: latest
```

### Operational meaning

- If consumer lag is below 100 messages, KEDA can scale the consumer to zero.
- If lag rises above 100, KEDA activates the consumer.
- HPA scales it up to 12 replicas as lag increases.
- In practice, do not set `maxReplicaCount` above the usable partition parallelism unless your consumer architecture supports additional concurrency.

## When not to use KEDA

KEDA is powerful, but it is not always the right tool.

Avoid or reconsider KEDA when:

- Your workload is latency-critical and cannot tolerate pod cold starts.
- You only need basic CPU/memory autoscaling.
- You have no reliable external workload signal.
- Your event source cannot tolerate frequent metric polling.
- You need predictive capacity planning rather than reactive event scaling.
- Your downstream system becomes the bottleneck before Kubernetes can scale pods.

## Practical reference architecture

A robust event-driven platform often looks like this:

```text
Producers
  API / IoT devices / upstream services
        |
        v
Event backbone
  Kafka / RabbitMQ / NATS / cloud queue
        |
        +-----------------------+
        |                       |
        v                       v
KEDA-managed consumers   KEDA-managed batch Jobs
        |                       |
        v                       v
Processing services      ETL / ML inference / reports
        |
        v
Databases / object storage / downstream APIs
```

KEDA sits between the event backbone and Kubernetes scheduling. It observes demand, translates it into Kubernetes replicas or Jobs, and lets the platform consume only the capacity required at that moment.  