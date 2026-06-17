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