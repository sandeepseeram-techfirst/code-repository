## Apache Kafka

Apache Kafka is an open-source **event-streaming platform**. In simple terms, it is a very fast, durable, and scalable system for moving real-time events between applications, services, databases, sensors, and analytics systems.

Think of Kafka as an enterprise-grade “central nervous system”: when something important happens—such as an order being placed, a payment completing, or a machine sensor reporting a temperature—Kafka receives that event and makes it available to many other systems.

It is not a traditional company selling a fixed product suite. Kafka is an Apache Software Foundation open-source project that can be self-hosted, run in Kubernetes, deployed across clouds, or consumed through managed Kafka services.

## Core concept

Kafka works around **events**.

An event is a small record describing something that happened:

```json
{
  "event": "payment_completed",
  "customer_id": "12345",
  "amount": 99.99,
  "timestamp": "2026-11-02T18:59:00Z"
}
```

A **producer** sends events into Kafka. Kafka stores them in a **topic**, such as `payments`, `orders`, or `iot-telemetry`. 
Then one or more **consumers** read those events and take action.

The important difference from a regular message queue is that Kafka does not delete an event immediately after it is consumed. Events remain stored for a configured retention period, so another service can replay them later.

## Products and capabilities

| Capability | What it does | Simplified explanation |
|---|---|---|
| **Kafka brokers** | Servers that store and distribute event streams | A distributed, fault-tolerant event log |
| **Topics** | Named streams for related events | Channels such as `orders` or `payments` |
| **Partitions** | Splits a topic into parallel streams | Enables horizontal scale and ordered processing per key |
| **Producer API** | Sends events to Kafka | The write side |
| **Consumer API** | Reads events from Kafka | The read side |
| **Consumer groups** | Lets multiple consumers share processing work | A team dividing incoming work |
| **Kafka Streams** | Processes streams in real time | Filter, join, enrich, aggregate, and analyze events |
| **Kafka Connect** | Moves data between Kafka and external systems | Prebuilt connectors for databases, storage, search, and analytics systems |
| **Admin APIs and CLI** | Manages topics, configurations, and clusters | Operational control plane |
| **Client libraries** | SDKs for Java, Python, Go, C/C++, and more | Lets applications integrate in their preferred language |

## How it works

1. **Something happens.** A customer places an order, a payment succeeds, a sensor sends telemetry, or a service changes state.

2. **A producer writes the event to a topic.** For example, an order service writes an `order_created` event to the `orders` topic.

3. **Kafka stores the event in partitions.** A topic is divided into partitions. Events with the same key—such as the same customer ID or order ID—go to the same partition, preserving their order.

4. **Kafka replicates the data.** In production, each partition is usually copied to multiple brokers so the system survives server or network failures.

5. **Consumers read independently.** One consumer group may process events for fraud detection, another for analytics, another for notifications, and another for archiving.

6. **Stream processing and delivery occur.** Kafka Streams can transform or aggregate events in real time. Kafka Connect can deliver processed data to databases, data lakes, search indexes, caches, or APIs.

## Key technical insights

- **Kafka decouples systems.** The producer does not need to know who will consume the event.
- **It is both a message broker and a durable log.** You can replay historical events to recover state or onboard new services.
- **Partitioning enables scale.** More partitions allow more parallel producers and consumers.
- **Ordering is per partition, not across an entire topic.** Use a meaningful key when order matters for a customer, order, device, or account.
- **Replication provides resilience.** A common production setup uses three replicas per partition.
- **Exactly-once processing is supported.** This matters for payments, inventory, billing, and compliance-sensitive systems.
- **It is cloud-agnostic.** Kafka can run on VMs, containers, Kubernetes, on-premises infrastructure, or multi-cloud environments.
- **Operations require planning.** Partition design, retention, consumer lag, security, schema evolution, monitoring, and disaster recovery are critical for production.

## Key business insights

- Kafka enables **real-time business decisions** instead of waiting for overnight batch jobs.
- It reduces **point-to-point integrations** by providing a shared event backbone.
- It improves **resilience** because downstream systems can catch up after outages.
- It supports **auditability and replay**, useful for finance, security, compliance, and incident investigation.
- It allows one event stream to serve many teams: operations, analytics, ML, security, customer support, and finance.

## Practical use cases

| Use case | How Kafka is used | Business value |
|---|---|---|
| **Payments and fraud detection** | Payment events are analyzed in real time for suspicious patterns | Faster fraud prevention |
| **E-commerce orders** | Order, payment, inventory, and shipping events are shared across services | Consistent customer and warehouse experience |
| **IoT and manufacturing** | Sensor events are ingested and analyzed for thresholds or anomalies | Predictive maintenance and safety |
| **Clickstream analytics** | User activity events feed dashboards and recommendations | Personalization and product insights |
| **Database change capture** | Database changes are streamed to analytics or cache systems | Near-real-time reporting |
| **Microservices** | Services communicate through domain events | Loose coupling and independent deployments |
| **Logistics and fleet tracking** | GPS and delivery events stream into monitoring systems | Live tracking and route optimization |
| **Security monitoring** | Logs, audit events, and alerts are centralized | Faster threat detection and response |
| **AI/ML pipelines** | Events feed feature stores, model serving, and monitoring | Real-time scoring and model observability |

## When to use Kafka

Kafka is a strong fit when you need:

- High-volume, low-latency event ingestion
- Real-time analytics
- Decoupled microservices
- IoT telemetry processing
- Streaming ETL or change data capture
- Replayable event history
- Event-driven architecture across cloud and on-premises systems

It may be overkill for a small application that only needs simple background jobs, occasional notifications, or basic request-response communication. In those cases, a simpler queue or direct API integration is often easier to operate.