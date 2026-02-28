# Local AI Helper

A containerized multi-mode AI assistant that provides persistent memory and specialized task modes for developers and power users using FastAPI, Ollama, Streamlit, ChromaDB, and PostgreSQL.

## Demo

![Demo](docs/demo.gif)

## Features

### Implemented (v1.0)

- Multi-Mode Operation: Specialized agents for math, writing, code, design, and general assistance
- Persistent Memory: RAG-based conversation retrieval using vector embeddings (ChromaDB)
- Model Flexibility: Support for Llama 3, Phi-3, Mistral, CodeLlama, and Qwen models
- Web UI: Streamlit-based interface with real-time streaming responses
- Tool System: Calculator, unit converter, and code executor tools
- Conversation History: PostgreSQL storage for message persistence

### Planned (v2.0)

- Hybrid Search: BM25 + vector search for improved retrieval
- Context Compression: Automatic conversation summarization for long sessions
- Multi-user Support: User authentication and session isolation
- Custom Tool Builder: User-defined tools via configuration

## Architecture

The system uses a multi-service architecture: Streamlit UI proxies requests to FastAPI backend. The backend routes to specialized agents that coordinate with Ollama for LLM inference, ChromaDB for vector storage, and PostgreSQL for conversation persistence.

```mermaid
graph LR
    A[Streamlit UI<br/>Port 8501] -->|HTTP| B[FastAPI Backend<br/>Port 8000]
    B -->|Generate| C[Ollama<br/>Port 11434]
    B -->|Query/Store| D[ChromaDB<br/>Port 8001]
    B -->|CRUD| E[PostgreSQL<br/>Port 5432]
```

## Setup

### Prerequisites

- Docker Desktop 4.0+
- 8GB+ RAM
- 10GB+ free disk space

### Quick Start

```bash
# Clone and start
git clone https://github.com/HY-D1/local-ai-helper.git
cd local-ai-helper
./start.sh

# Or without auto-opening browser
./start.sh --no-browser
```

Access UI at `http://localhost:8501`

### Run Tests

```bash
# Smoke tests (5 feature checks)
./test_features.sh

# Unit and integration tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=src --cov-report=html
```

### Configuration

Environment variables (see `.env.example`):

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection | `postgresql://aihelper:aihelper123@postgres:5432/aihelper` |
| `CHROMADB_HOST` | ChromaDB hostname | `chromadb` |
| `CHROMADB_PORT` | ChromaDB port | `8000` |
| `OLLAMA_HOST` | Ollama API URL | `http://ollama:11434` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `SKIP_MODEL_VALIDATION` | Skip model checks (for testing) | `0` |

Agent configuration in `config/agent_configs.yaml`.

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/chat` | POST | Chat completion with streaming |
| `/api/v1/chat/history/{session_id}` | GET | Retrieve session messages |
| `/api/v1/sessions` | GET | List all sessions |
| `/api/v1/sessions/{session_id}` | DELETE | Delete a session |
| `/api/v1/memory/search` | POST | Semantic search in memory |
| `/api/v1/models` | GET | List available models |
| `/api/v1/models/pull` | POST | Download a model |
| `/health` | GET | Health check |

**Example: Chat Request**
```json
{
  "message": "What is the derivative of x^2?",
  "session_id": "sess-123",
  "mode": "math",
  "model": "qwen2.5:7b"
}
```

**Example: Chat Response (streaming)**
```json
{
  "content": "The derivative of x^2 is 2x.",
  "done": true,
  "session_id": "sess-123"
}
```

## Data Model / Schema

PostgreSQL tables:

**conversations**
- `id` (UUID, PK)
- `session_id` (TEXT)
- `user_message` (TEXT)
- `assistant_message` (TEXT)
- `agent_mode` (TEXT)
- `model_used` (TEXT)
- `created_at` (TIMESTAMP)
- `metadata` (JSONB)

**sessions**
- `id` (UUID, PK)
- `session_id` (TEXT, UNIQUE)
- `title` (TEXT)
- `agent_mode` (TEXT)
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

**user_preferences**
- `id` (UUID, PK)
- `user_id` (TEXT)
- `default_model` (TEXT)
- `default_mode` (TEXT)
- `preferences` (JSONB)

ChromaDB collections:
- `conversations` - Vector embeddings of messages for semantic search

## Trade-offs & Design Decisions

**Chose:** Local LLMs via Ollama
- **Gave up:** Cloud API access (OpenAI, Claude)
- **Why:** Fully offline capable, no API keys required, no usage costs, data privacy

**Chose:** ChromaDB for vector storage
- **Gave up:** Pinecone, Weaviate, or hosted vector DBs
- **Why:** Simple deployment in Docker, no external dependencies, sufficient for single-user/small-scale use

**Chose:** FastAPI + Streamlit split architecture
- **Gave up:** Single monolithic Streamlit app
- **Why:** Clean API/frontend separation, enables headless API usage, easier testing, supports future alternative frontends

## Limitations

- Requires Docker for full functionality; local dev setup needs manual Ollama
- First model download takes 5-10 minutes (~2GB)
- No built-in user authentication (single-user deployment)
- GPU acceleration requires NVIDIA Docker setup (CPU fallback available)
- Context window limited by model capabilities (typically 4K-8K tokens)
- No multi-modal support (text-only)

## Next Steps

- [ ] Implement hybrid search (BM25 + vector) for better retrieval accuracy
- [ ] Add context compression for long conversation handling
- [ ] Build user authentication and multi-tenant session isolation
- [ ] Create custom tool builder UI
- [ ] Add export/import for conversation history
- [ ] Support for function calling with external APIs
