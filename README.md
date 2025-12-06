# Local AI Helper with Memory

A containerized multi-mode AI assistant built on open-source LLMs, featuring persistent memory and specialized task modes.

## Features

- **Multi-Mode Operation**: Specialized presets for math, writing, code, design, and general assistance
- **Persistent Memory**: RAG-based conversation retrieval using vector embeddings
- **Model Flexibility**: Switch between Llama 3, Phi-3, Mistral, and other open-source models
- **Local-First**: Fully offline capable, no API keys required
- **Docker Deployment**: Reproducible containerized environment

## Tech Stack

- **Backend**: Python 3.11, FastAPI
- **LLM Runtime**: Ollama
- **Frontend**: Streamlit
- **Vector Database**: ChromaDB
- **Storage**: PostgreSQL (conversation history), SQLite (metadata)
- **Containerization**: Docker, docker-compose
- **Version Control**: Git with feature branching

## Architecture

```
┌─────────────────┐
│   Streamlit UI  │
└────────┬────────┘
         │
┌────────▼───────────────────────┐
│      FastAPI Backend           │
│  ┌──────────┬──────────────┐   │
│  │  Agent   │   Memory     │   │
│  │ Manager  │   Manager    │   │
│  └────┬─────┴──────┬───────┘   │
└───────┼────────────┼───────────┘
        │            │
┌───────▼────┐  ┌────▼──────┐
│   Ollama   │  │ ChromaDB  │
│   (LLMs)   │  │ (Vectors) │
└────────────┘  └───────────┘
```

## Quick Start

### Prerequisites
- Docker Desktop (4.0+)
- 8GB+ RAM
- 10GB+ free disk space

### Installation

```bash
# Clone repository
git clone https://github.com/HY-D1/local-ai-helper.git
cd local-ai-helper

# Start all services (creates the required Docker network automatically)
docker-compose up -d

# Wait for containers to become healthy
docker-compose ps

# Open the UI
# macOS: open http://localhost:8501
# Others: visit http://localhost:8501 in your browser
```

### First-Time Setup in the UI
1. **Download a Model**: Sidebar → "📦 Download Models" → "⬇️ Download" on **Llama 3.2 (3B)** (recommended). Allow 5–10 minutes for the ~2GB download.
2. **Start Chatting**: Pick an agent mode (💬 General, 🔢 Math, 💻 Code, ✍️ Writing, 🎨 Design), type a message, and press Enter. Memory is on by default.

### Verify Installation

```bash
# Smoke test suite
./test_features.sh

# Expected output includes: ✅ Pass (5/5 tests)
```

## Project Structure

```
local-ai-helper/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── README.md
├── src/
│   ├── agents/
│   │   ├── base_agent.py
│   │   ├── math_agent.py
│   │   ├── code_agent.py
│   │   └── writing_agent.py
│   ├── memory/
│   │   ├── vector_store.py
│   │   └── conversation_db.py
│   ├── api/
│   │   └── main.py
│   └── ui/
│       └── streamlit_app.py
├── config/
│   └── agent_configs.yaml
└── tests/
    └── test_agents.py
```

## Usage

### Select Mode
Choose from preset modes:
- **Math Helper**: Step-by-step problem solving
- **Code Assistant**: Debug, explain, generate code
- **Writing Coach**: Essays, emails, creative writing
- **Design Advisor**: UI/UX suggestions, design principles

### Model Selection
Available models (auto-downloaded on first use):
- Llama 3.2 (3B/8B)
- Phi-3 Mini
- Mistral 7B
- CodeLlama 7B

### Memory Management
- Conversations automatically indexed for semantic search
- Retrieve relevant context from past sessions
- Export/import conversation history

## Development

### Local Setup (without Docker)
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Start Ollama separately
ollama serve

# Run the web UI
streamlit run src/ui/streamlit_app.py

# Or start the API directly
uvicorn src.api.main:app --reload --port 8000
```

### Using Make Commands
```bash
make setup       # Install Python deps locally
make start       # docker-compose up -d
make logs        # Tail container logs
make test        # pytest tests/ -v
make stop        # Stop containers
make clean       # Remove containers & volumes
```

### Running Tests
```bash
pytest tests/ -v

# With coverage report
pytest tests/ --cov=src --cov-report=html
```

## Troubleshooting

### Services won't start
```bash
# Check status
docker-compose ps

# View logs
docker-compose logs

# Restart all
docker-compose restart
```

### "GPU driver error" on Mac
Comment out the GPU block for the `ollama` service in `docker-compose.yml` (lines containing `deploy`, `nvidia`, and `gpu`).

### Memory not working
```bash
# Check ChromaDB
curl http://localhost:8001/api/v1/collections

# Should show "conversations" collection
```

### Slow responses
- Use a smaller model (Llama 3.2 3B vs 8B)
- Reduce `max_tokens` in sidebar settings
- Ensure Docker has 4GB+ RAM allocated

## Performance Benchmarks

| Model | Size | Response Time | Memory | Quality |
|-------|------|--------------|--------|---------|
| Llama 3.2 3B | 2.0 GB | ~1.5s | 3.2 GB | Good |
| Llama 3.2 8B | 4.7 GB | ~3.2s | 6.2 GB | Excellent |
| Phi-3 Mini | 2.3 GB | ~1.1s | 3.8 GB | Very Good |
| Mistral 7B | 4.1 GB | ~2.8s | 5.9 GB | Excellent |

*Tested on M1 Mac, 16GB RAM*

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## License

MIT License - see LICENSE file

## Contact

Harry Dai - [GitHub](https://github.com/HY-D1)

Project: https://github.com/HY-D1/local-ai-helper

---

**Portfolio Project** | Demonstrates: LLM Agent Systems, RAG, Docker, System Design, Async Python
