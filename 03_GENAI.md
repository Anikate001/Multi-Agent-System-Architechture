# SECTION 3: GENERATIVE AI — 15 S-TIER PROJECTS

> LLMs, RAG pipelines, multi-agent systems, fine-tuning, prompt engineering, and GenAI applications.
> These projects demonstrate cutting-edge GenAI skills with production-grade architecture.

---

## PROJECT 31: Multi-Agent Research Assistant with LangGraph Orchestration

**🎯 The Hook:** Built multi-agent system where specialized AI agents (researcher, analyst, writer, critic) collaborate via LangGraph state machine to produce publication-quality research reports — with human-in-the-loop review gates and tool-use capabilities.

**Difficulty:** █████████░ (9/10)

### 🧠 Why S-Tier?
- Multi-agent orchestration (LangGraph state machines — cutting-edge)
- Tool-augmented agents (web search, code execution, database queries)
- Human-in-the-loop with approval gates
- Structured output with Pydantic validation
- Shows agentic AI architecture — the hottest skill in 2026

### 🛠️ Tech Stack (100% Free Tier)
- **LLM:** Google Gemini API (free tier) / Groq (free, fast inference)
- **Orchestration:** LangGraph (state machines for agent coordination)
- **Tools:** Tavily API (web search, 1K/month free), E2B (code sandbox)
- **Memory:** Supabase PostgreSQL for conversation history
- **Output:** Structured JSON with Pydantic schemas
- **Deployment:** Streamlit Cloud + FastAPI on Railway.app

### 📐 Architecture Overview
1. User Query → "Research the impact of quantum computing on cryptography"
2. Planner Agent → Decomposes into sub-tasks (background, technical, implications)
3. Researcher Agent → Uses Tavily web search to gather sources
4. Analyst Agent → Synthesizes findings, identifies key insights
5. Coder Agent → Generates visualizations (matplotlib, charts)
6. Writer Agent → Produces structured report (intro, sections, conclusion)
7. Critic Agent → Reviews for accuracy, citations, coherence
8. Human Gate → User reviews, approves or requests revision
9. Output → PDF report with citations, visualizations, and bibliography

### 🔨 Implementation Phases
- **Week 1: Agent Design (7 days)** — Define agent roles with system prompts. Implement tool calling (search, code exec). Build Pydantic schemas for structured output. Test individual agents.
- **Week 2: LangGraph Orchestration (7 days)** — Design state machine (nodes=agents, edges=transitions). Implement conditional routing (critic → revision or approval). Add human-in-the-loop checkpoints. Handle errors and retries.
- **Week 3: Memory & Context (7 days)** — Implement conversation memory (Supabase). Build context window management (summarization for long contexts). Add source tracking and citation management.
- **Week 4: UI & Deployment (7 days)** — Build Streamlit interface with agent progress visualization. Show agent reasoning traces. Deploy on Railway.app. Add export to PDF/Markdown.

### ⚡ Key Challenges & Solutions
- **Challenge:** Agents lose context in long research tasks (token limit)
  - **Solution:** Implemented hierarchical summarization: each agent summarizes findings before passing to next. Used a "research state" object tracking all accumulated knowledge. Context window management with sliding window + summary.
- **Challenge:** Agent loops (critic keeps rejecting → infinite revision)
  - **Solution:** Max 3 revision cycles. Critic must provide specific, actionable feedback. After 3 rounds, escalate to human review. LangGraph conditional edges enforce this logic.
- **Challenge:** Hallucinated citations and facts
  - **Solution:** Every claim must link to a Tavily search result URL. Critic agent cross-references claims with sources. If unsupported, flags for revision. Built citation verification pipeline.

### 🎓 What You'll Learn (Interview Gold)
- Agentic AI architecture (multi-agent systems)
- LangGraph state machines and orchestration
- Tool-augmented LLM agents
- Human-in-the-loop design patterns
- Structured output with Pydantic
- Context management for long tasks

### 🔥 Interview Talking Points
- **Q:** Why LangGraph over simple prompt chaining?
  - **A:** Prompt chains are linear (A→B→C). LangGraph enables conditional routing, cycles (critic→writer→critic), parallel execution, and persistent state. My agents can branch on conditions, retry on failure, and maintain shared state — impossible with chains.
- **Q:** How do you prevent hallucinations in research output?
  - **A:** Three layers: (1) Tool-grounded generation — every claim must cite a Tavily search result, (2) Critic agent cross-references claims with sources, (3) Structured output schema requires citation fields for each finding. Reduced unsupported claims from 23% to 4%.
- **Q:** How do you handle long research tasks exceeding context window?
  - **A:** Hierarchical state management: each agent produces a structured summary stored in LangGraph state. Subsequent agents receive summaries + relevant chunks (not full history). For source documents, I use map-reduce: summarize each doc independently, then synthesize summaries.

**📊 Portfolio Impact:** ⭐⭐⭐⭐⭐
**Resume Bullet:** Architected multi-agent research system using LangGraph with 5 specialized agents (researcher, analyst, writer, critic, coder), tool-augmented generation, and human-in-the-loop — reducing hallucinations to 4% with citation verification

---

## PROJECT 32: Production RAG Pipeline with Hybrid Search & Evaluation

**🎯 The Hook:** Built enterprise RAG system with hybrid retrieval (dense + sparse + reranker), achieving 94% faithfulness on RAGAS evaluation — with chunking strategies, metadata filtering, and query decomposition.

**Difficulty:** █████████░ (9/10)

### 🧠 Why S-Tier?
- Production-grade RAG (not toy demo)
- Hybrid retrieval: dense (embeddings) + sparse (BM25) + neural reranker
- Advanced chunking (semantic, recursive, parent-child)
- RAGAS evaluation framework (faithfulness, relevance, recall)
- Query decomposition for complex questions

### 🛠️ Tech Stack (100% Free Tier)
- **LLM:** Gemini API / Groq (free inference)
- **Embeddings:** sentence-transformers (local) or Cohere embed (free tier)
- **Vector DB:** Qdrant Cloud (1GB free) or ChromaDB (local)
- **Sparse:** BM25 via rank_bm25
- **Reranker:** Cohere rerank API (1K/month free)
- **Evaluation:** RAGAS, DeepEval
- **UI:** Streamlit Cloud

### 📐 Architecture Overview
1. Document Ingestion → Parse PDF/HTML/MD with unstructured
2. Chunking → Semantic chunking (sentence-transformers similarity)
3. Dual Indexing → Dense embeddings (Qdrant) + Sparse (BM25 index)
4. Query Processing → Decompose complex queries into sub-queries
5. Hybrid Retrieval → Fetch from both indexes, reciprocal rank fusion
6. Neural Reranking → Cohere rerank for precision
7. Context Assembly → Dedup, order, add metadata
8. Generation → LLM with retrieved context + source citations
9. Evaluation → RAGAS metrics (faithfulness, relevance, context recall)

### 🔨 Implementation Phases
- **Week 1: Ingestion & Chunking (7 days)** — Build document parser for PDF/HTML/MD. Implement 3 chunking strategies: fixed-size, recursive, semantic. Compare chunk quality metrics. Add metadata extraction.
- **Week 2: Hybrid Retrieval (7 days)** — Set up Qdrant for dense retrieval. Implement BM25 for sparse retrieval. Build reciprocal rank fusion. Add Cohere reranker. Evaluate retrieval quality (MRR, Recall@K).
- **Week 3: Generation & Evaluation (7 days)** — Implement RAG generation with citation tracking. Build RAGAS evaluation pipeline. Optimize prompt engineering for faithfulness. Achieve 94% faithfulness score.
- **Week 4: Advanced Features (7 days)** — Query decomposition for multi-hop questions. Metadata filtering (date, source, topic). Conversation memory for follow-up questions. Deploy on Streamlit.

### ⚡ Key Challenges & Solutions
- **Challenge:** Single retrieval misses relevant context for complex questions
  - **Solution:** Query decomposition: break "Compare X and Y in context Z" into 3 sub-queries. Retrieve for each, deduplicate results. Improved context recall from 71% to 89%.
- **Challenge:** Retrieved context is relevant but answer is unfaithful
  - **Solution:** Structured generation prompt: "Answer ONLY using the provided context. For each claim, cite [Source N]." Added faithfulness check as post-processing step. Improved from 78% to 94% RAGAS faithfulness.
- **Challenge:** Embedding-based retrieval misses keyword matches
  - **Solution:** Hybrid retrieval: dense (semantic similarity) + sparse (BM25 keyword matching). Reciprocal rank fusion combines results. Best of both worlds — improved recall@10 from 82% (dense only) to 93% (hybrid).

### 🔥 Interview Talking Points
- **Q:** Why hybrid retrieval instead of just embeddings?
  - **A:** Embeddings are great for semantic similarity but miss exact keyword matches (product codes, names, acronyms). BM25 catches these. I fuse with reciprocal rank fusion: RRF(d) = Σ 1/(k + rank_i(d)). Improved recall@10 from 82% to 93%.
- **Q:** How do you evaluate RAG quality?
  - **A:** RAGAS framework measures 4 metrics: (1) Faithfulness — is answer supported by context? (94%), (2) Answer relevancy — does answer address the question? (91%), (3) Context precision — are retrieved docs relevant? (88%), (4) Context recall — did we retrieve all needed info? (89%).

**📊 Portfolio Impact:** ⭐⭐⭐⭐⭐
**Resume Bullet:** Built production RAG pipeline with hybrid retrieval (dense+sparse+reranker), query decomposition, and semantic chunking — achieving 94% RAGAS faithfulness with 93% recall@10

---

## PROJECT 33: LLM Fine-Tuning with LoRA/QLoRA on Custom Domain Data

**🎯 The Hook:** Fine-tuned Llama-3-8B on domain-specific data using QLoRA (4-bit quantization + LoRA adapters), achieving 91% domain accuracy with only 5K training samples — trained entirely on Colab free tier.

**Difficulty:** ████████░░ (8/10)

### 🧠 Why S-Tier?
- Parameter-efficient fine-tuning (LoRA/QLoRA — industry standard)
- 4-bit quantization for training on consumer hardware
- Custom dataset curation and formatting
- Evaluation beyond perplexity (task-specific benchmarks)
- Most freshers use APIs — you TRAINED the model

### 🛠️ Tech Stack: HuggingFace Transformers + PEFT + bitsandbytes + Colab + W&B
### Key Metrics: 91% domain accuracy, 5K samples, 4-bit training on Colab

### 📐 Architecture
1. Data Curation → Collect 5K domain-specific instruction-response pairs
2. Data Formatting → Convert to chat template (system/user/assistant)
3. QLoRA Setup → Load Llama-3-8B in 4-bit with NF4 quantization
4. LoRA Config → Rank=16, alpha=32, target modules (q_proj, v_proj, k_proj, o_proj)
5. Training → SFT (supervised fine-tuning) with packing
6. Evaluation → Domain-specific benchmark (not just perplexity)
7. Merge → Merge LoRA weights into base model
8. Deploy → Upload to HuggingFace Hub, serve via vLLM/Ollama

### Key Interview Points
- **Q:** Why LoRA instead of full fine-tuning?
  - **A:** Full fine-tuning of 8B model requires 60GB+ VRAM. LoRA trains only low-rank adapter matrices (0.1% of params). QLoRA adds 4-bit quantization, reducing memory to 6GB — fits on Colab free tier. I achieved 91% domain accuracy, matching full fine-tune at 2% of compute cost.
- **Q:** How do you evaluate fine-tuned LLMs beyond perplexity?
  - **A:** Perplexity measures language modeling, not task quality. I created a domain-specific benchmark: 200 questions with expert-annotated answers. Evaluated with: (1) LLM-as-judge (GPT-4 scores quality 1-5), (2) ROUGE/BERTScore vs reference, (3) Human evaluation on 50 samples.

**Resume Bullet:** Fine-tuned Llama-3-8B with QLoRA on 5K domain samples achieving 91% domain accuracy on Colab free tier — with custom evaluation benchmark and LoRA adapter merging

---

## PROJECT 34: AI-Powered Code Review Agent with AST Analysis

**🎯 The Hook:** Built automated code review agent that analyzes Pull Requests using AST parsing + LLM reasoning, detecting bugs, security vulnerabilities, and style issues — with 87% precision on real codebases.

**Difficulty:** ████████░░ (8/10)

### 🧠 Why S-Tier?
- Code understanding (AST analysis + LLM reasoning)
- GitHub integration (PR review automation)
- Security vulnerability detection
- Structured feedback with severity levels
- Practical DevOps AI application

### 🛠️ Tech Stack: tree-sitter (AST) + Gemini API + GitHub Actions + FastAPI
### Key Metrics: 87% precision, reviews PRs in <30 seconds, 12 vulnerability categories

**Resume Bullet:** Built AI code review agent with AST analysis + LLM reasoning detecting bugs and security vulnerabilities with 87% precision — integrated with GitHub Actions for automated PR reviews

---

## PROJECT 35: Conversational AI with Structured Tool Calling & Memory

**🎯 The Hook:** Built production chatbot with persistent memory, structured tool calling (12 tools: calendar, email, search, calculator), conversation summarization, and personality consistency — handling 1000+ turn conversations.

**Difficulty:** ████████░░ (8/10)

### 🧠 Why S-Tier?
- Structured tool calling with function schemas
- Persistent conversational memory (short-term + long-term)
- Conversation summarization for context management
- Personality consistency across sessions
- Production error handling and fallbacks

### 🛠️ Tech Stack: Gemini API + LangChain + Supabase + Redis + Streamlit
### Key Metrics: 12 tools, 1000+ turn conversations, 96% tool call accuracy

**Resume Bullet:** Developed conversational AI with 12 structured tools, persistent memory (short+long term), and conversation summarization — maintaining personality consistency across 1000+ turn conversations with 96% tool accuracy

---

## PROJECT 36: Document Intelligence — Multi-Modal Document Understanding Pipeline

**🎯 The Hook:** Built document understanding pipeline processing PDFs with tables, charts, and images using vision LLMs + OCR, extracting structured data with 93% accuracy — handling invoices, contracts, and research papers.

**Difficulty:** ████████░░ (8/10)

### 🧠 Why S-Tier?
- Multi-modal AI (text + images + tables)
- Document layout analysis
- Table extraction and structured output
- Vision LLM integration (Gemini vision)
- Real enterprise use case (invoice processing)

### 🛠️ Tech Stack: Gemini Vision + unstructured.io + pdfplumber + Pydantic + FastAPI
### Key Metrics: 93% extraction accuracy, handles tables/charts/images, 3 document types

**Resume Bullet:** Built multi-modal document intelligence pipeline using vision LLMs for PDF understanding — extracting structured data from tables, charts, and images with 93% accuracy across invoices, contracts, and papers

---

## PROJECT 37: Prompt Engineering Framework with Automatic Optimization

**🎯 The Hook:** Built prompt optimization framework using DSPy that automatically discovers optimal prompts through bootstrapping and optimization — improving task accuracy from 72% to 89% without manual prompt engineering.

**Difficulty:** ███████░░░ (7/10)

### 🧠 Why S-Tier?
- DSPy (programmatic prompt optimization — Stanford research)
- Automatic prompt discovery (beyond manual engineering)
- Few-shot example selection optimization
- Chain-of-thought optimization
- Shows systematic approach to prompting

### 🛠️ Tech Stack: DSPy + Gemini API + HuggingFace datasets + Streamlit
### Key Metrics: 72% → 89% accuracy via automatic optimization, zero manual prompt engineering

**Resume Bullet:** Built automatic prompt optimization framework using DSPy achieving 72%→89% accuracy improvement through bootstrapped few-shot selection and chain-of-thought optimization — zero manual engineering

---

## PROJECT 38: Text-to-SQL Agent with Schema Understanding & Self-Correction

**🎯 The Hook:** Built Text-to-SQL agent that converts natural language to SQL queries with 88% execution accuracy — using schema understanding, query validation, self-correction loops, and result explanation.

**Difficulty:** ████████░░ (8/10)

### 🧠 Why S-Tier?
- Text-to-SQL (practical business AI application)
- Schema understanding and relationship inference
- Self-correction (execute → check → fix → retry)
- Result explanation in natural language
- Handles complex queries (joins, subqueries, aggregations)

### 🛠️ Tech Stack: Gemini API + SQLite + LangChain + Streamlit + Supabase
### Key Metrics: 88% execution accuracy, handles JOINs/subqueries, self-correction improves 12%

**Resume Bullet:** Developed Text-to-SQL agent with schema understanding and self-correction loops achieving 88% execution accuracy on complex queries — with natural language result explanation

---

## PROJECT 39: LLM-Powered Data Analysis Agent (Code Interpreter Clone)

**🎯 The Hook:** Built AI data analysis agent that takes CSV/Excel data, generates and executes Python analysis code, produces visualizations, and delivers insights — like ChatGPT Code Interpreter but self-hosted.

**Difficulty:** ████████░░ (8/10)

### 🧠 Why S-Tier?
- Code generation + execution (sandboxed)
- Data analysis automation
- Iterative problem-solving (generate → execute → debug → refine)
- Visualization generation (matplotlib, plotly)
- Self-hosted Code Interpreter alternative

### 🛠️ Tech Stack: Gemini API + E2B (code sandbox) + Streamlit + pandas
### Key Metrics: Handles CSV/Excel, generates+executes analysis code, produces interactive plots

**Resume Bullet:** Built self-hosted Code Interpreter clone with LLM-powered data analysis — generating, executing, and debugging Python code in sandboxed environment with automatic visualization generation

---

## PROJECT 40: Guardrails & Safety Layer for LLM Applications

**🎯 The Hook:** Built comprehensive LLM safety framework with input/output guardrails — detecting prompt injection (97% catch rate), content moderation, PII redaction, and hallucination detection with <50ms overhead.

**Difficulty:** ████████░░ (8/10)

### 🧠 Why S-Tier?
- LLM safety (critical for production deployment)
- Prompt injection detection and prevention
- PII detection and redaction
- Content moderation (toxicity, bias)
- Hallucination detection with source verification
- Shows responsible AI engineering

### 🛠️ Tech Stack: NeMo Guardrails + Presidio (PII) + custom classifiers + FastAPI
### Key Metrics: 97% injection catch rate, PII redaction, <50ms overhead

### 📐 Architecture
1. Input Guardrails → Prompt injection classifier + PII detector + topic filter
2. Processing → LLM generates response
3. Output Guardrails → Hallucination check + toxicity filter + PII redaction
4. Logging → All flagged inputs/outputs logged for review
5. Metrics → False positive/negative rates, latency overhead
6. Dashboard → Real-time safety monitoring

### Key Interview Points
- **Q:** How do you detect prompt injection?
  - **A:** Multi-layer defense: (1) Fine-tuned classifier on injection dataset (97% recall), (2) Instruction hierarchy (system prompt > user prompt), (3) Output validation against expected format. No single layer is sufficient — defense in depth.
- **Q:** How do you handle PII in LLM applications?
  - **A:** Presidio for entity recognition (SSN, credit cards, emails, names). Redact before sending to LLM. Re-insert placeholders in response. Also train LLM to refuse PII-related queries.

**Resume Bullet:** Built LLM safety framework with prompt injection detection (97% catch rate), PII redaction, and hallucination detection — adding <50ms overhead with defense-in-depth architecture

---

## PROJECT 41: Voice-to-Action AI Assistant with Speech Understanding

**🎯 The Hook:** Built voice-controlled AI assistant that transcribes speech (Whisper), understands intent with LLM, executes actions (send email, set reminder, search), and responds with TTS — end-to-end voice AI pipeline.

**Difficulty:** ███████░░░ (7/10)

### 🧠 Why S-Tier?
- End-to-end voice AI pipeline
- Speech-to-text (Whisper) + LLM reasoning + text-to-speech
- Intent classification and action execution
- Multi-modal (voice + text) interaction
- Real-time processing

### 🛠️ Tech Stack: Whisper (STT) + Gemini API + Edge TTS + FastAPI + Streamlit
### Key Metrics: <2s end-to-end latency, 95% intent accuracy, 8 action types

**Resume Bullet:** Built end-to-end voice AI assistant with Whisper STT + LLM intent classification + action execution — handling 8 action types with 95% accuracy and <2s latency

---

## PROJECT 42: Multimodal RAG with Vision + Text + Table Understanding

**🎯 The Hook:** Built multimodal RAG system that retrieves and reasons over text, images, and tables from technical documents — achieving 89% answer accuracy on questions requiring cross-modal reasoning.

**Difficulty:** █████████░ (9/10)

### 🧠 Why S-Tier?
- Multimodal retrieval (text + image + table)
- Cross-modal reasoning (answer requires multiple modalities)
- Vision embedding for image retrieval
- Table serialization strategies
- Advanced RAG architecture

### 🛠️ Tech Stack: Gemini Vision + CLIP embeddings + Qdrant + unstructured + Streamlit
### Key Metrics: 89% answer accuracy on cross-modal questions, handles text+image+table

**Resume Bullet:** Built multimodal RAG system reasoning over text, images, and tables with 89% accuracy on cross-modal questions — using CLIP embeddings + vision LLMs for unified document understanding

---

## PROJECT 43: LLM Evaluation & Benchmarking Framework

**🎯 The Hook:** Built comprehensive LLM evaluation framework testing accuracy, reasoning, safety, cost, and latency across 10+ models — with automated benchmark suites and Elo-rating leaderboard.

**Difficulty:** ███████░░░ (7/10)

### 🧠 Why S-Tier?
- LLM evaluation (critical skill as models proliferate)
- Multi-dimensional benchmarking (accuracy, safety, cost, latency)
- Elo-rating system for model comparison
- Automated evaluation pipelines
- LLM-as-judge methodology

### 🛠️ Tech Stack: Multiple LLM APIs + lm-eval-harness + Streamlit + Supabase
### Key Metrics: 10+ models benchmarked, 500+ test cases, Elo leaderboard

**Resume Bullet:** Developed LLM evaluation framework benchmarking 10+ models across accuracy, reasoning, safety, cost, and latency — with Elo-rating leaderboard and automated evaluation pipelines

---

## PROJECT 44: Agentic Workflow Automation Platform

**🎯 The Hook:** Built no-code agentic workflow platform where users define multi-step AI workflows (data extraction → analysis → report → email) via drag-and-drop — executing complex business processes with LLM agents.

**Difficulty:** █████████░ (9/10)

### 🧠 Why S-Tier?
- Workflow automation with AI agents
- Visual workflow builder (drag-and-drop)
- Multi-step agent orchestration
- Error handling and retry logic
- Real business process automation

### 🛠️ Tech Stack: LangGraph + React Flow + Gemini API + FastAPI + Supabase
### Key Metrics: Visual workflow builder, 15+ node types, handles multi-step processes

**Resume Bullet:** Built agentic workflow automation platform with visual drag-and-drop builder and LangGraph orchestration — enabling non-technical users to create multi-step AI workflows for business process automation

---

## PROJECT 45: Knowledge Graph Construction & Querying with LLMs

**🎯 The Hook:** Built automated knowledge graph construction pipeline using LLMs to extract entities and relationships from unstructured text — with graph-based QA achieving 86% accuracy on complex multi-hop questions.

**Difficulty:** ████████░░ (8/10)

### 🧠 Why S-Tier?
- Knowledge graph construction (entity + relationship extraction)
- Graph-based question answering
- Multi-hop reasoning over graph structure
- LLM + graph database integration
- Advanced information extraction

### 🛠️ Tech Stack: Gemini API + Neo4j (free tier) + LangChain + Streamlit
### Key Metrics: 86% multi-hop QA accuracy, 50K+ extracted triples, interactive graph visualization

**Resume Bullet:** Built automated knowledge graph construction with LLM-based entity/relationship extraction (50K+ triples) and graph-based QA achieving 86% accuracy on multi-hop questions — deployed on Neo4j

---

> **END OF SECTION 3: GENERATIVE AI**
> See `04_AI_ENGINEERING.md` for the next 15 projects.
