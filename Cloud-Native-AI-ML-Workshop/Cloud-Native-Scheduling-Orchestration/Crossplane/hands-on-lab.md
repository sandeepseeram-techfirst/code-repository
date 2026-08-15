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

## Install Crossplane

Install the Crossplane Helm chart:

```bash
helm repo add crossplane-stable https://charts.crossplane.io/stable
helm repo update

helm install crossplane \
  crossplane-stable/crossplane \
  --namespace crossplane-system \
  --create-namespace \
  --wait
```

Validate installation:

```bash
kubectl get pods -n crossplane-system
kubectl get crds | grep crossplane
```

Expected output:

```text
NAME                                       READY   STATUS    RESTARTS   AGE
crossplane-...                             1/1     Running   0          1m
crossplane-rbac-manager-...                1/1     Running   0          1m
```

You should see CRDs such as:

```text
compositions.apiextensions.crossplane.io
compositeresourcedefinitions.apiextensions.crossplane.io
providerconfigs.aws.m.upbound.io
providers.pkg.crossplane.io
functions.pkg.crossplane.io
```
