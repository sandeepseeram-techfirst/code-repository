## System Design - Interview Frameworks

* SPIDER for system-design questions

* ETA for explaining concepts

* Tradeoff analysis for comparing options

* Debugging framework for incident-style questions

* STAR-L for behavioral answers


### SPIDER 
SPIDER is the main design-interview method: clarify the problem, identify requirements and constraints, propose an architecture, discuss tradeoffs, address risks, and define observability/rollout.

### ETA 
ETA is for concise conceptual explanations.

### Tradeoff Analysis 
forces explicit comparison of options rather than presenting one choice as obviously correct.

### Debugging structures 
incident-style answers around hypotheses, evidence, isolation, and remediation.

### STAR-L 
structures behavioral stories as Situation, Task, Action, Result, and Learning.


* Clear requirements and constraints before proposing an architecture.

* Explicit tradeoffs: latency, cost, quality, reliability, security, and operational complexity.

* Failure-mode thinking: what happens when retrieval is poor, a model degrades, an agent takes a wrong action, or a dependency fails.

* Observability: metrics, traces, evaluations, alerts, and rollback plans.

* Security and tenant isolation, especially for agents, MCP-style integrations, and multi-tenant systems.


SPIDER is a repeatable structure for answering AI system-design interview questions. It keeps your response organized, ensures you cover requirements and risks, and makes your tradeoffs explicit rather than jumping straight to an architecture.

### What SPIDER means

 | Letter | Meaning                     | What you do                                                                                                                            |
| ------ | --------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| S      | Situation                   | Clarify the business problem, users, scale, and success criteria.                                                                      |
| P      | Prerequisites / constraints | Identify functional and non-functional requirements: latency, cost, accuracy, privacy, compliance, availability, and data constraints. |
| I      | Initial design              | Propose a high-level architecture and data/control flow.                                                                               |
| D      | Deep dive                   | Examine the hardest components: retrieval, model selection, agent orchestration, caching, evaluation, security, or scaling.            |
| E      | Edge cases / failure modes  | Explain what breaks, how you detect it, and how the system degrades safely.                                                            |
| R      | Rollout / roadmap           | Define metrics, rollout strategy, monitoring, iteration, and future improvements.                                                      |


### Example answer skeleton
For “Design a RAG-based internal knowledge assistant”:

* Situation: Internal employees need accurate, cited answers from product and policy documentation.

* Prerequisites: p95 latency under 3 seconds, no cross-tenant data exposure, low hallucination rate, cost budget, and support for 10,000 daily users.

* Initial design: API gateway, hybrid retrieval, reranker, LLM generation, citations, guardrails, observability, and feedback loop.

* Deep dive: Permission-aware hybrid retrieval, chunking/index freshness, and evaluation of answer faithfulness.

* Edge cases: No relevant context, stale documents, prompt injection, provider outage, incorrect answers, and tenant isolation.

* Rollout: Offline evaluation, shadow traffic, canary launch, monitoring, rollback plan, and continuous evaluation.


### Key insight
SPIDER is less about producing a perfect diagram and more about demonstrating structured engineering judgment:

* Clarify before designing.

* State constraints explicitly.

* Justify every major component.

* Make tradeoffs visible.

* Design for failure, security, observability, and iteration.

* Finish with a credible production rollout plan.