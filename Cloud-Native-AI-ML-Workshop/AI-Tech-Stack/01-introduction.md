## AI Tech Stack 

## AI Agent

### Agent frameworks 
- **Agent Development Kit** — Build agent applications with structured tool use and workflows.
- **Agno** — Lightweight framework for building autonomous AI agents.
- **AutoGen** — Multi-agent conversation and orchestration framework.
- **CAMEL** — Framework for role-playing and cooperative multi-agent systems. 
- **CrewAI** — Build role-based teams of collaborating AI agents.
- **LangChain** — General-purpose framework for LLM applications, chains, tools, and integrations.
- **LangGraph** — Graph-based orchestration for stateful, controllable agent workflows.
- **Pydantic AI** — Type-safe agent framework with structured outputs and validation.
- **Semantic Kernel** — SDK for integrating LLMs, plugins, memory, and planners into applications.
- **Smolagents** — Minimal framework for building code-driven agents.
- **Strands** — Agent development framework for tool use and task execution.
- **kagent** — Kubernetes-native framework for building and operating AI agents.

### Vector databases
- **Chroma** — Embedded or server-based vector database for AI applications.
- **LanceDB** — Serverless vector database built around the Lance columnar format.
- **Marqo** — End-to-end vector search engine with integrated embedding generation.
- **Milvus** — Highly scalable distributed vector database.
- **pgvector** — PostgreSQL extension for storing and querying embeddings.
- **Qdrant** — Vector database optimized for high-performance similarity search.
- **Weaviate** — Vector database with modular embedding, hybrid search, and graph-like capabilities.
- **OpenSearch** — Search and analytics platform with vector search support.

### Workflow orchestration
- **Astron Agent** — Orchestration platform for agent-based applications.
- **Dify** — Low-code platform for building LLM apps, agents, and RAG workflows.
- **Hatchet** — Durable task and workflow orchestration engine.
- **Hive Commons** — Platform for coordinating AI workflows and agent activity.
- **Inngest** — Event-driven durable workflow orchestration for applications and agents.
- **Temporal** — Durable execution platform for long-running, reliable workflows.

### Agent tools
- **Browser Use** — Enables agents to operate and interact with web browsers.
- **Composio** — Managed tool and integration layer for agents.
- **Firecrawl** — Web crawling, scraping, and structured data extraction for AI systems.
- **Jina Reader** — Converts web pages and documents into clean model-readable content.
- **Selenium Grid** — Distributed browser automation infrastructure.

### Evaluation
- **Agent Evaluation** — Testing and assessment of agent behavior and outcomes.
- **DeepEval** — Unit-testing framework for LLM applications and RAG systems.
- **Promptfoo** — Prompt, model, and agent evaluation with regression testing.
- **Ragas** — Evaluation framework focused on RAG quality.
- **TruLens** — Instrumentation and evaluation for LLM and agent applications.

### RAG
- **Docling** — Document parsing and conversion for AI ingestion pipelines.
- **Haystack** — Framework for building search, RAG, and NLP applications.
- **LlamaIndex** — Data framework for indexing, retrieval, and context augmentation.
- **txtai** — Embeddings database and semantic search workflow toolkit.
- **Unstructured** — Extracts and transforms unstructured documents into usable data.

### Structured output
- **Guidance** — Controls LLM generation using structured templates and constraints.
- **Instructor** — Extracts validated structured data from LLM responses.
- **LMQL** — Query language for constrained and structured LLM generation.
- **Outlines** — Structured generation library using schemas, grammars, and finite-state constraints.

### Guardrails
- **Guardrails AI** — Validates and corrects LLM outputs against defined policies.
- **LLM Guard** — Security and safety controls for LLM inputs and outputs.
- **NeMo Guardrails** — Programmable guardrails for conversational AI systems.

### Knowledge graphs
- **Apache AGE** — Graph extension for PostgreSQL.
- **FalkorDB** — In-memory graph database designed for low-latency queries.
- **Neo4j** — Native graph database for relationships, knowledge graphs, and graph analytics.

### Protocols
- **Agent2Agent** — Protocol for interoperable communication between agents.
- **Model Context Protocol** — Standard protocol connecting models and agents to tools, data, and context.

### State and memory
- **Mem0** — Memory layer for persistent user, session, and agent context.
- **Apache HBase** — Distributed, scalable key-value store usable for stateful workloads.

## Inference

### Inference frameworks
- **KServe** — Kubernetes-native model serving with autoscaling and traffic management.
- **AIBrix** — Cloud-native control plane and infrastructure for LLM inference.
- **Arks** — AI inference serving and scheduling platform.
- **InferNex** — Platform for scalable model inference operations.
- **KAITO** — Kubernetes operator for automated AI model deployment.
- **llm-d** — Distributed LLM inference system for Kubernetes.
- **llmaz** — Kubernetes-native platform for serving large language models.
- **RBG** — Resource management and inference orchestration for AI workloads.
- **Volcano Kthena** — AI-native scheduling and inference platform built on Volcano.

### Runtime
- **llama.cpp** — Efficient local inference runtime for LLMs.
- **OpenVINO** — Optimized inference toolkit for Intel hardware.
- **Seldon** — Model serving and deployment platform.
- **SGLang** — High-performance LLM serving engine with structured generation support.
- **TGI** — Text Generation Inference server for production LLM deployment.
- **vLLM** — High-throughput LLM inference engine with paged attention and batching.

## Training

### Distributed training
- **DeepSpeed** — Microsoft’s optimization library for large-scale distributed training.
- **Horovod** — Distributed training framework for TensorFlow, PyTorch, and MXNet.
- **Kubeflow MPI Operator** — Runs MPI-based distributed training jobs on Kubernetes.
- **Kubeflow Training Operator** — Kubernetes operator for distributed ML training jobs.
- **Megatron-LM** — Framework for training very large transformer models.
- **Open MPI** — Message Passing Interface implementation for distributed computing.
- **PyTorch DDP** — Native distributed data-parallel training in PyTorch.
- **TensorFlow Distributed** — TensorFlow’s distributed training strategies.
- **TorchX** — PyTorch job launcher and distributed training orchestration tool.

### Post-training
- **Axolotl** — Fine-tuning toolkit for LLMs.
- **Hyperopt** — Hyperparameter optimization library.
- **Kubeflow Katib** — Kubernetes-native hyperparameter tuning and neural architecture search.
- **LlamaFactory** — Fine-tuning framework for large language models.
- **Optuna** — Hyperparameter optimization framework.
- **Unsloth** — Efficient fine-tuning library for LLMs.
- **verl** — Reinforcement learning framework for post-training LLMs.

### Evaluation
- **DeepEval** — LLM evaluation and testing framework.
- **lm-evaluation-harness** — Standardized benchmarking framework for language models.
- **OpenCompass** — Evaluation platform for large models.

## Data

### Data architecture
- **Fluid** — Dataset orchestration and acceleration for Kubernetes.
- **Apache HBase** — Distributed NoSQL key-value store.
- **Apache Druid** — Real-time analytical database.
- **Apache Flink** — Stream and batch data processing engine.
- **Apache Pinot** — Real-time OLAP datastore.
- **FEAST** — Open-source feature store for ML.
- **Hadoop HDFS** — Distributed file system for large-scale data storage.
- **Kubeflow Spark Operator** — Runs Apache Spark jobs on Kubernetes.
- **Memcached** — Distributed in-memory cache.
- **ScyllaDB** — High-performance NoSQL database.
- **Trino** — Distributed SQL query engine.
- **Alluxio** — Data orchestration and caching layer.
- **Cassandra** — Distributed NoSQL database.
- **ClickHouse** — Columnar analytical database.
- **Presto** — Distributed SQL query engine.
- **Redis** — In-memory data store and cache.
- **Valkey** — Open-source Redis-compatible in-memory data store.
- **Apache Spark** — Distributed data processing and analytics engine.
- **Kafka** — Distributed event streaming platform.
- **Numaflow** — Kubernetes-native stream processing platform.
- **Pulsar** — Distributed pub-sub messaging and event streaming platform.

### Data science
- **Apache Zeppelin** — Web-based notebook for data exploration and analytics.
- **Kubeflow Notebooks** — Kubernetes-native notebook environments.
- **Marimo** — Reactive Python notebook framework.
- **Project Jupyter** — Interactive computing and notebook ecosystem.
- **PyTorch** — Deep learning framework.
- **TensorFlow** — End-to-end machine learning framework.
- **XGBoost** — Gradient-boosted decision tree library.

## AI Native Infrastructure

### Gateway
- **Volcano Kthena** — AI-native gateway and inference platform.
- **AgentGateway** — Gateway for agent and model traffic.
- **Envoy AI Gateway** — Envoy-based gateway for AI workloads.
- **Kgateway** — Kubernetes-native API gateway.
- **MCP Gateway Registry** — Registry and gateway for MCP servers and tools.
- **Higress** — Cloud-native API gateway with AI traffic capabilities.

### Orchestration and scheduling
- **Karmada** — Multi-cluster Kubernetes management.
- **KEDA** — Event-driven autoscaling for Kubernetes.
- **Knative** — Serverless workloads on Kubernetes.
- **Kubernetes** — Container orchestration platform.
- **HAMi** — Heterogeneous AI device management and GPU virtualization.
- **Volcano** — Kubernetes batch and high-performance workload scheduler.
- **agent-sandbox** — Sandboxed execution environment for agents.
- **KubeRay** — Kubernetes operator for Ray clusters.
- **Kueue** — Kubernetes-native job queueing and quota management.
- **LeaderWorkerSet** — Kubernetes API for managing leader-worker workload groups.
- **NVIDIA NeMo** — Framework and platform for generative AI model development.
- **Topograph** — Topology-aware scheduling and resource mapping.
- **Yunikorn** — Lightweight resource scheduler for Kubernetes.
- **Armada** — Distributed batch job scheduler.
- **Backend.AI** — AI infrastructure and workload orchestration platform.
- **Cozystack** — Open-source cloud platform built on Kubernetes.
- **Koordinator** — Kubernetes workload scheduling and resource optimization.
- **Slurm** — High-performance computing workload manager.

### Workload runtime
- **containerd** — Industry-standard container runtime.
- **CRI-O** — Lightweight Kubernetes container runtime.
- **CubeSandbox** — Sandboxed execution environment.
- **E2B** — Secure cloud sandbox for running AI-generated code.
- **Firecracker** — Lightweight microVM runtime.
- **gVisor** — Application kernel for container sandboxing.
- **iSulad** — Lightweight container runtime.
- **Kata Containers** — Containers with hardware-level virtualization isolation.
- **Kuasar** — Multi-sandbox container runtime.
- **runc** — Low-level OCI container runtime.
- **Singularity** — Container platform for HPC and scientific workloads.
- **StratoVirt** — Lightweight virtualization runtime.
- **WasmEdge Runtime** — WebAssembly runtime for secure, lightweight workloads.
- **Daytona** — Development environment and workspace orchestration platform.

### Accelerator and SuperPod
- **Topograph** — Topology-aware accelerator and cluster mapping.
- **CANN** — Huawei’s heterogeneous computing architecture for AI acceleration.
- **NCCL** — NVIDIA Collective Communications Library for multi-GPU communication.
- **Triton** — Language and compiler for writing GPU kernels.

### Storage
- **CubeFS** — Cloud-native distributed file system.
- **Ceph** — Unified distributed storage system.
- **CSI** — Container Storage Interface standard.
- **JuiceFS** — Cloud-native distributed POSIX file system.
- **NoKV** — Key-value storage engine.

### Network
- **Cilium** — eBPF-based networking, security, and observability for Kubernetes.
- **CNI** — Container Network Interface standard.

### Model asset and registry
- **Kubeflow Model Registry** — Central registry for model versions and metadata.
- **MatrixHub** — Model and artifact distribution hub.
- **ModelPack** — Model packaging and artifact management.

### Governance, policy and security
- **Keycloak** — Identity and access management.
- **Kyverno-JSON** — JSON-based policy validation and mutation.
- **OPA/Gatekeeper** — Policy-as-code admission control for Kubernetes.
- **OPEA** — Open Platform for Enterprise AI.
- **Stacklok Minder** — Software supply-chain security and policy enforcement.
- **Permify** — Authorization and fine-grained access control service.
- **SpiceDB** — Google Zanzibar-inspired authorization database.

### Observability
- **OpenTelemetry** — Vendor-neutral telemetry standard for traces, metrics, and logs.
- **Prometheus** — Metrics collection and alerting system.
- **Deepchecks** — Testing and monitoring for ML models and data.
- **DeepFlow** — Observability platform with eBPF-based deep visibility.
- **InfluxDB** — Time-series database.
- **Langfuse** — LLM observability, tracing, and evaluation platform.
- **Okahu** — AI workload observability and monitoring.
- **TruLens** — LLM and agent observability and evaluation.
- **Weights & Biases** — Experiment tracking, model monitoring, and ML observability.
- **DataBuff** — AI observability and performance monitoring.
- **Grafana** — Visualization and observability dashboards.
- **Kepler** — Kubernetes-based energy and power monitoring.
- **Oodle AI** — AI observability and monitoring platform.
- **OpenLIT** — OpenTelemetry-native LLM observability tool.
- **OpenLLMetry** — OpenTelemetry instrumentation for LLM applications.

### CI/CD
- **BentoML** — Package, deploy, and scale ML models.
- **Kubeflow Pipelines** — Kubernetes-native ML workflow orchestration.
- **MLflow** — Experiment tracking, model registry, and ML lifecycle management.
- **MLRun** — MLOps orchestration and automation framework.
- **TensorFlow Extended** — End-to-end ML pipeline platform.