# LanceDB Deep Dive

LanceDB is an **AI-native multimodal lakehouse**. It combines the roles of a data lake, feature store, vector database, search index, and ML training-data store into one versioned table layer built on the open-source **Lance** format.

In simple terms: instead of keeping raw images/videos in object storage, metadata in a database, embeddings in a vector DB, features in a feature store, and training shards in Parquet/WebDataset, LanceDB lets you keep them in **one table** and query, curate, evolve, and train from that table.

## What It Is

LanceDB is both:

- **A database/service layer**: APIs for creating tables, inserting data, querying, filtering, updating, versioning, and searching.
- **A storage format ecosystem**: the Lance file/table format, designed for object storage and AI workloads.

Its core premise is that AI teams do not only run analytical scans like a traditional lakehouse. They repeatedly perform:

- Fast random access to individual records.
- Vector similarity search.
- Full-text and hybrid search.
- Metadata filtering.
- Feature backfills.
- Dataset branching and versioning.
- Large-scale training-data shuffles and streaming to GPUs.

LanceDB is designed around those access patterns rather than treating them as afterthoughts.

