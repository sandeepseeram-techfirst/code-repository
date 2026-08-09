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
