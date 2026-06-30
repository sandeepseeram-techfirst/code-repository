# Strands Agents: Deep Dive

**Strands Agents** is an open-source toolkit for building production-grade AI agents. It reduces agent development to a simple pattern: give a model a goal, provide typed tools, and let the model reason through an iterative tool-use loop until the task is complete.

It is deliberately model-agnostic: the same agent code can run against Anthropic, OpenAI, Google, Amazon Bedrock, Ollama, LiteLLM, Mistral, and other OpenAI-compatible endpoints. The project provides both a batteries-included **Harness** and a lower-level **SDK** for teams that want full control. 

## TL;DR

| Aspect | What it means |
|---|---|
| Core idea | An LLM decides which tools to call, receives results, and repeats until it can answer or complete a task |
| Main components | Agent loop, tools, model providers, memory/session state, MCP, observability, evaluation, sandboxing |
| Primary languages | Python and TypeScript |
| Deployment style | CLI, embedded library, service/API, or cloud runtime |
| Best fit | Multi-step workflows where deterministic scripts are too brittle but full autonomy is unnecessary |
| Key strength | Production-oriented abstractions: tools, memory, tracing, evaluation, permissions, and safety are first-class |

## What Problem It Solves

Traditional automation breaks when inputs, edge cases, or business rules change. A conventional script implements a fixed sequence:

```text
read input -> call API A -> transform -> call API B -> write output
```

That works only when the sequence is known in advance. Real operational work often requires judgment:

- Decide which system to query.
- Interpret incomplete or ambiguous input.
- Retry or choose an alternate path after a failure.
- Combine data from several sources.
- Produce a structured action or report.

A pure LLM cannot safely solve this either, because it cannot natively query a CRM, write to a ticketing system, inspect Kubernetes state, or execute a remediation workflow.

Strands bridges the gap:

```text
LLM reasoning + explicit tools + controlled execution environment
= practical agentic automation
```

The model does **planning and decision-making**; your code does **real work** through deterministic, testable functions.

## Core Architecture

At a high level, Strands separates concerns into model, agent, tools, state, and operations.

```text
                +----------------------+
User / Event -> | Agent Interface      |
                +----------+-----------+
                           |
                           v
                +----------------------+
                | Agent Loop           |
                | prompt + history     |
                +----------+-----------+
                           |
             model chooses action or final answer
                           |
        +------------------+------------------+
        |                                     |
        v                                     v
+----------------+                  +---------------------+
| Tool Registry  |                  | Final Response      |
| custom tools   |                  | structured output   |
| vended tools   |                  +---------------------+
| MCP tools      |
+-------+--------+
        |
        v
+----------------+
| Execution layer|
| APIs, files,   |
| shell, DBs,    |
| cloud systems  |
+----------------+

Supporting services:
- Session / memory store
- Context manager
- Guardrails / permissions
- Traces, metrics, evaluation
```

### 1. Model Provider Layer

The model provider abstracts the LLM API. You pass a model object—or rely on a default provider—and the rest of the agent code remains unchanged.

Examples:

```python
from strands import Agent
from strands.models.anthropic import AnthropicModel

model = AnthropicModel(model_id="claude-sonnet-5", max_tokens=4096)
agent = Agent(model=model)
```

Or with a local model:

```python
from strands import Agent
from strands.models.ollama import OllamaModel

model = OllamaModel(
    host="http://localhost:11434",
    model_id="llama3.1"
)
agent = Agent(model=model)
```

This is important for cloud-agnostic designs: the agent logic is portable, while the inference backend can be swapped based on cost, latency, data residency, or availability requirements.

### 2. Agent Loop

The agent loop is the heart of Strands.

```text
1. Receive user request
2. Build prompt from system instructions, conversation history, and tool definitions
3. Send prompt to model
4. Model returns either:
   - a tool call
   - a final response
5. If tool call:
   - validate and execute tool
   - append tool result to conversation history
   - return to step 3
6. If final response:
   - return result to caller
```

Conceptually:

```python
while not done:
    response = model(messages, tools)

    if response.has_tool_calls:
        for call in response.tool_calls:
            result = execute_tool(call)
            messages.append(tool_result(result))
    else:
        done = True
        final_answer = response.text
```

Strands handles this loop for you. Each invocation returns an `AgentResult` containing messages, metrics, and traces, which makes agent behavior inspectable rather than a black box.

### 3. Tools

Tools are the agent’s capabilities. A tool is usually a typed function with a clear docstring. Strands converts its signature, parameters, and description into a schema the model can understand.

```python
from strands import tool

@tool
def get_incident(severity: str, service: str) -> dict:
    """
    Find open incidents for a service filtered by severity.

    Args:
        severity: Incident severity, such as SEV1, SEV2, or SEV3.
        service: Name of the affected service.

    Returns:
        A dictionary containing matching incident details.
    """
    return incident_api.search(
        severity=severity,
        service=service
    )
```

The model sees something equivalent to:

```json
{
  "name": "get_incident",
  "description": "Find open incidents for a service filtered by severity.",
  "parameters": {
    "severity": "string",
    "service": "string"
  }
}
```

Good tools should be:

- Narrow: one clear responsibility.
- Deterministic where possible.
- Idempotent for risky operations.
- Explicit about inputs and outputs.
- Protected by validation and authorization.
- Observable through logs and traces.

### 4. Vended Tools

Strands includes ready-made tools for common agent needs:

| Tool category | Typical use |
|---|---|
| File editor | Read, create, modify, and inspect files |
| Shell execution | Run controlled local or sandboxed commands |
| HTTP request | Call external REST APIs |
| Memory tools | Store and retrieve long-term knowledge |
| Task tracking | Maintain a structured to-do list across a workflow |
| Subagents | Delegate specialized work to another agent |

These reduce boilerplate, but production systems should treat them like any other privileged component: restrict paths, commands, network access, credentials, and blast radius.

### 5. MCP Integration

Strands supports Model Context Protocol (MCP), an open standard for exposing tools and context to AI applications.

Instead of writing every integration yourself, you can connect an MCP server that exposes:

- Internal APIs
- Documentation
- Databases
- Observability systems
- Cloud services
- Developer tools
- Enterprise systems

Example concept:

```text
Strands Agent
   -> MCP client
      -> Jira MCP server
      -> GitHub MCP server
      -> Prometheus MCP server
      -> Internal runbook MCP server
```

This makes MCP useful for platform engineering: expose governed, auditable operations rather than giving an agent unrestricted infrastructure access.

### 6. Memory and Sessions

Strands distinguishes between:

| Concept | Scope | Example |
|---|---|---|
| Conversation state | One interaction or session | “What did I just ask?” |
| Session persistence | Across process restarts | Resume an incident investigation tomorrow |
| Long-term memory | Across sessions/users/tasks | “This customer prefers Slack alerts and uses PostgreSQL.” |

The Harness can persist sessions locally under `.agent/sessions`, while the SDK supports memory stores for durable, cross-session context.

A practical pattern is:

```text
Short-term context: current incident, active files, recent tool outputs
Long-term memory: team conventions, known failure patterns, customer preferences
External state: tickets, deployments, metrics, configuration
```

Do not put everything into model memory. Keep authoritative state in systems of record and use memory for useful, non-authoritative context.

### 7. Context Management

Long agent runs can exceed the model context window. Strands provides context management to preserve the relevant working state while trimming or summarizing less relevant history.

For example, an agent investigating a production incident may accumulate:

- Logs
- Metric queries
- Deployment history
- Runbook excerpts
- Previous hypotheses

Context management helps retain the current hypothesis, active incident ID, critical findings, and pending actions while compressing older material.

### 8. Observability and Evaluation

Production agents need more than logs. Strands provides tracing and metrics so you can answer:

- Which tools did the agent call?
- What inputs did it provide?
- How long did each tool take?
- Did the agent loop excessively?
- Which model calls were expensive?
- Did the final output meet expected criteria?
- Where did the agent make a wrong decision?

Strands Evals adds evaluation capabilities such as scoring outputs, diagnosing failures, and simulating scenarios before deployment.

A useful evaluation set includes:

| Test type | Example |
|---|---|
| Tool selection | Given a billing question, does it call the billing tool rather than invent an answer? |
| Parameter quality | Does it pass the correct customer ID and date range? |
| Error handling | After a 500 from an API, does it retry safely or escalate? |
| Safety | Does it refuse destructive actions without approval? |
| Output schema | Does the response match the required JSON structure? |
| Cost/latency | Is the task completed within acceptable token and time budgets? |

## Strands Product Layers

Strands is not one monolithic product. It is a layered toolkit.

| Layer | Purpose | When to use |
|---|---|---|
| `/harness` | Fully assembled agent with default tools, memory, context management, and task tracking | Fast prototyping and general-purpose assistants |
| `/harness-sdk` | Build a custom agent harness from primitives | You need control over the loop, tools, permissions, and runtime |
| `/box` | Sandboxed execution environment with OS containment and policy controls | Agents execute code or commands |
| `/shell` | Virtual shell designed for safe agent use | Agents need terminal-like capabilities with reduced risk |
| `/evals` | Test, score, diagnose, and simulate agents | Pre-production and continuous quality assurance |
| `/labs` | Experimental agent research and projects | Robotics, world models, benchmarks, advanced patterns |

### Harness vs SDK

Use the **Harness** when you want a working agent immediately:

```python
from strands_harness import create_harness

agent = create_harness()
agent("Research API versioning strategies and write a recommendation.")
```

Use the **SDK** when you need production control:

```python
from strands import Agent, tool

@tool
def lookup_order(order_id: str) -> dict:
    """Look up an order by ID."""
    return orders_db.get(order_id)

agent = Agent(tools=[lookup_order])
agent("What is the status of order ORD-123?")
```

The Harness is an opinionated product; the SDK is the composable foundation.

## Design Principles

### Model-driven, tool-grounded

The model chooses actions, but it cannot perform actions except through registered tools. This keeps capability explicit and auditable.

### Provider-agnostic

Model choice is an implementation detail. The same tool definitions and agent logic can target hosted or local models.

### Production-first

Strands treats observability, evaluation, memory, safety, and deployment as core requirements—not afterthoughts.

### Composable

You can start with one agent and one tool, then evolve to:

- Multiple tools
- MCP integrations
- Subagents
- Multi-agent workflows
- Human-in-the-loop approvals
- Sandboxed execution

### Least privilege

Agents should receive only the permissions required for their task. An incident-summary agent should not be able to delete production resources.

## Real-World Problems Solved

### 1. Incident Response and SRE Automation

An on-call engineer often needs to correlate alerts, logs, deployments, metrics, runbooks, and ticket history.

An agent can:

1. Receive an alert.
2. Query monitoring for affected services.
3. Inspect recent deployments.
4. Search runbooks.
5. Identify likely causes.
6. Draft an incident timeline.
7. Recommend or execute a safe remediation step.

Example workflow:

```text
PagerDuty alert
  -> Strands agent
     -> Prometheus metrics
     -> Kubernetes events
     -> Deployment records
     -> Runbook search
     -> Incident ticket creation
     -> Suggested mitigation
```

This reduces mean time to diagnosis, especially for repetitive investigations.

### 2. Customer Support Assistants

Support agents need account context, entitlements, order history, knowledge-base articles, and escalation rules.

A Strands agent can:

- Authenticate the request context.
- Retrieve relevant customer data.
- Search documentation.
- Classify intent.
- Draft a response.
- Create or update a ticket.
- Escalate when confidence is low.

The key design rule: the agent should propose or perform actions through governed APIs, not directly manipulate underlying databases.

### 3. Lead Routing and CRM Automation

A sales operations agent can classify inbound leads, enrich them from a CRM, calculate fit scores, assign owners, and create follow-up tasks.

```python
@tool
def classify_lead(email: str, company: str) -> dict:
    """Score and classify an inbound lead."""
    data = crm.lookup(company)
    return {
        "lead_id": crm.create_lead(email, company),
        "score": compute_icp_score(data),
        "segment": data["industry"],
    }

@tool
def route_to_rep(lead_id: str, region: str) -> str:
    """Assign a lead to the correct regional representative."""
    rep = crm.get_rep_for_region(region)
    crm.assign(lead_id, rep)
    return f"Assigned to {rep}"
```

This replaces brittle rules with a system that can handle varied inputs while still using deterministic business logic.

### 4. Research and Due Diligence

A research agent can search the web, read sources, compare findings, synthesize recommendations, and save a report.

Use cases include:

- Technology evaluations
- Competitor analysis
- Regulatory research
- Vendor assessments
- Market research
- Internal knowledge synthesis

The agent should cite sources, distinguish facts from inference, and write outputs to a controlled location.

### 5. Developer Productivity

Engineering agents can assist with:

- Repository analysis
- Dependency upgrade planning
- Test generation
- Code review preparation
- API documentation
- Migration planning
- Infrastructure drift analysis

For example, a dependency-upgrade agent could:

1. Identify outdated dependencies.
2. Read release notes.
3. Detect breaking changes.
4. Update manifests.
5. Run tests.
6. Summarize risk.
7. Open a pull request.

### 6. Security Operations

Security teams can use agents for:

- Alert triage
- Vulnerability enrichment
- Configuration drift detection
- Policy violation analysis
- Remediation recommendations
- Incident investigation

A secure design separates **read-only investigation** from **write actions**. Remediation should require explicit approval or operate within tightly scoped automation policies.

### 7. Data Engineering Operations

A data platform agent can help with:

- Pipeline failure diagnosis
- Schema drift detection
- Data quality checks
- Backfill planning
- Cost analysis
- Runbook execution

Example:

```text
Airflow task failed
  -> Agent queries logs
  -> Checks upstream table freshness
  -> Identifies schema change
  -> Finds owner and recent PR
  -> Drafts incident update
  -> Suggests compatibility fix
```

## Architecture Patterns

### Single Agent, Multiple Tools

Best for focused tasks.

```text
User request
  -> Agent
     -> CRM tool
     -> Ticketing tool
     -> Notification tool
  -> Final response
```

Use when the task has one owner and a bounded scope.

### Agent-as-Tool

One agent is exposed as a tool to another agent.

```text
Orchestrator agent
  -> Research agent
  -> Data analysis agent
  -> Writing agent
```

Use when you want separation of concerns or specialized prompts and toolsets.

### Multi-Agent Workflow

Multiple agents collaborate with explicit handoffs.

```text
Triage agent
  -> Investigation agent
  -> Remediation agent
  -> Reporting agent
```

Use when different phases require different permissions, models, or system access.

### Human-in-the-Loop

The agent prepares an action, but a human approves it.

```text
Agent identifies fix
  -> Creates change plan
  -> Requests approval
  -> Human approves
  -> Agent executes
  -> Agent verifies
```

This is essential for production infrastructure, financial operations, security remediation, and customer-impacting changes.

## Security and Production Design

### Threat Model

Agent systems introduce risks beyond a normal API service:

| Risk | Example | Mitigation |
|---|---|---|
| Prompt injection | Malicious web page tells agent to exfiltrate secrets | Treat external content as untrusted; isolate tools; restrict destinations |
| Excessive agency | Agent deletes resources without approval | Require approval for irreversible actions |
| Credential leakage | Agent receives broad cloud credentials | Use short-lived, scoped credentials and credential injection |
| Tool misuse | Agent calls an internal API incorrectly | Validate inputs; enforce authorization; rate-limit |
| Data exfiltration | Agent sends internal data to external endpoint | Egress controls and allowlists |
| Infinite loops | Agent repeatedly retries a failing tool | Set iteration, time, token, and cost limits |
| Incorrect output | Agent confidently returns wrong answer | Use retrieval, validation, evaluation, and human review |

### Recommended Controls

- Use separate identities per agent and per environment.
- Grant least-privilege permissions.
- Prefer read-only tools by default.
- Require explicit approval for destructive operations.
- Use sandboxing for shell and code execution.
- Restrict network egress.
- Log every tool invocation, input, output, decision, and latency.
- Set maximum iterations, timeouts, token budgets, and cost budgets.
- Validate structured outputs before downstream systems consume them.
- Separate development, staging, and production credentials.
- Use policy-as-code for permitted actions.
- Add evaluation gates in CI/CD.

## Hands-On Tutorial

This tutorial builds a small but realistic **incident triage agent** using Python. It will:

1. Check service health.
2. Fetch recent deployment information.
3. Analyze the likely cause.
4. Create an incident note.
5. Return a structured recommendation.

You can adapt the fake tools to real APIs later.

### Prerequisites

- Python 3.10 or newer
- Access to one model provider:
  - Anthropic API key
  - OpenAI API key
  - Google Gemini API key
  - Ollama running locally
  - AWS credentials for Bedrock

### Step 1: Create the Project

```bash
mkdir strands-incident-agent
cd strands-incident-agent

python -m venv .venv
source .venv/bin/activate
```

On Windows:

```powershell
python -m venv .venv
.venv\Scripts\activate
```

### Step 2: Install Strands

```bash
pip install strands-agents
```

For a non-default provider, install the relevant extra:

```bash
pip install 'strands-agents[anthropic]'
# or
pip install 'strands-agents[openai]'
# or
pip install 'strands-agents[gemini]'
# or
pip install 'strands-agents[ollama]'
```

### Step 3: Configure a Model Provider

Choose one option.

#### Anthropic

```bash
export ANTHROPIC_API_KEY="your-api-key"
```

#### OpenAI

```bash
export OPENAI_API_KEY="your-api-key"
```

#### Google Gemini

```bash
export GEMINI_API_KEY="your-api-key"
```

#### Ollama

```bash
ollama serve
ollama pull llama3.1
```

#### Amazon Bedrock

Configure AWS credentials using your preferred method:

```bash
aws configure
```

Or use a Bedrock API key:

```bash
export AWS_BEARER_TOKEN_BEDROCK="your-bedrock-api-key"
```

### Step 4: Create Fake Operational Tools

Create `tools.py`:

```python
import random
from strands import tool


@tool
def get_service_health(service: str) -> dict:
    """
    Get current health signals for a service.

    Args:
        service: Name of the service to inspect.

    Returns:
        A dictionary containing error rate, latency, and status.
    """
    # Replace with Prometheus, Datadog, CloudWatch, or another observability API.
    error_rate = round(random.uniform(0.1, 8.0), 2)
    latency_ms = random.randint(120, 1800)

    if error_rate > 5:
        status = "degraded"
    elif error_rate > 2:
        status = "warning"
    else:
        status = "healthy"

    return {
        "service": service,
        "status": status,
        "error_rate_percent": error_rate,
        "p99_latency_ms": latency_ms,
    }


@tool
def get_recent_deployments(service: str) -> list[dict]:
    """
    Get recent deployments for a service.

    Args:
        service: Name of the service to inspect.

    Returns:
        A list of recent deployment records.
    """
    # Replace with Argo CD, GitHub Actions, Spinnaker, or your deploy system.
    return [
        {
            "version": "v1.42.7",
            "deployed_at": "2026-10-26T14:12:00Z",
            "author": "platform-team",
            "change": "Increased worker concurrency",
        },
        {
            "version": "v1.42.6",
            "deployed_at": "2026-10-25T09:30:00Z",
            "author": "payments-team",
            "change": "Updated payment provider SDK",
        },
    ]


@tool
def search_runbooks(query: str) -> list[dict]:
    """
    Search internal operational runbooks.

    Args:
        query: Natural-language search query.

    Returns:
        A list of matching runbook excerpts.
    """
    # Replace with OpenSearch, Elasticsearch, Confluence, or an internal search API.
    return [
        {
            "title": "High error rate after deployment",
            "excerpt": (
                "If error rates rise immediately after a deployment, compare "
                "the current version with the previous version, inspect rollout "
                "configuration, and consider rollback if customer impact is high."
            )
        },
        {
            "title": "Payment provider failures",
            "excerpt": (
                "For payment provider errors, verify provider status, inspect "
                "credential rotation events, and check timeout configuration."
            )
        },
    ]


@tool
def create_incident_note(service: str, summary: str, recommendation: str) -> dict:
    """
    Create an incident investigation note.

    Args:
        service: Affected service name.
        summary: Short investigation summary.
        recommendation: Recommended next action.

    Returns:
        Confirmation of the created note.
    """
    # Replace with Jira, ServiceNow, PagerDuty, or your incident system.
    note_id = f"INC-NOTE-{random.randint(1000, 9999)}"
    return {
        "note_id": note_id,
        "service": service,
        "summary": summary,
        "recommendation": recommendation,
        "created": True,
    }
```

### Step 5: Create the Agent

Create `agent.py`:

```python
from strands import Agent
from strands.models.anthropic import AnthropicModel

from tools import (
    get_service_health,
    get_recent_deployments,
    search_runbooks,
    create_incident_note,
)

model = AnthropicModel(
    model_id="claude-sonnet-5",
    max_tokens=4096
)

agent = Agent(
    model=model,
    tools=[
        get_service_health,
        get_recent_deployments,
        search_runbooks,
        create_incident_note,
    ],
    system_prompt="""
You are a production incident triage agent.

Rules:
1. Investigate before recommending an action.
2. Use tools to gather evidence.
3. Do not invent metrics, deployment details, or runbook content.
4. Prefer safe, reversible actions.
5. Never claim that a remediation was performed unless a tool confirms it.
6. If the issue is severe or ambiguous, recommend human approval.
7. Return a concise final answer with evidence, likely cause, and next action.
"""
)

result = agent(
    """
    The checkout-service is showing elevated errors.
    Investigate the likely cause, create an incident note,
    and recommend the safest next action.
    """
)

print(result)
```

Run it:

```bash
python agent.py
```

### Step 6: Understand What Happens

The model receives:

- The system prompt
- The user request
- Four tool definitions

It may reason like this:

```text
1. I need current health data -> call get_service_health("checkout-service")
2. Error rate is high -> I should check recent changes
3. Call get_recent_deployments("checkout-service")
4. A deployment occurred recently -> search operational guidance
5. Call search_runbooks("high error rate after deployment")
6. Evidence supports a deployment-related regression
7. Create an incident note
8. Call create_incident_note(...)
9. Produce final recommendation
```

The important point is that the model does not execute the investigation itself. It selects and sequences your deterministic tools.

### Step 7: Add Structured Output

For production integrations, avoid parsing free-form text. Ask for structured output and validate it.

```python
from pydantic import BaseModel


class TriageResult(BaseModel):
    service: str
    status: str
    likely_cause: str
    confidence: float
    recommended_action: str
    requires_human_approval: bool


response = agent(
    """
    Investigate checkout-service and return a JSON object matching this schema:
    {
      "service": "string",
      "status": "string",
      "likely_cause": "string",
      "confidence": "number between 0 and 1",
      "recommended_action": "string",
      "requires_human_approval": "boolean"
    }

    Use the available tools for evidence.
    """
)

print(response)
```

In a real service, validate the response before sending it to a ticketing system, pager, or automation workflow.

### Step 8: Add Human Approval

For a production remediation flow, split investigation from execution.

```python
@tool
def propose_rollback(service: str, current_version: str, previous_version: str) -> dict:
    """
    Propose a rollback for human approval.

    Args:
        service: Service to roll back.
        current_version: Currently deployed version.
        previous_version: Version to roll back to.

    Returns:
        A rollback proposal requiring approval.
    """
    return {
        "proposal_id": "RB-123",
        "service": service,
        "from_version": current_version,
        "to_version": previous_version,
        "status": "pending_approval",
    }
```

The agent should call this tool, but it should not call a real rollback function until an authorized human or policy engine approves the proposal.

### Step 9: Make It Production-Ready

A production-ready architecture looks like this:

```text
Client / Alert source
        |
        v
API service
        |
        v
Strands Agent runtime
        |
        +-- Tool gateway
        |      |-- Observability API
        |      |-- Deployment API
        |      |-- Runbook search
        |      |-- Incident system
        |
        +-- Policy / approval service
        |
        +-- Trace and metrics backend
        |
        +-- Evaluation pipeline
```

Key implementation choices:

- Run the agent behind an API, queue consumer, or scheduled job.
- Use a per-tenant or per-workflow agent identity.
- Store conversation state in durable storage.
- Emit OpenTelemetry-compatible traces.
- Add retries with backoff for transient tool failures.
- Apply circuit breakers around external systems.
- Set hard limits on loop count, duration, tokens, and spend.
- Use canary evaluation before enabling autonomous actions.
- Keep destructive actions behind explicit approval.

## Practical Tool Design Example

Instead of one broad tool:

```python
@tool
def manage_service(service: str, action: str) -> str:
    """Manage a service."""
    ...
```

Use narrow, safer tools:

```python
@tool
def get_deployment_status(service: str) -> dict:
    """Read deployment status."""

@tool
def get_error_metrics(service: str, window_minutes: int) -> dict:
    """Read recent error metrics."""

@tool
def propose_rollback(service: str, target_version: str) -> dict:
    """Create a rollback proposal for approval."""
```

This improves:

- Security
- Testability
- Auditability
- Model tool-selection accuracy
- Failure isolation
- Human oversight

## When to Use Strands

### Good Fit

- Multi-step operational workflows
- Support and internal assistant applications
- Incident response and investigation
- Research and report generation
- Developer productivity tooling
- Data pipeline diagnostics
- Security alert triage
- CRM and business-process automation
- Agents that must integrate with several internal systems

### Poor Fit

- Simple deterministic ETL jobs
- Fixed approval workflows with no ambiguity
- High-frequency low-latency classification where a small ML model is enough
- Tasks where every action must be fully deterministic
- Systems where model cost, latency, or non-determinism is unacceptable

## Key Technical Takeaways

- Strands is an **agent harness and SDK**, not merely a prompt framework.
- Its central abstraction is the **reasoning-and-tool-use loop**.
- Tools are the security and capability boundary.
- Model providers are swappable, supporting multi-cloud and local inference.
- MCP enables standardized integration with external systems.
- Sessions, memory, and context management solve different persistence problems.
- Observability and evaluation are necessary for production confidence.
- The safest production pattern is: **read broadly, reason carefully, write narrowly, and approve destructive actions**.

## Minimal Mental Model

```text
Goal + Tools + Guardrails + Memory + Observability
= Production Agent
```

Strands is most valuable when your workflow needs judgment and adaptation, but its actions must remain controlled, observable, and safe.