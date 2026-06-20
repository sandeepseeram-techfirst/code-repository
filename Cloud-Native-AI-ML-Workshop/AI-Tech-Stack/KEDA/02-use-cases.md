## Real-world use cases

### 1. Kafka consumer autoscaling

A data platform ingests clickstream events into Kafka. During business hours, consumer lag rises; overnight, it falls to zero.

KEDA can scale consumers based on Kafka consumer-group lag, keeping processing latency low without permanently running a large consumer fleet.

### 2. Queue-based workers

An e-commerce order service publishes events to RabbitMQ or SQS. Workers handle payment validation, inventory reservation, email notifications, and fraud checks.

KEDA scales workers based on queue depth or message backlog, then scales them to zero during quiet periods.

### 3. AI/ML batch inference

An ML platform receives inference requests through Redis, Kafka, or a task queue. GPU or CPU inference pods are expensive, so keeping them always-on is wasteful.

KEDA can scale inference workers based on pending jobs, queue length, or a custom metric from an inference gateway.

### 4. Scheduled workloads

A reporting service only needs capacity at 06:00 and 18:00. A Cron trigger can scale it up on schedule and back down afterward.

### 5. CI/CD runner scaling

A platform team runs self-hosted GitHub Actions runners. Instead of maintaining fixed runner capacity, KEDA scales runners based on queued workflow jobs.

### 6. Database-driven processing

A legacy application writes work items to PostgreSQL. KEDA can scale a processor Deployment based on a SQL query result, avoiding a rewrite of the application’s event model.

### 7. Multi-tenant SaaS

A SaaS platform has hundreds of tenant-specific workers. Most tenants are inactive at any given time. KEDA enables a scale-to-zero model, reducing baseline compute consumption while preserving responsiveness.


## KEDA vs native HPA

| Capability | Native HPA | KEDA |
|---|---|---|
| CPU/memory scaling | Yes | Yes, via CPU/memory triggers |
| External event metrics | Requires custom metrics setup | Built-in through scalers |
| Scale-to-zero | Not practical for CPU/memory triggers | First-class for supported event triggers |
| Queue/stream lag scaling | Not native | Native |
| Batch Job scaling | Limited | Native via `ScaledJob` |
| Vendor integrations | Manual | 70+ built-in scalers |
| Replacement model | Core Kubernetes component | Add-on that extends HPA |

KEDA is therefore best understood as an **event-aware control plane for HPA**, not a competing autoscaler. 

### Choose the right metric

Prefer a metric that directly represents pending work:

- Kafka: consumer lag.
- RabbitMQ: queue length or unacknowledged messages.
- SQS: approximate number of visible messages.
- Prometheus: request rate, backlog size, or custom business KPI.
- Database: pending-row count from an indexed query.

Avoid scaling on indirect metrics when a direct backlog signal is available.

### Set realistic bounds

- Use `minReplicaCount: 0` only when cold-start latency is acceptable.
- Use `minReplicaCount: 1` for latency-sensitive consumers.
- Set `maxReplicaCount` based on downstream capacity: database connections, Kafka partitions, API rate limits, and GPU availability.
- Remember that scaling beyond the number of Kafka partitions usually does not increase parallelism for a single consumer group.

### Control scaling behavior

- Tune polling intervals to balance responsiveness against event-source load.
- Use cooldown periods to prevent flapping.
- Add stabilization windows where supported.
- Monitor KEDA decisions, HPA events, queue depth, pod startup time, and downstream saturation.

### Secure event-source access

- Store credentials in Kubernetes Secrets or use workload identity where possible.
- Use `TriggerAuthentication` rather than embedding credentials in `ScaledObject` metadata.
- Apply least-privilege permissions to queues, topics, databases, and metrics endpoints.
- Restrict who can create or modify KEDA resources with RBAC and admission policies.