## Prerequisites

For the local lab, use:

- Linux, macOS with Docker Desktop, or Windows with WSL2.
- Docker.
- `kubectl`.
- Helm 3.
- A local Kubernetes cluster: Kind, Minikube, k3d, or Rancher Desktop.
- At least 8 GB RAM recommended; 12–16 GB is more comfortable.
- Outbound internet access to download Fluid charts and demo files.

Fluid documents Kubernetes greater than 1.16 with CSI support, Helm 3, and Go 1.18+ for source builds. For this lab, a recent Kubernetes version is strongly preferred.


### Install local tools

```bash
# macOS example
brew install kubectl helm kind

# Linux example
curl -LO "https://dl.k8s.io/release/$(curl -Ls https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install kubectl /usr/local/bin/kubectl

curl -fsSL https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
```

### Create a Kind cluster

```bash
cat > kind-fluid.yaml <<'EOF'
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
- role: worker
- role: worker
EOF

kind create cluster --name fluid-lab --config kind-fluid.yaml
kubectl get nodes
```

Expected output:

```text
NAME                      STATUS   ROLES           AGE   VERSION
fluid-lab-control-plane   Ready    control-plane   1m    v1.x.x
fluid-lab-worker          Ready    <none>          1m    v1.x.x
fluid-lab-worker2         Ready    <none>          1m    v1.x.x
```

Two workers are useful because the lab creates two cache replicas.



## Install Fluid

Fluid is installed with Helm. The exact chart repository and version can change, so pin a released version in real environments rather than blindly using `latest`.

```bash
helm repo add fluid https://fluid-cloudnative.github.io/fluid-charts
helm repo update

kubectl create namespace fluid-system

helm install fluid fluid/fluid \
  --namespace fluid-system \
  --set dataset.controller.enabled=true \
  --set csi.enabled=true
```

If your chart version uses different values, inspect them first:

```bash
helm show values fluid/fluid > fluid-values.yaml
```

Then install with your reviewed values:

```bash
helm install fluid fluid/fluid \
  --namespace fluid-system \
  -f fluid-values.yaml
```

### Validate the control plane

```bash
kubectl get pods -n fluid-system
```

Expected pattern:

```text
NAME                                          READY   STATUS    RESTARTS   AGE
alluxioruntime-controller-xxxxxxxxxx-xxxxx    1/1     Running   0          1m
csi-nodeplugin-fluid-xxxxx                     2/2     Running   0          1m
csi-nodeplugin-fluid-yyyyy                     2/2     Running   0          1m
dataset-controller-xxxxxxxxxx-xxxxx            1/1     Running   0          1m
```

The exact Pod names vary by version. The important checks are that the dataset controller, runtime controller, and one CSI node plugin per eligible node are running. The official sample similarly expects controller and CSI node plugin Pods in `fluid-system`.  

## Lab: accelerate a remote dataset

This lab uses a public Apache HBase mirror as a simple web-backed source. It is deliberately easy to reproduce, but in production you would normally use S3-compatible object storage, NFS, HDFS, or another supported backend.  

### Create the Dataset

```bash
mkdir fluid-lab && cd fluid-lab

cat > dataset.yaml <<'EOF'
apiVersion: data.fluid.io/v1alpha1
kind: Dataset
metadata:
  name: hbase
spec:
  mounts:
    - mountPoint: https://downloads.apache.org/hbase/stable/
      name: hbase
EOF

kubectl apply -f dataset.yaml
kubectl get dataset hbase
```

Expected initial output:

```text
NAME    UFS TOTAL SIZE   CACHED   CACHE CAPACITY   CACHED PERCENTAGE   PHASE       AGE
hbase                    0B                                            NotBound    10s
```

**Why this matters:** the `Dataset` object tells Fluid *what* data to expose, but not yet *how* to cache it. `NotBound` means no cache runtime is attached.  

### Create the Alluxio cache runtime

```bash
cat > runtime.yaml <<'EOF'
apiVersion: data.fluid.io/v1alpha1
kind: AlluxioRuntime
metadata:
  name: hbase
spec:
  replicas: 2
  tieredstore:
    levels:
      - mediumtype: MEM
        path: /dev/shm
        quota: 2Gi
        high: "0.95"
        low: "0.7"
EOF

kubectl apply -f runtime.yaml
```

**Design decisions:**

- `replicas: 2` creates two cache workers, providing basic cache redundancy and spreading cached data across nodes.
- `mediumtype: MEM` uses `/dev/shm`, which is fast but ephemeral and consumes node memory.
- `quota: 2Gi` limits each worker’s cache usage in this lab.
- `high` and `low` control cache eviction behavior: Fluid/Alluxio begins evicting when usage crosses the high threshold and continues until it reaches the low threshold.

For a local laptop, reduce replicas or quota if memory pressure occurs. For production, memory-only caching is appropriate only for small, extremely hot datasets; larger datasets usually need an SSD or HDD tier.

### Watch the cache come up

```bash
kubectl get pods -w 
```

Expected output:

```text
NAME             READY   STATUS    RESTARTS   AGE
hbase-master-0   2/2     Running   0          1m
hbase-worker-0   2/2     Running   0          40s
hbase-worker-1   2/2     Running   0          40s
```

Then check the Dataset:

```bash
kubectl get dataset hbase
kubectl get alluxioruntime hbase -o wide
kubectl get pvc hbase
```

Expected pattern:

```text
NAME    UFS TOTAL SIZE   CACHED   CACHE CAPACITY   CACHED PERCENTAGE   PHASE   AGE
hbase   443.5MiB         0B       4GiB             0%                  Bound   2m

NAME    STATUS   VOLUME   CAPACITY   ACCESS MODES   STORAGECLASS   AGE
hbase   Bound    hbase    100Gi      RWX                           2m
```

Fluid creates a PVC named after the `Dataset`. Your application mounts that PVC; it does not need to know that Alluxio is underneath. 

## Consume the dataset from a Pod

```bash
cat > nginx.yaml <<'EOF'
apiVersion: v1
kind: Pod
metadata:
  name: nginx
spec:
  containers:
    - name: nginx
      image: nginx
      volumeMounts:
        - mountPath: /data
          name: hbase-vol
  volumes:
    - name: hbase-vol
      persistentVolumeClaim:
        claimName: hbase
EOF

kubectl apply -f nginx.yaml
kubectl wait --for=condition=Ready pod/nginx --timeout=180s
kubectl exec -it nginx -- ls -1 /data/hbase
```

Expected output resembles:

```text
CHANGES.md
RELEASENOTES.md
api_compare_2.2.5RC0_to_2.2.4.html
hbase-2.2.5-bin.tar.gz
hbase-2.2.5-client-bin.tar.gz
hbase-2.2.5-src.tar.gz
```

The application sees ordinary files under `/data/hbase`. This is the value of the Fluid abstraction: the workload uses a PVC, while Fluid and Alluxio handle remote mounting and caching. 

## Measure cold and warm reads

### Cold read

```bash
cat > copy-job.yaml <<'EOF'
apiVersion: batch/v1
kind: Job
metadata:
  name: fluid-copy-test
spec:
  template:
    spec:
      restartPolicy: OnFailure
      containers:
        - name: busybox
          image: busybox
          command: ["/bin/sh"]
          args:
            - "-c"
            - "set -x; time cp -r /data/hbase ./"
          volumeMounts:
            - mountPath: /data
              name: hbase-vol
      volumes:
        - name: hbase-vol
          persistentVolumeClaim:
            claimName: hbase
EOF

kubectl apply -f copy-job.yaml

kubectl wait --for=condition=complete job/fluid-copy-test --timeout=15m
POD=$(kubectl get pods -l job-name=fluid-copy-test -o jsonpath='{.items[0].metadata.name}')
kubectl logs "$POD"
```

The first run may take tens of seconds or minutes because it reads from the remote web source. In the official example, the first copy took about 63 seconds and the second took about 3 seconds after caching; your timings will vary substantially with network conditions.

### Verify caching

```bash
kubectl get dataset hbase
```

Expected:

```text
NAME    UFS TOTAL SIZE   CACHED    CACHE CAPACITY   CACHED PERCENTAGE   PHASE   AGE
hbase   443.5MiB         443.5MiB  4GiB             100%                Bound   9m
```

### Warm read

```bash
kubectl delete job fluid-copy-test
kubectl apply -f copy-job.yaml

kubectl wait --for=condition=complete job/fluid-copy-test --timeout=15m
POD=$(kubectl get pods -l job-name=fluid-copy-test -o jsonpath='{.items[0].metadata.name}')
kubectl logs "$POD"
```

Expected result: a much shorter elapsed time, assuming the data remains cached and the Pod can reach a cache worker.

## Preload before workloads start

Cold-cache performance is often unacceptable for production training. Use a `DataLoad` to warm the cache before launching expensive GPU jobs.

```bash
cat > preload.yaml <<'EOF'
apiVersion: data.fluid.io/v1alpha1
kind: DataLoad
metadata:
  name: hbase-warmup
spec:
  dataset:
    name: hbase
    namespace: default
  target:
    - path: /
      replicas: 1
EOF

kubectl apply -f preload.yaml
kubectl get dataload hbase-warmup -w
```

Expected phases:

```text
NAME            PHASE       PROGRESS   AGE
hbase-warmup    Executing   0%         5s
hbase-warmup    Executing   45%        30s
hbase-warmup    Complete    100%       2m
```

Exact status fields can vary by Fluid version. Validate completion with:

```bash
kubectl get dataload hbase-warmup -o yaml
kubectl get dataset hbase
```

**Production pattern:** create the `Dataset` and `Runtime`, run `DataLoad`, wait for completion, then submit the training Job. This avoids GPUs waiting on first-epoch data reads.

## Data-aware scheduling

Fluid can expose cache topology to the scheduler so that Pods are more likely to land on nodes holding the data they need. This is valuable for GPU clusters, where moving compute to data can materially improve throughput.

A practical pattern is:

1. Create the `Dataset`.
2. Create the cache `Runtime`.
3. Warm the cache.
4. Submit the workload with node affinity or Fluid-aware scheduling support enabled in your scheduler stack.

Do not assume that default Kubernetes scheduling alone will always place Pods optimally. For production, validate how your scheduler, cluster autoscaler, and Fluid version interact.

## Configuration for object storage

For a realistic S3-compatible source, use a secret-backed mount rather than embedding credentials in YAML.

```bash
kubectl create secret generic s3-credentials \
  --from-literal=awsAccessKeyId="$AWS_ACCESS_KEY_ID" \
  --from-literal=awsSecretKey="$AWS_SECRET_ACCESS_KEY"
```

Example conceptual Dataset:

```yaml
apiVersion: data.fluid.io/v1alpha1
kind: Dataset
metadata:
  name: training-images
spec:
  mounts:
    - mountPoint: s3://my-ml-bucket/training-images/
      name: images
      options:
        alluxio.underfs.s3.endpoint: http://minio.default.svc.cluster.local:9000
        alluxio.underfs.s3.disable.dns.buckets: "true"
      encryptOptions:
        - name: awsAccessKeyId
          valueFrom:
            secretKeyRef:
              name: s3-credentials
              key: awsAccessKeyId
        - name: awsSecretKey
          valueFrom:
            secretKeyRef:
              name: s3-credentials
              key: awsSecretKey
```

**Important:** exact option names depend on the Alluxio version and Fluid runtime implementation. Treat this as a template, verify against your installed chart’s samples, and never commit credentials to Git.

## Testing checklist

Run these checks after installation and after every upgrade.

```bash
# Control plane health
kubectl get pods -n fluid-system

# CRDs installed
kubectl get crd | grep fluid

# Dataset lifecycle
kubectl get dataset

# Runtime health
kubectl get alluxioruntime

# Cache and PVC
kubectl get pvc
kubectl get pv

# Workload access
kubectl exec -it nginx -- ls /data/hbase

# Cache utilization
kubectl get dataset hbase -o wide
```

A useful smoke test:

```bash
kubectl exec -it nginx -- sh -c 'time cp -r /data/hbase /tmp/test-copy && rm -rf /tmp/test-copy'
```

Run it twice. The second run should be faster if the dataset has been cached.

## Troubleshooting

| Symptom | Likely cause | What to check |
|---|---|---|
| Dataset remains `NotBound` | Runtime missing, invalid, or not ready | `kubectl get alluxioruntime`, controller logs |
| PVC not created | Dataset controller failure or CRD issue | `kubectl get dataset -o yaml`, controller logs |
| Pod cannot mount PVC | CSI plugin not running on that node | `kubectl get pods -n fluid-system -o wide` |
| Mount fails with permission error | Storage credentials or bucket policy | Secret contents, IAM policy, endpoint reachability |
| First read is slow | Expected cold-cache behavior | Use `DataLoad` before workload submission |
| Warm read is still slow | Cache miss, eviction, insufficient quota, Pod far from cache | Dataset cached percentage, worker logs, node placement |
| Worker OOMKilled | Memory cache quota too high | Reduce quota, add SSD tier, increase node memory |
| Cache does not scale | Runtime replicas fixed or autoscaling not configured | Runtime spec, controller events |
| Remote source changes not visible | Cache consistency semantics | Refresh policy, TTL, explicit reload operation |

### Useful diagnostics

```bash
kubectl describe dataset hbase
kubectl describe alluxioruntime hbase
kubectl describe pvc hbase
kubectl get events --sort-by=.lastTimestamp | tail -50

kubectl logs -n fluid-system deploy/dataset-controller
kubectl logs -n fluid-system deploy/alluxioruntime-controller
kubectl logs -n fluid-system daemonset/csi-nodeplugin-fluid
```

### Common failure: cache quota too small

If `CACHED PERCENTAGE` stays below 100% despite a completed `DataLoad`, increase the cache quota or add a lower-cost storage tier:

```yaml
tieredstore:
  levels:
    - mediumtype: MEM
      path: /dev/shm
      quota: 4Gi
      high: "0.95"
      low: "0.7"
    - mediumtype: SSD
      path: /mnt/fluid-ssd
      quota: 50Gi
      high: "0.95"
      low: "0.7"
```

This is a design template; confirm the exact `mediumtype`, paths, and volume mounts supported by your Fluid and Alluxio versions.

## Security guidance

### Credentials

- Store source-system credentials in Kubernetes Secrets or a external secret manager.
- Use workload identity or IAM roles where supported instead of static keys.
- Restrict Secret access with RBAC.
- Never place credentials directly in `Dataset` manifests.

### Kubernetes RBAC

Limit who can create or modify Fluid resources:

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: fluid-dataset-editor
  namespace: ml-team-a
rules:
  - apiGroups: ["data.fluid.io"]
    resources: ["datasets", "dataloads"]
    verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
```

Avoid giving application teams broad cluster-admin access to Fluid controllers.

### Network security

- Restrict egress from cache workers to approved storage endpoints.
- Use private endpoints for object storage where possible.
- Apply NetworkPolicies around cache workers and application namespaces.
- Encrypt data in transit to the source system using TLS.
- Consider encryption at rest for cache volumes if cached data is sensitive; validate the exact support and performance impact for your chosen runtime.

### Multi-tenancy

Fluid can share a dataset across namespaces, which is powerful but requires governance:

- Use separate `Dataset` objects for data with different confidentiality levels.
- Use namespace-scoped RBAC.
- Apply quotas for cache capacity and compute.
- Audit who can create `DataLoad` objects, because they can trigger large data transfers.

## Scaling and capacity planning

### Cache sizing

Start with this calculation:

```text
Required hot-cache capacity =
  size of actively reused dataset subset
  × safety factor for replication/overhead
```

Example:

- Active training dataset: 800 GB.
- Expected hot subset: 40%.
- Desired cache replicas: 2.
- Safety factor: 1.3.

```text
800 GB × 0.40 × 2 × 1.3 = 832 GB total cache capacity
```

Spread that across worker nodes, leaving headroom for the operating system, kubelet, container runtime, and other workloads.

### Scaling dimensions

| Dimension | Scale when | Method |
|---|---|---|
| Cache replicas | More concurrent readers or need redundancy | Increase `spec.replicas` |
| Cache capacity | More hot data or higher cache-hit target | Increase quota or add storage tier |
| Memory tier | Latency-sensitive, small hot set | Increase memory quota |
| SSD tier | Larger hot set, cost-sensitive | Add SSD-backed tier |
| Application Pods | More parallel compute | Scale workload independently |
| Nodes | Cache and compute compete for resources | Add nodes or isolate cache/workload pools |

### Avoid noisy neighbors

For production:

- Dedicate node pools for cache workers where feasible.
- Set CPU and memory requests/limits for cache components.
- Avoid sharing `/dev/shm` cache with memory-hungry inference or training Pods.
- Use Pod anti-affinity to avoid placing all cache replicas on one node.
- Monitor cache hit ratio, eviction rate, worker memory, disk I/O, and network throughput.

## Production operations

### Upgrade procedure

1. Read the release notes and breaking-change notes.
2. Back up `Dataset`, `Runtime`, `DataLoad`, PVC, and application manifests.
3. Test the upgrade in a staging cluster with representative data.
4. Drain or protect cache workers according to your availability requirements.
5. Upgrade Fluid controllers first, then validate CSI and runtime behavior.
6. Run the smoke test.
7. Roll forward only after cache hit ratio and workload latency are acceptable.

### Observability

Minimum metrics to collect:

- Dataset cached percentage.
- Cache capacity and usage.
- Cache hit ratio.
- Read/write throughput.
- Cache worker CPU, memory, disk, and network usage.
- FUSE mount errors.
- Controller error rates and reconciliation latency.
- Application job duration and GPU utilization.

Alert examples:

- Dataset not `Bound` for more than 10 minutes.
- Cache worker restarts.
- Cache usage above 90% for 15 minutes.
- CSI node plugin not ready on a node.
- DataLoad stuck in `Executing`.
- Training job read throughput drops below baseline.

### Backup and recovery

Fluid’s cache is disposable by design; the source system is the durable data store. Therefore:

- Back up source data using the source system’s native mechanism.
- Version-control all Fluid CRDs and application manifests.
- Do not treat cache contents as a backup.
- Document recovery steps: recreate `Dataset`, recreate `Runtime`, preload if needed, remount workloads.

## Clean up the lab

```bash
kubectl delete -f copy-job.yaml
kubectl delete -f nginx.yaml
kubectl delete -f preload.yaml
kubectl delete -f runtime.yaml
kubectl delete -f dataset.yaml

helm uninstall fluid -n fluid-system
kubectl delete namespace fluid-system

kind delete cluster --name fluid-lab
```

## Strengths and limitations

### Strengths

- Makes datasets Kubernetes-native through CRDs and PVCs.
- Reduces repeated remote reads through distributed caching.
- Supports preloading with `DataLoad`.
- Enables data-aware placement for compute workloads.
- Keeps workloads simple: applications mount a PVC.
- Is vendor-neutral and works with common data-intensive frameworks.
- Is a CNCF incubating project with an active open-source community. 

### Limitations

- Adds moving parts: controllers, CSI plugins, cache workers, FUSE, and runtime-specific configuration.
- Cache is not a substitute for durable storage or backup.
- Memory-only caches can be expensive and unstable if undersized.
- Performance gains depend heavily on access patterns; random one-time reads may not benefit.
- Operational complexity rises with multi-tenancy, multi-cluster, and heterogeneous storage.
- Version compatibility among Kubernetes, Fluid, CSI, container runtime, and cache engine must be tested.

## Alternatives and trade-offs

| Option | Best for | Trade-off versus Fluid |
|---|---|---|
| Direct object-store mounts | Simple, infrequent access | No dataset orchestration, cache affinity, or preload lifecycle |
| Read-only PVC backed by NFS | Shared POSIX data | Often simpler, but may bottleneck and lacks elastic distributed caching |
| Alluxio standalone | Teams that want direct control of caching | More manual integration with Kubernetes workloads and scheduling |
| JuiceFS | POSIX-style shared filesystem over object storage | Strong filesystem semantics; different operational model and feature set |
| Kubernetes-native PVC + local NVMe | Data already local or statically partitioned | Fast and simple, but less elastic and less data-aware |
| Spark native caching | Spark-only workloads | Works inside Spark, but does not provide a general Kubernetes dataset layer |
| Vendor-managed data acceleration | Teams wanting managed operations | Less portable and often higher cost; may reduce control |

## When to use Fluid

**Use Fluid when:**

- Multiple Kubernetes jobs repeatedly read the same large dataset.
- Training or analytics is bottlenecked by remote storage latency or throughput.
- You need preloading before scheduled jobs.
- You want cache scaling and data-aware scheduling.
- You need a vendor-neutral data-access layer across clouds or on-premises clusters.
- GPU utilization is suffering because data loading is slow.

**Avoid Fluid when:**

- The dataset is small and read once.
- Workloads already read local NVMe efficiently.
- The source storage is already close, fast, and not contended.
- Your team cannot operate additional controllers, CSI components, and cache workers.
- Strong transactional consistency or fine-grained write semantics are primary requirements.
- You need a fully managed solution and cannot accept operational ownership of the data plane.

## Key insights

Technically, Fluid turns “data location” into a schedulable Kubernetes concern. It separates the *logical dataset* from the *physical cache implementation*, allowing compute teams to consume data through PVCs while platform teams manage caching, placement, scaling, and observability.

From a business perspective, its value is highest when it converts idle or underutilized expensive compute—especially GPUs—into productive compute. If a training job spends 30% of its time waiting on storage, reducing that wait can deliver more value than adding another GPU node. However, Fluid is an accelerator and orchestration layer, not a replacement for sound storage architecture, data governance, backup, or capacity planning. 
