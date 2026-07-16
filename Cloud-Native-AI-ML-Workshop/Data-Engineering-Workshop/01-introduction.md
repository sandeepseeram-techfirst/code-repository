## Data Engineering Fundamentals 

### What Is Data Engineering?

Data engineering is about building systems that take raw data from various sources, transform it into meaningful information, and make it accessible for others to use.

### Extract, Transform, Load (ETL): 
Data is extracted from source systems, transformed, and then loaded into analytical systems. This traditional approach
is ideal when data requires significant cleansing or transformation before analysis.

### Extract, Load, Transform (ELT): 
Data is extracted, loaded into the target system first, and then transformed. This modern approach leverages the processing power of analytical systems and works well with cloud data warehouses.

### Note
The Apache Software Foundation (ASF) has played a pivotal role in shaping modern data engineering. The ASF now hosts
and maintains many of the most critical tools and frameworks that form the backbone of modern data infrastructure and processing pipelines. 

**Apache Spark** and **Kafka** have become fundamental technologies in data engineering. 
Spark transformed big data processing through its unified analytics engine, while Kafka established itself as the gold standard for distributed event streaming. 

**Apache Iceberg** has emerged as a key table format for managing large analytic datasets.

**NiFi** for data ingestion, **Flink** for stream processing, **Airflow** for workflow orchestration, and **Superset** for data
visualization – each serving a distinct role in the data engineering lifecycle.