# smolagents: Deep Dive

`smolagents` is Hugging Face’s lightweight, open-source Python framework for building **LLM-powered agents** that can reason, call tools, execute code, and iterate toward a goal. Its core idea is simple: an LLM is the “brain,” while tools, memory, and a controlled execution loop give it the ability to act in the real world.

## What it is

`smolagents` is designed to make agents easy to build in a few lines of Python. It supports both **code-writing agents** and conventional **JSON tool-calling agents**, and it is model-agnostic: you can use Hugging Face Inference Providers, OpenAI, Anthropic, LiteLLM, Transformers, Ollama, Azure OpenAI, Amazon Bedrock, or MLX-backed local models.

The library deliberately keeps its abstractions small. The agent logic is compact, while integrations and security controls provide the production-facing capabilities.