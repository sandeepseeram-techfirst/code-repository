## Prerequisites

Before production rollout, validate these platform requirements:

- A supported Linux distribution and kernel version; advanced features may require newer kernels.
- Kubernetes cluster with compatible API version.
- `helm` and `kubectl`.
- Cilium CLI.
- eBPF filesystem mounted, typically `/sys/fs/bpf`.
- Required kernel modules and privileges for eBPF program loading.
- Firewall and routing-table access appropriate for your chosen datapath.
- For some large-scale or legacy deployments, an external etcd key-value store may be considered; modern Cilium commonly uses Kubernetes CRDs.  

Cilium’s operations documentation explicitly highlights Linux distribution compatibility, kernel version, key-value store considerations, firewall rules, mounted eBPF filesystem, routing tables, and privileges as key system requirements.  


## Hands-on installation

The following is a clean, production-oriented baseline for a self-managed Kubernetes cluster. Adapt IPAM and datapath settings to your cloud or bare-metal network design.

### 1. Install tooling

```bash
curl -fsSL https://raw.githubusercontent.com/cilium/cilium-cli/main/stable.txt | \
  sh -s -- -- -b /usr/local/bin

cilium version

helm version
kubectl version --client
```

### 2. Validate the cluster

```bash
kubectl get nodes -o wide
kubectl get pods -n kube-system
kubectl get crd | grep cilium
```

Ensure no existing CNI is actively managing pod networking unless you are deliberately using CNI chaining or migrating from another CNI.

### 3. Create a values file

Avoid relying on long `--set` flags in production. Store configuration in Git.

```yaml
# cilium-values.yaml
kubeProxyReplacement: true

k8sServiceHost: "<API_SERVER_IP>"
k8sServicePort: "6443"

ipam:
  mode: kubernetes

hubble:
  enabled: true
  relay:
    enabled: true
  ui:
    enabled: true
  metrics:
    enabled:
      - dns
      - drop
      - tcp
      - flow
      - icmp
      - http

prometheus:
  enabled: true

operator:
  prometheus:
    enabled: true

encryption:
  enabled: true
  type: wireguard

gatewayAPI:
  enabled: true

upgradeCompatibility: "1.19"
```

Use `upgradeCompatibility` matching the version initially installed in the cluster to minimize datapath disruption during later upgrades.  

### 4. Install Cilium

```bash
helm repo add cilium https://helm.cilium.io/
helm repo update

helm upgrade --install cilium cilium/cilium \
  --namespace kube-system \
  --version 1.20.3 \
  -f cilium-values.yaml
```

Cilium charts are also available through OCI registries, which can support digest-pinned, supply-chain-conscious deployments.  

### 5. Validate installation

```bash
cilium status --wait
cilium connectivity test
```

Also verify:

```bash
kubectl -n kube-system get pods -l k8s-app=cilium -o wide
kubectl -n kube-system get ds cilium
kubectl -n kube-system get deploy cilium-operator
kubectl get ciliumendpoints -A
```

A healthy deployment should show all Cilium agents ready, the operator available, and successful connectivity tests.  

## Practical policy examples

### Default deny for a namespace

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny
  namespace: payments
spec:
  podSelector: {}
  policyTypes:
    - Ingress
    - Egress
```

This denies all ingress and egress for pods in `payments` unless another policy explicitly allows traffic.

### Allow frontend to checkout

```yaml
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata:
  name: frontend-to-checkout
  namespace: payments
spec:
  endpointSelector:
    matchLabels:
      app: checkout
  ingress:
    - fromEndpoints:
        - matchLabels:
            io.kubernetes.pod.namespace: shop
            app: frontend
      toPorts:
        - ports:
            - port: "8080"
              protocol: TCP
          rules:
            http:
              - method: "GET"
                path: "/api/v1/checkout"
```

This is identity-aware and HTTP-aware: only `GET /api/v1/checkout` from the `shop/frontend` identity is allowed.

### Restrict external DNS and HTTPS egress

```yaml
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata:
  name: checkout-egress
  namespace: payments
spec:
  endpointSelector:
    matchLabels:
      app: checkout
  egress:
    - toEndpoints:
        - matchLabels:
            k8s-app: kube-dns
      toPorts:
        - ports:
            - port: "53"
              protocol: UDP
            - port: "53"
              protocol: TCP
          rules:
            dns:
              - matchPattern: "*"
    - toFQDNs:
        - matchName: "api.payment-provider.example"
      toPorts:
        - ports:
            - port: "443"
              protocol: TCP
```

This demonstrates a zero-trust egress pattern: DNS is constrained, and external access is limited to an approved FQDN and port.

## Real-world use cases

### High-throughput microservices

Use Cilium as the CNI with kube-proxy replacement to reduce Service datapath overhead and improve east-west performance. Cilium explicitly supports high-performance CNI networking, L4 load balancing, kube-proxy replacement, bandwidth and latency optimization, and BGP.  

### Zero-trust platform

Apply default-deny namespaces, identity-based policies, DNS-aware egress controls, encryption, and Hubble flow auditing. Cilium’s security model is identity-aware and supports L3/L4/DNS network flow logs and transparent encryption.  

### Multi-cloud and hybrid connectivity

Use Cluster Mesh to connect clusters across clouds, data centers, or edge environments while retaining service discovery and policy controls. Cilium provides multi-cluster networking through Cluster Mesh, including load balancing, service discovery, and policy.  

### AI/ML and data platforms

For AI inference, feature pipelines, Spark, Ray, Kafka, and vector database workloads, Cilium helps with:

- High-throughput pod communication.
- Controlled egress to model registries, object storage, and external APIs.
- Flow-level visibility for noisy-neighbor and dependency analysis.
- Policy isolation between training, inference, and data-ingestion tenants.
- Bandwidth management for bursty data transfer workloads.  

### Egress control

Use Cilium Egress Gateway to route selected pod traffic through predictable source IPs or controlled egress paths—useful for partner allowlists, regulated outbound traffic, and SaaS integrations. Cilium lists Egress Gateway as a first-class use case. 
  
## Testing strategy

### Connectivity tests

```bash
cilium connectivity test
cilium connectivity test --multi-cluster <context-name>
```

### Policy tests

Use a temporary test workload:

```bash
kubectl run policy-test \
  --image=curlimages/curl \
  --namespace=payments \
  --restart=Never \
  --rm -it -- sh
```

Then verify allowed and denied paths:

```bash
curl -v http://checkout.payments.svc.cluster.local:8080/api/v1/checkout
curl -v http://checkout.payments.svc.cluster.local:8080/admin
```

Expected result: the approved HTTP path succeeds; unapproved paths are denied.

### Hubble validation

```bash
hubble observe --namespace payments
hubble observe --verdict DROPPED
hubble observe --protocol http
```

Hubble is designed for inspecting network flows and policy verdicts, including identity-aware L3/L4/DNS flow visibility. [cilium](https://cilium.io/)

## Observability and monitoring

### Metrics

Enable Prometheus metrics for both Cilium and Hubble. Cilium documentation provides dedicated guidance for Prometheus and Grafana, Cilium metrics, Hubble metrics, and Cluster Mesh API server metrics. [docs.cilium](https://docs.cilium.io/en/stable/)

Key alert categories:

- Agent readiness and restarts.
- Operator availability.
- Endpoint regeneration failures.
- Policy calculation errors.
- IPAM exhaustion.
- Hubble Relay availability.
- Dropped-flow spikes.
- Encryption handshake failures.
- Cluster Mesh session or route errors.

### Useful PromQL examples

```promql
sum(rate(cilium_drop_count_total[5m])) by (reason)
```

```promql
sum(rate(cilium_forward_count_total[5m])) by (direction)
```

```promql
sum(cilium_endpoint_state) by (state)
```

```promql
sum(rate(hubble_drop_total[5m])) by (verdict, destination_namespace)
```

### Dashboards

Minimum production dashboards:

- Cilium agent and operator health.
- Network throughput, packet drops, and latency indicators.
- Policy verdicts: forwarded versus dropped.
- DNS resolution and external egress.
- IPAM utilization.
- Encryption status.
- Cluster Mesh health.
- Hubble Relay throughput and errors.

## Logging and audit

Enable Hubble flow export to a durable log platform. Flow logs should include:

- Source and destination identity.
- Namespace and workload labels.
- Verdict: forwarded or dropped.
- L3/L4 metadata.
- DNS queries where applicable.
- HTTP method, path, and response code where L7 visibility is enabled.
- Policy name or policy revision where available.

Cilium supports identity-aware L3/L4/DNS flow logs and advanced protocol visibility, while Hubble provides flow inspection, service maps, and exporter configuration. [cilium](https://cilium.io/)

**Important:** L7 visibility adds operational value but also increases resource consumption and can introduce privacy/compliance considerations. Enable it selectively for sensitive or high-risk paths.

## Security hardening

### Platform controls

- Use least-privilege RBAC for Cilium components.
- Restrict who can create or modify `CiliumNetworkPolicy` and `CiliumClusterwideNetworkPolicy`.
- Protect the Cilium ConfigMap; changes can alter dataplane behavior.
- Use GitOps with peer review for all Cilium configuration.
- Pin Helm charts and images by version or digest.
- Enable image scanning and admission controls.
- Restrict privileged pod access around Cilium components.
- Use TLS for Hubble and Cluster Mesh communications.
- Rotate certificates automatically where possible.

Cilium’s documentation includes guidance on securing networks, restricting privileged Cilium pod access, and a formal threat model. [docs.cilium](https://docs.cilium.io/en/stable/)

### Network security baseline

1. Start with default-deny in sensitive namespaces.
2. Allow only required namespace-to-namespace traffic.
3. Constrain DNS egress.
4. Apply FQDN-based external egress controls.
5. Use L7 policy for high-value HTTP/gRPC APIs.
6. Enable WireGuard or IPsec encryption for traffic crossing untrusted networks.
7. Use host firewall policies for node-level protection.
8. Audit denied flows continuously.

## Performance tuning

### Start with the right datapath

Choose the datapath based on environment:

- Native routing is often preferred where the underlying network supports pod CIDR routing.
- Tunneling, such as VXLAN or Geneve, is useful where underlying network constraints prevent direct routing.
- Kube-proxy replacement should be evaluated carefully, especially for large Service counts and high connection churn.

Cilium provides a performance and scalability tuning guide, CNI performance benchmarks, and scalability documentation. [docs.cilium](https://docs.cilium.io/en/stable/)

### Tuning checklist

- Right-size Cilium agent CPU and memory based on endpoint count and policy complexity.
- Monitor eBPF map pressure and Service LB map sizing.
- Avoid excessive L7 policies on extremely high-traffic paths unless needed.
- Use bandwidth manager where appropriate for tenant fairness.
- Test MTU, checksum offload, and NIC driver behavior.
- Benchmark with production-like traffic patterns, not only synthetic ping tests.
- Validate behavior under node failure, agent restart, and rolling upgrade conditions.

## Common failure scenarios

| Symptom | Likely cause | First diagnostics |
|---|---|---|
| Pod cannot reach Service | Kube-proxy replacement, endpoint, or policy issue | `cilium status`, `cilium connectivity test`, Hubble flows |
| Intermittent DNS failures | DNS policy, DNS proxy, upstream resolver issue | `hubble observe --protocol dns`, Cilium agent logs |
| New pods have no network | IPAM exhaustion or CNI wiring failure | `cilium status`, CiliumNode/IPAM metrics, agent logs |
| Policy unexpectedly blocks traffic | Missing label selector, namespace mismatch, deny rule | `cilium policy get`, Hubble dropped flows |
| High CPU on Cilium agents | Large policy set, high endpoint churn, L7 proxy load | Agent metrics, endpoint count, policy revision rate |
| Cross-node traffic fails | Routing, tunnel, firewall, or MTU mismatch | Node routes, tunnel status, packet captures |
| Cluster Mesh service unavailable | Certificate, connectivity, or cluster configuration issue | Cluster Mesh status, Hubble, agent/operator logs |
| Upgrade causes connection resets | L7 proxy restart or incompatible configuration | Upgrade notes, preflight validation, Hubble |

Cilium’s troubleshooting documentation covers component and cluster health, Hubble flow observation, connectivity, policy, etcd/kvstore, Cluster Mesh, service mesh, and a symptom library. [docs.cilium](https://docs.cilium.io/en/stable/)

## Upgrades

Treat Cilium upgrades as control-plane and dataplane changes, not routine application deployments.

### Upgrade procedure

1. Read the version-specific upgrade notes.
2. Upgrade to the latest patch release of the current minor version.
3. Back up Helm values, Cilium CRDs, policies, and relevant custom resources.
4. Run the required preflight check.
5. Confirm preflight DaemonSet and validation Deployment readiness.
6. Delete the preflight resources.
7. Upgrade using a version-controlled values file.
8. Validate agents, operator, connectivity, policies, Hubble, and encryption.
9. Roll out to non-production first, then production in controlled batches.

Cilium states that the tested upgrade and rollback path is between consecutive minor releases, and recommends updating to the latest patch release before a minor upgrade. [docs.cilium](https://docs.cilium.io/en/stable/operations/upgrade/)

### Preflight example

```bash
helm template cilium/cilium \
  --version 1.20.3 \
  --namespace kube-system \
  --set preflight.enabled=true \
  --set agent=false \
  --set operator.enabled=false \
  > cilium-preflight.yaml

kubectl apply -f cilium-preflight.yaml
kubectl get ds -n kube-system | grep cilium
kubectl get deploy -n kube-system cilium-pre-flight-check
```

Once preflight pods match the number of Cilium agents and the validation Deployment is ready, remove preflight and proceed. [docs.cilium](https://docs.cilium.io/en/stable/operations/upgrade/)

### Rollback

```bash
helm history cilium --namespace kube-system
helm rollback cilium <revision> --namespace kube-system
```

Be cautious if the newer version has already created resources or enabled new features; Cilium warns that rollback after consuming new-version functionality may require additional preparation. [docs.cilium](https://docs.cilium.io/en/stable/operations/upgrade/)

## Backup and recovery

Cilium itself is stateless in the sense that agents reprogram eBPF from Kubernetes state, but its configuration and policy state are critical.

### What to back up

- Helm release values.
- Cilium CRDs and all Cilium custom resources.
- `CiliumNetworkPolicy` and `CiliumClusterwideNetworkPolicy` objects.
- `CiliumNode`, `CiliumEndpoint`, and identity-related resources where applicable.
- Cluster Mesh configuration and certificates.
- Hubble configuration and exporters.
- Kubernetes etcd backups, since Cilium state is ultimately tied to cluster state.

### Recovery approach

1. Restore Kubernetes control plane and etcd first.
2. Reinstall or restore Cilium using the pinned Helm chart and values.
3. Restore Cilium CRDs and custom resources.
4. Validate identity, policy, IPAM, and connectivity.
5. Run `cilium connectivity test` before admitting production workloads.

For identity-store migrations, Cilium documents both a one-off migration tool and a “Double Write” mode that enables a more gradual migration with rollback options. [docs.cilium](https://docs.cilium.io/en/stable/operations/upgrade/)

## Scaling and capacity planning

Plan for:

- Number of nodes.
- Pods per node.
- Total endpoints.
- Services, backends, and Service VIPs.
- Network policy count and complexity.
- L7 policy usage.
- Hubble flow rate.
- IPAM pool size.
- Cluster Mesh scale.
- Encryption overhead.

Cilium’s operator exposes IPAM-related metrics such as available, used, and needed IPs, which are useful for capacity alerting. [docs.cilium](https://docs.cilium.io/en/stable/operations/upgrade/)

## Production readiness checklist

- [ ] Supported kernel, OS, and Kubernetes versions validated.
- [ ] Cilium installed through Helm or GitOps with version-controlled values.
- [ ] `cilium status` and `cilium connectivity test` automated in CI.
- [ ] Hubble Relay, metrics, dashboards, and alerts deployed.
- [ ] Flow logs exported to durable storage.
- [ ] Default-deny policies applied to sensitive namespaces.
- [ ] DNS and external egress restricted.
- [ ] Encryption enabled where traffic crosses untrusted networks.
- [ ] Cilium RBAC and policy-change controls restricted.
- [ ] Upgrade runbook and rollback procedure tested.
- [ ] Capacity and IPAM alerts configured.
- [ ] Cluster Mesh certificates and renewal process managed.
- [ ] Chaos tests executed for agent restart, node loss, and policy rollout.
- [ ] Backup and restore tested end to end.

## Operational responsibilities

A platform team running Cilium should own:

- CNI lifecycle, upgrades, and compatibility testing.
- Network policy guardrails and golden policies.
- Hubble observability and flow-log retention.
- IPAM capacity planning.
- Cluster Mesh certificate and connectivity management.
- Security review of policy changes.
- Performance benchmarking and capacity testing.
- Incident response for dataplane and policy failures.
- Integration testing with Gateway API, ingress, service mesh, and runtime security tools.

Cilium is a strong default for platform teams that want to consolidate Kubernetes networking, security, and observability into one eBPF-based layer—but it requires disciplined operations because it sits directly in the packet path. Its CNCF Graduated status, broad production adoption, and extensive operational documentation make it a credible foundation for multi-cloud, security-sensitive, and high-throughput Kubernetes platforms. [cilium](https://cilium.io/)