## wasmCloud

wasmCloud is an **open-source, cloud-native platform for building, deploying, and orchestrating WebAssembly (Wasm) workloads** across Kubernetes, public clouds, datacenters, and edge devices. Think of it as a lightweight alternative or complement to container orchestration: instead of packaging applications as large container images, it runs small, portable, sandboxed Wasm components.

## What it is

wasmCloud is a CNCF incubating project, not a traditional commercial product company. Its core idea is to let teams compose applications from reusable, polyglot Wasm components—such as microservices, functions, event processors, or AI agents—and run them consistently in many environments.

A Wasm component is a small compiled artifact, often kilobytes to low megabytes in size. It starts in milliseconds, is isolated from the host by default, and can run anywhere a WASI-compatible runtime is available without recompilation.

## What it offers

| Offering | What it does | Simplified analogy |
|---|---|---|
| **`wash` CLI** | Builds, tests, and publishes Wasm components using languages such as Rust, Go, and TypeScript. | Developer toolkit for creating and shipping Wasm apps |
| **wasmCloud Runtime** | Executes Wasm components and manages the permissions they receive. | A secure application engine for Wasm |
| **Kubernetes Operator** | Installs and manages wasmCloud infrastructure through standard Kubernetes resources. | Kubernetes extension for running Wasm workloads |
| **Capability system** | Explicitly grants components access to files, network, databases, messaging, or other services. | Fine-grained firewall and permission model for application logic |
| **Orchestration layer** | Schedules, connects, scales, and recovers distributed Wasm components. | Lightweight distributed runtime for Wasm apps |

The platform is designed to work alongside existing container and Kubernetes estates rather than requiring a full replacement.

## How it works

1. **Build a component**: A developer writes business logic in a supported language and compiles it into a WebAssembly component.
2. **Publish it**: The component is pushed to an OCI registry, similar to how container images are stored.
3. **Declare capabilities**: The developer or platform team specifies what the component may access—for example, HTTP outbound, PostgreSQL, Kafka, or object storage.
4. **Deploy it**: wasmCloud deploys the component to Kubernetes, a VM, bare metal, an IoT gateway, or another host.
5. **Run it securely**: At runtime, the component can perform only the explicitly granted actions. Everything else is denied.
6. **Operate it**: Kubernetes-native features such as HPA, KEDA, GitOps, RBAC, observability, and backup tooling continue to work normally.

The major difference from containers is the security model. Containers commonly start with broad host and network access unless restrictions are added; Wasm components start with **no access** unless a capability is explicitly granted.

## Business insights

- **Lower infrastructure waste**: Small, fast-starting Wasm components can reduce idle capacity and improve density compared with conventional container-based workloads.
- **Faster delivery**: Reusable components can be shared across teams, reducing duplicated logic and making platform golden paths easier to enforce.
- **Lower operational burden**: Central teams can update, version, and govern shared components rather than patching hundreds of similar applications independently.
- **Better multi-cloud portability**: The same Wasm artifact can run across clouds, Kubernetes clusters, datacenters, and edge sites without platform-specific rebuilds.
- **Improved security posture**: Deny-by-default execution and explicit capability grants reduce the attack surface, especially for third-party or untrusted code.
- **Platform-engineering leverage**: wasmCloud fits well as a substrate for internal developer platforms, serverless/FaaS platforms, and standardized application delivery.

## Technical insights

- **Wasm components are not containers**: They are sandboxed bytecode artifacts, usually much smaller and faster to start.
- **WASI provides portability**: Components target the WebAssembly System Interface, allowing the same binary to run on conformant runtimes.
- **Capabilities replace implicit privileges**: Network, filesystem, database, and system access must be explicitly declared and granted.
- **Kubernetes remains the control plane**: The operator integrates with existing Kubernetes workflows, policies, autoscaling, and observability.
- **Polyglot by design**: Teams can use Rust, Go, TypeScript, and other languages that compile to Wasm components.
- **Complements, not replaces, containers**: It is most compelling for new event-driven services, plugins, edge workloads, and untrusted extension code—not necessarily for every legacy monolith.

## Practical use cases

- **Multi-tenant serverless/FaaS platform**: Run customer-supplied functions in isolated, capability-limited Wasm sandboxes with high density and fast cold starts.
- **Edge and IoT processing**: Deploy lightweight data-filtering, protocol-translation, or ML inference components on factory floors, gateways, vehicles, or retail sites.
- **Secure third-party extensions**: Let partners or customers upload plugins while strictly limiting filesystem, network, and database access.
- **Event-driven data pipelines**: Build small processing stages for Kafka, NATS, message queues, or streaming data, then reuse them across environments.
- **API backend services**: Run API handlers, authentication helpers, transformation logic, and business rules as independently deployable Wasm components.
- **AI agent tooling**: Host agent tools, guardrails, data connectors, and inference preprocessing as small, auditable components close to data or users.
- **Hybrid and multi-cloud applications**: Deploy the same component artifact across cloud providers, on-premises clusters, and edge locations to avoid lock-in.
- **Platform engineering golden paths**: Offer developers a curated catalog of reusable Wasm components, templates, policies, and deployment workflows.

## Where it fits best

wasmCloud is strongest when you need **portability, fast startup, high workload density, strict isolation, and distributed deployment**—particularly across Kubernetes, edge, and multi-cloud environments. It is less compelling for workloads that depend heavily on legacy native libraries, GPU-heavy training, complex OS-level integrations, or existing container images that already meet your operational and security requirements.