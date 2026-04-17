# 🧠 CRAG Project — Interview Guide & Technical Deep Dive

> A complete reference for understanding, explaining, and defending the **Corrective Retrieval-Augmented Generation (CRAG)** project in interviews.

---

## 📌 PART 1: WHAT IS THIS PROJECT?

### 🔍 What is the Project?

**CRAG (Corrective Retrieval-Augmented Generation)** is an end-to-end intelligent question-answering system that combines a local knowledge base with autonomous web-search fallback to produce accurate, grounded answers.

It is an **advanced evolution of standard RAG** (Retrieval-Augmented Generation) that adds a critical self-correction layer: before generating an answer, the system **evaluates whether the retrieved documents are actually relevant** to the question. If they are not, it automatically pivots to a live web search.

The system is deployed as:
- A **FastAPI** Python backend running the AI pipeline
- A **React (Vite)** frontend for interactive Q&A and pipeline visualization

---

### ❗ The Problem It Solves

Standard vanilla RAG has a critical flaw: **it blindly trusts the retriever.**

| Problem | Impact |
| :--- | :--- |
| Retriever returns irrelevant chunks | LLM hallucinates or gives wrong answers |
| No mechanism to verify document quality | Confidently wrong outputs |
| Static knowledge base only | Cannot answer questions about recent events |
| No transparency into pipeline | User doesn't know why an answer was generated |

**CRAG solves all of these** by scoring every retrieved document and correcting course before generation.

---

### ✅ How the Project Solves the Problem

1.  **Ingestion**: Users upload diverse knowledge sources (PDFs, web pages, YouTube videos, audio).
2.  **Retrieval**: On a question, semantically similar documents are fetched from the vector store.
3.  **Evaluation**: Each document gets a **relevance score (0.0–1.0)** from an LLM judge.
4.  **Correction**: Based on scores, the system decides:
    - `CORRECT` (score > 0.7) → proceed with local knowledge
    - `INCORRECT` (all scores < 0.3) → discard local docs, do web search
    - `AMBIGUOUS` → use both local docs AND web results
5.  **Refinement**: Accepted documents are decomposed into sentences, and each sentence is filtered for relevance.
6.  **Generation**: A clean, vetted context is passed to the LLM to generate the final answer.

---

## 🏗️ PART 2: PROJECT ARCHITECTURE

### System Architecture Overview

```
User Interface (React + Vite)
        ↓ HTTP Requests (Axios)
FastAPI Backend (main.py)
    ├── /ingest  → Ingestion Pipeline
    │   └── Extract → Clean → Chunk → Embed → Store (Qdrant)
    ├── /query   → CRAG Reasoning Graph (LangGraph)
    │   └── Retrieve → Evaluate → [Rewrite → WebSearch] → Refine → Generate
    └── /graph   → Exposes node state for frontend graph viz
```

### Directory Structure

```
10_crag/
├── backend/
│   ├── main.py                     # FastAPI entry point
│   ├── requirements.txt
│   ├── api/
│   │   ├── ingest.py               # POST /ingest route
│   │   ├── query.py                # POST /query route
│   │   └── graph.py                # GET /graph/nodes route
│   ├── graph/
│   │   └── crag_graph.py           # The full LangGraph CRAG pipeline
│   ├── services/
│   │   ├── chunking.py             # RecursiveCharacterTextSplitter
│   │   ├── embedding.py            # SentenceTransformer model
│   │   ├── vectorstore.py          # Qdrant client + upsert/query
│   │   ├── preprocessing.py        # Text cleaning
│   │   └── history.py              # In-memory query history
│   ├── document_ingestion/
│   │   ├── extractors.py           # PDF / Web / Audio / YouTube extractors
│   │   └── utils.py                # clean_text, to_markdown helpers
│   └── utils/
│       ├── file_loader.py          # Dispatches file type to extractor
│       └── web_loader.py           # URL + YouTube loaders
└── frontend/
    └── src/
        ├── pages/                  # Main chat UI page
        └── components/
            ├── UploadPanel.jsx     # File/URL upload
            ├── QueryPanel.jsx      # Q&A interface
            ├── GraphViewer.jsx     # Live LangGraph visualizer
            └── NodeTooltip.jsx     # Node detail popups
```

---

## ⚙️ PART 3: TECHNICAL EXPLANATION — KEY FUNCTIONS

---

### 1. `chunk_text()` — Recursive Text Splitter

**File**: `backend/services/chunking.py`

**Why it's needed**: Raw extracted text can be thousands of characters. LLMs have context limits, and a huge blob of text yields poor similarity matching. Splitting into smaller, overlapping chunks preserves semantic meaning while being retrievable.

**What it does**: Uses LangChain's `RecursiveCharacterTextSplitter` to split text recursively at natural boundaries (`\n\n`, `\n`, space, then character-by-character) until chunks fit under the target size.

```python
from langchain_text_splitters import RecursiveCharacterTextSplitter

CHUNK_SIZE = 500      # Max characters per chunk
CHUNK_OVERLAP = 75    # Overlap to preserve context at boundaries

def chunk_text(text: str) -> List[str]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP
    )
    chunks = splitter.split_text(text)
    return chunks
```

**Key Parameters**:
- `chunk_size=500`: Each chunk ≤ 500 characters → fits within embedding model's token limit.
- `chunk_overlap=75`: Last 75 characters of chunk N are also the first 75 of chunk N+1 → prevents losing context at boundaries.

---

### 2. `encode_documents()` / `get_embedding_model()` — Vector Embeddings

**File**: `backend/services/embedding.py`

**Why it's needed**: Computers cannot compare text semantically. Embeddings convert text into dense numerical vectors where **similar meanings have small distances** in vector space.

**What it does**: Uses `sentence-transformers/all-MiniLM-L6-v2`, a lightweight but powerful model that produces **384-dimensional** vectors for each chunk.

```python
from sentence_transformers import SentenceTransformer

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
_model = None  # Singleton to avoid reloading on every call

def get_embedding_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model

def encode_documents(texts: list[str]) -> list:
    model = get_embedding_model()
    embeddings = model.encode(texts)  # Returns shape: (N, 384)
    return embeddings
```

**Singleton Pattern**: The model is loaded once into memory — prevents expensive re-loading on every API call.

---

### 3. `store_chunks()` — Vector Database Upsert

**File**: `backend/services/vectorstore.py`

**Why it's needed**: Embeddings must be persisted in a database that can perform fast **Approximate Nearest Neighbor (ANN)** search at scale.

**What it does**: Uses **Qdrant** (a high-performance vector database) to store `PointStruct` objects — each containing a UUID, the embedding vector, and the original text as payload.

```python
from qdrant_client.models import VectorParams, Distance, PointStruct

COLLECTION_NAME = "documents"
VECTOR_SIZE = 384      # Must match embedding model output dim
DB_PATH = ".qdrant_data"  # Persistent on-disk storage

def store_chunks(chunks: List[str]):
    _ensure_collection()  # Creates collection if it doesn't exist
    client = get_client()
    emd_docs = encode_documents(chunks)

    points = [
        PointStruct(
            id=uuid.uuid4().hex,   # Unique ID for each chunk
            vector=emd_docs[i],    # 384-dim float vector
            payload={"text": chunks[i]}  # Original text for retrieval
        )
        for i in range(len(chunks))
    ]
    client.upsert(collection_name=COLLECTION_NAME, points=points)
    return len(points)
```

**Distance Metric**: `Distance.COSINE` — measures the angle between vectors. Score of 1.0 = identical, 0.0 = completely unrelated.

---

### 4. `eval_each_doc_node()` — The CRAG Corrective Core

**File**: `backend/graph/crag_graph.py`

**Why it's needed**: This is the heart of CRAG. Standard RAG skips this step — which causes hallucinations. This node gives the system the ability to **know what it doesn't know.**

**What it does**: For each retrieved document, it calls an LLM-as-judge chain to score relevance. Based on scores, it sets the `verdict` to `CORRECT`, `INCORRECT`, or `AMBIGUOUS`.

```python
class DocEvalScore(BaseModel):
    score: float   # 0.0 to 1.0
    reason: str    # Explanation for the score

UPPER_TH = 0.7   # Above this = trustworthy
LOWER_TH = 0.3   # Below this = irrelevant

def eval_each_doc_node(state: State) -> State:
    scores = []
    good = []
    for doc in state["docs"]:
        out = doc_eval_chain.invoke({"question": q, "chunk": doc.page_content})
        scores.append(out.score)
        if out.score > LOWER_TH:
            good.append(doc)

    if any(s > UPPER_TH for s in scores):
        return {"verdict": "CORRECT", "good_docs": good}
    elif all(s < LOWER_TH for s in scores):
        return {"verdict": "INCORRECT", "good_docs": []}
    else:
        return {"verdict": "AMBIGUOUS", "good_docs": good}
```

---

### 5. `refine()` — Sentence-Level Knowledge Distillation

**File**: `backend/graph/crag_graph.py`

**Why it's needed**: Even "good" documents contain noise — navigation text, unrelated sentences, boilerplate. Passing all of this to the generator leads to diluted, less accurate answers.

**What it does**: Splits context into individual sentences, then runs each sentence through an LLM filter (`KeepOrDrop`) to keep only those that **directly help answer the question.**

```python
class KeepOrDrop(BaseModel):
    keep: bool  # True = sentence is relevant, False = discard

def refine(state: State) -> State:
    # Decide which docs to use based on verdict
    if state["verdict"] == "CORRECT":
        docs_to_use = state["good_docs"]
    elif state["verdict"] == "INCORRECT":
        docs_to_use = state["web_docs"]  # Web search fallback
    else:  # AMBIGUOUS
        docs_to_use = state["good_docs"] + state["web_docs"]

    context = "\n\n".join(d.page_content for d in docs_to_use)
    strips = decompose_to_sentences(context)  # Split into sentences

    # LLM-based filter: keep only relevant sentences
    kept = [s for s in strips if filter_chain.invoke({
        "question": state["question"], "sentence": s
    }).keep]

    return {"kept_strips": kept, "refined_context": "\n".join(kept)}
```

---

### 6. `rewrite_query_node()` — Query Reformulation for Web

**File**: `backend/graph/crag_graph.py`

**Why it's needed**: A user question like "What is the capital of France?" is great for a human but poor for a web search engine. This node optimizes the query for keyword-based web search.

```python
class WebQuery(BaseModel):
    query: str  # The reformulated search query

rewrite_chain = rewrite_prompt | llm.with_structured_output(WebQuery)

def rewrite_query_node(state: State) -> State:
    out = rewrite_chain.invoke({"question": state["question"]})
    return {"web_query": out.query}
    # Example: "What is attention in transformers?" → "attention mechanism transformer neural network explained"
```

---

### 7. `POST /ingest` — The Full Ingestion Pipeline API

**File**: `backend/api/ingest.py`

**What it does**: Accepts file uploads or URLs, routes to the correct extractor, then runs the full pipeline: `Extract → Clean → Chunk → Embed → Store`.

```
Supported inputs:
- PDFs          (simple_pdf via PyMuPDF, ocr_pdf via Docling)
- Text files    (txt)
- Audio files   (audio via Groq Whisper)
- Web URLs      (website via Crawl4AI)
- YouTube URLs  (youtube via YouTubeTranscriptApi)
```

**Pipeline Flow**:
```python
raw_text = extract_text_from_file(tmp_path)       # Step 1: Extract
clean_text = process_text_to_markdown(raw_text)   # Step 2: Clean
chunks = chunk_text(clean_text)                   # Step 3: Chunk (500 chars, 75 overlap)
num_stored = store_chunks(chunks)                 # Step 4: Embed + Store in Qdrant
```

---

## 🎤 PART 4: INTERVIEW QUESTIONS & ANSWERS

---

### 🔵 Conceptual / Fundamentals

---

**Q1. What is RAG and what problem does it solve?**

> **A**: RAG (Retrieval-Augmented Generation) is a technique that grounds LLM responses in external, up-to-date, or private knowledge. Instead of relying solely on an LLM's parametric knowledge (which is static and can hallucinate), RAG retrieves relevant documents from a knowledge base and provides them as context to the LLM before generation. This reduces hallucination and allows the model to answer questions about data it was not trained on.

---

**Q2. What is the core difference between RAG and CRAG?**

> **A**: Standard RAG blindly passes retrieved documents to the LLM regardless of their quality. **CRAG adds a corrective step**: before generation, each retrieved document is evaluated for relevance. If the documents are poor, the system automatically falls back to a web search, preventing the LLM from hallucinating based on irrelevant context. CRAG is essentially RAG + self-evaluation + autonomous correction.

---

**Q3. What is a Vector Database? Why is Qdrant used here?**

> **A**: A vector database stores high-dimensional numerical vectors (embeddings) and supports ultra-fast **Approximate Nearest Neighbor (ANN)** search — returning vectors that are "closest" (most semantically similar) to a query vector. Qdrant is used here because it is:
> - **Open-source** and can run completely locally (no cloud dependency)
> - **Persistent**: data is saved to disk at `.qdrant_data` and survives restarts
> - **Fast**: uses HNSW graph indexing for sub-millisecond search
> - **Supports payload**: we store original text alongside vectors for easy retrieval

---

**Q4. What is Cosine Similarity? How is it used here?**

> **A**: Cosine similarity measures the angle between two vectors in a multi-dimensional space. A score of **1.0** means identical direction (semantically identical), **0.0** means orthogonal (completely unrelated), and **-1.0** means opposite. In this project, Qdrant is configured with `Distance.COSINE`. When a user asks a question, its embedding is compared against all stored chunk embeddings — the top-3 closest chunks (highest cosine similarity) are retrieved.

---

**Q5. What are Embeddings? Which model is used here?**

> **A**: Embeddings are dense numerical representations of text where semantic meaning is encoded as a vector of floating-point numbers. Similar sentences will have similar vectors. This project uses **`sentence-transformers/all-MiniLM-L6-v2`**, a lightweight model that produces **384-dimensional** embeddings. It is fast, runs on CPU, has good quality for English text, and is a popular choice for production RAG systems.

---

**Q6. What is RecursiveCharacterTextSplitter? Why use it over a simple splitter?**

> **A**: `RecursiveCharacterTextSplitter` splits text by trying multiple separators in order: `["\n\n", "\n", " ", ""]`. This means it first tries to split at paragraph boundaries, then line boundaries, then words, and only as a last resort at character level. This is superior to a naive fixed-size splitter because it respects the natural structure of the document (paragraphs, sentences) and is far less likely to split a sentence or a key concept in half.

---

**Q7. What is chunk overlap and why is it important?**

> **A**: Chunk overlap means the last N characters of one chunk are also the first N characters of the next chunk. In this project, `chunk_overlap=75`. This is important because a key piece of information might sit at the boundary between two chunks. Without overlap, that information is split and neither chunk contains it fully, meaning relevant content might not be retrieved. Overlap ensures continuity.

---

**Q8. What is LangGraph? How is it used in CRAG?**

> **A**: LangGraph is a framework from LangChain for building stateful, multi-step agentic workflows as **directed graphs**. Each node is a Python function that reads from and writes to a shared `State` dictionary. Edges define the execution flow, and **conditional edges** allow branching based on state values. In CRAG, LangGraph manages the entire reasoning pipeline: `retrieve → eval_each_doc → [rewrite_query → web_search] → refine → generate`. The `route_after_eval` function acts as the conditional router.

---

**Q9. What is Structured Output in LangChain? Why is it used here?**

> **A**: `llm.with_structured_output(PydanticModel)` forces the LLM to return a response that conforms to a Pydantic model schema (valid JSON). Without this, LLMs return free-text strings that require fragile parsing. In CRAG, it is used for:
> - `DocEvalScore` — ensures the evaluator always returns `{"score": float, "reason": str}`
> - `KeepOrDrop` — ensures the filter always returns `{"keep": bool}`
> - `WebQuery` — ensures the query rewriter returns `{"query": str}`

---

### 🟠 Architecture / Design

---

**Q10. Why is the Singleton Pattern used for the embedding model and Qdrant client?**

> **A**: Loading a machine learning model (like `all-MiniLM-L6-v2`) is expensive — it takes time and memory. If we reloaded the model on every API request, the application would be extremely slow. The Singleton pattern ensures the model is loaded **once** on first use and then reused across all subsequent requests:
> ```python
> _model = None
> def get_embedding_model():
>     global _model
>     if _model is None:
>         _model = SentenceTransformer(MODEL_NAME)
>     return _model
> ```

---

**Q11. How does the `/ingest` API handle different file types?**

> **A**: The `/ingest` endpoint receives an optional `source_type` form field. Based on its value, it dispatches to the appropriate extractor:
> - `simple_pdf` → `PyMuPDF4LLM` (fast, digital PDFs)
> - `ocr_pdf` → `Docling` (scanned/image-based PDFs, uses OCR)
> - `audio` → Groq Whisper API (transcription)
> - `youtube` → `YouTubeTranscriptApi`
> - `website` → `Crawl4AI` (async web crawler with JavaScript rendering)
> - Default → auto-detection by file extension

---

**Q12. What are the three CRAG verdicts and what happens in each case?**

> **A**:
> - **`CORRECT`**: At least one retrieved chunk has a relevance score > 0.7. The system trusts the local knowledge base and uses only the `good_docs` for context refinement.
> - **`INCORRECT`**: All retrieved chunks score < 0.3. The local knowledge base is useless for this query. The system triggers a web search via Tavily and uses only the `web_docs`.
> - **`AMBIGUOUS`**: No chunk is highly relevant (> 0.7) but some are weakly relevant (0.3–0.7). The system uses **both** the `good_docs` and the `web_docs` for maximum coverage.

---

**Q13. What is Tavily and why was it chosen over Google or Bing?**

> **A**: Tavily is a search API built specifically for AI agents and RAG systems. Unlike scraping Google results, Tavily:
> - Returns **clean, extracted text** from web pages (not ads, navigation, etc.)
> - Has a generous free tier
> - Is optimized for **low-latency, factual responses**
> - Integrates directly with LangChain via `TavilySearchResults`

---

**Q14. How does the frontend graph visualizer work?**

> **A**: After every query, the `crag_graph.py` tracks the input and output state of each LangGraph node using `graph.stream()` in `stream_mode="updates"`. These states are stored in `_last_run_node_states`. The frontend calls the `/graph/node-states` endpoint to fetch this data and `GraphViewer.jsx` renders the graph using a D3.js-based library, highlighting which nodes were activated and showing the data that flowed through them.

---

### 🔴 Advanced / Tricky

---

**Q15. Can CRAG still hallucinate? What are its limitations?**

> **A**: Yes. CRAG significantly reduces hallucination but doesn't eliminate it.
> - The **evaluator itself** (an LLM) can be wrong — it might score a relevant chunk low or an irrelevant chunk high.
> - The **thresholds** (0.3/0.7) are hardcoded heuristics and may not be optimal for all domains.
> - **Web search results** can themselves be incorrect or biased — CRAG trusts Tavily's results without further verification.
> - The **refinement filter** might discard genuinely useful sentences.

---

**Q16. What happens if both local retrieval AND web search return irrelevant results?**

> **A**: The `refine()` function would return an empty `kept_strips` list and an empty `refined_context`. The `generate()` function uses the prompt: *"If the context is empty or insufficient, say: 'I don't know.'"* — so the LLM would correctly respond with an "I don't know" rather than hallucinating.

---

**Q17. How would you scale this system for production?**

> **A**: Several improvements would be needed:
> 1. **Qdrant Cloud** instead of local file-based storage for horizontal scalability
> 2. **Async LLM calls** (parallel document evaluation instead of sequential)
> 3. **Redis caching** for frequently asked questions
> 4. **Database-backed history** (PostgreSQL/SQLite) instead of in-memory list
> 5. **Rate limiting** on the FastAPI endpoints
> 6. **Authentication** for multi-user support
> 7. **Background jobs** (Celery/ARQ) for large file ingestion tasks

---

**Q18. Why use `asyncio.to_thread()` for the Crawl4AI web crawler?**

> **A**: `Crawl4AI` uses `asyncio.run()` internally to manage its own event loop. In FastAPI, there is already a running event loop. Calling `asyncio.run()` inside an existing loop raises a `RuntimeError`. To solve this, the `sync_extract_webpage()` wrapper runs the async crawler in a **new thread** via `asyncio.to_thread()`, which gets its own event loop context and avoids the conflict.

---

**Q19. What is the purpose of `PointStruct` in Qdrant?**

> **A**: `PointStruct` is the data format that Qdrant uses to store a single vector entry. It contains three fields:
> - `id`: A unique identifier (here, a UUID hex string)
> - `vector`: The embedding array (384 floats for `all-MiniLM-L6-v2`)
> - `payload`: A dictionary of arbitrary metadata (here, `{"text": original_chunk}`)
> 
> When a query returns results, the `payload` is used to retrieve the original text, since Qdrant only stores and searches vectors — the payload is what carries the human-readable content.

---

**Q20. How does LangChain's `with_structured_output()` actually work under the hood?**

> **A**: When you call `llm.with_structured_output(PydanticModel)`, LangChain:
> 1. Converts the Pydantic model's schema to a JSON Schema definition
> 2. Passes this schema to the LLM as a **tool definition** or via `response_format` (depending on the provider)
> 3. For Groq (which uses the OpenAI API format), it uses **tool calling** — the model is instructed to call a specific "tool" with the required parameters
> 4. The response is automatically parsed back into the Pydantic model instance
> 
> This is far more reliable than prompt-based JSON extraction because the model's output is constrained at the API level.

---

## 📊 Quick Reference Summary

| Concept | Tool Used | Why |
| :--- | :--- | :--- |
| PDF Extraction | PyMuPDF4LLM, Docling | Handle both digital and OCR PDFs |
| Web Crawling | Crawl4AI | Renders JavaScript-heavy pages |
| Audio Transcription | Groq Whisper | Fast, accurate, free API |
| Text Chunking | RecursiveCharacterTextSplitter | Respects document structure |
| Embeddings | all-MiniLM-L6-v2 | Fast, lightweight, 384-dim |
| Vector Store | Qdrant (local) | Persistent, HNSW-indexed ANN search |
| Relevance Scoring | ChatGroq + Structured Output | LLM-as-judge with Pydantic enforcement |
| Web Search | Tavily | AI-native search with clean text output |
| LLM | Llama 3.3 70B (Groq) | Fast inference, large context window |
| Orchestration | LangGraph | Stateful, conditional graph pipelines |
| Backend | FastAPI | Async, high-performance Python API |
| Frontend | React + Vite | Fast, component-based SPA |

---

*Good luck with your interview! 🚀 — You built something impressive.*
