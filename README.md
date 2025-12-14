# Project 7 — Multi-Tool AI Agent (RAG + SQL + Tools)

🔗 **Code:** https://github.com/fidelisnguakaaga20/project-7-multi-tool-agent  
🎥 **Loom Demo:** https://www.loom.com/share/8c3cc7fedb7b463c9b60a12fec87bde0  
🎥 **YouTube Demo (Unlisted):** https://youtu.be/R5fbKYg5QjA  

---

## Overview

This project is a **local-first Multi-Tool AI Agent** built with **FastAPI**.  
The agent can **reason over documents (RAG)**, **query a database safely**, **use tools (calculator, web search)**, and **execute multi-step plans** while exposing full **tool traces and evaluation metrics**.

It is designed to reflect **real-world LLM engineering patterns**, not toy demos.

---

## Key Features

- 📄 **RAG (Retrieval-Augmented Generation)**
  - Upload PDFs / text files
  - Chunking + embeddings
  - Vector search with citations

- 🧮 **Calculator Tool**
  - Safe arithmetic evaluation
  - Deterministic routing

- 🗄️ **SQL Query Agent**
  - Read-only SQLite database
  - SELECT-only enforcement
  - Automatic safety validation
  - Table summaries returned

- 🌐 **Web Search Tool**
  - Lightweight local / cached search
  - Source-aware results

- 🧠 **Multi-Step Agent Planning**
  - Plans tool usage per request
  - Executes multiple tools sequentially
  - Returns one grounded answer

- 📊 **Observability & Evaluation**
  - Tool traces with latency
  - Automated evaluation harness
  - Accuracy reporting

---

## Example Prompts

calculate 19*23

Copy code
Show top 3 customers by total orders

Copy code
According to my documents, what is my professional summary?

Copy code
According to my documents, what is the policy?
Then calculate 12*19.
Also show top 3 customers by total orders.

markdown
Copy code

---

## API Endpoints

- `GET /health` — Health check
- `POST /agent/chat` — Main agent endpoint
- `POST /rag/index` — Index documents
- `POST /rag/query` — Query documents
- `POST /sql/query` — Debug SQL (SELECT-only)
- `POST /eval/run` — Run automated evaluation

Swagger UI:
http://127.0.0.1:8000/docs

yaml
Copy code

---

## Local Setup

### 1️⃣ Create virtual environment
```bash
python -m venv .venv
source .venv/Scripts/activate   # Windows (Git Bash)
2️⃣ Install dependencies
bash
Copy code
pip install -r requirements.txt
3️⃣ Seed database
bash
Copy code
cd backend
python -m app.db.seed
4️⃣ Run backend
bash
Copy code
python -m uvicorn app.main:app --reload
Evaluation
Run automated tests:

bash
Copy code
POST /eval/run
Example output:

json
Copy code
{
  "accuracy": 1.0,
  "passed": 4,
  "total": 4
}
Tech Stack
Python

FastAPI

SQLite

Chroma Vector DB

Sentence Transformers

Local-first tooling

No paid APIs

Why This Project Matters
This project demonstrates:

Real LLM agent design

Tool orchestration

Safety constraints

Observability

Evaluation-driven development

It reflects production thinking, not tutorial-level code.

Author
Nguakaaga Mvendaga
GitHub: https://github.com/fidelisnguakaaga20
LinkedIn: https://www.linkedin.com/in/nguakaaga-mvendaga