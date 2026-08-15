## Prerequisites

For the local lab, use:

- Docker or an equivalent container runtime
- A local Kubernetes cluster: `kind`, `k3d`, `minikube`, or Rancher Desktop
- `kubectl`
- At least 2 GB RAM available to the cluster
- Optional: cloud credentials if you want to create real cloud resources

The official composition quickstart requires a Kubernetes cluster with at least 2 GB RAM and Crossplane v2 installed.  

Create a local cluster with `kind`:

```bash
kind create cluster --name crossplane-lab
kubectl cluster-info
kubectl get nodes
```

Expected output should show a Ready control-plane node:

```text
NAME                          STATUS   ROLES           AGE   VERSION
crossplane-lab-control-plane  Ready    control-plane   1m    v1.x.x
```

