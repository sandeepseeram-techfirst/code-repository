# smolagents: Deep Dive

`smolagents` is Hugging Face’s lightweight, open-source Python framework for building **LLM-powered agents** that can reason, call tools, execute code, and iterate toward a goal. Its core idea is simple: an LLM is the “brain,” while tools, memory, and a controlled execution loop give it the ability to act in the real world.

## What it is

`smolagents` is designed to make agents easy to build in a few lines of Python. It supports both **code-writing agents** and conventional **JSON tool-calling agents**, and it is model-agnostic: you can use Hugging Face Inference Providers, OpenAI, Anthropic, LiteLLM, Transformers, Ollama, Azure OpenAI, Amazon Bedrock, or MLX-backed local models.

The library deliberately keeps its abstractions small. The agent logic is compact, while integrations and security controls provide the production-facing capabilities.

## Core architecture

At its center is a `MultiStepAgent` class that implements a **ReAct loop**: Reason, Act, Observe, Repeat.

```text
User task
   |
   v
System prompt + task + memory
   |
   v
LLM decides next action
   |
   +--> CodeAgent: generates Python code
   +--> ToolCallingAgent: generates JSON tool call
   |
   v
Executor runs action
   |
   v
Observation/result written to memory
   |
   v
Repeat until final_answer() or max steps
```






### Main components

| Component | Role |
|---|---|
| **Model** | The LLM that reasons and decides the next action |
| **Agent** | Orchestrates reasoning, tool use, memory, and termination |
| **Tools** | Typed Python functions exposed to the LLM, such as search, SQL, APIs, or custom business logic |
| **Memory / logs** | Stores the task, model outputs, tool results, and execution observations |
| **Executor** | Runs generated Python code or dispatches a JSON tool call |
| **Callbacks** | Hooks executed after each step for logging, tracing, guardrails, or telemetry |
| **Planning step** | Optional higher-level plan that can be periodically revised |
| **Multi-agent manager** | A parent agent that delegates subtasks to named child agents |

## How the ReAct loop works

1. **Initialization**  
   The system prompt is stored as a `SystemPromptStep`, and the user request is stored as a `TaskStep`.

2. **Memory serialization**  
   `agent.write_memory_to_messages()` converts the agent’s accumulated history into chat messages the LLM can understand.

3. **LLM reasoning**  
   The model receives the task, prior observations, tool descriptions, and available context. It then produces an action.

4. **Action execution**  
   - A `CodeAgent` generates Python code.
   - A `ToolCallingAgent` emits structured JSON.
   
   The framework executes the action and records the result as an `ActionStep`.

5. **Observation and iteration**  
   The result is appended to memory. The model sees the outcome and decides whether to continue, correct itself, call another tool, or finish.

6. **Termination**  
   The agent normally stops when it calls `final_answer()` or reaches its configured maximum number of steps. Custom `final_answer_checks` can validate the answer before accepting it.

## CodeAgent vs ToolCallingAgent

`smolagents` supports two main execution paradigms.

| Aspect | `CodeAgent` | `ToolCallingAgent` |
|---|---|---|
| Action format | Python code | JSON tool call |
| Example | `result = search_docs("...")` | `{"name": "search_docs", "arguments": {"query": "..."}}` |
| Expressiveness | High: loops, conditionals, function composition, transformations | Lower: mostly one tool call at a time |
| Reliability | Depends on generated-code quality | More predictable and schema-validated |
| Security surface | Higher: requires sandboxing or strict import controls | Lower: no arbitrary code execution |
| Best for | Data analysis, multi-step workflows, dynamic logic, coding tasks | API dispatch, retrieval, browser actions, constrained workflows |

### Why CodeAgent matters

A `CodeAgent` does not merely “write code for a human.” It **uses code as its action language**. Instead of forcing the model to express every operation as a predefined JSON tool call, it can compose tools:

```python
results = search_web("latest Kubernetes releases")
cleaned = extract_titles(results)
summary = summarize(cleaned)
final_answer(summary)
```

This gives the agent natural composability: nesting, loops, conditionals, variable reuse, and transformations.

## Tool system

A tool is an atomic capability with:

- A clear name
- A description
- Typed inputs
- Described arguments
- An output type
- A `forward()` implementation or decorated function body

These descriptions are injected into the agent’s system prompt, so the LLM knows what tools exist and how to use them.

### Built-in tools

With the `toolkit` extra, `smolagents` includes tools such as:

- Web search
- Python code interpreter
- Speech transcription using Whisper-Turbo

You can also import tools from MCP servers, LangChain, or Hugging Face Spaces.

## Security model

This is the most important production consideration.

### Local CodeAgent execution

By default, `CodeAgent` runs generated Python locally. The interpreter restricts imports to a safe allowlist and exposes primarily the tools you provide, plus limited built-ins such as `print` and `math`.

You can explicitly allow additional modules:

```python
agent = CodeAgent(
    tools=[],
    model=model,
    additional_authorized_imports=["requests", "bs4"]
)
```

However, the LLM can still generate arbitrary code. Never grant broad imports, filesystem access, credentials, or network permissions unless the execution boundary is properly isolated.

### Sandboxed execution

For production, use an isolated executor:

```python
CodeAgent(..., executor_type="docker")
```

Supported sandbox options include:

- Docker
- E2B
- Modal
- Blaxel

For enterprise environments, the strongest pattern is:

- Run the agent control plane outside the sensitive network.
- Run generated code in an ephemeral, network-restricted container.
- Mount no persistent credentials.
- Use scoped service identities.
- Apply egress allowlists.
- Capture stdout, stderr, artifacts, and telemetry.
- Set CPU, memory, timeout, and concurrency limits.

## Memory and observability

The agent’s memory is not just chat history. It records:

- The original task
- System prompt
- Model reasoning and generated actions
- Tool outputs
- Execution errors
- Final answers
- Optional plans

You can inspect:

```python
agent.logs
agent.write_memory_to_messages()
```

For production, integrate step callbacks with OpenTelemetry, Langfuse, Phoenix, or a custom tracing backend. This gives you:

- Token and cost tracking
- Latency per step
- Tool failure rates
- Retry behavior
- Prompt and response audit trails
- Root-cause analysis for failed runs

## Multi-agent architecture

`smolagents` supports hierarchical multi-agent systems. A manager agent can delegate work to specialized child agents.

```text
Manager agent
   |
   +--> Research agent: web search
   +--> Data agent: SQL / pandas
   +--> Ops agent: Kubernetes / incident data
   +--> Writing agent: report generation
```

Each child agent has its own:

- Name
- Description
- Toolset
- Memory
- Model configuration

This prevents context pollution. For example, a web-research agent does not need to carry every raw webpage into the memory of a code-generation agent.

## Real-world problems it solves

### 1. LLMs cannot act on their own

A base LLM can explain how to query a database, but it cannot actually query it. `smolagents` turns model output into executable actions through tools or code.

### 2. Multi-step tasks require state

Questions such as “investigate this incident,” “reconcile these invoices,” or “analyze this dataset” require multiple actions and intermediate results. The ReAct loop preserves that state.

### 3. Tool APIs are fragmented

Enterprises have APIs, databases, internal services, monitoring systems, ticketing systems, and document stores. `smolagents` provides a uniform tool abstraction over these systems.

### 4. Static pipelines break on ambiguous inputs

A fixed DAG works when inputs are predictable. Agents are useful when the next step depends on what was discovered in the previous step.

### 5. Code-heavy work needs composability

For analytics, data engineering, and DevOps tasks, code is often the best interface. A `CodeAgent` can combine parsing, filtering, aggregation, API calls, and validation naturally.

### 6. Specialization improves reliability

Instead of one overloaded agent, you can use focused agents for research, SQL, incident response, documentation, or deployment validation.

## Real-world use cases

### Agentic RAG

Build an agent that:

1. Understands the user question.
2. Rewrites it into retrieval queries.
3. Searches a vector database or document store.
4. Evaluates whether retrieved context is sufficient.
5. Queries again with different terms if needed.
6. Generates a cited answer.

This is stronger than a single retrieve-then-generate pipeline because the agent can decide when retrieval failed.

### Text-to-SQL with self-correction

An agent can:

1. Inspect schema metadata.
2. Generate SQL.
3. Execute it against a read-only replica.
4. Catch SQL or schema errors.
5. Revise the query.
6. Return the result with an explanation.

Use strict guardrails: read-only credentials, query timeouts, row limits, cost limits, and SQL allowlists.

### Cloud and SRE operations assistant

For a cloud-agnostic SRE workflow, an agent could:

- Query Prometheus for error-rate spikes.
- Inspect Kubernetes events.
- Fetch recent deployment metadata.
- Correlate alerts with changes.
- Draft a root-cause hypothesis.
- Recommend or execute a controlled remediation.

Keep destructive actions behind human approval.

### Data engineering copilot

An agent can:

- Read a data contract.
- Inspect schema drift.
- Profile a failed batch.
- Query logs and lineage metadata.
- Generate a fix or backfill plan.
- Validate row counts and null rates.

### Developer productivity agent

An agent can:

- Search repositories.
- Read documentation.
- Run tests.
- Analyze failures.
- Propose a patch.
- Validate the patch in a sandbox.

### Customer support operations

An agent can:

- Classify a ticket.
- Search knowledge bases.
- Query order or account systems.
- Draft a response.
- Escalate when confidence or policy rules require it.

## Hands-on tutorial

This tutorial builds a small **incident-analysis agent** using a `CodeAgent`, a custom tool, and safe execution practices.

### Prerequisites

You need:

- Python 3.10 or newer
- A Hugging Face token, or another supported model provider
- Docker if you want sandboxed execution

Set your token:

```bash
export HF_TOKEN="your_huggingface_token"
```

### Step 1: Install smolagents

```bash
python -m venv .venv
source .venv/bin/activate

pip install 'smolagents[toolkit]'
```

### Step 2: Create a minimal agent

Create `agent_basic.py`:

```python
from smolagents import CodeAgent, InferenceClientModel

model = InferenceClientModel()

agent = CodeAgent(
    tools=[],
    model=model
)

result = agent.run("Calculate the sum of numbers from 1 to 10.")
print(result)
```

Run it:

```bash
python agent_basic.py
```

The agent will generate Python code, execute it, observe the result, and return the final answer.

### Step 3: Add web search

Create `agent_search.py`:

```python
from smolagents import CodeAgent, InferenceClientModel, DuckDuckGoSearchTool

model = InferenceClientModel()

agent = CodeAgent(
    tools=[DuckDuckGoSearchTool()],
    model=model
)

result = agent.run(
    "Find the latest stable Kubernetes release and summarize its key changes."
)

print(result)
```

Run:

```bash
python agent_search.py
```

The agent may search once, inspect the result, search again for missing details, and then summarize.

### Step 4: Create a custom tool

Create `ops_tools.py`:

```python
import random
from smolagents import tool

@tool
def get_service_health(service: str) -> str:
    """
    Returns a simulated health status for a service.

    Args:
        service: Name of the service to inspect.
    """
    statuses = ["healthy", "degraded", "failing"]
    status = random.choice(statuses)
    return f"{service}: {status}"
```

In a real deployment, replace the random status with a call to Prometheus, Grafana, Kubernetes API, or your internal observability API.

### Step 5: Build an incident-analysis agent

Create `incident_agent.py`:

```python
from smolagents import CodeAgent, InferenceClientModel
from ops_tools import get_service_health

model = InferenceClientModel()

agent = CodeAgent(
    tools=[get_service_health],
    model=model,
    max_steps=6,
    verbosity_level=2
)

task = """
Investigate the health of the checkout-service.
If it is degraded or failing, identify likely next diagnostic steps.
Return a concise incident note.
"""

result = agent.run(task)
print(result)
```

Run:

```bash
python incident_agent.py
```

Expected flow:

1. The agent calls `get_service_health(service="checkout-service")`.
2. It observes the returned status.
3. If unhealthy, it reasons about likely next checks.
4. It produces a concise incident note.

### Step 6: Add answer validation

Create `incident_agent_validated.py`:

```python
from smolagents import CodeAgent, InferenceClientModel
from ops_tools import get_service_health

model = InferenceClientModel()

def contains_status(final_answer: str, agent_memory=None) -> bool:
    required = ["healthy", "degraded", "failing"]
    return any(status in final_answer.lower() for status in required)

agent = CodeAgent(
    tools=[get_service_health],
    model=model,
    final_answer_checks=[contains_status],
    max_steps=6
)

result = agent.run(
    "Check checkout-service health and return an incident note that includes its status."
)

print(result)
```

If the final answer does not include a valid status, the agent continues and tries again.

### Step 7: Run in Docker sandbox

For safer execution of generated code:

```python
from smolagents import CodeAgent, InferenceClientModel
from ops_tools import get_service_health

model = InferenceClientModel()

agent = CodeAgent(
    tools=[get_service_health],
    model=model,
    executor_type="docker",
    max_steps=6
)

result = agent.run(
    "Check checkout-service health and recommend next diagnostic actions."
)

print(result)
```

Ensure Docker is running before executing this version.

### Step 8: Add a manager and specialist agent

Create `multi_agent.py`:

```python
from smolagents import CodeAgent, InferenceClientModel
from ops_tools import get_service_health

model = InferenceClientModel()

ops_agent = CodeAgent(
    tools=[get_service_health],
    model=model,
    name="ops_health_agent",
    description=(
        "Checks simulated service health. "
        "Provide the service name as input."
    )
)

manager = CodeAgent(
    tools=[],
    model=model,
    managed_agents=[ops_agent],
    max_steps=8
)

result = manager.run(
    "Check the health of payment-service and produce an incident summary."
)

print(result)
```

The manager delegates the health check to `ops_health_agent`, receives the observation, and produces the final summary.

### Step 9: Add a Gradio interface

```python
from smolagents import CodeAgent, InferenceClientModel, GradioUI
from ops_tools import get_service_health

model = InferenceClientModel()

agent = CodeAgent(
    tools=[get_service_health],
    model=model
)

GradioUI(agent).launch()
```

Run:

```bash
python app.py
```

This launches a local chat interface where you can submit tasks and inspect the agent’s reasoning and tool activity.

## Production design checklist

- Use `ToolCallingAgent` for narrow, high-risk, API-driven workflows.
- Use `CodeAgent` when dynamic composition provides real value.
- Never run generated code with broad privileges.
- Prefer Docker, E2B, Modal, or Blaxel sandboxes for code execution.
- Give tools least-privilege credentials.
- Use read-only database roles where possible.
- Enforce timeouts, retry limits, and maximum steps.
- Log every prompt, action, observation, and final answer.
- Add output validators using `final_answer_checks`.
- Keep human approval for destructive operations.
- Separate agent memory by domain to avoid context bloat.
- Use specialized child agents rather than one do-everything agent.
- Monitor token usage, latency, tool failures, and cost per task.

## Key technical insights

- `smolagents` is an **agent runtime**, not just a prompt library.
- The central pattern is **ReAct**: reason, act, observe, repeat.
- `CodeAgent` treats Python as an action language, enabling composability.
- `ToolCallingAgent` prioritizes predictable, schema-driven tool invocation.
- Tools are the trust boundary: their descriptions, inputs, outputs, and permissions determine agent behavior.
- Memory is the agent’s working state; it must be curated to avoid context overload.
- Sandboxing is mandatory for untrusted generated code in production.
- Multi-agent systems improve separation of concerns but add orchestration and observability complexity.
- The best production agents are constrained: limited tools, validated outputs, scoped credentials, and human approval for irreversible actions.
