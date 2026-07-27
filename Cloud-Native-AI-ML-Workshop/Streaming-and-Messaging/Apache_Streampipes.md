## Apache StreamPipes  

Apache StreamPipes is an **open-source platform for industrial data**. 

It connects to machines and software systems, processes data as it arrives, keeps selected history, and turns it into charts and dashboards. It runs on your own servers using Docker Compose or Kubernetes.

Think of it as a **factory data platform**. Normally, connecting a machine, processing its data, storing it, and charting it requires four separate tools. StreamPipes combines them into one platform: **Connect, Pipelines, Datasets, Charts, Dashboards, and Assets**.

It is not a commercial SaaS company. It is an Apache Software Foundation project, so the platform is free, open source, and self-hosted. Companies around the project can provide paid support or training if needed.

## What it offers

| Module | What it does | Simple example |
|---|---|---|
| **Connect** | Adapters connect to machines, brokers, and software. It supports 147 integrations, including OPC UA, Siemens S7, Modbus, MQTT, Kafka, Pulsar, NATS, InfluxDB, IoTDB, PostgreSQL, Slack, ROS, and Milvus. | Read temperature and vibration from a PLC using OPC UA. |
| **Pipelines** | Filter, enrich, detect conditions in, and route live data through a visual editor. Pipeline elements are checked against the stream schema before saving. | “If vibration stays above a limit for five minutes, send an alert.” |
| **Datasets** | Store selected streams as history, inspect them, import CSVs, set retention rules, and export data as CSV, JSON, or Excel. | Keep 90 days of machine data and export it for analysis. |
| **Charts and dashboards** | Query a dataset, choose a chart type, and combine several charts into a dashboard for a team. | Build an uptime, fault, and temperature dashboard for operators. |
| **Assets and sites** | Model plants, lines, and machines, then attach the streams, datasets, pipelines, and dashboards that belong to each. | Attach “Line 3 oven” data and alerts to the “Plant A / Line 3” asset. |
| **Developer tools** | Python and Java clients, REST APIs, event-driven Functions, and an SDK for custom adapters, processors, and sinks. | Run a Python anomaly-detection model on a live stream. |
| **Enterprise controls** | SSO, roles, groups, permissions, audit logs, retention/archival, encrypted secrets, certificate management, Prometheus metrics, and Helm deployment. | Control who can edit pipelines and track security changes. |

## How it works

1. **Machines and systems produce data** through OPC UA, S7, MQTT, Kafka, files, or HTTP.
2. **An adapter turns raw signals into a typed stream.** You can inspect incoming events before saving and fix field names, data types, and units once.
3. **A pipeline processes the stream as events arrive.** It can clean values, filter noise, calculate aggregates, detect thresholds, enrich events, or route them.
4. **A sink sends results onward** to Kafka, a time-series database, another system, or a notification channel.
5. **A dataset keeps history** for later inspection, export, and analysis.
6. **Charts and dashboards show the result** to operators and teams.

### Architecture in plain language

StreamPipes has several services around a message broker:

- **Interfaces:** Web UI for daily work, plus Java and Python clients and a REST API for automation.
- **Core:** Tracks adapters, pipelines, datasets, assets, and users; monitors what is running and serves the UI.
- **Messaging layer:** NATS or Kafka moves events between adapters, pipelines, and sinks. Components do not talk point-to-point, so each can run where it makes sense.
- **Extension services:** Adapters, processors, sinks, and Functions are separate services. You can write your own with the SDK and install them while the platform is running.
- **Time-series storage:** Datasets go into a time-series database. Retention rules decide how long data stays, and it can be exported as CSV, JSON, or Excel.

### Edge-to-core deployment

Each plant can run a small extension service next to its PLCs and machines. That service connects **outbound** to the broker, so no inbound ports need to be opened into the OT network. The core, storage, and heavier processing stay in the data center or cloud.

This means you can process data close to the machines while keeping management and storage centralized.

## Key business insights

- **It reduces tool sprawl.** Connecting a machine, processing its data, storing it, and charting it usually means four tools; StreamPipes makes them modules of one platform.
- **It speeds up industrial data projects.** Visual pipelines and dashboards let operations and reliability teams build monitoring without waiting for a custom software project.
- **It is vendor-neutral and self-hosted.** Everything runs on infrastructure you control, with no usage metering, no proprietary format, and exportable datasets.
- **It supports gradual adoption.** One Docker Compose host is enough to try it; the same services can scale on Kubernetes later without redesigning existing pipelines.
- **It is enterprise-ready without an enterprise edition.** SSO, custom roles, user groups, resource permissions, audit logs, retention/archival, encrypted secrets, and certificate management are included.
- **It supports a plant-by-plant rollout.** Each plant can run its own edge extension service while sharing a central platform, broker, and storage layer.

## Key technical insights

- **Schema-first streaming:** A stream is defined once with field types, units, and metadata. Pipelines and dashboards build on that definition, reducing malformed-data and integration errors.
- **Broker-centric event flow:** NATS or Kafka decouples adapters, processors, and sinks, making the architecture modular and easier to distribute.
- **Edge-native extensibility:** Custom adapters and Functions can run next to machines, while central services handle management, storage, and heavier processing.
- **OT-safe connectivity:** Edge services use outbound-only communication, optionally over TLS with token authentication, which is valuable in restricted plant networks.
- **Live extension model:** New adapters, processors, sinks, and Functions can be installed while the platform is running, without modifying the core.
- **Practical AI/ML integration:** Load a dataset into pandas, train a model in a notebook, deploy it as a Python Function, and receive predictions as another live stream.

## Where you can use it

### Manufacturing and industrial operations

- **Condition monitoring with OPC UA:** Connect machines, watch the values that matter, and get a message when a trend or threshold needs attention.
- **Predictive maintenance:** Detect anomalies in machine behavior and identify degradation before unplanned failures.
- **Machine state tracking:** Turn running, blocked, and fault signals into states, measure how long each lasts, and see where time went by line and shift.
- **Quality control:** Attach control and warning limits to measurements, alert when values break limits, and spot slow drift before a part goes out of spec.
- **Alarm and event management:** Receive OPC UA alarms and events, measure how long states last, and send a message to the right channel when something changes.
- **WinCC alarm analysis:** Read Siemens WinCC alarm archives, turn them into a stream, and find which alarms keep coming back and how long they stay active.

### Data engineering and platform engineering

- **PLC data to Kafka and InfluxDB:** Read Siemens S7 and Modbus controllers, clean units and field names, and forward events to systems IT already runs.
- **MQTT and a unified namespace:** Subscribe to existing MQTT topics, turn raw payloads into typed streams with context, and publish results back into the namespace.
- **Edge data reduction:** Clean raw payloads with a script at the adapter, keep only the changes that matter, compress the rest, and send a fraction of the original volume to the cloud.
- **Streaming ETL:** Use visual pipelines for standard transformations and custom Functions for complex business logic.
- **Operational analytics and ML:** Store curated datasets, analyze them in notebooks, and deploy models against live streams.

## Best fit

StreamPipes is a strong fit for organizations that need a **self-hosted, open-source, cloud-agnostic industrial streaming platform** for machine telemetry, edge processing, event detection, historical storage, and operational dashboards.

It is especially useful when factory systems use OPC UA, Siemens S7, Modbus, MQTT, or Kafka and the team wants to move from disconnected machine data to a unified, event-driven industrial data platform. It is not intended to replace an ERP, a full MES, or hard real-time control-loop systems.