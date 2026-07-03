# AutoGen Deep Dive

AutoGen is an open-source framework for building AI agents and multi-agent applications. It provides two complementary layers: **AgentChat** for fast, high-level agent development, and **Core** for event-driven, production-oriented multi-agent systems. 

## What AutoGen Is

AutoGen lets you compose autonomous or semi-autonomous software agents that can:

- Reason using an LLM.
- Call tools, APIs, databases, and code executors.
- Communicate with other agents through messages.
- Execute workflows with human approval, retries, validation, and distributed execution.
- Operate locally, in containers, or across processes and machines.

It is not a model provider. You bring the model—OpenAI-compatible APIs, Azure OpenAI, local models, or other supported providers—and AutoGen supplies the agent runtime, messaging, orchestration, and extension model.

## Architecture

AutoGen’s architecture separates **agent logic** from **communication infrastructure**.

```text
User / Application
        |
        v
+----------------------+
|     AgentChat        |  High-level agents, teams, tools
+----------------------+
        |
        v
+----------------------+
|       Core           |  Agent runtime, messages, subscriptions
+----------------------+
        |
        v
+----------------------+
|     Extensions       |  Model clients, MCP, Docker, gRPC, etc.
+----------------------+
        |
        v
LLMs / APIs / Tools / Databases / Code / External systems
```

### Core Components

| Component | Purpose |
|---|---|
| **Agent** | A unit with an identity and behavior. It may use an LLM, deterministic code, tools, or a combination. |
| **Agent Runtime** | The messaging and lifecycle layer. It routes messages, creates agents, and manages execution. |
| **Messages** | Typed data passed between agents. |
| **Topics and subscriptions** | Pub/sub-style communication. Agents subscribe to topics and receive relevant messages. |
| **Tools** | Python functions or external integrations that agents can invoke. |
| **Model clients** | Abstractions over LLM providers. |
| **Extensions** | Integrations for MCP, Docker code execution, OpenAI Assistants, gRPC distributed runtimes, and more. |

### AgentChat vs Core

| Aspect | AgentChat | Core |
|---|---|---|
| Abstraction level | High-level | Low-level |
| Best for | Rapid prototyping and conversational agents | Scalable, deterministic, distributed workflows |
| Programming model | Agents, teams, model clients, tools | Actors, messages, topics, subscriptions |
| Communication | Managed conversations and team orchestration | Explicit message routing and event-driven execution |
| Distribution | Primarily local/application-level | Supports agents across processes, machines, languages, and dependencies |
| Example | A research assistant with web-search and file tools | An order-processing system with planner, validator, payment, and notification agents |

## How It Works

### Single-Agent Flow

A basic AgentChat agent follows this loop:

1. The user submits a task.
2. The agent sends the task and conversation history to the configured model.
3. The model may respond directly or request a tool call.
4. AutoGen executes the tool and returns the result to the model.
5. The model produces a final response.
6. The response is streamed or returned to the caller.

For example, a weather agent receives “What is the weather in New York?”, calls a `get_weather` tool, receives the result, and returns a natural-language answer.

### Multi-Agent Flow

In Core, agents communicate through an **Agent Runtime**.

```text
User
  |
  v
Planner Agent
  |
  +--> Research Agent
  |         |
  |         +--> Writer Agent
  |                    |
  +--> Reviewer Agent <--+
              |
              v
          Final output
```

Each agent:

- Registers with a runtime.
- Declares the message types it handles.
- Subscribes to one or more topics.
- Processes a message independently.
- Publishes new messages or sends direct replies.

The runtime decouples agents from one another. A research agent does not need to know how the writer is implemented, where it runs, or which language it uses. It only needs to publish a message to the correct topic.

### Event-Driven Design

AutoGen Core behaves like an actor system:

- Agents are isolated units of state and behavior.
- Messages are asynchronous.
- Topics provide publish/subscribe communication.
- The runtime handles delivery, lifecycle, and concurrency.
- Agent behavior can be deterministic code, LLM reasoning, or both.

This makes it suitable for workflows where reliability, auditability, and control matter—not just free-form chat.

## Key Technical Insights

### 1. Agents Are Not Just LLM Wrappers

An AutoGen agent can be:

- An LLM-powered assistant.
- A deterministic Python service.
- A validator or policy engine.
- A human-in-the-loop approval step.
- A containerized code executor.
- A distributed worker exposing an agent interface.

This is important for production: not every step should consume tokens or make non-deterministic decisions.

### 2. The Runtime Is the Real Platform

The Agent Runtime is analogous to a lightweight message broker plus actor framework. It handles:

- Agent registration.
- Agent instantiation.
- Message delivery.
- Topic subscriptions.
- Lifecycle management.
- Local or distributed execution.

Agent logic remains separate from transport, which makes systems easier to test and scale.

### 3. Tools Enable Real-World Action

LLMs are good at planning and explanation, but tools let agents interact with real systems:

- Query a database.
- Call a REST or GraphQL API.
- Search documents.
- Read or write files.
- Run generated code in a sandbox.
- Trigger Kubernetes, Terraform, CI/CD, or ITSM workflows.
- Use MCP servers for standardized tool access.

### 4. Multi-Agent Systems Need Guardrails

A useful production pattern is to separate responsibilities:

- **Planner**: decides what to do.
- **Executor**: performs actions through tools.
- **Validator**: checks constraints, schemas, and business rules.
- **Critic/Reviewer**: reviews output quality.
- **Human approval agent**: pauses for permission on risky actions.
- **Auditor**: records decisions and tool calls.

This avoids giving one agent unchecked authority.

### 5. Determinism and LLM Reasoning Can Coexist

A robust design uses LLMs only where they add value:

```text
LLM: interpret request and choose workflow
Deterministic code: validate inputs and enforce policy
Tool/API: perform the action
LLM: summarize result
Deterministic code: log, audit, and route output
```

This is more reliable than asking an LLM to perform every step.

## Real-World Problems It Solves

| Problem | AutoGen-Based Solution |
|---|---|
| Manual research and synthesis | Research agent searches sources, extraction agent structures findings, writer agent drafts a report, reviewer checks citations and claims |
| Slow incident response | Alert ingestion agent classifies incidents, diagnostic agent queries metrics/logs, remediation agent proposes or executes runbooks, human approval gates risky changes |
| Code generation and review | Developer agent writes code, test agent generates tests, executor runs them in Docker, reviewer agent checks security and quality |
| Customer-support automation | Intent agent classifies requests, knowledge agent retrieves documentation, action agent creates tickets or performs account actions, escalation agent involves humans |
| Data-pipeline troubleshooting | Pipeline agent inspects failures, schema agent validates data contracts, remediation agent suggests fixes, approval agent controls deployment |
| Business-process automation | Invoice, procurement, onboarding, compliance, and approval workflows with specialized agents |
| Platform engineering | Agents that inspect infrastructure state, generate Terraform changes, validate policies, and request human approval before applying changes |

## Practical Use Cases

### SRE and Platform Engineering

An agent team can receive an alert, inspect Prometheus or OpenTelemetry data, correlate logs, identify a likely root cause, and propose a remediation.

Example flow:

```text
Alert Agent
  -> Diagnostic Agent
  -> Root-Cause Agent
  -> Remediation Planner
  -> Policy Validator
  -> Human Approval
  -> Runbook Executor
```

The key principle: the agent should **recommend or stage** changes; destructive production actions should require explicit approval and policy checks.

### AI-Assisted Software Engineering

Agents can collaborate to implement a feature:

- Requirements agent converts a ticket into acceptance criteria.
- Coder agent produces a patch.
- Test agent writes unit and integration tests.
- Executor agent runs tests in an isolated container.
- Reviewer agent checks security, style, and correctness.
- Human engineer approves the pull request.

### Enterprise Knowledge Assistant

A retrieval-augmented agent can answer questions from internal documentation, tickets, wikis, and databases.

A typical team:

- Query classifier.
- Retrieval agent.
- Source validator.
- Answer generator.
- Citation and policy checker.

### Data Engineering Operations

Agents can help with pipeline failures:

- Detect failed DAG runs.
- Inspect error logs.
- Check schema drift.
- Query data-quality metrics.
- Recommend a fix.
- Open a ticket or trigger a controlled retry.

### Security Operations

A security agent team can:

- Ingest alerts.
- Enrich indicators with threat intelligence.
- Correlate events.
- Classify severity.
- Recommend containment.
- Require analyst approval before isolation or blocking actions.

## Hands-On Tutorial

This tutorial builds a small AutoGen system with:

1. A single tool-using agent.
2. A two-agent workflow.
3. A practical multi-agent pattern.

### Prerequisites

- Python 3.10 or newer.
- An LLM API key from an OpenAI-compatible provider.
- Docker optional, but recommended for safe code execution.

Set your API key:

```bash
export OPENAI_API_KEY="your-api-key"
```

### Step 1: Create a Project

```bash
mkdir autogen-demo
cd autogen-demo
python -m venv .venv
source .venv/bin/activate
```

Create:

```bash
touch app.py
```

### Step 2: Install AutoGen

```bash
pip install -U "autogen-agentchat" "autogen-ext[openai]"
```

### Step 3: Build a Tool-Using Agent

Create `app.py`:

```python
import asyncio

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import OpenAIChatCompletionClient


async def get_weather(city: str) -> str:
    """Get the current weather for a city."""
    # Replace with a real weather API in production.
    return f"The weather in {city} is 24°C and clear."


async def main() -> None:
    model_client = OpenAIChatCompletionClient(
        model="gpt-4o",
    )

    weather_agent = AssistantAgent(
        name="weather_agent",
        model_client=model_client,
        tools=[get_weather],
        system_message=(
            "You are a concise weather assistant. "
            "Use the weather tool when asked about current conditions."
        ),
        reflect_on_tool_use=True,
    )

    await Console(
        weather_agent.run_stream(
            task="What is the weather in Visakhapatnam?"
        )
    )

    await model_client.close()


asyncio.run(main())
```

Run:

```bash
python app.py
```

Expected behavior:

```text
User: What is the weather in Visakhapatnam?
Agent calls: get_weather(city="Visakhapatnam")
Tool returns: The weather in Visakhapatnam is 24°C and clear.
Agent: The weather in Visakhapatnam is 24°C and clear.
```

### Step 4: Understand the Tool Loop

The important sequence is:

```text
User task
  -> Model decides to call tool
  -> AutoGen executes tool
  -> Tool result returns to model
  -> Model writes final answer
```

`reflect_on_tool_use=True` means the model sees the tool result and produces a polished final answer instead of merely returning raw tool output.

### Step 5: Build a Two-Agent Workflow

Create `team_demo.py`:

```python
import asyncio

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import OpenAIChatCompletionClient


async def main() -> None:
    model_client = OpenAIChatCompletionClient(
        model="gpt-4o",
    )

    researcher = AssistantAgent(
        name="researcher",
        model_client=model_client,
        system_message=(
            "You are a technical researcher. "
            "Provide a concise, factual analysis of the topic."
        ),
    )

    reviewer = AssistantAgent(
        name="reviewer",
        model_client=model_client,
        system_message=(
            "You are a critical reviewer. "
            "Check the researcher's response for accuracy, clarity, and gaps. "
            "End your final response with APPROVED when the answer is acceptable."
        ),
    )

    termination = TextMentionTermination("APPROVED")

    team = RoundRobinGroupChat(
        participants=[researcher, reviewer],
        termination_condition=termination,
    )

    await Console(
        team.run_stream(
            task="Explain the trade-offs of event-driven microservices."
        )
    )

    await model_client.close()


asyncio.run(main())
```

Run:

```bash
python team_demo.py
```

What happens:

1. The researcher produces an initial explanation.
2. The reviewer critiques it.
3. They alternate until the reviewer includes `APPROVED`.
4. The team stops.

This is a simple quality-control loop.

### Step 6: Build an Event-Driven Core Workflow

Create `core_demo.py`:

```python
import asyncio
from dataclasses import dataclass

from autogen_core import (
    AgentId,
    MessageContext,
    RoutedAgent,
    SingleThreadedAgentRuntime,
    default_subscription,
    message_handler,
)


@dataclass
class Ticket:
    title: str
    severity: str


@default_subscription
class TriageAgent(RoutedAgent):
    @message_handler
    async def handle_ticket(
        self, message: Ticket, ctx: MessageContext
    ) -> None:
        print(f"[Triage] Received: {message.title}")

        if message.severity == "critical":
            print("[Triage] Routing to on-call remediation.")
        else:
            print("[Triage] Adding to standard support queue.")


async def main() -> None:
    runtime = SingleThreadedAgentRuntime()

    await TriageAgent.register(
        runtime,
        "triage_agent",
        lambda: TriageAgent("Incident triage agent"),
    )

    runtime.start()

    await runtime.send_message(
        Ticket(
            title="Payment API latency above SLO",
            severity="critical",
        ),
        AgentId("triage_agent", "default"),
    )

    await runtime.stop_when_idle()


asyncio.run(main())
```

Run:

```bash
python core_demo.py
```

This demonstrates Core’s essential pattern:

- Define a typed message.
- Create an agent that handles that message.
- Register the agent with a runtime.
- Send a message to the agent.
- Let the runtime manage execution.

### Step 7: Add a Realistic Multi-Agent Pattern

For an SRE incident workflow, use separate responsibilities:

```text
AlertIntakeAgent
  -> DiagnosticAgent
  -> RemediationPlannerAgent
  -> PolicyValidatorAgent
  -> HumanApprovalAgent
  -> RunbookExecutorAgent
```

Conceptual implementation:

```python
@dataclass
class Alert:
    service: str
    metric: str
    severity: str


@dataclass
class Diagnosis:
    alert: Alert
    probable_cause: str
    evidence: list[str]


@dataclass
class RemediationPlan:
    diagnosis: Diagnosis
    actions: list[str]
    risk_level: str


@dataclass
class ApprovalDecision:
    plan: RemediationPlan
    approved: bool
    approver: str
```

Each agent handles one message type:

```python
class DiagnosticAgent(RoutedAgent):
    @message_handler
    async def handle_alert(self, alert: Alert, ctx: MessageContext):
        # Query metrics, logs, traces, topology, runbooks
        diagnosis = Diagnosis(
            alert=alert,
            probable_cause="Database connection pool exhaustion",
            evidence=["p99 latency increased", "active connections at limit"],
        )
        await self.publish_message(diagnosis, DefaultTopicId())


class RemediationPlannerAgent(RoutedAgent):
    @message_handler
    async def handle_diagnosis(
        self, diagnosis: Diagnosis, ctx: MessageContext
    ):
        plan = RemediationPlan(
            diagnosis=diagnosis,
            actions=[
                "Increase connection pool limit",
                "Restart affected service pods",
                "Verify latency recovery",
            ],
            risk_level="medium",
        )
        await self.publish_message(plan, DefaultTopicId())
```

In production, the `PolicyValidatorAgent` should check:

- Whether the action is allowed for the environment.
- Whether it requires change approval.
- Whether it violates security or compliance policy.
- Whether rollback is available.
- Whether the blast radius is acceptable.

The `HumanApprovalAgent` should stop execution for high-risk actions.

## Production Design Recommendations

### Security

- Never place raw API keys in source code; use a secrets manager.
- Restrict tool permissions using least privilege.
- Run generated code in isolated containers with no broad network access.
- Validate all tool inputs and outputs.
- Log prompts, tool calls, decisions, and approvals for auditability.
- Apply data-loss-prevention controls before sending sensitive data to external models.
- Use human approval for destructive or financially significant actions.

### Reliability

- Add timeouts for every model and tool call.
- Use retries with exponential backoff for transient failures.
- Make agent workflows idempotent.
- Persist workflow state for long-running tasks.
- Separate transient errors from terminal failures.
- Use circuit breakers around external APIs.
- Define explicit termination conditions to prevent infinite agent loops.

### Observability

Emit structured telemetry for:

- Agent identity.
- Conversation or workflow ID.
- Model provider and model name.
- Token usage and latency.
- Tool name, inputs, outputs, and duration.
- Errors and retries.
- Approval decisions.
- Final outcome.

A useful trace structure:

```text
workflow_id
  -> agent_run
       -> model_call
       -> tool_call
       -> validation
       -> decision
```

### Cost Control

- Use smaller models for classification, routing, and extraction.
- Reserve larger models for complex reasoning.
- Cache repeated retrieval and tool results.
- Limit conversation history and context size.
- Set maximum iterations and token budgets.
- Prefer deterministic code where LLM reasoning is unnecessary.

## When to Use AutoGen

Use AutoGen when you need:

- LLM agents that can call tools.
- Multi-step workflows with validation and approval.
- Collaboration among specialized agents.
- Event-driven agent systems.
- Distributed agents across services or machines.
- A framework that separates agent behavior from messaging infrastructure.

Avoid it when you only need a basic chatbot, a simple RAG pipeline, or a fixed deterministic workflow with no LLM decision-making. In those cases, a direct API integration, workflow engine, or retrieval framework may be simpler.

## Mental Model

Think of AutoGen as:

```text
LLM-powered actors + typed messaging + tools + guardrails
```

- **AgentChat** helps you build quickly.
- **Core** helps you build production-grade, event-driven systems.
- **Extensions** connect the system to models, MCP servers, containers, and distributed runtimes.
- **Your architecture** should supply the security, observability, policy, and operational controls.

The strongest AutoGen designs do not ask one agent to do everything. They create small, specialized agents with clear responsibilities, connect them through controlled messaging, and keep humans and deterministic policy checks in the loop where risk demands it.