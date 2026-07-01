# Pydantic AI: Deep Dive

## What it is

Pydantic AI is an open-source Python SDK for building AI agents and LLM applications. It provides:

- A typed **agent loop** around LLMs.
- **Tools** that models can call.
- **Structured outputs** validated with Pydantic.
- **Dependency injection** for databases, APIs, users, and secrets.
- **Provider-agnostic model access**—OpenAI, Anthropic, Google, Bedrock, Azure AI Foundry, Groq, Mistral, xAI, Ollama, and others.
- **Observability** through OpenTelemetry and Pydantic Logfire.
- **Production capabilities** such as persistence, durable execution, guardrails, memory, planning, sub-agents, and context management.

In one sentence: **Pydantic AI turns LLM calls into typed, testable Python functions and workflows.**

## The core problem it solves

Most LLM applications start as:

```text
prompt -> model -> free-text response -> string parsing -> hope
```

That works for demos but fails in production because:

- The model may return invalid JSON.
- Tool arguments may be malformed.
- Business rules may be violated.
- Failures are hard to trace.
- Switching model vendors requires rewriting integration code.
- Long-running agents can crash or lose state.
- Evaluating agent quality is subjective and difficult.

Pydantic AI replaces that with:

```text
typed request -> agent -> validated tool calls -> validated output -> traceable result
```

It moves many errors from runtime and production into development time.

## Architecture

### High-level architecture

```text
+---------------------------+
|        Your Application    |
|  API / CLI / Web / Worker  |
+-------------+-------------+
              |
              v
+---------------------------+
|         Pydantic AI        |
|  Agent / Capabilities      |
|  Tools / Instructions      |
|  Dependencies / Output     |
+-------------+-------------+
              |
              v
+---------------------------+
|      Model Provider        |
| OpenAI / Anthropic / etc.  |
+---------------------------+

Optional sidecars:
- Pydantic Logfire / OpenTelemetry
- Pydantic Evals
- Pydantic Graph
- Durable execution engine
- MCP servers
- External APIs and databases
```

### Main components

| Component | Purpose | Example |
|---|---|---|
| `Agent` | Orchestrates model calls, tools, instructions, and output validation | `Agent("openai:gpt-4.1")` |
| Model provider | Connects the agent to an LLM | OpenAI, Anthropic, Ollama, Bedrock |
| Instructions | System-level guidance for the model | “You are a bank support agent.” |
| Tools | Python functions the model can invoke | `get_balance()`, `search_orders()` |
| Dependencies | Runtime context injected into tools | DB connection, user ID, HTTP client |
| Output type | Pydantic model defining the required response | `SupportOutput` |
| Capabilities | Reusable bundles of tools, instructions, hooks, and settings | Web search, filesystem access, customer context |
| Toolsets | Collections of tools, often from external systems | MCP server, database toolset |
| Hooks | Code executed around agent lifecycle events | Log before/after tool call |
| Graph | Typed control flow for multi-step workflows | Approval workflow, research pipeline |
| Evals | Tests and scores agent behavior | Output accuracy, tool-call trajectory |

## How the agent loop works

A typical Pydantic AI run follows this sequence:

1. Your application calls `agent.run(...)`.
2. Pydantic AI builds the prompt from instructions, conversation history, tools, and dependencies.
3. The request is sent to the selected model provider.
4. The model responds with either:
   - A final answer, or
   - A request to call one or more tools.
5. If tools are requested, Pydantic AI validates the arguments against Python type hints.
6. Your Python tool functions execute.
7. Tool results are returned to the model.
8. The loop repeats until the model produces a final response.
9. The final response is validated against the configured `output_type`.
10. A typed `result` object is returned to your application.

```text
User input
   |
   v
Agent run
   |
   v
LLM call
   |
   +--> Tool call requested? --> Validate args --> Run Python tool --> Return result --> LLM call
   |
   v
Final response
   |
   v
Pydantic validation
   |
   v
Typed result
```

## Key design principles

### 1. Type safety end to end

Pydantic AI uses Python type hints and Pydantic models across the entire agent boundary.

```python
from pydantic import BaseModel

class ExtractedInvoice(BaseModel):
    invoice_id: str
    vendor: str
    total: float
    currency: str
```

Instead of parsing raw model text, you declare the expected structure. The framework validates the model response and raises a clear error if it is invalid.

### 2. Tools are normal Python functions

A tool is just a function with a docstring and type hints.

```python
from pydantic_ai import RunContext

async def get_order_status(
    ctx: RunContext[AppDependencies],
    order_id: str,
) -> str:
    """Return the current status for an order."""
    return await ctx.deps.db.get_order_status(order_id)
```

The model sees:

- Function name
- Docstring
- Parameter names
- Parameter types
- Return type

Your code controls execution, authorization, validation, and side effects.

### 3. Dependency injection

Dependencies carry runtime context into tools without exposing secrets or connections to the model.

```python
from dataclasses import dataclass

@dataclass
class AppDependencies:
    user_id: str
    db: Database
    http: HttpClient
```

This enables clean testing:

```python
deps = AppDependencies(
    user_id="test-user",
    db=FakeDatabase(),
    http=FakeHttpClient(),
)
```

### 4. Provider-agnostic model access

A model is usually just a string:

```python
agent = Agent("openai:gpt-4.1")
agent = Agent("anthropic:claude-sonnet-4")
agent = Agent("google-gla:gemini-2.5-pro")
agent = Agent("ollama:llama3.1")
```

The same agent logic can often run against another provider by changing the model identifier. This matters for:

- Avoiding vendor lock-in.
- Cost optimization.
- Model fallback.
- Local development with Ollama.
- Privacy-sensitive deployments.
- Benchmarking models against the same task.

### 5. Capabilities as composable building blocks

A capability bundles related behavior:

- Tools
- Instructions
- Hooks
- Model settings
- Context

Examples include:

- Web search
- Filesystem access
- Shell execution
- Repository context
- Memory
- Guardrails
- Planning
- Sub-agents
- MCP integration

Instead of copying prompts and tools across projects, you compose capabilities.

```python
agent = Agent(
    "openai:gpt-4.1",
    capabilities=[
        WebSearch(),
        Coder(),
    ],
)
```

## What Pydantic AI does not do

Pydantic AI is not:

- A model provider.
- A vector database.
- A workflow engine by itself.
- A hosted agent platform.
- A replacement for your application backend.

It is the **agent application layer** between your Python services and LLM providers.

## Real-world problems it solves

### Problem 1: Unreliable unstructured LLM output

**Before**

```python
response = llm.generate(prompt)
data = json.loads(response)
```

This fails when the model returns markdown, explanation text, malformed JSON, or missing fields.

**With Pydantic AI**

```python
class Invoice(BaseModel):
    invoice_id: str
    total: float

result = await agent.run(document_text, output_type=Invoice)
invoice = result.output
```

The output is validated and typed.

### Problem 2: Unsafe or unclear tool execution

Agents often need to query databases, call APIs, read files, or trigger workflows. Pydantic AI makes tool boundaries explicit.

```python
@support_agent.tool
async def block_card(
    ctx: RunContext[SupportDependencies],
    reason: str,
) -> str:
    """Block a customer card after fraud verification."""
    return await ctx.deps.bank.block_card(
        customer_id=ctx.deps.customer_id,
        reason=reason,
    )
```

The model can request the action, but your Python code decides whether it is allowed and how it is executed.

### Problem 3: Difficult testing

You can replace real models and dependencies with test doubles.

```python
test_agent = Agent("test")
```

The `test` model runs offline, allowing you to test agent logic, tools, validation, and workflows without spending tokens or calling external APIs.

### Problem 4: Poor observability

Agent systems involve multiple model calls, tool calls, retries, and external services. Pydantic AI emits OpenTelemetry-compatible traces for model and tool activity.

You can send those traces to:

- Pydantic Logfire
- Jaeger
- Grafana Tempo
- Honeycomb
- Datadog
- Any OTLP-compatible backend

### Problem 5: Long-running and failure-prone workflows

An agent may need to run for minutes, hours, or days. Durable execution lets an agent resume after a process restart.

Supported execution engines include:

- Temporal
- DBOS
- Prefect
- Restate
- AWS Lambda
- Airflow
- Absurd
- pgtask

This is useful for workflows involving human approval, external systems, retries, or scheduled work.

### Problem 6: Hard-to-measure agent quality

Pydantic Evals evaluates:

- Final answers
- Tool-call sequences
- Agent trajectories
- Dataset-based test cases
- Samples of live production traffic

This shifts agent quality from “it looked good” to measurable, repeatable evaluation.

## Real-world use cases

### 1. Customer support agent

An agent answers customer questions using internal systems.

```text
Customer: “Where is my refund?”

Agent:
1. Identifies customer from authenticated session.
2. Calls refund_status tool.
3. Returns a structured answer.
4. Escalates if policy thresholds are exceeded.
```

Useful outputs:

```python
class SupportResult(BaseModel):
    answer: str
    escalate: bool
    risk_score: int
```

### 2. Document and invoice extraction

Extract structured fields from PDFs, emails, contracts, receipts, or forms.

```text
Raw document -> LLM extraction -> validated Pydantic object -> ERP/database
```

Examples:

- Invoice processing
- KYC document review
- Contract clause extraction
- Insurance claim intake
- Resume parsing
- Purchase-order matching

### 3. Internal enterprise copilot

A chat assistant connected to company knowledge and systems.

Tools may include:

- Search Confluence or SharePoint
- Query a data warehouse
- Create a Jira ticket
- Check incident status
- Retrieve runbooks
- Trigger a deployment approval

The agent becomes an interface over governed internal APIs rather than a direct database chatbot.

### 4. SRE incident assistant

For an SRE or platform team, an agent can assist with:

- Incident triage
- Log analysis
- Runbook retrieval
- Kubernetes diagnostics
- Alert enrichment
- Change-risk assessment
- Post-incident report drafting

Example flow:

```text
PagerDuty alert
  -> Agent receives alert context
  -> Queries metrics, logs, deployments
  -> Identifies likely failure domain
  -> Suggests remediation
  -> Requests human approval before executing changes
```

### 5. Coding agent

A coding agent can:

- Read repository files
- Search code
- Run tests
- Apply patches
- Review pull requests
- Generate migration plans
- Explain failures

Safety controls are important:

- Restrict filesystem paths.
- Allowlist shell commands.
- Require approval for destructive operations.
- Run in a sandbox or container.

### 6. Data engineering assistant

An agent can help analysts and engineers work with data:

- Translate natural language to SQL.
- Validate generated SQL.
- Explain query results.
- Recommend transformations.
- Generate dbt models.
- Investigate pipeline failures.

A safer design has the agent generate SQL, validate it, run it through a controlled query service, and return summarized results.

### 7. Financial operations agent

Examples:

- Transaction categorization
- Fraud triage
- Expense-report review
- Reconciliation assistance
- Risk scoring
- Compliance checklist generation

High-risk actions should remain human-approved.

### 8. Multi-agent research workflow

A research agent can coordinate specialized sub-agents:

```text
Coordinator agent
  -> Web research agent
  -> Internal document agent
  -> Data analysis agent
  -> Report-writing agent
```

Pydantic Graph is useful when the workflow requires deterministic branching, retries, approvals, or parallel execution.

## Simplified mental model

Think of Pydantic AI as:

```text
FastAPI-style typed boundaries + an LLM agent loop
```

| Traditional software | Pydantic AI equivalent |
|---|---|
| HTTP request schema | User message and dependencies |
| Controller | Agent |
| Service layer | Tools |
| Response schema | `output_type` |
| Dependency injection | `deps_type` |
| Middleware | Capabilities and hooks |
| Observability | OpenTelemetry / Logfire |
| Integration tests | Evals and test model |
| Workflow engine | Durable execution / Pydantic Graph |

## Hands-on tutorial

This tutorial builds a small **customer support agent** that can:

- Look up a customer’s account balance.
- Classify support risk.
- Return a validated structured response.

### Prerequisites

- Python 3.11 or newer
- `uv` or `pip`
- An API key for at least one provider, such as OpenAI or Anthropic
- Optional: Ollama for a local model

### Step 1: Create the project

```bash
mkdir pydantic-ai-demo
cd pydantic-ai-demo

uv init
uv add pydantic-ai
```

Or with pip:

```bash
python -m venv .venv
source .venv/bin/activate

pip install pydantic-ai
```

### Step 2: Configure the model provider

For OpenAI:

```bash
export OPENAI_API_KEY="your-api-key"
```

For Anthropic:

```bash
export ANTHROPIC_API_KEY="your-api-key"
```

For a local Ollama model:

```bash
ollama pull llama3.1
```

### Step 3: Create the database fake

Create `database.py`:

```python
from dataclasses import dataclass


@dataclass
class DatabaseConn:
    customers: dict[int, dict]

    async def customer_name(self, id: int) -> str:
        return self.customers[id]["name"]

    async def customer_balance(
        self,
        id: int,
        include_pending: bool = False,
    ) -> float:
        customer = self.customers[id]
        balance = customer["balance"]
        if include_pending:
            balance += customer.get("pending", 0)
        return balance
```

### Step 4: Define dependencies and output

Create `agent.py`:

```python
from dataclasses import dataclass

from pydantic import BaseModel, Field

from database import DatabaseConn


@dataclass
class SupportDependencies:
    customer_id: int
    db: DatabaseConn


class SupportOutput(BaseModel):
    support_advice: str = Field(description="Advice returned to the customer")
    block_card: bool = Field(description="Whether to block the customer's card")
    risk: int = Field(description="Risk level from 0 to 10", ge=0, le=10)
```

### Step 5: Define the agent and tools

Append this to `agent.py`:

```python
from pydantic_ai import Agent, RunContext


support_agent = Agent(
    "openai:gpt-4.1",
    deps_type=SupportDependencies,
    output_type=SupportOutput,
    instructions=(
        "You are a bank support agent. "
        "Answer customer questions using the available tools. "
        "Assess the risk level of the request. "
        "Only recommend blocking a card for clear security concerns."
    ),
)


@support_agent.tool
async def customer_balance(
    ctx: RunContext[SupportDependencies],
    include_pending: bool,
) -> float:
    """Return the customer's current account balance."""
    return await ctx.deps.db.customer_balance(
        id=ctx.deps.customer_id,
        include_pending=include_pending,
    )
```

### Step 6: Run the agent

Append this to `agent.py`:

```python
import asyncio


async def main():
    db = DatabaseConn(
        customers={
            123: {
                "name": "Alice",
                "balance": 500.00,
                "pending": 25.50,
            }
        }
    )

    deps = SupportDependencies(
        customer_id=123,
        db=db,
    )

    result = await support_agent.run(
        "What is my current balance, including pending transactions?",
        deps=deps,
    )

    print(result.output)


if __name__ == "__main__":
    asyncio.run(main())
```

Run it:

```bash
python agent.py
```

Expected output shape:

```python
SupportOutput(
    support_advice="Your current balance, including pending transactions, is $525.50.",
    block_card=False,
    risk=1,
)
```

The exact wording varies by model, but the structure is guaranteed by `SupportOutput`.

### Step 7: Test without an LLM

Create `test_agent.py`:

```python
import pytest

from agent import SupportDependencies, support_agent
from database import DatabaseConn


@pytest.mark.asyncio
async def test_balance_tool():
    db = DatabaseConn(
        customers={
            123: {
                "name": "Alice",
                "balance": 100.0,
                "pending": 20.0,
            }
        }
    )

    deps = SupportDependencies(customer_id=123, db=db)

    result = await support_agent.run(
        "What is my balance?",
        deps=deps,
    )

    assert result.output.risk >= 0
    assert result.output.risk <= 10
    assert isinstance(result.output.block_card, bool)
```

Install test dependencies:

```bash
uv add --dev pytest pytest-asyncio
```

Run:

```bash
pytest
```

For offline testing, replace the provider model with:

```python
support_agent = Agent(
    "test",
    deps_type=SupportDependencies,
    output_type=SupportOutput,
)
```

### Step 8: Add observability

Install Logfire:

```bash
uv add logfire
```

Add this near the top of `agent.py`:

```python
import logfire

logfire.configure()
logfire.instrument_pydantic_ai()
```

Run the agent again. You should see traces for:

- The agent run
- Each LLM call
- Each tool invocation
- Tool arguments and results
- Errors and retries

If you prefer vendor-neutral observability, export OpenTelemetry spans to your existing backend.

### Step 9: Add a second tool

Add a card-blocking tool:

```python
@support_agent.tool
async def block_card(
    ctx: RunContext[SupportDependencies],
    reason: str,
) -> str:
    """Block the customer's card for security reasons."""
    # In production, enforce authentication, authorization, and audit logging.
    return f"Card blocked for customer {ctx.deps.customer_id}: {reason}"
```

Now ask:

```python
result = await support_agent.run(
    "I lost my card and think someone may have used it.",
    deps=deps,
)
```

The model may call `customer_balance` and/or `block_card`, depending on its reasoning and your instructions.

### Step 10: Add a guardrail concept

Never rely on the model alone for dangerous actions. Add checks inside the tool:

```python
@support_agent.tool
async def block_card(
    ctx: RunContext[SupportDependencies],
    reason: str,
) -> str:
    """Block the customer's card after verification."""

    if len(reason) < 10:
        return "Refused: insufficient justification provided."

    if not ctx.deps.db.customer_exists(ctx.deps.customer_id):
        return "Refused: customer not found."

    return await ctx.deps.bank.block_card(
        customer_id=ctx.deps.customer_id,
        reason=reason,
    )
```

Production rule: **the LLM proposes; your application authorizes and executes.**

## Production architecture pattern

```text
Client
  |
  v
API Gateway / Auth
  |
  v
Agent Service
  |
  +--> Pydantic AI Agent
  |       |
  |       +--> Model Gateway / Provider
  |       +--> Tool layer
  |       +--> Policy / authorization
  |       +--> Audit log
  |
  +--> Durable execution engine
  +--> Observability backend
  +--> Evaluation pipeline
  +--> Vector / document search
  +--> Business systems
```

### Recommended production controls

- Authenticate the user before constructing dependencies.
- Pass only the minimum necessary context to the agent.
- Keep secrets in a secret manager, not in prompts.
- Validate every tool argument.
- Enforce authorization inside tools.
- Rate-limit model and tool calls.
- Log prompts, tool calls, outputs, costs, latency, and errors.
- Use structured outputs for machine-readable decisions.
- Use human approval for destructive or irreversible actions.
- Run evals before deployment and on sampled production traffic.
- Separate read-only tools from write tools.
- Sandbox code execution and shell access.
- Set token, cost, and execution-time budgets.

## When to choose Pydantic AI

Choose Pydantic AI when you want:

- Python-native agent development.
- Strong typing and validation.
- Easy model-provider swapping.
- Testable tool architecture.
- OpenTelemetry-based observability.
- Structured outputs for downstream systems.
- Composable agent capabilities.
- Production workflows with durable execution.

It is especially strong for teams already comfortable with Python, Pydantic, FastAPI-style dependency injection, and typed service boundaries.

## Quick reference

```python
from dataclasses import dataclass
from pydantic import BaseModel
from pydantic_ai import Agent, RunContext


@dataclass
class Deps:
    user_id: str
    db: Database


class Answer(BaseModel):
    response: str
    confidence: float


agent = Agent(
    "openai:gpt-4.1",
    deps_type=Deps,
    output_type=Answer,
    instructions="Answer using the provided tools.",
)


@agent.tool
async def lookup_data(ctx: RunContext[Deps], query: str) -> str:
    """Look up internal data for the user."""
    return await ctx.deps.db.search(query)


async def main():
    deps = Deps(user_id="u_123", db=Database())
    result = await agent.run("Find my latest invoice", deps=deps)
    print(result.output.response)
```