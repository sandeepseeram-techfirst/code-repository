 ## Strimzi

**Strimzi is an open-source project that makes it easy to run and manage Apache Kafka on Kubernetes.** It is not a company selling a proprietary product, and it is not a replacement for Kafka. Instead, it is an automation layer: you describe the Kafka setup you want, and Strimzi creates and maintains it inside Kubernetes. 

Think of Kafka as a high-speed messaging and event-streaming system that applications use to send and receive data. Strimzi makes Kafka behave like a normal Kubernetes application: deployable through YAML, automatically healed when something fails, scalable through configuration, and manageable with standard Kubernetes tools.

## What it offers

Strimzi provides several main components:

| Component | What it does | Simple explanation |
|---|---|---|
| **Cluster Operator** | Installs, configures, scales, upgrades, and repairs Kafka clusters | The main controller that runs Kafka for you |
| **Topic Operator** | Manages Kafka topics using Kubernetes YAML | You create a topic by writing a resource file |
| **User Operator** | Manages Kafka users, passwords, certificates, and permissions | Controls who can connect and what they can access |
| **HTTP Bridge** | Lets applications use Kafka through HTTP/REST | Useful for apps that cannot use native Kafka clients |
| **Kafka Connect support** | Manages connectors that move data between Kafka and other systems | Connect Kafka to databases, files, cloud storage, and more |
| **MirrorMaker support** | Replicates data between Kafka clusters | Useful for disaster recovery or copying data between regions |
| **Drain Cleaner** | Helps safely move Kafka brokers during Kubernetes node maintenance | Reduces disruption during patching or node upgrades |

## How it works

1. **Install Strimzi in Kubernetes.** This adds custom Kubernetes resource types such as `Kafka`, `KafkaTopic`, and `KafkaUser`.

2. **Describe Kafka in YAML.** For example, you can say: “Create a Kafka cluster with three brokers, persistent storage, TLS encryption, and external access.”

3. **Strimzi creates the cluster.** The Cluster Operator creates Kafka broker pods, storage volumes, networking services, certificates, and required configuration.

4. **Kubernetes keeps it running.** If a broker pod crashes, Kubernetes restarts it. Strimzi ensures Kafka-specific configuration and recovery steps are handled correctly.

5. **You manage topics and users declaratively.** Instead of running manual Kafka commands, you create a `KafkaTopic` or `KafkaUser` YAML file. Strimzi applies the change.

6. **Applications connect to Kafka normally.** Standard Kafka clients work directly. If an application only supports HTTP, the Strimzi HTTP Bridge can expose Kafka operations through REST APIs.

## Simple example

A team wants a Kafka cluster for processing online orders.

- The platform team creates a `Kafka` resource requesting three brokers, 500 GB of storage, TLS, and internal access.
- Strimzi deploys the brokers on Kubernetes.
- The payments team creates a `KafkaTopic` called `orders`.
- The fraud team creates a `KafkaUser` with permission to read that topic.
- The order service produces events such as “order created,” “payment completed,” and “order shipped.”
- Analytics, notification, inventory, and fraud-detection services consume those events independently.

No team needs to manually install Kafka, create certificates, configure storage, or manage broker restarts.

## Business insights

- **Lower operational cost:** Strimzi automates deployment, upgrades, scaling, certificate handling, and recovery, reducing manual platform work.
- **Faster delivery:** Developers can request Kafka resources through YAML instead of waiting for infrastructure teams to provision systems manually.
- **Consistency across environments:** The same Kafka definitions can be reused across development, staging, and production, reducing configuration drift.
- **Cloud flexibility:** Because it runs on Kubernetes, Strimzi works across on-premises, private cloud, and public cloud environments.
- **Better governance:** Kafka configuration, topics, users, and access rules can be stored in Git, reviewed through pull requests, and deployed through CI/CD.
- **Avoids vendor lock-in:** Teams can use the same Kafka operational model across multiple clouds or move workloads without redesigning the platform.

## Technical insights

- **Kafka becomes Kubernetes-native:** Kafka clusters are managed through Kubernetes custom resources and controllers.
- **Declarative model:** You define the desired end state; Strimzi continuously works to make the live system match it.
- **Automated lifecycle management:** It handles provisioning, scaling, upgrades, configuration changes, and failure recovery.
- **Security by design:** It supports TLS encryption, authentication, authorization, certificates, and user management.
- **High-availability patterns:** Kafka brokers can be distributed across nodes or availability zones, with persistent storage and controlled pod disruption.
- **GitOps-friendly:** Kafka infrastructure can be managed with tools such as Helm, Argo CD, Flux, and standard Kubernetes deployment pipelines.
- **Still requires SRE discipline:** Strimzi automates operations, but teams still need to plan storage capacity, broker sizing, network throughput, backup strategy, monitoring, and disaster recovery.

## Where to use it

### Event-driven microservices

Use Strimzi when services need to communicate asynchronously. For example, an order service publishes an event, while inventory, billing, notification, and analytics services consume it independently.

### Real-time data pipelines

Use it to ingest logs, application events, clickstreams, sensor data, or database changes and stream them into processing systems, data lakes, warehouses, or dashboards.

### IoT and telemetry

Use it to collect high-volume device data, absorb traffic bursts, and distribute events to monitoring, alerting, storage, and analytics systems.

### AI and ML platforms

Use it to stream training features, inference requests, model predictions, user feedback, and monitoring events into real-time data pipelines.

### Internal developer platform

Platform teams can offer Kafka as a self-service capability. Product teams submit YAML manifests for clusters, topics, and users, while the platform team controls standards, quotas, security, and lifecycle policies.

### Multi-cloud and hybrid deployments

Use Strimzi when you need Kafka to run consistently across Kubernetes clusters in different clouds, data centers, or edge locations.

### Disaster recovery

Use Kafka replication through MirrorMaker to copy data between clusters or regions, helping support failover and business continuity.

## When Strimzi is the right choice

Choose Strimzi if you already use Kubernetes, want Kafka managed as code, need portability across clouds, or have a platform engineering team that wants control over Kafka operations.

Choose a fully managed Kafka service instead if your team has limited Kubernetes expertise or wants the vendor to take responsibility for capacity planning, upgrades, patching, and operational support. Strimzi gives more control and flexibility; managed services reduce day-to-day operational responsibility.