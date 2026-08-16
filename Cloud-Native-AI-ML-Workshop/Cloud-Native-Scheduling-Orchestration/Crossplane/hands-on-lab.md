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

## Lab 1: Build an `App` platform API

This lab creates a developer-facing `App` API. Creating an `App` produces a Deployment and Service. This demonstrates Crossplane’s central idea: expose a simple, governed API while hiding implementation details.
  
### Define the API schema

Save as `01-app-xrd.yaml`:

```yaml
apiVersion: apiextensions.crossplane.io/v2
kind: CompositeResourceDefinition
metadata:
  name: apps.example.crossplane.io
spec:
  scope: Namespaced
  group: example.crossplane.io
  names:
    kind: App
    plural: apps
  versions:
    - name: v1
      served: true
      referenceable: true
      schema:
        openAPIV3Schema:
          type: object
          properties:
            spec:
              type: object
              properties:
                image:
                  type: string
                  description: Container image for the application.
              required:
                - image
            status:
              type: object
              properties:
                replicas:
                  type: integer
                address:
                  type: string
```

Purpose:

- `group`, `kind`, and `plural` define the Kubernetes API.
- `spec` is the developer input contract.
- `status` is platform-owned output, such as available replicas and service address.
- `scope: Namespaced` allows teams to create apps in their own namespaces.

Apply it:

```bash
kubectl apply -f 01-app-xrd.yaml
kubectl get xrd apps.example.crossplane.io
```

Expected output:

```text
NAME                        ESTABLISHED   OFFERED   AGE
apps.example.crossplane.io  True          True      20s
```

