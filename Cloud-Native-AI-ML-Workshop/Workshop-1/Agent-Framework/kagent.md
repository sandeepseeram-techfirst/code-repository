# kagent: Kubernetes-Native Agentic AI Runtime

**kagent** is an open-source, Kubernetes-native runtime for deploying, operating, observing, and governing AI agents. It treats agents as first-class Kubernetes workloads—defined declaratively as CRDs, deployed with Helm/GitOps, secured with RBAC and service mesh controls, and observed through the same OpenTelemetry/Prometheus stack used for conventional services.

## What It Is

kagent is a **CNCF Sandbox project** created by Solo.io, designed to bring agentic AI directly into the Kubernetes ecosystem rather than treating agents as a separate platform bolted onto infrastructure. Its core premise: if your platform team already runs pods, services, RBAC, and GitOps, AI agents should follow the same operational model—not require learning a new toolchain.

The project supports multiple LLM providers (OpenAI, Anthropic, Gemini, xAI, Azure OpenAI, AWS Bedrock, Vertex AI, Ollama, Hugging Face), multiple agent frameworks (LangGraph, CrewAI, Google ADK), and multiple tool protocols (MCP, A2A, OpenAI-compatible endpoints) — emphasizing a "bring your own everything" philosophy with no vendor lock-in.

## Architecture Overview

kagent consists of four main components running inside and around a Kubernetes cluster:

| Component | Role |
|---|---|
| **Controller** | A Go-based Kubernetes controller that reconciles custom CRDs (Agent, Session) to create and manage AI agent resources in the cluster |
| **App/Engine** | The core runtime that executes the agent's conversation loop; supports Python ADK (default, built on Google ADK) and Go ADK runtimes |
| **CLI** | Terminal entry point for managing resources and interacting with agents (install, get, invoke, dashboard commands) |
| **Dashboard (UI)** | Web interface for creating, configuring, and chatting with agents, including a setup wizard for first-time users |

```text
┌─────────────────────────────────────────────────────────┐
│                    Kubernetes Cluster                    │
│  ┌──────────────────┐    ┌──────────────────────────┐   │
│  │ kagent Controller│───▶│ Agent CRDs (declarative) │   │
│  │  (Go, reconciles)│    │  Agent / Session / Tools │   │
│  └──────────────────┘    └──────────────────────────┘   │
│           │                        │                     │
│           ▼                        ▼                     │
│  ┌──────────────────┐    ┌──────────────────────────┐   │
│  │  kagent Engine   │◀──▶│    MCP Tool Layer        │   │
│  │ (conversation    │    │  kubectl / prom / argocd │   │
│  │  loop, runtimes) │    │  github / pagerduty      │   │
│  └──────────────────┘    └──────────────────────────┘   │
│           │                        │                     │
│           ▼                        ▼                     │
│  ┌──────────────────┐    ┌──────────────────────────┐   │
│  │ Service Mesh     │    │ OpenTelemetry Pipeline   │   │
│  │ (Istio/Ambient,  │    │ (traces, metrics, logs)  │   │
│  │  mTLS, egress)   │    └──────────────────────────┘   │
│  └──────────────────┘                                   │
└─────────────────────────────────────────────────────────┘
```

### Control Plane: Controller + CRDs

The controller watches for `Agent` and `Session` custom resources. When you `kubectl apply` an agent manifest, the controller provisions the runtime pod, wires up RBAC, and registers the agent with the service mesh. This means agent lifecycle (create, update, rollback, delete) follows standard Kubernetes reconciliation patterns—versioned in Git, reviewed via PRs, rolled out via ArgoCD or Flux.

### Runtime: App/Engine

The engine is where the actual agent reasoning happens. It runs the conversation loop: receiving a prompt, invoking the LLM, calling tools via MCP, and iterating until a final answer. Two runtime options exist:

- **Python ADK** (default): Built on Google's Agent Development Kit, with native support for CrewAI, LangGraph, and OpenAI frameworks.
- **Go ADK**: A native Go implementation offering ~2 second startup vs ~15 seconds for Python, with lower resource consumption—useful for high-density or latency-sensitive deployments.

Both runtimes support MCP tools, human-in-the-loop (HITL) gates, and persistent memory.

### Tool Layer: MCP

Tools are exposed via the **Model Context Protocol (MCP)**, a standard for connecting LLMs to external capabilities. kagent ships MCP servers for common platform tools (kubectl, Prometheus, ArgoCD, GitHub, PagerDuty, docs) and lets you register custom MCP servers pointing at REST APIs, gRPC services, or databases. This is the "hands" of the agent—without MCP tools, an agent can only reason, not act.

### Agent-to-Agent (A2A)

For multi-agent workflows, kagent implements the **Agent-to-Agent (A2A)** protocol, letting agents discover and delegate to each other across the cluster. One agent can triage an incident, hand off to an investigation agent, which then delegates remediation to a third—all with full trace visibility at each hop.

### Observability & Security

Every prompt, tool call, and token emits OpenTelemetry spans, flowing into the same tracing/metrics pipeline as the rest of your stack. Security is layered: mTLS via Istio or Ambient Mesh, fine-grained Kubernetes RBAC, policy-driven egress control for agent traffic, and optional NVIDIA NemoClaw guardrails for content safety and privacy enforcement on every LLM call.

## How It Works: Request Flow

1. **User submits a prompt** via Dashboard UI, CLI (`kagent invoke`), or a chat channel (Slack/Discord/Telegram via A2A).
2. **Engine receives the request** and loads the agent's configuration: system prompt, selected LLM, attached MCP tools, memory context.
3. **LLM reasons** and decides whether to answer directly or invoke a tool.
4. **MCP tool call executes** (e.g., `kubectl get pods`, PromQL query, GitHub API call) with results returned to the engine.
5. **Loop iterates** — LLM may chain multiple tool calls before producing a final answer.
6. **Telemetry emitted** at every step: OTel spans for each prompt/tool call/token, Prometheus metrics for latency and token usage, structured logs for audit.
7. **Response returned** to the user, with full traceability of which tool, which prompt, and which token caused latency or cost.

## Real-World Problems It Solves

| Problem | How kagent Solves It |
|---|---|
| Agents live outside the ops toolchain | Agents become CRDs—same GitOps, RBAC, and rollout workflow as any other workload |
| No visibility into agent behavior | OTel traces show every prompt, tool call, and token—debug latency/cost like any distributed system |
| Tool integration is ad-hoc per agent | MCP standardizes tool exposure across all agents, reusable and declarative |
| Multi-agent orchestration is custom-coded | A2A protocol provides first-class delegation and hand-off between agents |
| Security teams block AI adoption | mTLS, RBAC, egress policies, and audit logs use existing zero-trust controls |
| Agent frameworks create lock-in | BYO framework support (LangGraph, CrewAI, ADK) with no rewrite tax when switching |
| Long conversations blow token budgets | Context compaction auto-summarizes history to keep agents coherent within limits |
| Agents forget context between sessions | Persistent vector-backed long-term memory across sessions |

## Real-World Use Cases

- **Incident Response**: Pager-aware agent triages alerts, correlates traces, drafts runbooks, and opens rollback PRs—with human approval gates at each step.
- **Observability Copilot**: Conversational PromQL and trace navigation; ask "why did checkout p99 spike at 3am" and get a cited answer.
- **Platform Self-Service**: Developers request namespaces, databases, or CI pipelines in plain English; agent files the GitOps PR, existing approval workflows handle the rest.
- **Knowledge Agents**: RAG over runbooks, ADRs, and Slack history—with mTLS, RBAC, and audit logs security teams will actually approve.
- **Multi-Agent Workflows**: Chain triage → investigation → remediation agents, coordinated via A2A with full observability.
- **Chat Providers**: One agent exposed across Telegram, WhatsApp, Slack, Discord via A2A—write once, deploy everywhere.

## Hands-On Tutorial: First Agent in 10 Minutes

### Prerequisites

- `kind` (local Kubernetes cluster)
- `helm`
- `kubectl`
- An OpenAI API key (or configure an alternative provider)

### Step 1: Set Your API Key

```bash
export OPENAI_API_KEY="your-api-key-here"
```

### Step 2: Install the kagent CLI

```bash
# macOS via Homebrew
brew install kagent

# Or via curl (Linux/macOS)
curl https://raw.githubusercontent.com/kagent-dev/kagent/refs/heads/main/scripts/get-kagent | bash
```

### Step 3: Create a Local Cluster (if needed)

```bash
kind create cluster --name kagent-demo
kubectl cluster-info --context kind-kagent-demo
```

### Step 4: Install kagent

```bash
# Demo profile: includes preloaded agents and MCP tools
kagent install --profile demo

# Or minimal install (no preloaded agents)
kagent install --profile minimal
```

### Step 5: Launch the Dashboard

```bash
kagent dashboard
# Opens http://localhost:8082 with port-forward active
```

### Step 6: Create Your First Agent via Wizard

1. Click **"Let's Get Started"** in the welcome wizard.
2. **Step 1 — Configure AI Model**: Select `gpt-4.1-mini` (or your preferred model).
3. **Step 2 — Set up the AI Agent**: Review default Kubernetes agent details.
4. **Step 3 — Select Tools**: Review preselected MCP tools (kubectl, etc.).
5. **Step 4 — Review & Create**: Click **"Create kagent/my-first-k8s-agent & Finish"**.

### Step 7: Chat With Your Agent

In the dashboard, click your `kagent/my-first-k8s-agent` card and enter:

```text
What API resources are running in my cluster?
```

The agent will invoke the `kubectl` MCP tool, list API resources, and return a structured answer. Expand the **Arguments** and **Results** panels to see the exact tool calls and outputs.

### Step 8: Interact via CLI

```bash
# List installed agents
kagent get agent

# Invoke an agent directly from terminal
kagent invoke -t "What Helm charts are in my cluster?" --agent helm-agent
```

### Step 9: Define an Agent Declaratively (CRD)

For GitOps workflows, define agents as YAML instead of using the wizard:

```yaml
apiVersion: kagent.dev/v1alpha1
kind: Agent
metadata:
  name: my-k8s-agent
  namespace: kagent
spec:
  description: "Kubernetes troubleshooting agent"
  systemPrompt: |
    You are a Kubernetes SRE assistant. Use available tools
    to investigate cluster state before answering.
  model: gpt-4.1-mini
  tools:
    - mcpServer: kubectl
  runtime: go  # or python for ADK features
```

```bash
kubectl apply -f agent.yaml
```

### Step 10: Clean Up

```bash
kagent uninstall
kind delete cluster --name kagent-demo
```

## Key Technical Insights

- **Declarative-first**: Agents are CRDs, not imperative scripts—this is the core differentiator vs. agent frameworks that run as standalone processes.
- **Runtime choice matters**: Go ADK's ~2s cold start vs Python's ~15s is significant for serverless-style, high-churn agent deployments.
- **MCP is the integration contract**: Standardizing on MCP means tool integrations are portable across agents and frameworks, not bespoke per-agent glue code.
- **Observability is not optional**: Every token and tool call is traced—critical for cost control and debugging in production.
- **Security inherits from Kubernetes**: Rather than building a parallel security model, kagent reuses mesh mTLS, RBAC, and admission controllers—lowering the barrier for security team sign-off.
- **A2A enables composition**: Multi-agent systems aren't hardcoded pipelines; agents discover and delegate dynamically, more like microservices than monolithic workflows. 