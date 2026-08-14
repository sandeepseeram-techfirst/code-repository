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



## Step 4: Deploy a queue consumer

Create a simple Python consumer image locally.

Create `consumer.py`:

```python
import os
import time
import pika

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "keda")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD", "keda-password")
QUEUE = os.getenv("QUEUE_NAME", "tasks")

def main():
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
    parameters = pika.ConnectionParameters(
        host=RABBITMQ_HOST,
        credentials=credentials,
        heartbeat=60,
        blocked_connection_timeout=300,
    )

    while True:
        try:
            connection = pika.BlockingConnection(parameters)
            channel = connection.channel()
            channel.queue_declare(queue=QUEUE, durable=True)
            channel.basic_qos(prefetch_count=1)

            def callback(ch, method, properties, body):
                print(f"Processing: {body.decode()}", flush=True)
                time.sleep(2)
                ch.basic_ack(delivery_tag=method.delivery_tag)

            channel.basic_consume(
                queue=QUEUE,
                on_message_callback=callback,
            )
            print("Consumer ready", flush=True)
            channel.start_consuming()
        except Exception as exc:
            print(f"Connection error: {exc}; retrying", flush=True)
            time.sleep(5)

if __name__ == "__main__":
    main()
```

Create `Dockerfile`:

```dockerfile
FROM python:3.12-slim

WORKDIR /app
RUN pip install --no-cache-dir pika==1.3.2
COPY consumer.py .

CMD ["python", "consumer.py"]
```

Build and load it into `kind`:

```bash
docker build -t keda-lab-consumer:1.0 .
kind load docker-image keda-lab-consumer:1.0 --name keda-lab
```

Purpose: the consumer is the workload KEDA will scale. Its processing time is intentionally slow so you can observe queue backlog and replica growth.

## Step 5: Create the consumer Deployment

Create `consumer-deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: task-consumer
  namespace: default
spec:
  replicas: 0
  selector:
    matchLabels:
      app: task-consumer
  template:
    metadata:
      labels:
        app: task-consumer
    spec:
      containers:
        - name: consumer
          image: keda-lab-consumer:1.0
          env:
            - name: RABBITMQ_HOST
              value: rabbitmq.default.svc.cluster.local
            - name: RABBITMQ_USER
              valueFrom:
                secretKeyRef:
                  name: rabbitmq-auth
                  key: username
            - name: RABBITMQ_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: rabbitmq-auth
                  key: password
          resources:
            requests:
              cpu: 100m
              memory: 128Mi
            limits:
              cpu: 500m
              memory: 256Mi
```

Create the credential Secret:

```bash
kubectl create secret generic rabbitmq-auth \
  --from-literal=username=keda \
  --from-literal=password=keda-password
```

Apply the Deployment:

```bash
kubectl apply -f consumer-deployment.yaml
```

Purpose: start with `replicas: 0` to prove KEDA’s scale-from-zero behavior. In a normal non-KEDA Deployment, zero replicas would mean the service is unavailable; KEDA will activate it when work appears.

## Step 6: Create the ScaledObject

Create `consumer-scaledobject.yaml`:

```yaml
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: task-consumer-scaler
  namespace: default
spec:
  scaleTargetRef:
    name: task-consumer
  pollingInterval: 10
  cooldownPeriod: 60
  minReplicaCount: 0
  maxReplicaCount: 10
  triggers:
    - type: rabbitmq
      metadata:
        host: amqp://keda:keda-password@rabbitmq.default.svc.cluster.local:5672
        queueName: tasks
        mode: QueueLength
        value: "5"
        activationValue: "1"
```

Apply it:

```bash
kubectl apply -f consumer-scaledobject.yaml
```

Verify that KEDA created an HPA:

```bash
kubectl get scaledobject task-consumer-scaler
kubectl get hpa
```

Expected output:

```text
NAME                    SCALETARGETKIND      SCALETARGETNAME   MIN   MAX   TRIGGERS    AUTHENTICATION   READY   ACTIVE
task-consumer-scaler    apps/v1.Deployment   task-consumer     0     10   rabbitmq                     True    False
```

### Configuration decisions

| Field | Why it matters |
|---|---|
| `pollingInterval: 10` | KEDA checks RabbitMQ every 10 seconds. Shorter intervals react faster but increase broker/API load. |
| `cooldownPeriod: 60` | Prevents rapid scale-down flapping after a burst. |
| `minReplicaCount: 0` | Enables scale-to-zero. |
| `maxReplicaCount: 10` | Provides a hard cost and capacity guardrail. |
| `mode: QueueLength` | Scales based on total messages in the queue. |
| `value: "5"` | Requests one additional replica for every 5 queued messages. |
| `activationValue: "1"` | Activates the workload when at least one message exists. |

For throughput-sensitive systems, consider `mode: MessageRate` where supported, but queue length is the simplest and most deterministic lab trigger.

## Step 7: Publish test messages

Create `producer.py`:

```python
import pika

credentials = pika.PlainCredentials("keda", "keda-password")
parameters = pika.ConnectionParameters(
    host="localhost",
    port=5672,
    credentials=credentials,
)

connection = pika.BlockingConnection(parameters)
channel = connection.channel()
channel.queue_declare(queue="tasks", durable=True)

for i in range(100):
    message = f"task-{i}"
    channel.basic_publish(
        exchange="",
        routing_key="tasks",
        body=message.encode(),
        properties=pika.BasicProperties(delivery_mode=2),
    )
    print(f"Published {message}")

connection.close()
```

Expose RabbitMQ temporarily:

```bash
kubectl port-forward svc/rabbitmq 5672:5672
```

In another terminal:

```bash
python producer.py
```

Expected output:

```text
Published task-0
Published task-1
...
Published task-99
```
## Step 8: Observe scaling

Watch pods:

```bash
kubectl get pods -l app=task-consumer -w
```

Watch HPA status:

```bash
kubectl get hpa -w
```

Inspect KEDA’s view of the trigger:

```bash
kubectl get scaledobject task-consumer-scaler -o yaml
```

Expected behavior:

1. Initially, the consumer Deployment has zero pods.
2. After publishing messages, KEDA detects queue depth greater than `activationValue`.
3. The operator scales the Deployment from zero to one.
4. The HPA then increases replicas based on queue depth and the `value: "5"` threshold.
5. As the consumer drains the queue, KEDA scales down after the cooldown period.

Example expected progression:

```text
NAME                            READY   STATUS    RESTARTS   AGE
task-consumer-xxxxxxxxx-xxxxx   1/1     Running   0          10s
task-consumer-xxxxxxxxx-xxxxx   1/1     Running   0          25s
task-consumer-xxxxxxxxx-xxxxx   1/1     Running   0          40s
```

## Step 9: Validate scale-to-zero

Wait until all messages are processed:

```bash
kubectl get pods -l app=task-consumer
```

After the cooldown period:

```bash
kubectl get deployment task-consumer
```

Expected output:

```text
NAME            READY   UP-TO-DATE   AVAILABLE   AGE
task-consumer   0/0     0            0           10m
```

Then publish one message:

```bash
python producer.py
```

KEDA should activate the Deployment again within the polling interval.

## Testing checklist

| Test | Command | Expected result |
|---|---|---|
| KEDA installed | `kubectl get pods -n keda` | Operator and webhook are Running |
| CRDs registered | `kubectl get crd \| grep keda` | KEDA CRDs exist |
| ScaledObject valid | `kubectl get scaledobject` | `READY=True` |
| HPA created | `kubectl get hpa` | KEDA-managed HPA exists |
| Scale from zero | Publish one message | One consumer pod starts |
| Horizontal scale | Publish 100 messages | More pods appear |
| Scale down | Stop publishing and wait | Pods reduce after cooldown |
| Failure handling | Stop RabbitMQ | Consumer retries; KEDA logs scaler errors |

## Troubleshooting

### ScaledObject is not ready

```bash
kubectl describe scaledobject task-consumer-scaler
kubectl logs -n keda deploy/keda-operator
```

Common causes:

- Wrong RabbitMQ host, port, username, or password.
- Queue does not exist.
- NetworkPolicy blocks KEDA-to-RabbitMQ traffic.
- Scaler metadata uses an unsupported field for your KEDA version.

### Workload does not scale from zero

Check:

```bash
kubectl get scaledobject task-consumer-scaler -o yaml
kubectl get hpa
kubectl logs -n keda deploy/keda-operator
```

Common causes:

- `minReplicaCount` is not zero.
- `activationValue` is higher than the current queue depth.
- The scaler cannot authenticate.
- The Deployment selector does not match the target workload.
- Another HPA already controls the same Deployment.

KEDA’s admission webhook is designed to catch conflicting ScaledObjects targeting the same workload before runtime.  

### Pods scale but messages are not consumed

Check consumer logs:

```bash
kubectl logs -l app=task-consumer --tail=100
```

Likely causes:

- Consumer cannot resolve `rabbitmq.default.svc.cluster.local`.
- Credentials are wrong.
- Consumer crashes before consuming.
- Prefetch or concurrency settings create a bottleneck.
- The queue name differs from the scaler’s `queueName`.

### Scaling is too slow

Tune:

```yaml
pollingInterval: 5
cooldownPeriod: 30
```

Also consider whether the application itself has slow startup, image pull delays, long readiness probes, or insufficient cluster capacity. KEDA can request replicas quickly, but pod startup time remains a major contributor to end-to-end latency.

### Scaling oscillates

Increase `cooldownPeriod`, use a more stable metric such as consumer lag rather than instantaneous queue length, and ensure the application gracefully drains work before termination.

## Security hardening

### Do not put credentials in scaler metadata

The lab uses a URI in `ScaledObject` metadata for simplicity. In production, use `TriggerAuthentication` and Kubernetes Secrets.

Example:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: rabbitmq-secret
  namespace: default
type: Opaque
stringData:
  host: amqp://rabbitmq.default.svc.cluster.local:5672
  username: keda
  password: keda-password
---
apiVersion: keda.sh/v1alpha1
kind: TriggerAuthentication
metadata:
  name: rabbitmq-auth
  namespace: default
spec:
  secretTargetRef:
    - parameter: host
      name: rabbitmq-secret
      key: host
    - parameter: username
      name: rabbitmq-secret
      key: username
    - parameter: password
      name: rabbitmq-secret
      key: password
---
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: task-consumer-scaler
  namespace: default
spec:
  scaleTargetRef:
    name: task-consumer
  minReplicaCount: 0
  maxReplicaCount: 10
  triggers:
    - type: rabbitmq
      authenticationRef:
        name: rabbitmq-auth
      metadata:
        queueName: tasks
        mode: QueueLength
        value: "5"
        activationValue: "1"
```

`TriggerAuthentication` supports secrets and cloud-native identity mechanisms, keeping event-source access credentials out of workload specifications.


### Production controls

- Run KEDA in a dedicated namespace.
- Restrict RBAC so only platform teams manage `ScaledObject` and `TriggerAuthentication`.
- Use least-privilege broker credentials; KEDA should read metrics, not administer the broker.
- Encrypt traffic to event sources with TLS where supported.
- Apply NetworkPolicies so only KEDA can reach broker metric endpoints.
- Scan KEDA images and pin versions through a GitOps workflow.
- Enable audit logging for changes to scaling resources.
- Avoid placing highly sensitive credentials in `ScaledObject` metadata.

## Scaling and performance

KEDA itself is lightweight, but its effectiveness depends on the event source and workload design.

### Tuning recommendations

| Concern | Recommendation |
|---|---|
| Fast burst absorption | Lower `pollingInterval`, pre-pull images, use fast readiness probes |
| Cost control | Set realistic `maxReplicaCount`, use scale-to-zero only for interruptible work |
| Stability | Increase `cooldownPeriod`; avoid volatile metrics |
| Throughput | Tune consumer concurrency, prefetch, batching, and worker resource requests |
| Large fleets | Use separate KEDA instances or namespace boundaries where operationally justified |
| Observability | Export KEDA and HPA metrics to Prometheus and alert on scaler errors |

### Capacity model

For a queue-based consumer:

```text
Required pods ≈ ceil(queue_depth / messages_per_replica)
```

If one consumer processes 5 messages concurrently and each message takes 2 seconds:

```text
Per-pod throughput = 5 / 2 = 2.5 messages/second
```

For a target of 100 messages/second:

```text
Required pods = ceil(100 / 2.5) = 40
```

Set `maxReplicaCount` above this calculated requirement, but validate with load testing.

