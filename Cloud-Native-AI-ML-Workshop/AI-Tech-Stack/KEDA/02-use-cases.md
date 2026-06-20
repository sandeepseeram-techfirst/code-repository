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