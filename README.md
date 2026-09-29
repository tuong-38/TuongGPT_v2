# 🚀 TuongGPT v2 - Full-Stack Multi-Tenant Agentic AI Platform

**TuongGPT v2** is an enterprise-ready, multi-tenant Agentic AI web platform built with **FastAPI**, **LangChain / LangGraph**, **Google Gemini 3.x**, and **Supabase (PostgreSQL + pgvector)**. The platform features end-to-end multimodal vision understanding, real-time web search with Tavily, secure JWT authentication, persistent multi-user session storage, and an automated CI/CD pipeline powered by GitHub Actions.

---

## 🌟 Key Features

* **🤖 Autonomous Agentic Workflow**: Dynamic task routing via LangGraph / ReAct agent, combining retrieval-augmented generation and automated web searches via the **Tavily Search API**.
* **👁️ Multimodal Vision Support**: Direct image upload and visual analysis (diagrams, math formulas, screenshots) powered by **Gemini 3.5 Flash-Lite** and **Gemini 3.6 Flash**.
* **🔐 Multi-Tenant Enterprise Security**:
  * Secure password hashing with **Bcrypt**.
  * Stateless token authentication via **JWT (JSON Web Tokens)**.
  * Strict multi-tenant isolation ensuring users access only their own sessions and data.
* **💾 Persistent Chat Storage (Supabase PostgreSQL)**:
  * Real-time persistence for conversation threads (`conversations`) and chat history (`chat_messages`).
  * Instant session restoring and context switching across devices.
  * Schema-ready support for user profiling and memory (`long_term_memory`).
* **🎨 Modern UI & Low-Latency Streaming**:
  * Token-by-token streaming via **Server-Sent Events (SSE)**.
  * Mathematical expression rendering using **KaTeX** and rich Markdown support.
* **⚙️ Automated CI/CD Pipeline**:
  * Static syntax linting and quality inspection with **Flake8**.
  * Automated Unit Testing with **Pytest** in isolated GitHub Actions runners.
  * Production deployment ready for **Render** and **Railway** via `Procfile`.

---

## 🛠️ Tech Stack & Dependencies

* **Backend Runtime**: Python 3.11, FastAPI, Uvicorn, SQLAlchemy, Pydantic v2
* **Agent Framework**: LangChain, LangGraph, LangSmith Tracing
* **LLM Engine**: Google Gemini API (`gemini-3.5-flash-lite`, `gemini-3.6-flash`, `gemini-3.7-flash`)
* **Embedding Model**: Google Generative AI (`gemini-embedding-001`)
* **Database**: PostgreSQL hosted on Supabase
* **Search Engine**: Tavily AI Search API
* **Frontend**: Vanilla HTML5, CSS3, JavaScript (ES6+), KaTeX, FontAwesome
* **DevOps & Testing**: Pytest, Flake8, GitHub Actions, Render Cloud

---

## 📁 Project Structure

```text
TuongGPT_v2/
├── .github/
│   └── workflows/
│       └── ci.yml               # Automated CI/CD pipeline configuration
├── static/                      # Static assets (CSS, JS)
├── templates/
│   └── index.html               # Frontend interface (Chat, Sidebar, Vision, KaTeX)
├── tests/
│   └── test_auth.py             # Unit tests for Authentication & JWT verification
├── uploads/                     # Temporary folder for file/image uploads (Git-ignored)
├── auth.py                      # Password hashing, token creation, and auth dependencies
├── database.py                  # SQLAlchemy models, session engine, and Supabase client
├── main.py                      # FastAPI application, REST endpoints, and SSE stream
├── rag.py                       # Document parsing, chunking, and embedding logic
├── Procfile                     # Cloud process file for Render / Railway deployment
├── requirements.txt             # Python production dependencies
├── .gitignore                   # Ignores environment variables, databases, and local artifacts
└── README.md                    # Project documentation