# LanceDB Deep Dive

LanceDB is an **AI-native multimodal lakehouse**. It combines the roles of a data lake, feature store, vector database, search index, and ML training-data store into one versioned table layer built on the open-source **Lance** format.

In simple terms: instead of keeping raw images/videos in object storage, metadata in a database, embeddings in a vector DB, features in a feature store, and training shards in Parquet/WebDataset, LanceDB lets you keep them in **one table** and query, curate, evolve, and train from that table. 