# Chroma: Deep Dive, Simplified

Chroma is an **open-source AI-native search database**. It stores documents, metadata, embeddings, and indexes, then lets applications retrieve the most relevant information using semantic vector search, keyword/full-text search, regex search, and metadata filtering.

In one sentence: **Chroma turns unstructured content—text, code, images, audio, or other AI artifacts—into searchable context for LLMs, agents, and retrieval applications.**

---

## 1. What Problem Does Chroma Solve?

LLMs are powerful but have two major limitations:

1. **They do not inherently know your private or recent data.**
2. **Their context window is finite**, so you cannot paste an entire knowledge base, repository, ticket history, or document corpus into every prompt.

Chroma solves the retrieval side of this problem:

- Store millions of documents and their embeddings.
- Search them by *meaning*, not just exact keyword match.
- Filter results using structured metadata.
- Return only the most relevant chunks to an LLM.
- Combine semantic similarity with lexical precision.
- Run locally for development or self-host/cloud for production.

This is the core pattern behind **RAG (Retrieval-Augmented Generation)**, agentic search, enterprise knowledge assistants, code search, and semantic recommendation systems.

---

## 2. Simplified Mental Model

Think of Chroma as a specialized database with four core concepts:

| Concept | What it means | Example |
|---|---|---|
| **Database** | The top-level deployment or namespace | A production knowledge-base database |
| **Collection** | A logical index/table for related records | `support_docs`, `product_manuals`, `code_chunks` |
| **Record** | A document, embedding, metadata, and unique ID | A support article with `team=support`, `product=billing` |
| **Query** | A search request against embeddings, text, metadata, or a combination | “How do I reset my billing API key?” |

