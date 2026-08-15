# Crossplane  

Crossplane is a Kubernetes-based control-plane framework for platform engineering. Instead of writing custom Kubernetes controllers, you define business-friendly APIs (such as `App`, `Database`, or `Environment`) and let Crossplane compose and continuously reconcile the underlying Kubernetes or cloud resources.

It is especially useful for building an internal developer platform: developers request a product-level abstraction, while the platform team controls the actual cloud resources, defaults, guardrails, credentials, and lifecycle behavior. Crossplane is a CNCF project and is built on Kubernetes APIs, RBAC, and the Kubernetes resource model.

## What problem it solves

Traditional infrastructure-as-code tools such as Terraform describe *how* to create infrastructure, but they generally do not provide a continuously reconciled, Kubernetes-native API for application teams to consume.

With Crossplane, an application team can request:

```yaml
apiVersion: platform.example.com/v1alpha1
kind: ManagedApp
metadata:
  name: payments
spec:
  size: small
  environment: dev
```

The platform team decides that `ManagedApp` means a Deployment, Service, ConfigMap, HPA, network policy, database, DNS record, and observability configuration. Crossplane creates and maintains those resources, correcting drift when they diverge from the desired state.

## Architecture

```text
+--------------------------------------------------------------+
|                       Kubernetes Cluster                      |
|                                                               |
|  Developer / CI / GitOps / AI agent                           |
|        |                                                      |
|        | kubectl apply App / Database / Environment           |
|        v                                                      |
|  +----------------------+      +---------------------------+  |
|  | Kubernetes API Server | ---> | Crossplane Composition   |  |
|  | CRDs: App, Database   |     | Engine / Function Pipeline|  |
|  +----------------------+      +---------------------------+  |
|                                          |                    |
|                                          v                    |
|                     +------------------------------------+    |
|                     | Desired composed resources         |    |
|                     | Deployment, Service, ConfigMap, MR |    |
|                     +------------------------------------+    |
|                            |                |                 |
|                            v                v                 |
|              +----------------+   +------------------------+  |
|              | Kubernetes     |   | Provider controllers   |  |
|              | controllers    |   | AWS / Azure / GCP /    |  |
|              |                |   | GitHub / DNS providers |  |
|              +----------------+   +------------------------+  |
|                                          |                    |
+------------------------------------------|--------------------+
                                           v
                              External cloud / SaaS systems
```

Internally, Crossplane watches XRs, invokes the configured composition functions, applies the resulting composed resources, observes their status, and writes relevant status back to the XR. If an external resource drifts, the provider controller reconciles it back toward the desired state.

