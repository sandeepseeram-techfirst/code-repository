# Cilium: Cloud-Native Architecture Guide

Cilium is a CNCF Graduated, eBPF-based Kubernetes CNI and networking platform that provides high-performance pod networking, identity-aware security policy, load balancing, encryption, and deep network observability. Its central idea is to implement much of the Kubernetes data plane directly in the Linux kernel using eBPF, reducing reliance on iptables and sidecar proxies.

## Why Cilium matters

For a production platform, Cilium is not merely “another CNI.” It consolidates several traditionally separate functions:

| Capability | Cilium component / feature | Typical alternative |
|---|---|---|
| Pod-to-pod networking | Cilium CNI | Calico, Flannel, cloud CNI |
| Service load balancing | eBPF kube-proxy replacement | kube-proxy + iptables/IPVS |
| Network policy | Kubernetes NetworkPolicy, CiliumNetworkPolicy | Calico policy, Istio authorization |
| L7-aware policy | HTTP, gRPC, DNS-aware policies | Service mesh sidecars |
| Flow visibility | Hubble | VPC flow logs, manual tcpdump |
| Encryption | WireGuard or IPsec | Service mesh mTLS |
| Multi-cluster connectivity | Cluster Mesh | VPN, service mesh federation |
| Runtime security | Tetragon | Falco, custom eBPF agents |

Cilium is positioned for high-performance networking, kube-proxy replacement, Cluster Mesh, egress control, Gateway API, service mesh, identity-aware flow logs, transparent encryption, and runtime security.  

## Core concepts

### eBPF dataplane

eBPF programs are safely loaded into the Linux kernel and attached to networking hooks. Cilium uses them to classify, route, load-balance, encrypt, and enforce policy on packets with minimal per-packet overhead.

Practical consequence: instead of traversing long iptables rule chains for every Service lookup, Cilium can program efficient eBPF maps and datapath logic. This is why Cilium is often selected for high-throughput east-west traffic, large clusters, and latency-sensitive platforms.

### Security identities

Cilium assigns a security identity to workloads based on Kubernetes labels, namespaces, service accounts, and other selected metadata. Policies are enforced against these identities rather than unstable pod IPs.

Example: a policy can allow `app=frontend` in namespace `shop` to call `app=checkout` in namespace `payments`, regardless of pod rescheduling or IP changes.

### Policy enforcement

Cilium supports:

- Kubernetes `NetworkPolicy` for portable L3/L4 controls.
- `CiliumNetworkPolicy` for richer Cilium-specific capabilities.
- `CiliumClusterwideNetworkPolicy` for cluster-wide controls.
- DNS-based egress policy.
- HTTP/gRPC-aware L7 policy.
- Deny rules and host firewall policies. 

### Hubble

Hubble is Cilium’s observability layer. It exposes network flows, service dependencies, policy verdicts, drops, DNS activity, and protocol-level visibility through the CLI, UI, metrics, and flow export.  

## Reference architecture

```text
                 Kubernetes Control Plane
                            |
        +-------------------+-------------------+
        |                                       |
   Cilium Operator                        Cilium Agents
   - IPAM reconciliation                  DaemonSet on every node
   - CiliumNode / IPAM state              - eBPF program loading
   - CRD lifecycle                        - identity + policy maps
   - Cluster Mesh support                 - Service LB / kube-proxy replacement
                                          - Hubble local observer
        |                                       |
        +-------------------+-------------------+
                            |
                    Linux kernel / eBPF
                            |
        Pod veth/netkit dataplane | node interfaces
                            |
             Hubble Relay -> Prometheus / Grafana / Loki
```

### Main components

- **cilium-agent**: A DaemonSet pod on every node. It programs eBPF, manages endpoint identities and policies, participates in service load balancing, and exposes local APIs.
- **cilium-operator**: Handles cluster-scoped reconciliation, IPAM, node lifecycle, and operator-level tasks.
- **eBPF maps and programs**: Kernel-resident state and datapath logic for routing, NAT, load balancing, policy, and encryption.
- **Hubble**: Local flow observer; Hubble Relay aggregates flows across nodes.
- **Hubble UI**: Visual service map and flow inspection.
- **Cilium CLI**: Installation, status, connectivity, and troubleshooting utility.
- **CRDs**: `CiliumNetworkPolicy`, `CiliumClusterwideNetworkPolicy`, `CiliumEndpoint`, `CiliumNode`, `CiliumIdentity`, and others.  

## Where it fits in the ecosystem

Cilium is a foundational platform layer rather than an application-layer add-on.

```text
Application / AI / data workloads
        |
Service mesh, Gateway API, ingress
        |
Cilium: CNI, policy, LB, encryption, Hubble
        |
Kubernetes: scheduler, kubelet, API server, etcd
        |
Linux nodes / cloud VMs / bare metal
```

It integrates naturally with:

- **Prometheus and Grafana** for metrics and dashboards.
- **Loki, Elasticsearch, or Splunk** for Hubble flow logs.
- **OpenTelemetry** for broader tracing and telemetry workflows.
- **Gateway API** for modern ingress and L7 routing.
- **Cert-manager** for certificate lifecycle management.
- **Tetragon** for eBPF-based runtime security.
- **Cluster Mesh** for multi-cluster and hybrid-cloud connectivity.  