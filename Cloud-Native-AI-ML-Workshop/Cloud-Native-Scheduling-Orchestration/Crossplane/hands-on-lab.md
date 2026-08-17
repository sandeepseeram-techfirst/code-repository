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

### Install a composition function

Use the Go templating function for this lab. It is familiar if you have used Helm templates and supports conditional logic.  

Save as `02-function.yaml`:

```yaml
apiVersion: pkg.crossplane.io/v1
kind: Function
metadata:
  name: crossplane-contrib-function-go-templating
spec:
  package: xpkg.crossplane.io/crossplane-contrib/function-go-templating:v0.9.2
```

Apply and validate:

```bash
kubectl apply -f 02-function.yaml
kubectl get functions
```

Expected output:

```text
NAME                                            INSTALLED   HEALTHY   PACKAGE
crossplane-contrib-function-go-templating       True        True      xpkg.crossplane.io/...
```





### Create the composition

Save as `03-app-composition.yaml`:

```yaml
apiVersion: apiextensions.crossplane.io/v1
kind: Composition
metadata:
  name: app-templated-yaml
spec:
  compositeTypeRef:
    apiVersion: example.crossplane.io/v1
    kind: App
  mode: Pipeline
  pipeline:
    - step: create-deployment-and-service
      functionRef:
        name: crossplane-contrib-function-go-templating
      input:
        apiVersion: gotemplating.fn.crossplane.io/v1beta1
        kind: GoTemplate
        source: Inline
        inline:
          template: |
            ---
            apiVersion: apps/v1
            kind: Deployment
            metadata:
              annotations:
                gotemplating.fn.crossplane.io/composition-resource-name: deployment
              labels:
                example.crossplane.io/app: {{ .observed.composite.resource.metadata.name }}
            spec:
              replicas: 2
              selector:
                matchLabels:
                  example.crossplane.io/app: {{ .observed.composite.resource.metadata.name }}
              template:
                metadata:
                  labels:
                    example.crossplane.io/app: {{ .observed.composite.resource.metadata.name }}
                spec:
                  containers:
                    - name: app
                      image: {{ .observed.composite.resource.spec.image }}
                      ports:
                        - containerPort: 80
            ---
            apiVersion: v1
            kind: Service
            metadata:
              annotations:
                gotemplating.fn.crossplane.io/composition-resource-name: service
              labels:
                example.crossplane.io/app: {{ .observed.composite.resource.metadata.name }}
            spec:
              selector:
                example.crossplane.io/app: {{ .observed.composite.resource.metadata.name }}
              ports:
                - protocol: TCP
                  port: 8080
                  targetPort: 80
            ---
            apiVersion: example.crossplane.io/v1
            kind: App
            status:
              replicas: {{ get (getComposedResource . "deployment").status "availableReplicas" | default 0 }}
              address: {{ get (getComposedResource . "service").spec "clusterIP" | default "" | quote }}
```

Purpose of key fields:

- `compositeTypeRef` binds this composition to `App` resources.
- `mode: Pipeline` enables Crossplane v2 function pipelines.
- `functionRef` selects the installed function.
- The template emits a Deployment, Service, and status update.
- The Deployment and Service labels ensure the Service selects the correct pods.

Apply it:

```bash
kubectl apply -f 03-app-composition.yaml
kubectl get composition app-templated-yaml
```

### Consume the API

Save as `04-my-app.yaml`:

```yaml
apiVersion: example.crossplane.io/v1
kind: App
metadata:
  name: my-app
  namespace: default
spec:
  image: nginx
```

Apply it:

```bash
kubectl apply -f 04-my-app.yaml
kubectl get app my-app
```

Expected output:

```text
NAME      SYNCED   READY   COMPOSITION             AGE
my-app    True     True    app-templated-yaml      1m
```

Inspect generated resources:

```bash
kubectl get deploy,service -l example.crossplane.io/app=my-app
```

Expected output:

```text
NAME                              READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/my-app-xxxxx      2/2     2            2           1m

NAME                    TYPE        CLUSTER-IP     PORT(S)    AGE
service/my-app-yyyyy    ClusterIP   10.96.x.x      8080/TCP   1m
```

Validate reconciliation:

```bash
kubectl describe app my-app
kubectl get deployment -l example.crossplane.io/app=my-app -o yaml
```

Now change the image:

```bash
kubectl patch app my-app --type merge -p '{"spec":{"image":"nginx:1.27"}}'
kubectl get deployment -l example.crossplane.io/app=my-app \
  -o jsonpath='{.items[0].spec.template.spec.containers[0].image}'
```

Expected output:

```text
nginx:1.27
```

This proves continuous reconciliation: the XR is the source of truth, and the Deployment is updated to match it.  

Delete the XR:

```bash
kubectl delete app my-app
kubectl get deploy,service -l example.crossplane.io/app=my-app
```

Expected output:

```text
No resources found
```

Crossplane deletes the composed Deployment and Service when the owning `App` is deleted.  

## Lab 2: Add a real cloud managed resource

This lab shows how Crossplane extends beyond Kubernetes into external infrastructure. The official example creates an AWS S3 bucket through a `Bucket` managed resource. 

> Use a disposable AWS account or tightly scoped credentials for this section. Do not use an administrator role.

### Install the S3 provider

Save as `05-aws-s3-provider.yaml`:

```yaml
apiVersion: pkg.crossplane.io/v1
kind: Provider
metadata:
  name: crossplane-contrib-provider-aws-s3
spec:
  package: xpkg.crossplane.io/crossplane-contrib/provider-aws-s3:v2.0.0
```

Apply it:

```bash
kubectl apply -f 05-aws-s3-provider.yaml
kubectl get providers
```

Expected output:

```text
NAME                                       INSTALLED   HEALTHY   PACKAGE
crossplane-contrib-provider-aws-s3         True        True      ...
crossplane-contrib-provider-family-aws     True        True      ...
```

The S3 provider installs the AWS family provider, which manages AWS authentication for related providers.

### Store credentials securely

Create `aws-credentials.ini` locally:

```ini
[default]
aws_access_key_id = YOUR_ACCESS_KEY_ID
aws_secret_access_key = YOUR_SECRET_ACCESS_KEY
```

Create the Kubernetes Secret:

```bash
kubectl create secret generic aws-secret \
  --namespace crossplane-system \
  --from-file=creds=./aws-credentials.ini

rm aws-credentials.ini
```

Purpose:

- Credentials never belong in a Git repository.
- The provider reads them from a Kubernetes Secret.
- In production, prefer an external secrets manager or workload identity rather than long-lived static keys.

### Configure the provider

Save as `06-aws-provider-config.yaml`:

```yaml
apiVersion: aws.m.upbound.io/v1beta1
kind: ClusterProviderConfig
metadata:
  name: default
spec:
  credentials:
    source: Secret
    secretRef:
      namespace: crossplane-system
      name: aws-secret
      key: creds
```

Apply it:

```bash
kubectl apply -f 06-aws-provider-config.yaml
kubectl get clusterproviderconfigs
```




Delete the bucket:

```bash
kubectl delete buckets.s3.aws.m.upbound.io crossplane-lab-bucket-xxxxx
```

Crossplane deletes the corresponding AWS S3 bucket. Delete cloud resources before uninstalling providers or destroying the cluster; otherwise cleanup cannot occur automatically.  

## Testing strategy

### Functional tests

Test the platform API, not just generated YAML:

```bash
kubectl apply -f 04-my-app.yaml
kubectl wait --for=condition=Ready app/my-app --timeout=180s
kubectl get deploy,service -l example.crossplane.io/app=my-app
```

### Drift test

Manually scale the generated Deployment:

```bash
DEPLOY=$(kubectl get deploy -l example.crossplane.io/app=my-app -o name)
kubectl scale "$DEPLOY" --replicas=1
sleep 20
kubectl get "$DEPLOY"
```

Expected behavior: Crossplane restores the desired replica count to 2 because the composition defines two replicas.

### Deletion test

```bash
kubectl delete app my-app
kubectl get deploy,service -l example.crossplane.io/app=my-app
```

Expected behavior: both composed resources disappear.

### Cloud resource test

For the AWS bucket:

```bash
kubectl wait --for=condition=Ready bucket.s3.aws.m.upbound.io/<bucket-name> --timeout=300s
kubectl get bucket.s3.aws.m.upbound.io/<bucket-name> -o jsonpath='{.status.atProvider}'
```

Validate in AWS that the bucket exists and has the expected region and tags.

## Troubleshooting

### XR remains not ready

Check the XR:

```bash
kubectl describe app my-app
kubectl get app my-app -o yaml
```

Look at `status.conditions`, especially `Synced`, `Ready`, and `ComposeResources`.

Check composition events:

```bash
kubectl describe composition app-templated-yaml
```

Common causes:

- Function not installed or unhealthy.
- Template syntax error.
- Missing RBAC permission for Crossplane to create a composed resource type.
- Invalid field path or unsupported template function.

### Provider is unhealthy

```bash
kubectl get providers
kubectl describe provider crossplane-contrib-provider-aws-s3
kubectl get pods -n crossplane-system
kubectl logs -n crossplane-system deploy/crossplane -f
```

Common causes:

- Package registry unreachable.
- Provider image pull failure.
- Incompatible Crossplane and provider versions.
- Insufficient cluster resources.

### Managed resource is not synced

```bash
kubectl describe bucket.s3.aws.m.upbound.io <bucket-name>
kubectl get clusterproviderconfig default -o yaml
kubectl get secret aws-secret -n crossplane-system
```

Common causes:

- Invalid or expired cloud credentials.
- Provider configuration missing or misnamed.
- Cloud API permission denied.
- Resource name collision, especially for globally unique names such as S3 buckets.
- Region unavailable or quota exceeded.

### Function pipeline fails

```bash
kubectl get functions
kubectl describe function crossplane-contrib-function-go-templating
kubectl logs -n crossplane-system deploy/crossplane -f
```

Use a small composition first, then add complexity incrementally. For nontrivial logic, prefer a dedicated function implementation over a very large inline template.

## Security model

Crossplane inherits Kubernetes RBAC, authentication, audit logging, and namespace isolation. It extends Kubernetes’ control model beyond containers, allowing the same Kubernetes security ecosystem to govern infrastructure APIs.  

Apply these controls:

- Use Kubernetes RBAC to restrict who can create or modify XRs, compositions, providers, and provider configurations.
- Treat XRDs and Compositions as privileged platform artifacts; only platform engineers should manage them.
- Give developers access only to namespaced XRs, not directly to providers or cloud managed resources.
- Use workload identity, OIDC federation, or short-lived credentials instead of static access keys where possible.
- Store secrets in Kubernetes Secrets only as a baseline; integrate External Secrets Operator, Vault, or a cloud secrets manager for production.
- Enable Kubernetes audit logs and alert on changes to `Provider`, `ProviderConfig`, `ClusterProviderConfig`, `Composition`, and `XRD`.
- Pin provider and function package versions; avoid `latest` in production.
- Use admission policies, such as Kyverno or OPA Gatekeeper, to enforce naming, labels, regions, encryption, and ownership tags.

## Scaling and production operations

### Control-plane scaling

Crossplane runs as Kubernetes workloads, so scale and operate it like other Kubernetes control-plane components:

- Start with resource requests and limits based on observed CPU, memory, and API request rates.
- Scale provider replicas when provider controllers become saturated.
- Separate platform control planes by blast radius: for example, development, staging, production, or regulated workloads.
- Avoid placing every team and every cloud account under one unbounded control plane.

### GitOps operating model

Recommended flow:

```text
Platform repo -> XRDs, Compositions, Functions, Providers
App team repo -> App / Database / Environment XRs
CI -> lint, validate, test compositions
Argo CD / Flux -> apply platform and tenant manifests
Observability -> Crossplane metrics, Kubernetes events, cloud audit logs
```

Keep platform APIs and implementations in separate repositories or at least separate directories. This preserves the contract between platform engineers and application teams.

### Observability

Monitor:

- Crossplane pod CPU, memory, restarts, and API latency.
- XR reconciliation latency and failure rate.
- Provider reconciliation errors and external API rate limits.
- Number of XRs, composed resources, providers, and functions.
- Kubernetes events for failed composition or provider operations.
- Cloud-side audit logs for every mutation performed by provider credentials.

### Upgrade strategy

- Upgrade one non-production control plane first.
- Read release notes and EOL dates before upgrading; Crossplane publishes maintained release and end-of-life dates in its repository.  
- Test provider upgrades independently from Crossplane core upgrades.
- Back up Kubernetes resources: XRDs, Compositions, Functions, Providers, ProviderConfigs, and XRs.
- Verify that all managed resources are `SYNCED` and `READY` before and after upgrade.

## Real-world use cases

### Internal developer platform

Expose `Application`, `Database`, `Cache`, `Bucket`, and `Environment` APIs. Developers self-service standard stacks while the platform team enforces security, cost, and reliability defaults.

### Multi-cloud abstraction

Create a `PostgresInstance` API backed by different providers per environment or business unit. The consumer API remains stable while the implementation changes.

### SaaS and developer tooling automation

Use providers or custom resources to manage GitHub repositories, CI/CD resources, DNS, certificates, observability tenants, or external SaaS configuration.

### Regulated environments

Encode mandatory controls—encryption, private networking, retention, tagging, approval workflows—directly into platform APIs. Developers cannot easily create noncompliant infrastructure if the API does not expose that capability.

### AI platform operations

Expose `ModelEndpoint`, `VectorDatabase`, `InferenceDeployment`, or `TrainingJob` APIs. Crossplane can orchestrate Kubernetes workloads and external services while policy and quota controls remain centralized.

## Strengths and limitations

| Area | Strengths | Limitations |
|---|---|---|
| Platform APIs | Kubernetes-native, declarative, auditable, self-service | Requires disciplined API design |
| Reconciliation | Continuous drift correction and lifecycle management | Debugging reconciliation can be harder than reading a Terraform plan |
| Extensibility | Providers, functions, packages, multiple configuration languages | Ecosystem maturity varies by provider |
| Developer experience | Simple product-like APIs | Poorly designed XRDs can become confusing or overly restrictive |
| Multi-cloud | Common control model across providers | Does not eliminate provider-specific differences or cost models |
| Operations | GitOps and Kubernetes-native integration | Requires Kubernetes expertise and operational maturity |
| Security | Inherits Kubernetes RBAC and audit controls | Provider credentials and package supply chain need strong governance |

## Alternatives and trade-offs

| Tool | Best fit | Main trade-off |
|---|---|---|
| Terraform / OpenTofu | General-purpose infrastructure provisioning, strong ecosystem | Usually plan/apply oriented rather than a continuously reconciled platform API |
| Pulumi | Teams preferring general-purpose programming languages | Less Kubernetes-native API abstraction by default |
| Helm | Packaging Kubernetes applications | Not designed as a general external-infrastructure control plane |
| Kustomize | Kubernetes manifest overlays | No external resource reconciliation or product-level API |
| Kro | Kubernetes-native resource composition with CEL | Narrower scope than Crossplane’s provider ecosystem |
| Custom controllers | Highly specialized control logic | High engineering and maintenance cost |
| Cloud-native IaC services | Deep integration with one cloud | Reduces cloud neutrality and portability |

## When to use Crossplane

Use Crossplane when:

- You are building an internal developer platform on Kubernetes.
- You need stable, product-like APIs for application teams.
- You want GitOps-friendly, declarative infrastructure with continuous reconciliation.
- You need a consistent control model across Kubernetes and external systems.
- You want to centralize guardrails, defaults, credentials, and lifecycle policy.
- You have platform engineering capacity to design and operate APIs and compositions.

Avoid Crossplane when:

- You only need occasional, manually approved infrastructure provisioning.
- Your team has no Kubernetes operational experience.
- You need a single-cloud, deeply managed service with minimal platform overhead.
- Your primary need is complex application packaging rather than infrastructure and platform APIs.
- You cannot operate provider credentials, upgrades, RBAC, observability, and incident response properly.

## Key insights

Technically, Crossplane turns Kubernetes into a framework for building control planes. Its main architectural advantage is separation between *what users request* and *how the platform implements it*.  

From a business perspective, it reduces repeated infrastructure work, standardizes delivery, improves auditability, and enables safer self-service. The cost is real: successful adoption requires strong API design, Kubernetes competence, secrets management, package governance, and production-grade observability.

For a cloud-agnostic SRE or platform team, a pragmatic starting point is to build one narrow API—such as `App` or `ObjectStore`—prove its reconciliation, deletion, security, and observability behavior, then expand only after the operating model is reliable.