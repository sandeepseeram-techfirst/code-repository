# Dgraph Deep Dive: A Distributed Graph Database

Dgraph is an open-source, distributed **property graph database** designed for highly connected, real-time workloads. Its core value is that it lets you model entities and their relationships natively, query them with GraphQL or DQL, and scale horizontally across a cluster without application-level sharding.

## What It Is

Dgraph stores data as **nodes** (entities such as users, products, or accounts), **predicates/properties** (attributes such as `name`, `age`, or `email`), and **edges** (relationships such as `friend`, `purchased`, or `located_in`). Each node has a unique internal identifier called a UID.  

You can ingest data as RDF triples or JSON, and both are stored internally as graph structures. RDF is useful for semantic/knowledge-graph workloads, while JSON is more natural for application developers.  

Example RDF:

```rdf
<0x1> <name> "Alice" .
<0x1> <age> "30" .
<0x1> <friend> <0x2> .
```

Equivalent JSON:

```json
{
  "uid": "0x1",
  "name": "Alice",
  "age": 30,
  "friend": {
    "uid": "0x2"
  }
}
```

## Architecture

Dgraph is built as a distributed system from the ground up. Data is automatically sharded across server groups, and queries are routed to the relevant shards in parallel, with results aggregated before being returned to the client.  

### Core architectural ideas

- **Graph-native storage:** Data is represented as nodes, predicates, and edges rather than rows and foreign keys.
- **Automatic sharding:** The graph is partitioned across multiple Dgraph server groups, enabling horizontal scale for very large graphs.
- **Parallel query execution:** Multi-hop traversals can be distributed across relevant shards, reducing latency for connected-data queries.
- **Replication and failover:** Each shard can have replicas, so the cluster remains available if individual nodes fail.
- **ACID transactions:** Mutations can span multiple operations and are handled with transactional consistency across the distributed cluster.
- **Schema-aware indexes:** Although Dgraph can operate schema-less, defining predicates, types, and indexes enables efficient filtering, sorting, and graph functions.  

### Simplified request flow

```text
Client
  |
  | GraphQL query / DQL query / mutation
  v
Dgraph GraphQL layer or Dgraph Alpha
  |
  | Parse, plan, and route query
  v
Relevant server groups / shards
  |
  | Parallel local graph traversal
  v
Aggregated result returned to client
```

The application does not need to know which shard contains a particular node or edge; Dgraph handles distribution, routing, and aggregation transparently.  

## GraphQL and DQL

Dgraph provides two primary query interfaces.

| Interface | Best for | How it works |
|---|---|---|
| **GraphQL API** | Product teams and application backends | Define a GraphQL schema; Dgraph generates queries, mutations, and optionally subscriptions automatically.    |
| **DQL** | Graph engineers and advanced queries | Write graph-native queries with traversals, filters, recursion, aggregation, pagination, and variables.   |

### GraphQL-first development

With Dgraph’s GraphQL API, a schema definition can generate a complete API and graph backend without manually writing resolvers for standard CRUD operations. Dgraph also supports custom resolvers, Lambda resolvers, GraphQL subscriptions through `@withSubscription`, and Apollo Federation integration.  

Example GraphQL schema concept:

```graphql
type Person {
  id: ID!
  name: String! @search(by: [hash])
  age: Int
  friends: [Person] @dgraph(pred: "friend")
}
```

From this schema, Dgraph can expose operations such as:

```graphql
query {
  queryPerson(filter: { name: { eq: "Alice" } }) {
    name
    age
    friends {
      name
    }
  }
}
```

### DQL traversal example

```graphql
{
  person(func: eq(name, "Alice")) {
    name
    age
    friend {
      name
      friend {
        name
      }
    }
  }
}
```

This starts at Alice, follows the `friend` edge to her direct friends, then follows another `friend` edge to friends-of-friends, returning the nested graph in one request.  

## How Mutations Work

In Dgraph, writes are called **mutations**. A mutation can create nodes, update properties, add or remove edges, and delete nodes. Multiple operations can be batched into one transaction.  

Example JSON mutation:

```json
{
  "set": [
    {
      "uid": "_:alice",
      "dgraph.type": "Person",
      "name": "Alice",
      "age": 30
    },
    {
      "uid": "_:bob",
      "dgraph.type": "Person",
      "name": "Bob",
      "age": 32
    },
    {
      "uid": "_:alice",
      "friend": {
        "uid": "_:bob"
      }
    }
  ]
}
```

This creates two `Person` nodes and connects Alice to Bob through a `friend` edge.

## Schema and Indexing

Dgraph can accept arbitrary predicates without a predefined schema, but production systems should define one. A schema declares predicate types and indexes, which are required for many query functions such as equality filters, full-text search, regular expressions, sorting, and geographic queries.  

Example schema:

```graphql
name: string @index(hash) .
age: int .
email: string @index(hash) @upsert .
friend: [uid] @reverse .
```

Key schema concepts:

- **Predicates:** Named properties or edges, such as `name`, `age`, or `friend`.
- **Types:** Optional named node types, such as `Person`, `Product`, or `Organization`.
- **Indexes:** Enable efficient lookup and filtering.
- **Reverse edges:** Allow traversal in the opposite direction, such as finding everyone who follows a user.
- **Upsert:** Helps enforce uniqueness or conditional writes for fields such as email or external IDs.

## Real Problems It Solves

Dgraph is most valuable when relationships are central to the application and relational joins or document-store aggregations become complex.

### 1. Social networks and identity graphs

Model users, follows, friendships, blocks, groups, posts, likes, and comments. Queries such as “find friends of friends who like similar content” are natural multi-hop graph traversals rather than expensive multi-table joins.

### 2. Recommendations

Connect users, products, categories, purchases, ratings, and behavioral events. You can traverse signals such as:

```text
User -> purchased -> Product -> similar_to -> Product
User -> follows -> User -> purchased -> Product
```

This supports collaborative-filtering-style recommendations and personalized feeds.

### 3. Knowledge graphs

Represent entities, concepts, documents, and relationships in RDF-like triples. This is useful for enterprise search, semantic search, entity resolution, compliance analysis, and AI retrieval systems.

### 4. Fraud and risk analysis

Connect accounts, devices, IP addresses, transactions, merchants, and identities. Graph queries can expose patterns such as shared devices, circular fund flows, synthetic identities, or unusually connected accounts.

### 5. Access control and authorization

Represent users, roles, permissions, resources, organizations, and ownership relationships. Dgraph’s enterprise ACL capability also supports predicate-level permissions for multi-tenant environments.  

### 6. IT, cloud, and security asset graphs

Model Kubernetes clusters, workloads, services, identities, vulnerabilities, network paths, and cloud resources. This enables questions such as:

```text
Which internet-exposed workload can reach a database containing sensitive data?
Which vulnerable pod is reachable from a compromised service account?
```

### 7. Supply chain and logistics

Connect suppliers, parts, factories, shipments, routes, and customers. Graph traversal helps identify dependency risk, alternate sourcing paths, and downstream impact of disruptions.

## Why It Fits Cloud-Native Systems

For an SRE or platform-engineering perspective, Dgraph is attractive because it separates the data model from infrastructure scaling concerns:

- **Stateless application tier:** Your services call Dgraph through GraphQL or DQL.
- **Stateful database tier:** Dgraph manages sharding, replication, and failover.
- **Horizontal scale:** Add capacity by scaling the cluster rather than redesigning application data access.
- **Operability:** It supports backups, restore, metrics, Prometheus/Grafana integration, encryption, and ACLs.  
- **API-first integration:** The generated GraphQL API can serve as a backend-for-frontend or domain data API, reducing boilerplate resolver code.  

A typical production topology would run Dgraph in Kubernetes with persistent volumes, pod anti-affinity, resource requests/limits, readiness/liveness probes, network policies, TLS, backup jobs, and Prometheus scraping.

## Hands-On Tutorial

This tutorial runs a local Dgraph instance with Docker, defines a small social graph, inserts data, and queries it.

### Prerequisites

Install:

- Docker
- `curl`
- A GraphQL client such as Altair, Insomnia, Postman, or `curl`

### Step 1: Start Dgraph

Create a directory for Dgraph data:

```bash
mkdir -p ~/dgraph-demo/data
cd ~/dgraph-demo
```

Start a standalone Dgraph Zero and Alpha:

```bash
docker run --rm -it \
  --name dgraph \
  -p 8080:8080 \
  -p 9080:9080 \
  -p 8000:8000 \
  -v "$PWD/data:/dgraph" \
  dgraph/dgraph:latest \
  dgraph all --my=127.0.0.1:7180
```

Ports:

| Port | Purpose |
|---|---|
| `8080` | Dgraph Alpha HTTP and GraphQL endpoint |
| `9080` | Dgraph Alpha gRPC endpoint |
| `8000` | Ratel UI |

Open Ratel at:

```text
http://localhost:8000
```

### Step 2: Define a GraphQL Schema

Create a file named `schema.graphql`:

```graphql
type Person {
  id: ID!
  name: String! @search(by: [hash])
  age: Int
  email: String @search(by: [hash]) @id
  friends: [Person]
}
```

Apply it:

```bash
curl -X POST \
  http://localhost:8080/admin/schema \
  --data-binary '@schema.graphql'
```

Dgraph generates GraphQL queries and mutations from this schema, including `addPerson`, `updatePerson`, `deletePerson`, and `queryPerson`.  

### Step 3: Add People

Create `add-people.json`:

```json
{
  "query": "mutation AddPeople($input: [AddPersonInput!]!) { addPerson(input: $input) { person { id name email } } }",
  "variables": {
    "input": [
      {
        "name": "Alice",
        "age": 30,
        "email": "alice@example.com"
      },
      {
        "name": "Bob",
        "age": 32,
        "email": "bob@example.com"
      },
      {
        "name": "Carol",
        "age": 28,
        "email": "carol@example.com"
      }
    ]
  }
}
```

Send it:

```bash
curl -X POST \
  http://localhost:8080/graphql \
  -H 'Content-Type: application/json' \
  --data-binary '@add-people.json'
```

You should receive generated UIDs for Alice, Bob, and Carol.

### Step 4: Create Relationships

Create `add-friendships.json`:

```json
{
  "query": "mutation AddFriendships($input: [AddPersonInput!]!) { addPerson(input: $input, upsert: true) { person { id name friends { name } } } }",
  "variables": {
    "input": [
      {
        "email": "alice@example.com",
        "friends": [
          { "email": "bob@example.com" },
          { "email": "carol@example.com" }
        ]
      },
      {
        "email": "bob@example.com",
        "friends": [
          { "email": "carol@example.com" }
        ]
      }
    ]
  }
}
```

Send it:

```bash
curl -X POST \
  http://localhost:8080/graphql \
  -H 'Content-Type: application/json' \
  --data-binary '@add-friendships.json'
```

The graph now looks like this:

```text
Alice ──friend──> Bob
Alice ──friend──> Carol
Bob   ──friend──> Carol
```

### Step 5: Query Direct Friends

Create `query-friends.json`:

```json
{
  "query": "query { queryPerson(filter: { email: { eq: \"alice@example.com\" } }) { name age friends { name email } } }"
}
```

Run it:

```bash
curl -X POST \
  http://localhost:8080/graphql \
  -H 'Content-Type: application/json' \
  --data-binary '@query-friends.json'
```

Expected logical result:

```json
{
  "data": {
    "queryPerson": [
      {
        "name": "Alice",
        "age": 30,
        "friends": [
          { "name": "Bob", "email": "bob@example.com" },
          { "name": "Carol", "email": "carol@example.com" }
        ]
      }
    ]
  }
}
```

### Step 6: Query Two-Hop Relationships

Create `query-friends-of-friends.json`:

```json
{
  "query": "query { queryPerson(filter: { email: { eq: \"alice@example.com\" } }) { name friends { name friends { name } } } }"
}
```

Run it:

```bash
curl -X POST \
  http://localhost:8080/graphql \
  -H 'Content-Type: application/json' \
  --data-binary '@query-friends-of-friends.json'
```

This returns Alice’s friends and each friend’s friends, demonstrating a two-hop graph traversal in one request.

### Step 7: Use DQL Directly

In Ratel, open the DQL console and run:

```graphql
{
  person(func: eq(name, "Alice")) {
    name
    age
    friend {
      name
      friend {
        name
      }
    }
  }
}
```

This shows DQL’s nested traversal style, which is especially useful for deeper graph exploration, filtering, aggregation, and recursive queries.  

### Step 8: Clean Up

Stop and remove the container:

```bash
docker stop dgraph
```

Because the data directory is mounted locally, it remains in `~/dgraph-demo/data` unless you delete it.

## When to Choose Dgraph

Choose Dgraph when:

- Relationships are first-class domain data.
- You need multi-hop traversals with low latency.
- You want a GraphQL API generated directly from the data model.
- Your graph may grow to billions of nodes or edges.
- You need horizontal scalability and high availability.
- You are building recommendation, identity, fraud, knowledge-graph, authorization, or asset-inventory systems.  

Consider alternatives when:

- Your workload is primarily transactional and relational, with few complex joins.
- You need mature analytical SQL, warehouse semantics, or BI tooling.
- Your graph is small enough that PostgreSQL with recursive CTEs is simpler to operate.
- You need specialized vector search, streaming, or time-series capabilities as the primary workload.

## Key Takeaways

- Dgraph treats relationships as native data, not as joins across separate tables.
- Its distributed design automatically shards and queries the graph in parallel.
- GraphQL provides an application-friendly API, while DQL provides deeper graph-native control.
- It is strongest for real-time connected-data use cases such as recommendations, fraud detection, identity graphs, knowledge graphs, and authorization.
- For production, invest early in schema design, indexes, reverse edges, backup strategy, observability, TLS, and access control.  