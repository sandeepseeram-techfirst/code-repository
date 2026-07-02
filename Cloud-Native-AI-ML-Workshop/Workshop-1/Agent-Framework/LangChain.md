# LangChain Middleware: Deep Dive, Simplified

LangChain Middleware is a **cross-cutting control layer for AI agents**. It lets you intercept, inspect, modify, retry, secure, and terminate an agent’s execution at well-defined points—without rewriting the agent loop or embedding operational logic inside every tool.

In simple terms: **the model decides what to do; middleware enforces how, when, whether, and safely it can do it.**

***

## 1. What Problem Does It Solve?

A production AI agent is not just “prompt + LLM + tools.” It must survive real-world failures and constraints:

- LLM APIs fail, rate-limit, or time out.
- Tools call flaky external APIs, databases, or shell commands.
- Agents can enter expensive loops.
- Long conversations exceed context windows.
- Users may submit PII, secrets, or unsafe requests.
- High-risk actions such as sending email, deleting data, or issuing payments require approval.
- Enterprises need audit logs, cost controls, guardrails, and predictable behavior.

Without middleware, these concerns get scattered across prompts, tool functions, application code, and deployment scripts. Middleware centralizes them into reusable, testable components.

**Core value proposition:** separate *agent intelligence* from *agent governance*.

***

## 2. Simplified Mental Model

Think of LangChain Middleware like an **HTTP middleware stack**, but for an AI agent loop.

```text
User request
   ↓
before_agent hooks
   ↓
Agent loop:
   before_model hooks
   wrap_model_call middleware
   LLM call
   after_model hooks
   wrap_tool_call middleware
   Tool execution
   after_tool hooks
   repeat until no more tool calls
   ↓
after_agent hooks
   ↓
Final response
```

Each middleware can:

- Observe state.
- Modify prompts, model requests, tool selections, or responses.
- Update agent state.
- Retry or replace a call.
- Short-circuit execution.
- Pause for human approval.
- Emit logs, metrics, traces, or security events.

***

## 3. Architecture and Design

### 3.1 Agent Loop

The base LangChain agent follows a loop:

1. Receive user input.
2. Call the LLM.
3. If the LLM requests tools, execute them.
4. Feed tool results back to the LLM.
5. Repeat until the model produces a final answer with no further tool calls.

Middleware inserts hooks around each major stage of this loop.

### 3.2 Middleware as Graph Hooks

Middleware is **not a separate runtime**. It runs inside the compiled LangGraph graph produced by `create_agent`.

That means an agent with middleware can be embedded as a node or subgraph inside a larger workflow. Its middleware continues working in that larger graph.

Example architecture:

```text
StateGraph
├── classify_request
├── routing logic
├── support_agent (with middleware)
├── billing_agent (with middleware)
└── final_response
```

Each specialized agent can carry its own middleware: PII redaction, approval requirements, retry behavior, call limits, and logging.

### 3.3 Two Hook Styles

| Hook style | Purpose | Examples |
|---|---|---|
| **Node-style** | Run sequentially at a lifecycle point | Logging, validation, state updates |
| **Wrap-style** | Wrap around a model or tool call | Retry, fallback, caching, transformation |

### Node-Style Hooks

| Hook | When it runs |
|---|---|
| `before_agent` | Once before the agent starts |
| `before_model` | Before every LLM call |
| `after_model` | After every LLM response |
| `after_agent` | Once after the agent finishes |

### Wrap-Style Hooks

| Hook | When it runs |
|---|---|
| `wrap_model_call` | Around every LLM call |
| `wrap_tool_call` | Around every tool execution |

Wrap hooks control whether the inner handler runs:

- **Zero times:** short-circuit and return a synthetic response.
- **Once:** normal execution.
- **Multiple times:** retry or fallback logic.

***

## 4. Execution Order

For this configuration:

```python
middleware=[middleware1, middleware2, middleware3]
```

Execution behaves like nested layers:

```text
before_agent: 1 → 2 → 3
before_model: 1 → 2 → 3
wrap_model_call:
    middleware1
      └── middleware2
            └── middleware3
                  └── model
after_model: 3 → 2 → 1
after_agent: 3 → 2 → 1
```

Key rules:

- `before_*` hooks run in declaration order.
- `after_*` hooks run in reverse order.
- `wrap_*` hooks nest like function calls.
- The first middleware in the list is the outermost wrapper.
- Place critical controls—security, rate limiting, approvals—early in the list.

***

## 5. State and Control Flow

### 5.1 State Updates

Node-style hooks return a dictionary that is merged into agent state through LangGraph reducers.

Example:

```python
@after_model
def increment_counter(state, runtime):
    return {
        "model_call_count": state.get("model_call_count", 0) + 1
    }
```

Middleware can extend the state schema to carry custom operational data:

```python
class CustomState(AgentState):
    model_call_count: NotRequired[int]
    user_id: NotRequired[str]
    blocked_reason: NotRequired[str]
```

This enables cross-cutting features such as:

- Token or cost accounting.
- Request tracing.
- User-specific permissions.
- Loop detection.
- Security flags.
- Retry counters.

### 5.2 Agent Jumps

Middleware can redirect the agent graph:

| Jump target | Effect |
|---|---|
| `"end"` | End agent execution |
| `"tools"` | Jump directly to tool execution |
| `"model"` | Jump back to the model node |

Example: stop execution if a safety rule is violated.

```python
@after_model
@hook_config(can_jump_to=["end"])
def block_unsafe_output(state, runtime):
    last = state["messages"][-1]

    if "BLOCKED" in last.content:
        return {
            "messages": [AIMessage("I cannot respond to that request.")],
            "jump_to": "end",
        }

    return None
```

This is powerful for guardrails: instead of hoping the model behaves, middleware can deterministically terminate or redirect execution.

***

## 6. Built-In Middleware Capabilities

LangChain ships production-oriented middleware for common agent concerns.

| Middleware | Real-world purpose |
|---|---|
| `ToolErrorMiddleware` | Converts tool exceptions into model-readable error messages |
| `ToolRetryMiddleware` | Retries failed tool calls with backoff |
| `ModelRetryMiddleware` | Retries transient LLM API failures |
| `ModelFallbackMiddleware` | Switches to backup models during outages |
| `SummarizationMiddleware` | Compresses old conversation history near context limits |
| `HumanInTheLoopMiddleware` | Pauses before risky tool execution |
| `ModelCallLimitMiddleware` | Prevents runaway LLM usage and cost |
| `ToolCallLimitMiddleware` | Limits tool usage globally or per tool |
| `PIIMiddleware` | Detects and handles sensitive data |
| `TodoListMiddleware` | Adds planning and task-tracking capability |
| `LLMToolSelectorMiddleware` | Selects only relevant tools before the main model call |
| `ProviderToolSearchMiddleware` | Defers tool discovery to provider-side search |
| `ShellToolMiddleware` | Gives agents a controlled shell execution environment |
| `FilesystemMiddleware` | Gives agents file-based short- and long-term context |
| `SubagentMiddleware` | Enables delegation to subagents |
| `ContextEditingMiddleware` | Trims or clears tool results to manage context |
| `RubricGradingMiddleware` | Lets an agent evaluate output against a rubric |

***

## 7. Key Technical Insights

### 7.1 Middleware Is an Agent Reliability Layer

The biggest insight is that middleware turns an agent from a demo into a production system.

A basic agent optimizes for capability:

```text
Can the model complete the task?
```

A middleware-equipped agent optimizes for operability:

```text
Can it complete the task safely, economically, observably,
recoverably, and within policy?
```

### 7.2 Separation of Concerns

Middleware cleanly separates:

| Concern | Owner |
|---|---|
| Reasoning and planning | LLM |
| Business capability | Tools |
| Orchestration | LangGraph |
| Policy, safety, retries, limits | Middleware |
| Workflow topology | Outer StateGraph |

This is analogous to separating application logic from Kubernetes admission control, service-mesh policies, or API-gateway middleware.

### 7.3 Wrap Hooks Are Control Points

`wrap_model_call` and `wrap_tool_call` are the most architecturally important hooks because they can replace or multiply execution.

Use cases:

- Retry a failed model call.
- Fall back from a premium model to a cheaper one.
- Cache identical requests.
- Redact sensitive fields before a model sees them.
- Block a tool call entirely.
- Add tracing spans.
- Enforce per-tool quotas.
- Convert exceptions into structured feedback.

### 7.4 State Makes Middleware Composable

Middleware becomes more useful when it can share state.

For example:

1. `before_model` records the incoming request category.
2. `wrap_tool_call` uses that category to decide allowed tools.
3. `after_model` records cost, tokens, and policy decisions.
4. `after_agent` emits an audit event.

This creates an observable, policy-aware execution pipeline.

### 7.5 Middleware Is Not a Sandbox by Itself

Middleware can enforce policy, but it does not automatically make arbitrary tool execution safe.

For example, `ShellToolMiddleware` can expose shell access, but using `HostExecutionPolicy` gives the agent broad host access. For untrusted workloads, use container or sandbox-based execution policies, least-privilege credentials, network controls, and output redaction.

**Security principle:** middleware is a control plane; sandboxing, identity, secrets management, and network isolation remain separate security controls.

***

## 8. Real-World Problems Solved

### 8.1 Cost Control

Agents can call expensive models repeatedly, especially when tools return large results or the model keeps retrying.

Middleware solves this with:

- Model call limits.
- Tool call limits.
- Dynamic model selection.
- Context summarization.
- Tool filtering.

Example policy:

```text
Use a small model for simple requests.
Use a larger model only for complex multi-step tasks.
Stop after 10 model calls or 20 tool calls.
```

### 8.2 Reliability and Resilience

External dependencies fail. Middleware provides:

- Retries with exponential backoff.
- Jitter to avoid thundering-herd behavior.
- Model fallback across providers.
- Tool error normalization.
- Graceful failure messages.

This mirrors classic SRE resilience patterns: timeout, retry, backoff, circuit breaking, and fallback.

### 8.3 Context-Window Management

Long agent conversations accumulate messages, tool outputs, search results, and logs.

`SummarizationMiddleware` compresses older history while preserving recent messages. This prevents context overflow while retaining task continuity.

Typical policy:

```python
SummarizationMiddleware(
    model="small-model",
    trigger=("tokens", 4000),
    keep=("messages", 20),
)
```

### 8.4 Human Oversight

Some actions should never execute autonomously:

- Sending email.
- Creating tickets.
- Writing to production databases.
- Deploying infrastructure.
- Issuing payments.
- Deleting resources.

`HumanInTheLoopMiddleware` pauses execution and requires approval, editing, or rejection.

This is essential for regulated industries, internal enterprise tools, and any agent with write access.

### 8.5 Data Protection and Compliance

Agents often process user messages, support tickets, logs, documents, and API responses containing sensitive data.

`PIIMiddleware` can:

- Redact emails, credit cards, IPs, URLs, and MAC addresses.
- Mask partial values.
- Hash identifiers.
- Block requests containing secrets.
- Apply custom detectors for internal identifiers or API keys.

Example:

```python
PIIMiddleware("api_key", detector=r"sk-[a-zA-Z0-9]{32}", strategy="block")
```

### 8.6 Tool Sprawl

Agents with dozens of tools suffer from:

- Larger prompts.
- Higher token cost.
- Worse tool-selection accuracy.
- More opportunities for incorrect calls.

Middleware can dynamically expose only relevant tools:

```python
@wrap_model_call
def select_tools(request, handler):
    relevant = select_relevant_tools(request.state, request.runtime)
    return handler(request.override(tools=relevant))
```

This is especially useful for enterprise agents connected to many internal systems.

***

## 9. Real-World Use Cases

### 9.1 Customer Support Agent

**Scenario:** An agent answers customer questions, reads orders, issues refunds, and escalates tickets.

**Middleware stack:**

```text
PIIMiddleware
HumanInTheLoopMiddleware
ToolCallLimitMiddleware
ToolRetryMiddleware
SummarizationMiddleware
LoggingMiddleware
```

**Behavior:**

- Redact customer PII before it reaches the model.
- Require approval before issuing a refund.
- Limit database queries.
- Retry transient CRM or payment API failures.
- Summarize long support threads.
- Log every tool invocation for audit.

### 9.2 SRE Incident Assistant

**Scenario:** An on-call assistant investigates alerts, queries metrics, reads runbooks, and proposes remediation.

**Middleware stack:**

```text
PIIMiddleware
LLMToolSelectorMiddleware
ToolRetryMiddleware
ModelFallbackMiddleware
ModelCallLimitMiddleware
ShellToolMiddleware with sandbox policy
AuditLoggingMiddleware
```

**Behavior:**

- Select only relevant observability tools.
- Retry temporary Prometheus, Grafana, or API failures.
- Fall back to another model during provider disruption.
- Limit shell commands and run them in an isolated container.
- Prevent automatic production changes without approval.

### 9.3 Kubernetes Operations Agent

**Scenario:** An agent diagnoses pod failures, inspects logs, and suggests fixes.

**Middleware stack:**

```text
ToolCallLimitMiddleware
HumanInTheLoopMiddleware
ToolErrorMiddleware
ToolRetryMiddleware
PIIMiddleware
Audit trail middleware
```

**Behavior:**

- Read-only tools run automatically.
- `kubectl delete`, `kubectl scale`, or Helm upgrades require approval.
- Tool failures are returned as structured errors.
- Sensitive namespace names, tokens, or secrets are redacted.
- Every proposed change is recorded.

### 9.4 Financial Operations Agent

**Scenario:** An agent reconciles transactions, detects anomalies, and drafts payment actions.

**Middleware stack:**

```text
PIIMiddleware
HumanInTheLoopMiddleware
ModelCallLimitMiddleware
ToolCallLimitMiddleware
ModelFallbackMiddleware
Audit middleware
```

**Behavior:**

- Mask account and card numbers.
- Require human approval before payment submission.
- Cap expensive model calls.
- Maintain provider redundancy.
- Preserve a complete decision trail.

### 9.5 Developer Productivity Agent

**Scenario:** An agent fixes bugs, runs tests, edits files, and prepares pull requests.

**Middleware stack:**

```text
TodoListMiddleware
FilesystemMiddleware
ShellToolMiddleware with Docker isolation
ToolRetryMiddleware
ModelCallLimitMiddleware
HumanInTheLoopMiddleware
```

**Behavior:**

- Plan multi-step work with a to-do list.
- Store intermediate artifacts on a filesystem.
- Execute tests in a container.
- Retry flaky test commands.
- Require approval before pushing code or opening a PR.

***

## 10. Hands-On Tutorial

This tutorial builds a small production-style agent with:

- A custom tool.
- Logging.
- Retry logic.
- Model-call limits.
- Human approval for a risky action.
- PII redaction.

### Step 1: Install Dependencies

```bash
python -m venv .venv
source .venv/bin/activate

pip install -U langchain langgraph
```

Set your model provider credentials according to the model you use:

```bash
export OPENAI_API_KEY="your-key"
```

Or use another provider supported by your LangChain installation.

***

### Step 2: Create a Simple Tool

Create `agent_demo.py`:

```python
from langchain.tools import tool


@tool
def get_order_status(order_id: str) -> str:
    """Look up the status of a customer order."""

    # Replace with a real database, API, or service call.
    orders = {
        "ORD-1001": "Shipped",
        "ORD-1002": "Processing",
        "ORD-1003": "Delivered",
    }

    if order_id not in orders:
        raise ValueError(f"Unknown order ID: {order_id}")

    return f"Order {order_id} status: {orders[order_id]}"


@tool
def issue_refund(order_id: str, amount: float) -> str:
    """Issue a refund for an order. This is a high-risk action."""

    # Replace with a real payment-provider call.
    return f"Refund of {amount} issued for order {order_id}."
```

`get_order_status` is low risk.  
`issue_refund` is high risk and should require human approval.

***

### Step 3: Add Basic Middleware

Create an agent with retry, call limits, and human approval:

```python
from langchain.agents import create_agent
from langchain.agents.middleware import (
    HumanInTheLoopMiddleware,
    ModelCallLimitMiddleware,
    ModelRetryMiddleware,
    ToolRetryMiddleware,
)
from langgraph.checkpoint.memory import InMemorySaver

from agent_demo import get_order_status, issue_refund

agent = create_agent(
    model="your-model-id",
    tools=[get_order_status, issue_refund],
    checkpointer=InMemorySaver(),
    middleware=[
        ModelRetryMiddleware(
            max_retries=2,
            backoff_factor=2.0,
            initial_delay=1.0,
        ),
        ToolRetryMiddleware(
            max_retries=2,
            backoff_factor=2.0,
            initial_delay=1.0,
        ),
        ModelCallLimitMiddleware(
            run_limit=8,
            thread_limit=25,
            exit_behavior="end",
        ),
        HumanInTheLoopMiddleware(
            interrupt_on={
                "issue_refund": {
                    "allowed_decisions": ["approve", "edit", "reject"],
                },
                "get_order_status": False,
            }
        ),
    ],
)
```

What each middleware does:

| Middleware | Purpose |
|---|---|
| `ModelRetryMiddleware` | Handles temporary LLM API failures |
| `ToolRetryMiddleware` | Handles transient tool/API failures |
| `ModelCallLimitMiddleware` | Stops runaway or expensive agent loops |
| `HumanInTheLoopMiddleware` | Requires approval before refunds |

***

### Step 4: Invoke the Agent

Append this to `agent_demo.py`:

```python
result = agent.invoke(
    {
        "messages": [
            {
                "role": "user",
                "content": "What is the status of order ORD-1001?",
            }
        ]
    },
    config={"configurable": {"thread_id": "customer-42"}},
)

print(result["messages"][-1].content)
```

Run it:

```bash
python agent_demo.py
```

Expected behavior:

1. The agent calls the model.
2. The model chooses `get_order_status`.
3. The tool returns the order status.
4. The model produces the final answer.
5. No approval interrupt occurs because `get_order_status` is not gated.

***

### Step 5: Trigger Human Approval

Change the user request:

```python
result = agent.invoke(
    {
        "messages": [
            {
                "role": "user",
                "content": "Issue a refund of 25.00 for order ORD-1002.",
            }
        ]
    },
    config={"configurable": {"thread_id": "customer-42"}},
)
```

The agent should pause before executing `issue_refund`.

In a real application, you would surface the pending tool call to a reviewer in a UI, Slack approval flow, ticketing system, or internal admin console.

The reviewer can choose:

- `approve`: execute the refund.
- `edit`: modify arguments before execution.
- `reject`: prevent execution.

***

### Step 6: Add Custom Logging Middleware

Create a class-based middleware that records model and tool activity:

```python
from typing import Any, Callable

from langchain.agents.middleware import AgentMiddleware
from langchain.agents.middleware import (
    ModelRequest,
    ModelResponse,
)
from langchain.messages import ToolMessage
from langchain.tools.tool_node import ToolCallRequest


class AuditMiddleware(AgentMiddleware):
    def before_model(self, state, runtime):
        print("[AUDIT] Preparing model call")
        return None

    def after_model(self, state, runtime):
        last_message = state["messages"][-1]
        print(f"[AUDIT] Model response: {last_message.content}")
        return None

    def wrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], ToolMessage],
    ):
        tool_name = request.tool_call["name"]
        tool_args = request.tool_call["args"]

        print(f"[AUDIT] Tool requested: {tool_name}")
        print(f"[AUDIT] Tool arguments: {tool_args}")

        try:
            result = handler(request)
            print(f"[AUDIT] Tool succeeded: {tool_name}")
            return result
        except Exception as exc:
            print(f"[AUDIT] Tool failed: {tool_name}: {type(exc).__name__}")
            raise
```

Add it to the middleware list:

```python
agent = create_agent(
    model="your-model-id",
    tools=[get_order_status, issue_refund],
    checkpointer=InMemorySaver(),
    middleware=[
        AuditMiddleware(),
        ModelRetryMiddleware(max_retries=2),
        ToolRetryMiddleware(max_retries=2),
        ModelCallLimitMiddleware(run_limit=8, thread_limit=25),
        HumanInTheLoopMiddleware(
            interrupt_on={
                "issue_refund": {
                    "allowed_decisions": ["approve", "edit", "reject"],
                }
            }
        ),
    ],
)
```

Now every model and tool interaction produces an audit trail.

***

### Step 7: Add PII Protection

Add PII middleware to prevent sensitive data from reaching the model:

```python
from langchain.agents.middleware import PIIMiddleware

pii_middleware = PIIMiddleware(
    "email",
    strategy="redact",
    apply_to_input=True,
)

credit_card_middleware = PIIMiddleware(
    "credit_card",
    strategy="mask",
    apply_to_input=True,
)
```

Update the agent:

```python
agent = create_agent(
    model="your-model-id",
    tools=[get_order_status, issue_refund],
    checkpointer=InMemorySaver(),
    middleware=[
        AuditMiddleware(),
        pii_middleware,
        credit_card_middleware,
        ModelRetryMiddleware(max_retries=2),
        ToolRetryMiddleware(max_retries=2),
        ModelCallLimitMiddleware(run_limit=8, thread_limit=25),
        HumanInTheLoopMiddleware(
            interrupt_on={
                "issue_refund": {
                    "allowed_decisions": ["approve", "edit", "reject"],
                }
            }
        ),
    ],
)
```

If a user sends:

```text
My email is jane@example.com and my card is 4111 1111 1111 1111.
```

The middleware can transform it before the model sees it:

```text
My email is [REDACTED_EMAIL] and my card is ****-****-****-1111.
```

***

### Step 8: Add Dynamic Model Selection

Use a cheaper model for simple requests and a stronger model for complex requests:

```python
from langchain.chat_models import init_chat_model
from langchain.agents.middleware import wrap_model_call

simple_model = init_chat_model("your-small-model-id")
complex_model = init_chat_model("your-large-model-id")


@wrap_model_call
def dynamic_model(request, handler):
    if len(request.messages) > 10:
        model = complex_model
    else:
        model = simple_model

    return handler(request.override(model=model))
```

Add it before retry middleware:

```python
middleware=[
    AuditMiddleware(),
    pii_middleware,
    credit_card_middleware,
    dynamic_model,
    ModelRetryMiddleware(max_retries=2),
    ToolRetryMiddleware(max_retries=2),
    ModelCallLimitMiddleware(run_limit=8, thread_limit=25),
    HumanInTheLoopMiddleware(
        interrupt_on={
            "issue_refund": {
                "allowed_decisions": ["approve", "edit", "reject"],
            }
        }
    ),
]
```

This is a practical cost-optimization pattern: avoid paying premium-model prices for trivial requests.

***

### Step 9: Add a Safety Guardrail

Block requests that contain an obvious secret pattern:

```python
from langchain.agents.middleware import (
    after_model,
    hook_config,
)
from langchain.messages import AIMessage


@after_model
@hook_config(can_jump_to=["end"])
def block_sensitive_output(state, runtime):
    last_message = state["messages"][-1]

    if "sk-" in str(last_message.content):
        return {
            "messages": [
                AIMessage("I cannot return sensitive credentials.")
            ],
            "jump_to": "end",
        }

    return None
```

Add it to the middleware list:

```python
middleware=[
    AuditMiddleware(),
    pii_middleware,
    credit_card_middleware,
    block_sensitive_output,
    dynamic_model,
    ModelRetryMiddleware(max_retries=2),
    ToolRetryMiddleware(max_retries=2),
    ModelCallLimitMiddleware(run_limit=8, thread_limit=25),
    HumanInTheLoopMiddleware(
        interrupt_on={
            "issue_refund": {
                "allowed_decisions": ["approve", "edit", "reject"],
            }
        }
    ),
]
```

This demonstrates deterministic enforcement: even if the model attempts to expose a secret, middleware can stop the response.

***

## 11. Production Reference Architecture

```text
                       ┌────────────────────────┐
                       │      Client / UI       │
                       └───────────┬────────────┘
                                   │
                       ┌───────────▼────────────┐
                       │     API / Agent Service │
                       └───────────┬────────────┘
                                   │
                    ┌──────────────▼───────────────┐
                    │        LangGraph Workflow     │
                    └──────────────┬───────────────┘
                                   │
                     ┌─────────────▼──────────────┐
                     │     Agent with Middleware   │
                     └─────────────┬──────────────┘
                                   │
        ┌──────────────┬───────────┼────────────┬──────────────┐
        │              │           │            │              │
┌───────▼──────┐ ┌─────▼─────┐ ┌───▼────┐ ┌─────▼──────┐ ┌─────▼──────┐
│ Security /   │ │ Retry /   │ │ Cost / │ │ Human      │ │ Logging /  │
│ PII          │ │ Fallback  │ │ Limits │ │ Approval   │ │ Tracing    │
└──────────────┘ └───────────┘ └────────┘ └────────────┘ └────────────┘
                                   │
                     ┌─────────────▼──────────────┐
                     │      Tools / Integrations   │
                     └─────────────┬──────────────┘
                                   │
              ┌────────────┬───────┴───────┬────────────┐
              │            │               │            │
        ┌─────▼─────┐ ┌────▼─────┐ ┌───────▼────┐ ┌─────▼─────┐
        │ Databases │ │ APIs     │ │ Kubernetes │ │ Filesystem│
        └───────────┘ └──────────┘ └────────────┘ └───────────┘
```

***

## 12. Design Guidelines

### Keep Middleware Small

One middleware should do one job:

- `RetryMiddleware`
- `AuditMiddleware`
- `PIIMiddleware`
- `ApprovalMiddleware`
- `CostLimitMiddleware`

Avoid creating a giant “GodMiddleware.”

### Put Critical Controls First

Security and policy middleware should generally be outermost:

```python
middleware=[
    SecurityMiddleware,
    PIIMiddleware,
    ApprovalMiddleware,
    RetryMiddleware,
    LoggingMiddleware,
]
```

This ensures security checks run before less critical concerns.

### Use Node Hooks for Observation

Use `before_model`, `after_model`, and `after_agent` for:

- Logging.
- Metrics.
- Validation.
- State enrichment.
- Audit events.

### Use Wrap Hooks for Control

Use `wrap_model_call` and `wrap_tool_call` for:

- Retry.
- Fallback.
- Caching.
- Redaction.
- Dynamic model or tool selection.
- Blocking execution.

### Make Failures Explicit

Decide whether failures should:

- Return a controlled message to the model.
- Raise an exception.
- End the agent.
- Require human review.

Do not silently swallow errors in production.

### Test Middleware Independently

Treat middleware like infrastructure code:

- Unit-test each hook.
- Test retry behavior with simulated failures.
- Test PII detection with known sensitive inputs.
- Test approval interrupts.
- Test call limits.
- Test execution order.

***

## 13. When to Use Middleware

Use middleware when you need any of the following:

- Observability across every model and tool call.
- Retry and fallback behavior.
- Cost and rate-limit enforcement.
- PII or secret protection.
- Human approval for dangerous actions.
- Dynamic prompts or tool selection.
- Context-window management.
- Deterministic guardrails.
- Reusable operational policy across multiple agents.

Do **not** use middleware for core business logic that belongs in a tool. For example, the logic to calculate a refund amount belongs in the refund service or tool—not in middleware.

***

## 14. Bottom Line

LangChain Middleware is best understood as **agent governance as code**.

It gives you a clean, composable way to add the operational qualities that real AI systems need:

```text
Capability = model + tools
Production readiness = capability + middleware
```

For an SRE, platform, or AI-engineering team, the practical takeaway is:

- Use middleware to enforce **policy, safety, resilience, cost, and observability**.
- Keep business logic in tools and services.
- Use LangGraph for broader workflow orchestration.
- Treat middleware like a control plane: small, testable, explicit, and security-aware.