# LangGraph Deep Dive

LangGraph is a low-level **agent orchestration framework and runtime** for building long-running, stateful AI workflows. Its core idea is simple: model an application as a graph of discrete steps (**nodes**), pass shared data through **state**, and let either deterministic code or an LLM decide the next transition. [docs.langchain](https://docs.langchain.com/oss/python/langgraph/overview)

It is not an LLM provider, prompt library, or complete agent product. It is the control plane that coordinates models, tools, databases, APIs, humans, retries, checkpoints, and streaming in one explicit execution graph. [docs.langchain](https://docs.langchain.com/oss/python/langgraph/overview)

## Simplified mental model

Think of LangGraph as a **stateful workflow engine for AI systems**:

- A **node** is one unit of work: call an LLM, query a database, validate input, call an API, request human approval, or write to a system of record.
- **State** is the shared working memory available to nodes.
- **Edges** define static transitions.
- **Conditional routing** lets a node decide the next node based on the current state.
- **Checkpointing** saves progress so a workflow can pause, fail, recover, or resume later.
- **Interrupts** make human approval a first-class workflow step.

A useful analogy: LangGraph is to AI agents what a workflow engine is to microservices. Instead of scattering orchestration logic across queues, callbacks, and application code, you define the process, state, transitions, failure behavior, and human checkpoints explicitly. [docs.langchain](https://docs.langchain.com/oss/python/langgraph/overview)

## Architecture

### Core components

| Component | Role | Production analogy |
|---|---|---|
| `StateGraph` | Defines the workflow topology and shared state schema | DAG/workflow definition |
| Node | A Python function that reads state, performs work, and returns state updates | Service step, task handler, or worker |
| State | Typed shared data structure passed between nodes | Workflow context / transaction state |
| Edge | Static connection between nodes | Pipeline dependency |
| Conditional edge / `Command` | Dynamic routing based on runtime state | Business rules or router |
| Checkpointer | Persists graph state at node boundaries | Durable execution / workflow state store |
| Interrupt | Pauses execution for external input | Human approval gate |
| Subgraph | Reusable nested graph | Modular service or reusable workflow component |
| Store | Long-term memory across sessions | External memory / knowledge store |
| Streaming | Emits intermediate updates and tokens as execution proceeds | Event stream / progress channel |

LangGraph’s design is influenced by Pregel and Apache Beam, while its public graph interface draws inspiration from NetworkX. It can be used standalone and does not require LangChain. [docs.langchain](https://docs.langchain.com/oss/python/langgraph/overview)

### Execution model

At runtime, LangGraph executes one node at a time:

1. Receive an initial input state.
2. Start at the `START` node.
3. Execute the current node.
4. Merge the node’s returned updates into the shared state.
5. Determine the next node from static edges, conditional edges, or a `Command` returned by the node.
6. Repeat until the graph reaches `END`.
7. Persist checkpoints at node boundaries so execution can be resumed.

This makes the agent’s behavior inspectable: at any point, you can see the current node, state, decision, tool result, and next transition. [docs.langchain](https://docs.langchain.com/oss/python/langgraph/thinking-in-langgraph)

### State design

State is the most important architectural decision in LangGraph.

A good state contains data that must survive across steps:

- Original user request or document.
- Extracted entities and identifiers.
- Classification or routing decisions.
- Tool and retrieval results.
- Draft outputs.
- Error context.
- Execution metadata.

A good practice is to keep state **raw** and format prompts only inside nodes. This avoids coupling your persistent workflow state to a particular prompt template and makes debugging clearer. [docs.langchain](https://docs.langchain.com/oss/python/langgraph/thinking-in-langgraph)

Example:

```python
from typing import TypedDict

class SupportAgentState(TypedDict):
    email_content: str
    sender_email: str
    classification: dict | None
    search_results: list[str] | None
    draft_response: str | None
    error: str | None
```

Do not store formatted prompts, transient UI text, or values easily derived from other state fields.

## How it works

### Deterministic plus agentic execution

LangGraph’s major strength is that it does not force every decision to be made by an LLM.

You can combine:

- **Deterministic steps**: validation, schema checks, policy rules, database lookups, calculations.
- **Agentic steps**: LLM classification, reasoning, tool selection, drafting, summarization.
- **Action steps**: create tickets, send emails, call payment APIs, provision infrastructure.
- **Human-in-the-loop steps**: approval, clarification, exception handling.

This is crucial for production systems. You want the LLM where flexibility is valuable, but deterministic code where correctness, auditability, and repeatability matter. [docs.langchain](https://docs.langchain.com/oss/python/langgraph/overview)

### Dynamic routing

A node can return a `Command` containing both a state update and the next destination:

```python
from langgraph.types import Command

def classify_request(state):
    classification = llm_classify(state["user_request"])

    if classification["risk"] == "high":
        next_node = "human_review"
    elif classification["intent"] == "technical":
        next_node = "retrieve_docs"
    else:
        next_node = "draft_answer"

    return Command(
        update={"classification": classification},
        goto=next_node,
    )
```

This keeps control flow explicit and traceable. You can inspect why the workflow routed to human review, retrieval, or an external action. [docs.langchain](https://docs.langchain.com/oss/python/langgraph/thinking-in-langgraph)

### Persistence and durable execution

LangGraph checkpointers save graph state at node boundaries. If a process crashes, a deployment restarts, or a workflow waits for human input, it can resume from the last checkpoint rather than restarting from the beginning. [docs.langchain](https://docs.langchain.com/oss/python/langgraph/overview)

This solves a major real-world problem: many useful AI workflows are not single synchronous API calls. They may run for minutes, hours, or days because they involve approvals, external systems, batch jobs, or multi-step research.

### Human-in-the-loop

`interrupt()` pauses graph execution and waits for external input. The state is checkpointed, so the workflow can resume later—potentially days later—without losing context. [docs.langchain](https://docs.langchain.com/oss/python/langgraph/thinking-in-langgraph)

Typical use cases:

- Approve an outbound customer email.
- Approve a high-risk financial transaction.
- Provide a missing account ID or order number.
- Review a generated incident remediation plan.
- Approve infrastructure changes before execution.

### Fault tolerance

LangGraph encourages treating errors as part of the workflow:

| Error type | Strategy |
|---|---|
| Network failure, rate limit, transient outage | Retry with backoff |
| Tool failure or malformed LLM output | Return the error to the LLM and let it adapt |
| Missing user information | Pause with `interrupt()` |
| Unexpected programming error | Let it surface for debugging |
| Failed external side effect | Run a compensation or rollback branch |

You can attach retry policies, timeouts, and error handlers to individual nodes. This is especially important when nodes call external APIs, databases, payment systems, or infrastructure controllers. [docs.langchain](https://docs.langchain.com/oss/python/langgraph/thinking-in-langgraph)

## Key technical insights

1. **Graphs make agent behavior auditable.**  
   Instead of an opaque agent loop, you can inspect every state transition and routing decision.

2. **State is the contract between steps.**  
   Design state carefully; it determines testability, recoverability, and observability.

3. **Small nodes improve resilience.**  
   Checkpoints occur at node boundaries. Smaller nodes reduce repeated work after failures and make external-service failures easier to isolate. [docs.langchain](https://docs.langchain.com/oss/python/langgraph/thinking-in-langgraph)

4. **Do not make the LLM the orchestrator by default.**  
   Use code for deterministic rules and the LLM for judgment, interpretation, and generation.

5. **Treat side effects carefully.**  
   Sending email, charging payment, creating tickets, and mutating infrastructure should be isolated nodes with retries, approvals, and compensation paths.

6. **Human approval is a workflow primitive.**  
   `interrupt()` is not a UI hack; it is a durable pause point in the execution graph. [docs.langchain](https://docs.langchain.com/oss/python/langgraph/thinking-in-langgraph)

7. **Observability is essential.**  
   Tracing, state inspection, and evaluation are necessary because agent failures are often semantic: wrong retrieval, poor reasoning, unsafe tool use, or incorrect routing. [docs.langchain](https://docs.langchain.com/oss/python/langgraph/overview)

## Real-world problems it solves

### 1. Unreliable “one-shot” LLM applications

A single LLM call is often insufficient for real work. Production tasks require retrieval, validation, tool use, retries, approvals, and audit trails.

LangGraph solves this by making the full process explicit rather than hiding it inside an agent loop.

### 2. Long-running workflows

Customer support, document review, financial onboarding, incident response, and research tasks may require waiting on humans or external systems.

Checkpointing and interrupts allow execution to pause and resume without losing state. [docs.langchain](https://docs.langchain.com/oss/python/langgraph/overview)

### 3. Unsafe autonomous actions

Agents that directly send emails, modify records, or execute infrastructure changes need controls.

LangGraph lets you insert validation, policy checks, and human approval before irreversible actions.

### 4. Poor debugging experience

Agent failures are hard to reproduce when logic is spread across prompts, function calls, and implicit loops.

LangGraph exposes the execution path, state changes, and decisions between nodes, making root-cause analysis more practical. [docs.langchain](https://docs.langchain.com/oss/python/langgraph/overview)

### 5. Mixed reliability requirements

Some parts of an AI system must be deterministic and compliant; others benefit from model reasoning.

LangGraph lets you place each kind of logic exactly where it belongs. [docs.langchain](https://docs.langchain.com/oss/python/langgraph/overview)

## Real-world use cases

| Use case | Example workflow | Why LangGraph fits |
|---|---|---|
| Customer support automation | Read email, classify intent, search docs, draft response, human approval, send reply | Needs routing, retrieval, drafting, and approval |
| Financial operations | Parse invoice, validate vendor, check policy, approve exception, initiate payment | Requires auditability and human control |
| Incident response | Ingest alert, enrich with telemetry, diagnose, propose remediation, approve change, execute | Benefits from durable execution and tool orchestration |
| Kubernetes / SRE copilot | Inspect alerts, query metrics, inspect logs, identify root cause, draft remediation, require approval | Separates read-only diagnosis from risky mutation |
| Document intelligence | Extract fields, validate against source systems, flag discrepancies, route for review | Combines OCR/models, business rules, and human review |
| Sales and CRM automation | Qualify lead, enrich data, score fit, draft outreach, approve message, update CRM | Requires external integrations and approval gates |
| Data engineering copilot | Interpret request, generate SQL, validate schema, run query, explain result | Separates generation from execution and validation |
| Security triage | Ingest alert, correlate signals, classify severity, recommend action, approve containment | Needs policy controls and human oversight |

For an SRE or platform-engineering context, a particularly strong pattern is a **read-only diagnostic agent** followed by a **human-approved remediation graph**. The agent can inspect metrics, logs, traces, and Kubernetes events, but any restart, scale change, rollback, or configuration mutation requires explicit approval.

## Hands-on tutorial

This tutorial builds a small but production-shaped **support-ticket triage agent**.

It will:

1. Receive a support request.
2. Classify intent and urgency using an LLM.
3. Retrieve relevant knowledge-base articles.
4. Draft a response.
5. Require human approval for high-risk requests.
6. Send the approved response.

### Prerequisites

```bash
python -m venv .venv
source .venv/bin/activate
pip install -U langgraph langchain langchain-openai
```

Set your model provider key:

```bash
export OPENAI_API_KEY="your-api-key"
```

You can substitute any LangChain-compatible chat model. LangGraph itself does not require OpenAI or LangChain. [docs.langchain](https://docs.langchain.com/oss/python/langgraph/overview)

### Project structure

```text
langgraph-demo/
├── agent.py
└── requirements.txt
```

```text
# requirements.txt
langgraph
langchain
langchain-openai
```

### Step 1: Define the state

Create `agent.py`:

```python
from typing import TypedDict, Literal
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command, interrupt, RetryPolicy
from langchain_openai import ChatOpenAI


class Classification(TypedDict):
    intent: Literal["question", "bug", "billing", "other"]
    urgency: Literal["low", "medium", "high", "critical"]
    topic: str


class TicketState(TypedDict):
    ticket_id: str
    customer_message: str
    classification: Classification | None
    knowledge_results: list[str] | None
    draft_response: str | None
    approval: bool | None
    final_response: str | None
```

The state stores raw workflow data. Prompt formatting happens inside nodes.

### Step 2: Create the LLM

```python
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
```

For production, inject the model and credentials through configuration or secrets management rather than hard-coding them.

### Step 3: Build the classification node

```python
def classify_ticket(state: TicketState) -> Command:
    structured_llm = llm.with_structured_output(Classification)

    prompt = f"""
    Classify the following customer support request.

    Customer message:
    {state["customer_message"]}

    Return:
    - intent: question, bug, billing, or other
    - urgency: low, medium, high, or critical
    - topic: short topic label
    """

    classification = structured_llm.invoke(prompt)

    if classification["urgency"] in ("high", "critical"):
        next_node = "retrieve_knowledge"
    elif classification["intent"] == "billing":
        next_node = "human_review"
    else:
        next_node = "retrieve_knowledge"

    return Command(
        update={"classification": classification},
        goto=next_node,
    )
```

This node combines an LLM decision with a deterministic routing rule.

### Step 4: Build the retrieval node

```python
FAKE_KNOWLEDGE_BASE = {
    "password": [
        "Users can reset passwords from Settings > Security > Reset Password.",
        "Password resets require access to the registered email address."
    ],
    "export": [
        "PDF export failures can occur when reports contain unsupported embedded fonts.",
        "Try exporting to CSV while the PDF issue is investigated."
    ],
    "billing": [
        "Duplicate charges are refunded after verification by the billing team.",
        "Billing escalations require human approval before customer communication."
    ],
}


def retrieve_knowledge(state: TicketState) -> Command:
    classification = state["classification"] or {}
    topic = classification.get("topic", "").lower()

    results = []

    for keyword, docs in FAKE_KNOWLEDGE_BASE.items():
        if keyword in topic or keyword in state["customer_message"].lower():
            results.extend(docs)

    if not results:
        results = ["No directly relevant knowledge-base article was found."]

    return Command(
        update={"knowledge_results": results},
        goto="draft_response",
    )
```

In a real deployment, replace the dictionary with a vector database, search service, internal API, or RAG pipeline.

### Step 5: Build the drafting node

```python
def draft_response(state: TicketState) -> Command:
    classification = state["classification"] or {}
    knowledge = state["knowledge_results"] or []

    docs = "\n".join(f"- {item}" for item in knowledge)

    prompt = f"""
    Draft a concise, professional customer-support response.

    Customer message:
    {state["customer_message"]}

    Classification:
    Intent: {classification.get("intent")}
    Urgency: {classification.get("urgency")}
    Topic: {classification.get("topic")}

    Relevant knowledge:
    {docs}

    Rules:
    - Do not promise refunds or account changes.
    - If the issue is billing-related, say it requires specialist review.
    - Be clear and helpful.
    """

    response = llm.invoke(prompt)

    if classification.get("urgency") in ("high", "critical"):
        next_node = "human_review"
    else:
        next_node = "send_response"

    return Command(
        update={"draft_response": response.content},
        goto=next_node,
    )
```

### Step 6: Add human approval

```python
def human_review(state: TicketState) -> Command:
    decision = interrupt(
        {
            "ticket_id": state["ticket_id"],
            "customer_message": state["customer_message"],
            "draft_response": state["draft_response"],
            "action": "Approve or edit this response before sending",
        }
    )

    approved = decision.get("approved", False)
    edited_response = decision.get("edited_response")

    if not approved:
        return Command(
            update={"approval": False},
            goto=END,
        )

    return Command(
        update={
            "approval": True,
            "final_response": edited_response or state["draft_response"],
        },
        goto="send_response",
    )
```

The graph pauses at this node. It saves its state and waits for a resume command.

### Step 7: Add the send node

```python
def send_response(state: TicketState) -> dict:
    response = state.get("final_response") or state.get("draft_response")

    print("\n--- SENT RESPONSE ---")
    print(response)

    return {}
```

In production, this node would call your email, ticketing, CRM, or messaging API. Keep it isolated so it can have its own retry policy and audit trail.

### Step 8: Wire the graph

```python
workflow = StateGraph(TicketState)

workflow.add_node("classify_ticket", classify_ticket)
workflow.add_node(
    "retrieve_knowledge",
    retrieve_knowledge,
    retry_policy=RetryPolicy(max_attempts=3),
)
workflow.add_node("draft_response", draft_response)
workflow.add_node("human_review", human_review)
workflow.add_node("send_response", send_response)

workflow.add_edge(START, "classify_ticket")
workflow.add_edge("send_response", END)

app = workflow.compile(checkpointer=InMemorySaver())
```

The graph topology is intentionally minimal because most routing is performed by nodes through `Command`. [docs.langchain](https://docs.langchain.com/oss/python/langgraph/thinking-in-langgraph)

### Step 9: Run the workflow

```python
initial_state = {
    "ticket_id": "TICKET-1001",
    "customer_message": (
        "I was charged twice for my subscription this month. "
        "This is urgent and I need this resolved today."
    ),
}

config = {
    "configurable": {
        "thread_id": "customer-123"
    }
}

result = app.invoke(initial_state, config)

print(result)
```

Because the request is billing-related, the graph routes to `human_review` and pauses.

### Step 10: Resume after approval

```python
from langgraph.types import Command

resume_input = Command(
    resume={
        "approved": True,
        "edited_response": (
            "We understand the urgency of a potential duplicate charge. "
            "Our billing team will review the transaction and follow up shortly."
        ),
    }
)

final_result = app.invoke(resume_input, config)

print(final_result)
```

The workflow resumes exactly at `human_review`, applies the approved response, and proceeds to `send_response`.

## Complete runnable example

```python
from typing import TypedDict, Literal
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command, interrupt, RetryPolicy
from langchain_openai import ChatOpenAI


class Classification(TypedDict):
    intent: Literal["question", "bug", "billing", "other"]
    urgency: Literal["low", "medium", "high", "critical"]
    topic: str


class TicketState(TypedDict):
    ticket_id: str
    customer_message: str
    classification: Classification | None
    knowledge_results: list[str] | None
    draft_response: str | None
    approval: bool | None
    final_response: str | None


llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

FAKE_KNOWLEDGE_BASE = {
    "password": [
        "Users can reset passwords from Settings > Security > Reset Password.",
    ],
    "billing": [
        "Duplicate charges are reviewed by the billing team before refunds.",
    ],
}


def classify_ticket(state: TicketState) -> Command:
    structured_llm = llm.with_structured_output(Classification)

    classification = structured_llm.invoke(
        f"""
        Classify this customer support request:

        {state["customer_message"]}

        Return intent, urgency, and topic.
        """
    )

    if classification["intent"] == "billing":
        next_node = "human_review"
    else:
        next_node = "retrieve_knowledge"

    return Command(
        update={"classification": classification},
        goto=next_node,
    )


def retrieve_knowledge(state: TicketState) -> Command:
    classification = state["classification"] or {}
    topic = classification.get("topic", "").lower()

    results = []

    for keyword, docs in FAKE_KNOWLEDGE_BASE.items():
        if keyword in topic or keyword in state["customer_message"].lower():
            results.extend(docs)

    return Command(
        update={"knowledge_results": results or ["No relevant article found."]},
        goto="draft_response",
    )


def draft_response(state: TicketState) -> Command:
    classification = state["classification"] or {}
    knowledge = state["knowledge_results"] or []

    response = llm.invoke(
        f"""
        Draft a professional support response.

        Customer message:
        {state["customer_message"]}

        Classification:
        {classification}

        Knowledge:
        {knowledge}

        Do not promise refunds or account changes.
        """
    )

    if classification.get("urgency") in ("high", "critical"):
        next_node = "human_review"
    else:
        next_node = "send_response"

    return Command(
        update={"draft_response": response.content},
        goto=next_node,
    )


def human_review(state: TicketState) -> Command:
    decision = interrupt(
        {
            "ticket_id": state["ticket_id"],
            "draft_response": state["draft_response"],
            "action": "Approve or edit before sending",
        }
    )

    if not decision.get("approved"):
        return Command(update={"approval": False}, goto=END)

    return Command(
        update={
            "approval": True,
            "final_response": decision.get(
                "edited_response",
                state["draft_response"],
            ),
        },
        goto="send_response",
    )


def send_response(state: TicketState) -> dict:
    response = state.get("final_response") or state.get("draft_response")
    print("\n--- SENT RESPONSE ---")
    print(response)
    return {}


workflow = StateGraph(TicketState)

workflow.add_node("classify_ticket", classify_ticket)
workflow.add_node(
    "retrieve_knowledge",
    retrieve_knowledge,
    retry_policy=RetryPolicy(max_attempts=3),
)
workflow.add_node("draft_response", draft_response)
workflow.add_node("human_review", human_review)
workflow.add_node("send_response", send_response)

workflow.add_edge(START, "classify_ticket")
workflow.add_edge("send_response", END)

app = workflow.compile(checkpointer=InMemorySaver())

initial_state = {
    "ticket_id": "TICKET-1001",
    "customer_message": (
        "I was charged twice for my subscription. "
        "Please resolve this urgently."
    ),
}

config = {"configurable": {"thread_id": "customer-123"}}

paused_result = app.invoke(initial_state, config)
print("\nPaused for human review:")
print(paused_result)

resume_input = Command(
    resume={
        "approved": True,
        "edited_response": (
            "We understand the urgency of a potential duplicate charge. "
            "Our billing team will review the transaction and follow up shortly."
        ),
    }
)

final_result = app.invoke(resume_input, config)
print("\nFinal result:")
print(final_result)
```

## Production design checklist

- Use a durable checkpointer backed by a database or managed state store, not in-memory storage, for real deployments.
- Assign a stable `thread_id` per conversation, ticket, incident, or business transaction.
- Keep external side effects in dedicated nodes.
- Add retries and timeouts for transient failures.
- Add human approval before irreversible actions.
- Store raw data in state; format prompts inside nodes.
- Use structured outputs for classification and routing decisions.
- Add tracing and evaluation before production rollout.
- Use subgraphs for reusable capabilities such as retrieval, approval, or tool execution.
- Separate read-only diagnosis from write-capable remediation.
- Apply least-privilege credentials to each tool and node.
- Log state transitions, tool inputs, tool outputs, model versions, and approval decisions.

## When to use LangGraph

Use LangGraph when you need any of the following:

- Multi-step agents with explicit control flow.
- Durable, resumable workflows.
- Human approval before sensitive actions.
- Deterministic business rules combined with LLM reasoning.
- Tool orchestration across internal and external systems.
- Observable and testable agent behavior.
- Long-running automation that must survive restarts or wait for humans.

Use a simpler higher-level agent abstraction when your use case is a basic tool-calling loop and you do not yet need durable state, human-in-the-loop control, complex branching, or production-grade workflow semantics. LangGraph is deliberately low-level to give you that control. [docs.langchain](https://docs.langchain.com/oss/python/langgraph/overview)