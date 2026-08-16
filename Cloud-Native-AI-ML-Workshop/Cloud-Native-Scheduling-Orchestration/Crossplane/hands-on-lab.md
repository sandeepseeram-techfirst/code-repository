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

