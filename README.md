# Azure_AI_Agent_Backend


## Purpose
An RAG-based application designed for high-accuracy product queries with strict hallucination controls

## Main Techology 

Refined RAG Architecture & Workflow

1. Scalable Foundation and Async HandlingThe application is built on FastAPI and served via Uvicorn, optimized for high-concurrency environments. It utilizes the AsyncAzureOpenAI client to ensure that all network calls to Azure—both for generating embeddings and fetching chat completions—are non-blocking. This allows the server to handle multiple user requests simultaneously without waiting for the LLM to respond.

2. High-Performance Retrieval with HNSWProduct documentation is processed by splitting files into semantic chunks and storing them in a PostgreSQL database. To ensure "blazing fast" retrieval as data grows, a Hierarchical Navigable Small World (HNSW) index is applied to the vector column. Unlike standard indexes, HNSW builds a multi-layered graph that allows the system to find the most relevant product information in sub-millisecond time, trading a small amount of memory for significant gains in search speed and accuracy.

3. Consolidating the Retrieve ToolA custom Retrieve Tool acts as the bridge between the user's intent and the technical backend. This single tool call encapsulates two critical steps: first, it uses the Embedding Tool to convert the user's natural language question into a 1536-dimensional vector via text-embedding-3-small. Second, it immediately passes that vector to the Postgres Tool, which executes a pgvector similarity search using the HNSW index to pull the most contextually relevant text chunks.

4. Orchestration and Logging via Semantic KernelSemantic Kernel serves as the central brain, orchestrating the interaction between the LLM and the Retrieve Tool. It manages the flow of data and provides an observability layer for the entire process. By utilizing the kernel's ability to coordinate agents and tools, the system ensures that every prompt sent to the LLM is grounded in fact, significantly reducing the risk of hallucination while maintaining high reponse accuracy.

To ensure a production-ready interface, Pydantic is used to restructure and validate the final output format. Rather than returning unstructured text, the system maps the LLM's response into a strict schema, enforcing consistent data types for fields like answer content, file citations, and confidence scores.

5. To optimize operational efficiency, the application implements a PostgreSQL Response Caching layer using exact-match logic. When a query is submitted, the system checks for existing answers, but grants user agency: users can choose to retrieve a stored response or generate a fresh one.

Selecting a fresh response triggers a new Azure OpenAI call, which then updates the database for future reference. This "cache-first" approach significantly reduces latency and token consumption, preserving the API quota for unique queries while providing a cost-effective, tailored user experience.

## Test Results

1. Question:Teach me simple English with less than 1000 characters

<img width="2190" height="1144" alt="image" src="https://github.com/user-attachments/assets/f73ab0a1-00d8-4f86-8312-3b2cb59af082" />

2. Question:what is Homellm

<img width="2146" height="1174" alt="image" src="https://github.com/user-attachments/assets/ff0776d8-1584-40b4-8155-a29a9377ca12" />

3. Question:what is homellM

<img width="2174" height="1288" alt="image" src="https://github.com/user-attachments/assets/3f3e60d4-51af-4d67-a487-09fd381c4f78" />

4. Question:what is homel

<img width="2182" height="1210" alt="image" src="https://github.com/user-attachments/assets/baf015df-e162-4387-83fa-681ca0dc0d41" />

5. Question:Is homell creative home insurance product

<img width="2196" height="1184" alt="image" src="https://github.com/user-attachments/assets/e8825231-7ce2-4f30-8578-f738ec405e09" />

6. Question:Provide pricing for homellm

<img width="2192" height="1224" alt="image" src="https://github.com/user-attachments/assets/2064c8bc-4245-4c59-a246-efc3b9605adb" />




