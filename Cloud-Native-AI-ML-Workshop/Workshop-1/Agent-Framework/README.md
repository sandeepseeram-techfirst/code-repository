An **Agent Framework** is a developer toolkit for building AI systems that can reason, use tools, retain context, and execute multi-step tasks—either as a single agent or as coordinated multi-agent workflows. It sits between your application and an LLM, adding the production scaffolding that a raw model API does not provide.  

## What it is

An agent framework typically provides:

- **Agent runtime:** wraps an LLM so it can interpret a goal, decide actions, call tools, and produce responses.
- **Tool/MCP integration:** lets the agent invoke APIs, databases, search, code execution, Kubernetes, or internal services.
- **State and memory:** maintains conversation/session state and longer-term context.
- **Orchestration:** connects multiple agents and functions through explicit workflows, routing, retries, and checkpoints.
- **Middleware and observability:** intercepts actions for policy enforcement, logging, tracing, evaluation, and human approval.
- **Model portability:** commonly supports multiple providers such as OpenAI, Anthropic, Gemini, Bedrock, Ollama, and local models.  

In the CNCF AI Native landscape, “Agent Framework” is its own category and includes projects such as **LangChain, LangGraph, AutoGen, CrewAI, Semantic Kernel, Pydantic AI, Agno, ADK, and kagent**.  

## How it works

Most frameworks implement an **observe → reason → act → evaluate** loop:

1. **Receive goal/context:** user request, event, scheduled job, or upstream agent output.
2. **Retrieve context:** pull relevant memory, documents, system state, or knowledge-base results.
3. **Plan and select a tool:** the LLM decides whether to answer directly, call an API, query a database, run code, or delegate to another agent.
4. **Execute action:** the framework validates and invokes the tool, often through MCP or a typed function/tool interface.
5. **Evaluate result:** inspect output, retry on failure, request human approval, or continue the plan.
6. **Return or hand off:** produce a response, update state, trigger a workflow, or escalate to a person.  

For example, an SRE incident agent could receive an alert, query Prometheus, inspect Kubernetes events, read recent deployment changes, propose a rollback, and wait for approval before executing it. The framework supplies tool calling, state, guardrails, tracing, and workflow control rather than leaving you to hand-code all of that.

## Single agent vs. workflow

| Need | Use an agent | Use an agent workflow |
|---|---|---|
| Task shape | Open-ended, conversational, exploratory | Deterministic, well-defined sequence |
| Control | LLM plans and chooses tools | Explicit graph/execution path |
| Complexity | One LLM plus tools may suffice | Multiple agents/functions must coordinate |
| Examples | Research assistant, coding copilot | Approval pipeline, data remediation, incident-response runbook |

Microsoft’s Agent Framework makes this distinction explicitly: agents are best for autonomy and planning, while graph-based workflows are better when execution order and coordination must be controlled.  

## Practical use cases

- **Platform engineering and SRE:** triage alerts, correlate traces/logs, diagnose failed deployments, generate runbooks, and execute guarded remediation.
- **Kubernetes operations:** an agent uses cluster APIs and MCP tools to inspect workloads, identify misconfigurations, and recommend or apply changes after policy checks.
- **Data engineering:** detect pipeline failures, inspect lineage and data quality, repair or rerun jobs, and notify owners.
- **Customer support:** resolve tickets using knowledge bases and CRM tools, then escalate edge cases to humans.
- **Code and DevOps automation:** review pull requests, reproduce bugs, run tests, propose fixes, and open follow-up tasks.
- **Enterprise process automation:** employee onboarding, access provisioning, compliance checks, and approval workflows across HR, IT, and identity systems.  

## Cloud-agnostic architecture

For a production, provider-neutral deployment, keep the framework as the orchestration layer and externalize the platform concerns:

- **Model layer:** OpenAI-compatible endpoint, vLLM, Ollama, or another self-hosted inference service.
- **Tool layer:** MCP servers or typed tools for internal APIs, databases, observability systems, and Kubernetes.
- **Memory/state:** PostgreSQL/Redis/object storage or a dedicated vector store such as Qdrant, Milvus, or pgvector.
- **Workflow durability:** Temporal, Hatchet, or Kubernetes-native orchestration for long-running, recoverable tasks.
- **Security:** OPA/Gatekeeper or Kyverno policy checks, least-privilege tool credentials, audit logs, and human-in-the-loop approval for destructive actions.
- **Observability:** OpenTelemetry traces, Prometheus metrics, and evaluation tools such as Langfuse, DeepEval, or Promptfoo.  

The key design rule: **never give an agent unrestricted credentials or direct production mutation rights.** Give it scoped, auditable tools, policy gates, and explicit approval for high-impact operations.