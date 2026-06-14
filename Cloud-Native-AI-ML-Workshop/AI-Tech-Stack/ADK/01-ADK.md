### Agent Development Kit (ADK)

# Agent Development Kit (ADK)

ADK is an open-source framework for building, evaluating, and deploying AI agents. It provides the core building blocks—agents, tools, sessions, state, memory, artifacts, callbacks, and runners—needed to turn an LLM into a system that can reason, act on external systems, and operate reliably in production. 

## How ADK Works

ADK uses an event-driven execution model. A user message, webhook, scheduled job, or system event enters a `Runner`; the runner maintains a `Session`; an agent processes the event; and the agent may call tools, delegate to other agents, update state, create artifacts, or return a response.

```text
User / Event
   ↓
Runner
   ↓
Agent
   ↓
Tool calls / sub-agents / state updates
   ↓
Events, artifacts, final response
```

### Core Components

| Component | Purpose |
|---|---|
| `Agent` | The basic unit of work. An `LlmAgent` uses an LLM for reasoning; workflow agents control deterministic execution. |
| `Tool` | Lets an agent call APIs, query databases, run code, search systems, or invoke another agent. |
| `Runner` | Executes agents, processes events, and connects the agent to runtime services. |
| `Session` | Holds the context and event history for one conversation or task. |
| `State` | Short-term working memory for the current session. |
| `Memory` | Long-term information retained across sessions or users. |
| `Artifact` | Versioned storage for files and binary data, such as reports, PDFs, images, or generated documents. |
| `Callback` | Hooks for validation, redaction, logging, policy enforcement, and behavior modification. |
| `Event` | The atomic unit of runtime activity: user input, model output, tool request, tool result, or state change. |

### Execution Lifecycle

1. An event enters the system.
2. The runner creates or resumes a session.
3. The active agent receives the event and its context.
4. An LLM agent decides whether to answer directly, call a tool, delegate, or ask for clarification.
5. Tools perform real work against APIs, databases, Kubernetes, CI/CD systems, or internal services.
6. Tool results return as events and may update session state.
7. The agent continues until it produces a final answer or completes a workflow.

This design makes agent behavior inspectable: every prompt, tool call, result, and state update can be traced and debugged.

## Orchestration Models

ADK supports both deterministic and adaptive orchestration.

### Deterministic Workflows

Use workflow agents when the sequence must be predictable:

- `SequentialAgent`: run steps in a fixed order.
- `ParallelAgent`: run independent steps concurrently.
- `LoopAgent`: repeat steps until a condition is met.
- Custom workflow agents: implement organization-specific control flow.

Example: an incident-response agent may always follow **classify → enrich → diagnose → recommend → notify**.

### Adaptive LLM Routing

Use an LLM agent when the next action depends on intent, ambiguity, or context. The model can route to a specialist, choose a tool, or request more information.

Example: a support agent classifies a request as billing, provisioning, or security-related, then delegates to the appropriate specialist agent.

### Graph Workflows

Graph workflows combine deterministic paths with adaptive AI reasoning. They are useful when you need explicit branches, conditional transitions, approvals, retries, and predictable outcomes while still allowing model-driven decisions inside individual nodes.

## Tools and Integrations

Tools are how an agent affects the outside world.

ADK supports:

- **Function tools**: expose normal application functions to the model.
- **Agent tools**: allow one agent to call another agent as a reusable capability.
- **MCP tools**: connect to Model Context Protocol servers.
- **OpenAPI tools**: turn API specifications into agent-callable operations.
- **Code execution**: support calculations, transformations, and dynamic logic.
- **Long-running tools**: handle asynchronous operations that may not finish immediately.

For platform and SRE teams, common tools include Kubernetes APIs, Prometheus or Grafana queries, Terraform wrappers, PagerDuty, GitHub, ServiceNow, cloud provider APIs, and internal service catalogs.

## Context Management

ADK separates context into distinct layers instead of forcing everything into the prompt.

| Layer | Lifetime | Use |
|---|---|---|
| Event history | Session | Conversation transcript and tool-call trace |
| State | Session | Temporary values and intermediate results |
| Memory | Across sessions | User preferences, prior incidents, durable knowledge |
| Artifacts | Session/user scope | Files, reports, images, generated outputs |

This separation improves reliability and cost efficiency. Keep transient working data in state, durable knowledge in memory, and large binary outputs in artifacts.

## Production Capabilities

ADK includes capabilities aimed at real deployments:

- Local developer UI and CLI for interactive testing and debugging.
- API server runtime for exposing agents over HTTP.
- Deployment paths for containerized environments and Kubernetes-based runtimes.
- Observability through logs, metrics, and traces.
- Evaluation with multi-turn datasets, user simulation, environment simulation, custom metrics, and optimization.
- Safety controls using callbacks and guardrails.
- Streaming support for real-time text, audio, and multimodal interactions.
- Agent-to-agent interoperability through the A2A protocol.

## Real-World Use Cases

### SRE Incident Triage

An agent receives an alert, queries metrics and logs, inspects recent deployments, identifies likely failure domains, retrieves relevant runbooks, and drafts a remediation plan.

```text
Alert webhook
  → Incident classifier
  → Metrics and logs tools
  → Runbook retrieval
  → Human approval
  → Remediation action
  → Incident timeline artifact
```

Useful integrations include Prometheus, Loki, Kubernetes, PagerDuty, Grafana, GitHub, and ServiceNow.

### Kubernetes Operations Copilot

A platform engineer asks why a service is failing. The agent inspects pod events, logs, resource usage, deployment history, and network policies, then proposes a rollback, scaling action, or configuration fix.

Destructive actions should always require explicit human approval.

### Data Pipeline Diagnostics

A data engineering agent investigates failed Airflow, Spark, dbt, or ETL jobs.

It can:

- Read job metadata and error logs.
- Check upstream table freshness.
- Detect schema drift.
- Identify missing partitions or delayed files.
- Recommend a backfill plan.
- Generate a postmortem document.

The agent should diagnose and recommend; destructive backfills should remain human-controlled.

### Enterprise Knowledge Assistant

A retrieval agent answers employee questions using internal documentation, tickets, policies, and code repositories.

ADK helps separate the current conversation, long-term user preferences, retrieved documents, and generated reports.

### Secure Access Request Automation

An agent processes access requests by checking identity, role definitions, entitlement policies, and approval chains.

```text
Request
  → Policy evaluation
  → Risk scoring
  → Manager approval
  → Provisioning
  → Audit artifact
```

Use the LLM to classify and explain; use deterministic policy code to authorize.

### Customer Support Agent Team

A front-desk agent routes requests to specialist agents:

- Billing agent
- Order-status agent
- Technical-support agent
- Refund agent

Narrow agents are easier to test, secure, evaluate, and maintain than one large general-purpose agent.

### Voice and Field Operations

Voice agents can support contact centers, field technicians, and internal help desks using real-time audio streaming, tool calls, and live session state.

## Architectural Best Practices

### Keep Agents Narrow

Prefer multiple focused agents over one oversized agent.

```text
Orchestrator
├── Incident classifier
├── Kubernetes diagnostician
├── Runbook advisor
└── Remediation executor
```

This improves permissions, prompt quality, testability, and failure isolation.

### Make Tools Contract-Driven

Each tool should define:

- Clear purpose.
- Typed inputs and outputs.
- Explicit error behavior.
- Idempotency where possible.
- Authentication and authorization.
- Audit logging.

The model should not decide whether it is allowed to perform an action; the tool runtime should enforce that decision.

### Separate Reasoning from Authority

Use the LLM for:

- Interpretation.
- Classification.
- Planning.
- Explanation.
- Choosing among permitted actions.

Use deterministic code for:

- Authorization.
- Financial limits.
- Destructive operations.
- Compliance checks.
- Retry and timeout policy.

### Require Human Approval

Any irreversible action—deployment, deletion, access grant, payment, customer communication—should have an approval gate.

### Evaluate Before Deployment

Treat agents as software systems:

- Build golden datasets.
- Test tool-selection accuracy.
- Test refusal behavior.
- Test multi-turn context retention.
- Simulate adversarial users.
- Measure latency, cost, and success rate.
- Trace every tool invocation.

## Hands-On Tutorial: Python Time Agent

This tutorial creates a minimal agent that answers questions about the current time in selected cities using a tool.

### Prerequisites

- Python 3.10 or later
- `pip`
- A Gemini API key

### Step 1: Create a Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

On Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

### Step 2: Install ADK

```bash
pip install google-adk
```

### Step 3: Scaffold the Agent

```bash
adk create time_agent
```

This creates:

```text
time_agent/
├── agent.py
├── .env
└── __init__.py
```

### Step 4: Add a Tool

Replace `time_agent/agent.py` with:

```python
from google.adk.agents.llm_agent import Agent


def get_current_time(city: str) -> dict:
    """Returns the current time in a specified city."""
    mock_times = {
        "Hyderabad": "5:20 PM IST",
        "Bengaluru": "5:20 PM IST",
        "London": "12:50 PM BST",
        "New York": "7:50 AM EDT",
    }

    time = mock_times.get(city)

    if not time:
        return {
            "status": "error",
            "city": city,
            "message": "City not supported by this demo tool.",
        }

    return {
        "status": "success",
        "city": city,
        "time": time,
    }


root_agent = Agent(
    model="gemini-flash-latest",
    name="time_agent",
    description="Tells the current time in supported cities.",
    instruction=(
        "You are a helpful assistant that tells the current time in cities. "
        "Always use the get_current_time tool. "
        "If the tool returns an error, tell the user which cities are supported."
    ),
    tools=[get_current_time],
)
```

The function docstring is important because it becomes the tool description available to the model.

### Step 5: Configure the API Key

Edit `time_agent/.env`:

```bash
GOOGLE_API_KEY="your_gemini_api_key"
```

Do not commit this file to source control.

### Step 6: Run in the CLI

From the parent directory containing `time_agent/`:

```bash
adk run time_agent
```

Ask:

```text
What time is it in Hyderabad?
```

Expected flow:

1. The LLM recognizes a time request.
2. It calls `get_current_time(city="Hyderabad")`.
3. The tool returns structured JSON.
4. The agent responds with the time.

### Step 7: Run the Developer UI

From the parent directory:

```bash
adk web --port 8000
```

Open:

```text
http://localhost:8000
```

Select `time_agent`, then ask:

```text
What time is it in London?
```

The web UI is intended for development and debugging, not production deployment.

## Hands-On Tutorial: SRE Triage Agent

This example demonstrates a production-style multi-agent pattern using mock tools.

### Project Structure

```text
sre_agent/
├── agent.py
├── .env
└── __init__.py
```

### agent.py

```python
from google.adk.agents.llm_agent import Agent


def get_alert_details(alert_id: str) -> dict:
    """Returns mock alert metadata for an incident."""
    return {
        "alert_id": alert_id,
        "service": "checkout-api",
        "environment": "staging",
        "severity": "high",
        "summary": "Elevated HTTP 5xx rate",
        "affected_deployment": "checkout-api-v42",
    }


def get_recent_deployments(service: str) -> dict:
    """Returns mock deployment history for a service."""
    return {
        "service": service,
        "recent_deployments": [
            {
                "version": "checkout-api-v42",
                "author": "platform-team",
                "change": "Increased checkout timeout",
                "time": "14 minutes ago",
            },
            {
                "version": "checkout-api-v41",
                "author": "payments-team",
                "change": "Dependency upgrade",
                "time": "2 days ago",
            },
        ],
    }


def get_service_metrics(service: str) -> dict:
    """Returns mock service health metrics."""
    return {
        "service": service,
        "error_rate_percent": 18.4,
        "p99_latency_ms": 2400,
        "cpu_utilization_percent": 41,
        "memory_utilization_percent": 63,
        "dependency_errors": {
            "payments-api": 0.2,
            "inventory-api": 17.9,
        },
    }


incident_classifier = Agent(
    name="incident_classifier",
    model="gemini-flash-latest",
    description="Classifies an incident and identifies affected services.",
    instruction=(
        "Classify the incident. Identify the affected service, environment, "
        "severity, and likely failure domain. Be concise."
    ),
    tools=[get_alert_details],
)

diagnostician = Agent(
    name="diagnostician",
    model="gemini-flash-latest",
    description="Diagnoses likely root cause using metrics and deployment data.",
    instruction=(
        "Use metrics and recent deployments to identify the most likely root cause. "
        "Do not recommend destructive actions. Clearly separate observations, "
        "hypotheses, and recommended next steps."
    ),
    tools=[get_service_metrics, get_recent_deployments],
)

root_agent = Agent(
    name="sre_triage_orchestrator",
    model="gemini-flash-latest",
    description="Coordinates SRE incident triage.",
    instruction=(
        "You coordinate incident triage. First delegate to incident_classifier. "
        "Then delegate to diagnostician. Produce a final incident summary with: "
        "impact, likely root cause, evidence, recommended action, and required "
        "human approval."
    ),
    tools=[incident_classifier, diagnostician],
)
```

### Run It

```bash
adk run sre_agent
```

Prompt:

```text
Investigate alert INC-4821 and produce an incident triage report.
```

### Expected Behavior

```text
1. Call get_alert_details("INC-4821")
2. Identify checkout-api in staging
3. Call get_service_metrics("checkout-api")
4. Call get_recent_deployments("checkout-api")
5. Correlate high inventory-api errors with the recent deployment
6. Produce a structured triage report
```

### Production Hardening

For a real SRE agent:

- Replace mock functions with authenticated API clients.
- Use least-privilege service identities.
- Add rate limits and timeouts to every tool.
- Store incident timelines as artifacts.
- Emit traces for every agent and tool call.
- Require approval before rollback, restart, scale, or configuration changes.
- Evaluate the agent against historical incidents.
- Keep secrets in a secret manager, not in `.env` in production.

## When to Use ADK

ADK is a strong fit when you need:

- Multi-step agents that call real systems.
- Deterministic workflows combined with LLM reasoning.
- Multi-agent delegation.
- Session state, memory, and artifact handling.
- Local debugging with production deployment paths.
- Evaluation and observability from the beginning.
- Model flexibility across different LLM providers.

 