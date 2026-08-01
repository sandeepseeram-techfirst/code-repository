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