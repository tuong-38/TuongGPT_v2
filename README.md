# TuongGPT v2

TuongGPT v2 is a FastAPI chat application with a LangGraph agent, Google Gemini, Tavily search, document retrieval, and PostgreSQL-backed conversations. The web interface is served from `templates/`.

## Features

- Chat responses streamed to the browser with Server-Sent Events (SSE).
- Gemini-powered chat and image understanding.
- Tavily web search and retrieval from uploaded documents.
- JWT authentication and conversation storage in PostgreSQL.
- Docker images for local runtime and CI checks.

## Requirements

- Docker with the Docker Compose plugin, or Python 3.11 and pip.
- A PostgreSQL database for application use.
- Google AI and Tavily API keys for AI and search features.

## Configure environment variables

Copy `.env.example` to `.env`, then replace its placeholder values with your own. In PowerShell:

```powershell
Copy-Item .env.example .env
```

In macOS/Linux:

```sh
cp .env.example .env
```

Set a long, random `JWT_SECRET_KEY`. `DATABASE_URL` must point to a PostgreSQL database. Keep `.env` private; it is excluded from Git and Docker build context. LangSmith settings are optional.

## Run with Docker Compose

Build and start the web application:

```sh
docker compose up --build -d web
```

Open [http://localhost:8000](http://localhost:8000). The health check is available at [http://localhost:8000/health](http://localhost:8000/health). Check service status and logs with:

```sh
docker compose ps
docker compose logs -f web
```

Stop the application with `docker compose down`.

Run the tests in the separate test image. This uses SQLite and a test-only JWT key; it does not need your PostgreSQL or API credentials:

```sh
docker compose run --rm test
```

## Run locally with Python

Create and activate a Python 3.11 virtual environment, then install dependencies:

```sh
python -m venv .venv
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

macOS/Linux:

```sh
source .venv/bin/activate
```

Install and start the app:

```sh
pip install -r requirements.txt
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Run tests separately with `pytest tests/` after installing pytest (`pip install pytest`).

## CI and deployment

GitHub Actions runs on pushes and pull requests targeting `main` or `master`. It builds both Docker targets, runs selected Flake8 error checks, and runs the tests in the test image. This workflow is continuous integration (CI); it does not publish an image or deploy the application. `Procfile` provides a start command for platforms that support that format; deployment must be configured separately on the chosen platform.

## Project structure

```text
.
├── .github/workflows/ci.yml  # Build and verification workflow
├── templates/index.html      # Web interface
├── tests/test_auth.py        # Authentication tests
├── main.py                   # FastAPI routes, including /health
├── auth.py                   # Password and JWT helpers
├── database.py               # SQLAlchemy models and database access
├── agent.py                  # LangGraph agent setup
├── rag.py                    # Document retrieval
├── Dockerfile                # Runtime and test build targets
├── docker-compose.yml        # Local web and test services
├── .dockerignore             # Files excluded from Docker build context
├── .env.example              # Environment variable template
└── Procfile                  # Platform process start command
```

## License

See [LICENSE](LICENSE).
