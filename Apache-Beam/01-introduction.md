### Apache Beam

Apache Beam is an open-source, unified programming model and set of SDKs used to define parallel data processing pipelines for both batch (bounded) and streaming (unbounded) datasets.

Its name originates from combining **Batch + strEAM.** Rather than executing the data processing jobs itself, Beam acts as an abstraction layer: you write your processing logic once in your language of choice, and Beam translates and runs that logic on distributed processing engines (such as Apache Flink, Apache Spark, or Google Cloud Dataflow).

### Core Concepts: How Apache Beam Works

1. Pipeline: Encapsulates your entire data processing task from ingestion to output. It manages the user-constructed Directed Acyclic Graph (DAG) of transformations.

PCollection (Parallel Collection): Represents the distributed dataset that your pipeline operates on. It can be bounded (a fixed historical batch, like a CSV file) or unbounded (a continuous real-time stream, like a Kafka topic).

PTransform (Parallel Transform): An operation that takes one or more PCollections as input, applies computation (such as Map, Filter, GroupByKey, or custom ParDo functions), and produces new PCollections.

PipelineRunner: The adapter that converts your Beam pipeline into native code compatible with a distributed backend. Supported runners include:

Google Cloud Dataflow (fully managed cloud runner)

Apache Flink (popular for low-latency streaming)

Apache Spark (widely used in large on-prem/hybrid clusters)

Direct Runner (runs locally on your machine for testing and debugging)