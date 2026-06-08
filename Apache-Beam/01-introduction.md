### Apache Beam

Apache Beam is an open-source, unified programming model and set of SDKs used to define parallel data processing pipelines for both batch (bounded) and streaming (unbounded) datasets.

Its name originates from combining **Batch + strEAM.** Rather than executing the data processing jobs itself, Beam acts as an abstraction layer: you write your processing logic once in your language of choice, and Beam translates and runs that logic on distributed processing engines (such as Apache Flink, Apache Spark, or Google Cloud Dataflow).