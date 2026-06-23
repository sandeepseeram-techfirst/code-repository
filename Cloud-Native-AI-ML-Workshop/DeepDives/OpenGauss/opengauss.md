# openGauss: Deep Dive, Simplified 

**openGauss** is an enterprise-grade, open-source relational database management system (RDBMS). It is designed for transactional workloads where throughput, availability, security, and operational automation matter—especially on multi-core, NUMA-aware server hardware.

## In One Sentence

openGauss is a PostgreSQL-lineage-style SQL database that stores structured data in tables, executes SQL transactions, and adds enterprise capabilities such as primary/standby replication, fast failover, encryption, auditing, and AI-assisted tuning.

## What Problem It Solves

Traditional applications need a reliable system of record: banking ledgers, order systems, inventory, customer profiles, and IoT metadata. A plain database may work for development, but production systems require:

- High concurrent read/write throughput.
- Minimal downtime when a database node fails.
- Strong access control, encryption, and auditability.
- Predictable performance as data and traffic grow.
- Lower operational burden for DBAs and platform teams.

openGauss addresses these requirements by combining a relational SQL engine with high-availability replication, security controls, performance optimizations, and AI-based operations tooling.

## Core Architecture

### Logical Layers

```text
Applications / BI tools / ORMs
          |
        SQL API
          |
   SQL Parser & Optimizer
          |
   Executor / Transaction Manager
          |
   Storage Engine / Buffer Cache
          |
   WAL / Replication / Checkpoints
          |
   Primary and Standby Database Nodes
```

### Main Components

| Component | Role |
|---|---|
| SQL engine | Parses, plans, optimizes, and executes SQL statements |
| Transaction manager | Provides ACID transaction behavior, locking, and concurrency control |
| Storage engine | Manages tables, indexes, pages, buffers, and persistent data |
| WAL / redo log | Records changes before they are applied durably, enabling crash recovery |
| Replication layer | Streams changes from primary to standby nodes |
| HA / election layer | Detects failures, promotes a standby, and restores service |
| Security layer | Handles authentication, authorization, encryption, masking, and audit |
| AI/O&M layer | Provides tuning recommendations, index advice, slow-query diagnostics, and monitoring |

## How It Works

### 1. SQL Request Flow

When a client sends SQL:

1. The client authenticates using a database user and credentials.
2. The SQL parser converts the statement into an internal query tree.
3. The optimizer chooses an execution plan, such as an index scan, sequential scan, join method, or parallel plan.
4. The executor reads or modifies rows through the storage engine.
5. Changes are written to the write-ahead log before being considered durable.
6. The result is returned to the client.

### 2. Transactions and Consistency

openGauss follows the relational database model: data is organized into tables of rows and columns, with relationships enforced through keys and constraints. SQL is the primary interface for creating, reading, updating, and deleting data.

A typical transaction:

```sql
BEGIN;

UPDATE accounts
SET balance = balance - 100
WHERE id = 1;

UPDATE accounts
SET balance = balance + 100
WHERE id = 2;

COMMIT;
```

If any statement fails, the transaction can be rolled back, preventing partial money movement.

### 3. Durability and Recovery

openGauss uses write-ahead logging. Before a data change is safely considered committed, its change record is persisted in the WAL. On restart after a crash, the database replays WAL entries to restore a consistent state.

This is why a database can survive a process crash or host reboot without losing committed transactions.

### 4. High Availability

openGauss supports standalone and HA deployments. In HA mode, one node acts as the primary and one or more nodes act as standbys.

```text
             Application
                  |
           Virtual endpoint / proxy
                  |
        +---------+---------+
        |                   |
    Primary DB         Standby DB(s)
        |                   ^
        +--- WAL stream ----+
```

Replication modes include:

- **Synchronous replication:** The primary waits for standby acknowledgment before committing, prioritizing durability.
- **Asynchronous replication:** The primary commits without waiting, prioritizing lower latency.
- **Cascaded standby:** A standby receives replication from another standby, reducing load on the primary.

If the primary fails, the HA framework can promote a standby to primary. openGauss documentation describes recovery and promotion designed to restore service within about 10 seconds.

### 5. Performance Design

openGauss is optimized for modern multi-core servers.

Key techniques include:

- **Multi-core concurrency control:** Reduces contention as CPU core count increases.
- **NUMA-aware structures:** Places frequently accessed data and structures closer to the CPU sockets that use them.
- **SQL bypass fast engine:** Uses optimized paths for simple, high-frequency SQL patterns.
- **USTORE storage engine:** Targets update-heavy workloads where rows change frequently.
- **Kunpeng hardware optimization:** Tuned for ARM-based Kunpeng servers, while remaining usable in broader Linux environments.

## Security Model

openGauss provides defense in depth:

| Control | Purpose |
|---|---|
| Authentication | Verifies users and clients before access |
| Role-based access control | Limits what each user or role can do |
| Encryption in transit | Protects client-database and replication traffic |
| Encryption at rest | Protects stored data from unauthorized access |
| Fully encrypted computation | Supports processing over encrypted data in suitable scenarios |
| Dynamic data masking | Hides sensitive values such as phone numbers or ID numbers from unauthorized users |
| Database audit | Records security-relevant and operational activity |
| Data page CRC | Detects corrupted data pages |

For regulated industries, the important point is that security is not only “encrypt the disk.” openGauss includes identity, authorization, audit, masking, and integrity controls as part of the database platform.

## AI-Native Operations

openGauss includes operational intelligence features:

- **AI parameter tuning:** Recommends database configuration parameters based on workload behavior.
- **Index recommendation:** Suggests indexes that may improve query performance.
- **Slow SQL diagnosis:** Identifies expensive or problematic queries.
- **Self-monitoring views:** Exposes runtime metrics for capacity, sessions, locks, cache, and query behavior.
- **SQL time forecasting:** Uses learned behavior to estimate query execution time.

For SRE and platform teams, this reduces time spent manually correlating slow queries, missing indexes, memory settings, and connection behavior.

## Deployment Models

| Model | Description | Best For |
|---|---|---|
| Standalone | One database instance | Development, testing, low-risk workloads |
| Primary-standby HA | One primary plus one or more standbys | Production transactional systems |
| Multi-standby HA | Primary plus up to four standbys | Read scaling, stronger availability posture |
| Cascaded standby | Standby replicates from another standby | Large replication topologies or network-constrained environments |

A standalone deployment can host multiple instances on one host, but it is not recommended for data-security-sensitive production use because the host becomes a single failure domain.

## Real-World Use Cases

### Financial Services

A payment platform can use openGauss as the transactional system of record for accounts, transactions, balances, and reconciliation records. Synchronous replication and fast failover help protect against data loss and service interruption.

### E-Commerce

Order management, inventory, pricing, customer accounts, and promotional systems benefit from ACID transactions. During sales events, high concurrency and efficient indexing matter more than raw storage capacity.

### Telecom and IoT

Device registries, subscriber profiles, alarms, network inventory, and event metadata can be stored relationally. openGauss can serve as the operational database behind data pipelines that ingest telemetry and feed analytics systems.

### Government and Regulated Enterprises

Audit trails, dynamic masking, access control, encryption, and support for Chinese cryptographic algorithms such as SM3 and SM4 make it relevant where data sovereignty and compliance controls are important.

### Cloud-Native Platforms

openGauss can run in containers or virtual machines and be managed with Kubernetes operators, Terraform, Prometheus exporters, and GitOps workflows. It fits a cloud-agnostic architecture where the database is deployed on any supported Linux infrastructure.

## When to Choose openGauss

Choose openGauss when you need:

- A production-grade open-source relational database.
- Strong HA and fast failover.
- High concurrency on multi-core hardware.
- Built-in database security and audit capabilities.
- AI-assisted tuning and operational diagnostics.
- An alternative to commercial databases or a self-managed PostgreSQL-compatible-style relational platform.

Be more cautious when:

- Your workload is primarily document-oriented, graph-oriented, or wide-column analytical.
- You require a very large managed-database ecosystem with broad third-party tooling.
- Your team has no capacity to operate database HA, backups, upgrades, and security patching.

## Hands-On Tutorial

This tutorial runs a single openGauss instance locally using Docker, creates a database and table, inserts data, queries it, and tests basic transactional behavior.

### Prerequisites

Install:

- Docker
- Docker Compose
- A terminal
- Basic SQL familiarity

### Step 1: Create a Project Directory

```bash
mkdir opengauss-lab
cd opengauss-lab
```

### Step 2: Create a Docker Compose File

Create `docker-compose.yml`:

```yaml
services:
  opengauss:
    image: opengauss/opengauss:latest
    container_name: opengauss-lab
    environment:
      GS_PASSWORD: "OpenGauss@2026"
    ports:
      - "5432:5432"
    volumes:
      - opengauss_data:/var/lib/opengauss
    restart: unless-stopped

volumes:
  opengauss_data:
```

The password must meet openGauss complexity requirements. The example uses uppercase, lowercase, numbers, and a special character.

### Step 3: Start the Database

```bash
docker compose up -d
```

Check that it is running:

```bash
docker ps
docker logs -f opengauss-lab
```

Wait until the logs indicate that the database is ready.

### Step 4: Connect to openGauss

Enter the container:

```bash
docker exec -it opengauss-lab bash
```

Connect using the built-in SQL client:

```bash
gsql -d postgres -U gaussdb -W "OpenGauss@2026" -p 5432
```

You should see a SQL prompt similar to:

```text
postgres=#
```

### Step 5: Create a Demo Database

```sql
CREATE DATABASE shop;
```

Exit the current session:

```sql
\q
```

Connect to the new database:

```bash
gsql -d shop -U gaussdb -W "OpenGauss@2026" -p 5432
```

### Step 6: Create Tables

```sql
CREATE TABLE customers (
    customer_id SERIAL PRIMARY KEY,
    full_name VARCHAR(120) NOT NULL,
    email VARCHAR(180) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE accounts (
    account_id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
    balance NUMERIC(18,2) NOT NULL DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE transactions (
    transaction_id SERIAL PRIMARY KEY,
    from_account INTEGER REFERENCES accounts(account_id),
    to_account INTEGER REFERENCES accounts(account_id),
    amount NUMERIC(18,2) NOT NULL CHECK (amount > 0),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Step 7: Insert Sample Data

```sql
INSERT INTO customers (full_name, email)
VALUES
  ('Asha Rao', 'asha@example.com'),
  ('Ravi Kumar', 'ravi@example.com');

INSERT INTO accounts (customer_id, balance)
VALUES
  (1, 1000.00),
  (2, 500.00);
```

Verify:

```sql
SELECT * FROM customers;
SELECT * FROM accounts;
```

### Step 8: Run an Atomic Money Transfer

```sql
BEGIN;

UPDATE accounts
SET balance = balance - 200,
    updated_at = CURRENT_TIMESTAMP
WHERE account_id = 1;

UPDATE accounts
SET balance = balance + 200,
    updated_at = CURRENT_TIMESTAMP
WHERE account_id = 2;

INSERT INTO transactions (from_account, to_account, amount)
VALUES (1, 2, 200.00);

COMMIT;
```

Check the result:

```sql
SELECT account_id, balance
FROM accounts
ORDER BY account_id;
```

Expected result:

```text
 account_id | balance
------------+----------
          1 |  800.00
          2 |  700.00
```

### Step 9: Test Rollback

```sql
BEGIN;

UPDATE accounts
SET balance = balance - 10000
WHERE account_id = 1;

-- Intentionally cancel the transaction
ROLLBACK;
```

Verify that the balance is unchanged:

```sql
SELECT account_id, balance
FROM accounts
WHERE account_id = 1;
```

### Step 10: Create an Index

```sql
CREATE INDEX idx_transactions_from_account
ON transactions (from_account);

CREATE INDEX idx_transactions_created_at
ON transactions (created_at);
```

Run an indexed query:

```sql
SELECT *
FROM transactions
WHERE from_account = 1
ORDER BY created_at DESC;
```

Inspect the query plan:

```sql
EXPLAIN ANALYZE
SELECT *
FROM transactions
WHERE from_account = 1;
```

Look for an index scan in the output. With very small data volumes, the optimizer may still choose a sequential scan, which is normal.

### Step 11: Create a Read-Only User

```sql
CREATE USER analytics_user WITH PASSWORD 'Analytics@2026';

GRANT CONNECT ON DATABASE shop TO analytics_user;

GRANT USAGE ON SCHEMA public TO analytics_user;

GRANT SELECT ON customers, accounts, transactions TO analytics_user;
```

Exit and test the restricted user:

```bash
\q
gsql -d shop -U analytics_user -W "Analytics@2026" -p 5432
```

Try reading:

```sql
SELECT COUNT(*) FROM transactions;
```

Try writing:

```sql
INSERT INTO customers (full_name, email)
VALUES ('Test User', 'test@example.com');
```

The insert should fail because `analytics_user` has only `SELECT` permission.

### Step 12: Check Database Metadata

```sql
\dt
\d+ accounts
SELECT version();
```

Useful commands:

```sql
SELECT datname FROM pg_database;

SELECT relname, n_live_tup
FROM pg_stat_user_tables;

SELECT pid, usename, datname, state, query
FROM pg_stat_activity;
```

### Step 13: Back Up the Database

From inside the container:

```bash
exit
```

Create a logical backup:

```bash
docker exec -it opengauss-lab bash -c \
  "gs_dump -U gaussdb -W 'OpenGauss@2026' -d shop -F c -f /tmp/shop.dump"
```

Copy it to the host:

```bash
docker cp opengauss-lab:/tmp/shop.dump ./shop.dump
```

### Step 14: Clean Up

Stop and remove the lab:

```bash
docker compose down
```

To remove persistent data as well:

```bash
docker compose down -v
```

## Production Checklist

- Deploy at least one primary and one standby; do not use a single node for critical data.
- Use synchronous replication when losing a recently committed transaction is unacceptable.
- Use asynchronous replication when write latency is more important than zero-replication-lag durability.
- Automate backups with full, incremental, and WAL archiving strategies.
- Test failover regularly; HA that has never been tested is not HA.
- Encrypt client, replication, and backup traffic.
- Use least-privilege database roles; avoid application access through superuser accounts.
- Enable audit logging and ship logs to a centralized security platform.
- Monitor connections, replication lag, WAL growth, lock waits, cache hit ratio, disk latency, and slow queries.
- Keep database version upgrades, extensions, and security patches in a controlled release process.

## Key Technical Takeaways

- openGauss is a relational, SQL-based, open-source database built for enterprise transactional workloads.
- Its HA design uses primary/standby replication, WAL streaming, failure detection, and standby promotion.
- Its performance design targets multi-core and NUMA hardware, making it particularly relevant for dense server deployments.
- Its security model spans authentication, authorization, encryption, masking, auditing, and data-page integrity.
- Its AI-assisted operations reduce manual tuning and troubleshooting.
- For a cloud-agnostic platform, openGauss can be deployed on VMs, bare metal, or Kubernetes, with observability and infrastructure managed through open-source tooling.