# 🚀 OpsPilot — AI Cloud Operations Copilot

OpsPilot is a production-grade AI-powered DevOps platform that provides real-time log intelligence, anomaly detection, incident management, and an AI chat copilot for cloud operations teams.

---

## ✨ Features

| Feature | Description |
|---|---|
| **Live Dashboard** | Real-time system health overview with charts for log trends, severity distribution, and service activity |
| **Log Intelligence** | Ingest, classify, and summarize logs using transformer models with rule-based fallback |
| **Anomaly Detection** | Statistical detection of metric spikes across CPU, memory, latency, and throughput |
| **Root Cause Analysis** | Correlates errors, metric anomalies, and system events to suggest probable root causes |
| **Incident Management** | Auto-generate and track incidents from critical log events with status lifecycle (OPEN → RESOLVED) |
| **AI Chat Copilot** | Conversational AI assistant for troubleshooting, self-healing suggestions, and operational Q&A |
| **System Metrics** | Per-service CPU, memory, latency, and error-rate metrics with historical charting |
| **Reports** | Downloadable operational reports (CSV/PDF) with summary statistics |
| **Monitoring** | Integrated Prometheus metrics endpoint + Grafana dashboard support |

---

## 🏗️ Tech Stack

**Backend**
- [FastAPI](https://fastapi.tiangolo.com/) — async API framework
- [SQLAlchemy](https://www.sqlalchemy.org/) — ORM (SQLite for local dev, PostgreSQL for production)
- [Pydantic](https://docs.pydantic.dev/) — data validation and settings

**AI / ML**
- [Hugging Face Transformers](https://huggingface.co/transformers/) — log classification & summarization
- [Sentence Transformers](https://www.sbert.net/) — semantic embeddings
- [FAISS](https://github.com/facebookresearch/faiss) — vector similarity search
- [scikit-learn](https://scikit-learn.org/) — anomaly detection

**Frontend**
- [Jinja2](https://jinja.palletsprojects.com/) — server-side templates
- [HTMX](https://htmx.org/) — dynamic partial page updates
- [TailwindCSS](https://tailwindcss.com/) — utility-first styling
- [Chart.js](https://www.chartjs.org/) — interactive dashboards

**Infrastructure**
- [Docker & Docker Compose](https://www.docker.com/) — containerized deployment
- [Prometheus](https://prometheus.io/) + [Grafana](https://grafana.com/) — observability stack
- [PostgreSQL](https://www.postgresql.org/) — production database

---

## 📁 Project Structure

```
OpsPilot/
├── app/
│   ├── main.py               # FastAPI app entry point & page routes
│   ├── config.py             # Settings (env vars, model names, DB URL)
│   ├── ai_engine/
│   │   ├── classifier.py     # Log classification (transformer + rule-based)
│   │   ├── summarizer.py     # Log summarization (BART)
│   │   ├── embeddings.py     # Semantic embeddings (Sentence-BERT)
│   │   ├── anomaly_detector.py  # Metric anomaly detection
│   │   └── root_cause.py     # Root cause analysis engine
│   ├── api/
│   │   ├── logs.py           # Log ingestion & retrieval endpoints
│   │   ├── incidents.py      # Incident CRUD endpoints
│   │   ├── chat.py           # AI chat/copilot endpoint
│   │   ├── metrics.py        # Metrics ingestion & retrieval
│   │   └── stats.py          # Dashboard statistics endpoints
│   ├── database/
│   │   ├── models.py         # SQLAlchemy ORM models
│   │   ├── crud.py           # Database operations
│   │   └── session.py        # Database session management
│   ├── templates/            # Jinja2 HTML templates
│   └── static/               # CSS, JS, assets
├── monitoring/
│   └── prometheus.yml        # Prometheus scrape configuration
├── vector_store/             # FAISS index persistence
├── docker-compose.yml        # Full stack (app + db + Prometheus + Grafana)
├── run.py                    # Local dev runner (no Docker required)
├── seed_data.py              # Sample data generator
├── requirements.txt          # Full dependencies (with AI models)
├── requirements-local.txt    # Lightweight dependencies for local dev
└── .env                      # Environment configuration
```

---

## ⚡ Quick Start

### Option 1 — Local (No Docker, SQLite)

The fastest way to run OpsPilot on your machine — no PostgreSQL or Docker needed.

**1. Clone & set up a virtual environment**
```bash
git clone https://github.com/your-org/opspilot.git
cd opspilot
python -m venv venv
venv\Scripts\activate      # Windows
# source venv/bin/activate  # macOS/Linux
```

**2. Install lightweight dependencies**
```bash
pip install -r requirements-local.txt
```

> For full AI features (log classification, summarization, semantic search), uncomment the optional packages in `requirements-local.txt` and re-install. ⚠️ This downloads ~2 GB of model weights.

**3. Configure environment**

The default `.env` is already set for local SQLite use:
```env
USE_SQLITE=true
SECRET_KEY=local-dev-secret-key-change-in-prod
DEBUG=true
```

**4. Seed sample data (optional)**
```bash
python seed_data.py
```

**5. Run the server**
```bash
python run.py
```

Open **http://localhost:8000** in your browser.

---

### Option 2 — Docker Compose (Full Stack)

Runs the app with PostgreSQL, Prometheus, and Grafana.

```bash
docker compose up --build
```

| Service | URL |
|---|---|
| OpsPilot App | http://localhost:8000 |
| Prometheus | http://localhost:9090 |
| Grafana | http://localhost:3000 |

---

## ⚙️ Environment Variables

| Variable | Default | Description |
|---|---|---|
| `USE_SQLITE` | `true` | Use SQLite instead of PostgreSQL |
| `POSTGRES_HOST` | `localhost` | PostgreSQL host |
| `POSTGRES_PORT` | `5432` | PostgreSQL port |
| `POSTGRES_USER` | `postgres` | PostgreSQL username |
| `POSTGRES_PASSWORD` | `postgres` | PostgreSQL password |
| `POSTGRES_DB` | `opspilot` | PostgreSQL database name |
| `SECRET_KEY` | *(required)* | JWT signing secret — **change in production** |
| `DEBUG` | `true` | Enable debug mode |

---

## 🔌 API Reference

The interactive API docs are available at **http://localhost:8000/docs** (Swagger UI) and **http://localhost:8000/redoc**.

### Key Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/logs` | Ingest a new log entry |
| `GET` | `/api/logs` | List logs (with filtering) |
| `GET` | `/api/incidents` | List all incidents |
| `POST` | `/api/incidents` | Create an incident |
| `PATCH` | `/api/incidents/{id}` | Update incident status |
| `POST` | `/api/chat` | Send a message to the AI copilot |
| `POST` | `/api/metrics` | Ingest service metrics |
| `GET` | `/api/metrics/{service_id}` | Get metrics for a service |
| `GET` | `/api/stats/dashboard` | Dashboard summary statistics |
| `GET` | `/metrics` | Prometheus scrape endpoint |

---

## 🤖 AI Engine

OpsPilot's AI engine is designed with graceful degradation — if heavy ML models aren't available, the system falls back to rule-based logic automatically.

| Module | Model | Fallback |
|---|---|---|
| Log Classifier | `cardiffnlp/twitter-roberta-base-sentiment-latest` | Keyword-based rules |
| Summarizer | `facebook/bart-large-cnn` | Extractive first-line summary |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` | TF-IDF vectors |
| Anomaly Detector | Statistical Z-score / IQR | Rule-based thresholds |
| Root Cause Analyzer | Correlation engine | Pattern matching |

---

## 📊 Pages

| Page | Route | Description |
|---|---|---|
| Dashboard | `/` | System health overview with live charts |
| Logs | `/logs` | Log explorer with filtering and severity scoring |
| Incidents | `/incidents` | Active incident tracker |
| AI Copilot | `/chat` | Conversational AI for troubleshooting |
| Metrics | `/metrics` | Per-service performance metrics |
| Reports | `/reports` | Operational reports and exports |

---

## 🧪 Running Tests

```bash
pytest
```

---

## 🛡️ Security Notes

- Change `SECRET_KEY` to a strong random value before deploying to production.
- Do not commit `.env` to version control — add it to `.gitignore`.
- The default PostgreSQL credentials are for development only.

---

## 📄 License

MIT — see [LICENSE](LICENSE) for details.
