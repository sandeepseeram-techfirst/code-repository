The **thundering herd problem** occurs when many clients simultaneously request the same resource or react to the same event, overwhelming a shared component such as a cache, database, upstream service, or message consumer.

## How it happens

A common case is **cache expiration**:

1. A frequently used cache key expires.
2. Thousands of concurrent requests miss the cache.
3. All of them query the database or origin service for the same value.
4. The database is flooded with duplicate work, causing latency spikes, timeouts, or cascading failures.

Other triggers include:

- A service restart causing all clients to reconnect at once.
- A scheduled job releasing many tasks simultaneously.
- A broadcast event waking many idle consumers or workers.
- A DNS or configuration change causing mass re-resolution or reconnects.

## Mitigation strategies

- **Request coalescing / single-flight:** allow only one request to populate the cache; other callers wait for and reuse that result.
- **Distributed lock:** acquire a lock around cache repopulation so only one instance rebuilds the value.
- **Stale-while-revalidate:** serve the previous cached value immediately while asynchronously refreshing it.
- **Jittered expiration:** add random TTL jitter so keys do not expire simultaneously.
- **Early refresh:** refresh popular entries before their TTL expires.
- **Rate limiting and backpressure:** cap concurrent origin requests and queue or reject excess work safely.
- **Exponential backoff with jitter:** prevent clients from retrying in synchronized waves after failures.
- **Sharding and load spreading:** distribute keys, consumers, or connections so no single component receives the full burst.

## Practical example

For a product page cache, instead of all 10,000 requests hitting PostgreSQL after a cache miss, one request rebuilds the entry while the others wait briefly or receive the stale cached value. This turns a potentially damaging database stampede into one origin query.

## Key insight

The root issue is usually **correlated work**: many clients doing the same expensive operation at the same time. The fix is to make that work happen once, spread it over time, or absorb it safely with caching, locking, queues, and backpressure.