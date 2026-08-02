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

