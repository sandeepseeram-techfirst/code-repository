## Apache Pulsar 

Apache Pulsar is an open-source, cloud-native **distributed messaging and streaming platform**. In simple terms, it is the high-speed “postal system” for applications: producers send event messages to topics, and consumers receive and process them—either one at a time like a work queue, or continuously like a data stream.

## What the project is

Apache Pulsar is maintained by the Apache Software Foundation and is designed for large-scale, real-time systems. It combines capabilities often split across systems such as Kafka-style event streaming, RabbitMQ-style queues, and pub/sub messaging into one platform. It is built to run well on Kubernetes and can handle millions of messages per second across very large numbers of topics.

## Products and capabilities

Pulsar is not a commercial product suite; it is an open-source platform with several major capabilities.

| Capability | What it does | Simplified explanation |
|---|---|---|
| Topics | Named channels for messages | A service publishes events such as `orders.created` or `iot.telemetry` to a topic |
| Producers | Applications that write messages | Example: a checkout service publishes an order event |
| Consumers | Applications that read messages | Example: a fraud service, analytics service, and notification service each consume the same order event |
| Subscriptions | Ways consumers receive messages | Shared subscriptions distribute work; exclusive/failover subscriptions support ordered or highly available processing |
| Pulsar Functions | Lightweight serverless processors | Small Java, Go, or Python programs that transform, filter, enrich, or route messages without deploying a full application |
| Connectors / IO | Sources and sinks | Move data into Pulsar from systems such as MySQL, or out to systems such as Elasticsearch, Cassandra, or other databases |
| Multi-tenancy | Isolated namespaces for teams | One platform can serve many teams with separate access controls, quotas, and policies |
| Geo-replication | Copies data across regions/clusters | Keeps messaging available if a region or data center fails |
| Tiered storage | Moves older data to cheaper storage | Keeps recent data on fast storage while retaining historical event data cost-effectively |

## How it works

Pulsar separates the **serving layer** from the **storage layer**.

1. **Producer sends a message.** An application publishes a message to a topic, such as `payments.transactions`.
2. **Broker receives it.** A stateless Pulsar broker accepts the message, routes it, and serves consumers. Brokers do not permanently own data.
3. **BookKeeper stores it.** The message is written to an append-only ledger in Apache BookKeeper. By default, each segment is replicated across three BookKeeper nodes.
4. **Consumer reads it.** A consumer receives the message, processes it, and acknowledges it. Pulsar can acknowledge individual messages or a range of messages.
5. **Pulsar Functions process it.** If needed, a lightweight function can enrich the event—for example, adding customer tier, geolocation, or risk score—before forwarding it to another topic.
6. **Connectors deliver it.** A sink connector can send processed events to Elasticsearch for search, a database for persistence, or an analytics system.

The important architectural idea is that brokers can be added or removed quickly because they are stateless, while BookKeeper stores data durably and can scale without moving existing data. This makes Pulsar effective for sudden traffic spikes.

## Key technical insights

- **Compute and storage are decoupled.** Brokers handle messaging traffic; BookKeeper handles durable storage. This enables independent scaling of processing and storage.
- **It supports both queue and stream semantics.** You can use it for task queues with individual acknowledgments, or for ordered event streams with cumulative acknowledgments.
- **Multi-tenancy is built in.** Tenants, namespaces, topics, authorization, quotas, and isolation make it suitable as a shared internal messaging platform.
- **Geo-replication is first-class.** You can replicate topics across clusters and support client failover during regional outages.
- **It is Kubernetes-friendly.** Brokers, BookKeeper, functions, and connectors can run as containerized workloads, making it a strong fit for cloud-native platform engineering.
- **Retention and replay are possible.** Consumers can reconnect and read retained historical messages, which is useful for recovery, backfills, audits, and rebuilding downstream state.
- **It supports many languages.** Official clients include Java, Go, Python, C++, Node.js, and C#.

## Business insights

- **Platform consolidation:** Pulsar can reduce the operational burden of running separate Kafka, RabbitMQ, and ActiveMQ-style systems by offering queueing, streaming, and pub/sub in one platform.
- **Team autonomy with central governance:** Platform teams can operate one messaging backbone while application teams retain self-service control over their own namespaces and topics.
- **Lower integration friction:** When all services use one event backbone, cross-team integrations become simpler than bridging separate messaging systems.
- **Cost control:** Tiered storage lets you retain large event histories without keeping all of it on expensive hot storage.
- **Operational resilience:** Replication, geo-replication, and durable acknowledgment semantics support business-critical systems where message loss is unacceptable.
- **Faster scaling during peaks:** Its architecture is particularly valuable for seasonal spikes, flash sales, IoT bursts, or AI inference request surges.

## Practical use cases

### Real-time data platform

Use Pulsar as the event backbone for clickstreams, application logs, telemetry, and user activity. Producers publish events; stream processors or Pulsar Functions enrich them; consumers load them into search, analytics, feature stores, or data lakes.

**Example:** An e-commerce platform publishes clicks, cart updates, payments, and inventory changes. Downstream systems use those events for recommendations, fraud detection, dashboards, and order fulfillment.


### Microservices event backbone

Services communicate through domain events rather than direct point-to-point API calls. This reduces coupling and makes it easier to add consumers later.

**Example:** When `order.created` is published, separate services handle inventory reservation, payment capture, email notification, analytics, and loyalty points—without the order service knowing about each consumer.

### Task and job queues

Use shared subscriptions to distribute jobs across worker fleets, with individual acknowledgments and retries for failed work.

**Examples:** Video transcoding, image thumbnail generation, PDF processing, ML batch inference, report generation, webhook delivery, and data-file ingestion.

### IoT and telemetry ingestion

Pulsar is well suited to high-volume device events because it supports many topics, horizontal scale, and low-latency consumption.

**Example:** Connected vehicles, industrial sensors, smart buildings, or retail IoT devices publish telemetry to Pulsar. Functions detect anomalies, and downstream services trigger maintenance workflows or alerts.

### AI/ML and feature pipelines

Use Pulsar to move model inputs, predictions, feedback, and monitoring events in real time.

**Example:** A fraud model consumes transaction events, returns a risk score, and publishes `transaction.scored`. A decision service consumes that event and approves, challenges, or blocks the transaction. Feedback events can later be used for model monitoring and retraining.

### Mission-critical event processing

For payments, banking, order management, and healthcare workflows, Pulsar’s durable writes and replicated storage help reduce the risk of losing accepted messages.

**Example:** A payment service publishes a transaction event only after it is durably stored; downstream settlement, ledger, notification, and audit services consume it reliably.

## When to choose Pulsar

Choose Pulsar when you need:

- One platform for both message queues and event streams
- Strong multi-tenancy for a large engineering organization
- Geo-replication and regional failover
- High-volume IoT, telemetry, or event ingestion
- Kubernetes-native messaging infrastructure
- Fast scale-out during unpredictable traffic spikes
- Durable, replicated messaging for business-critical workflows

It may be more complexity than needed for a small application with only a few services and modest message volume. For those cases, a simpler managed queue or lightweight broker can be easier to operate. But for a multi-team, cloud-native, high-scale event platform, Pulsar is a strong candidate. 