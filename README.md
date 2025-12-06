# Local AI Helper with Memory

A containerized multi-mode AI assistant using open-source LLMs, featuring persistent memory and specialized task modes.

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

# Start all services
docker-compose up -d

# Wait ~30 seconds for services to initialize
sleep 30

# Open UI
open http://localhost:8501  # macOS
# or visit http://localhost:8501 in browser
```

### First Time Setup

1. **Download a Model** (in UI):
   - Open sidebar → "📦 Download Models"
   - Click "⬇️ Download" on Llama 3.2 (3B) - recommended
   - Wait 5-10 minutes (2GB download)

2. **Start Chatting**:
   - Select agent mode (💬 General, 🔢 Math, 💻 Code, etc.)
   - Type message and press Enter
   - Memory is enabled by default

### Verify Installation

```bash
# Run automated tests
./test_features.sh

# Should see:
# ✅ Pass (5/5 tests)
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

# Run app
streamlit run src/ui/streamlit_app.py
```

### Using Make Commands
```bash
make setup       # Initial setup
make start       # Start all services
make logs        # View logs
make test        # Run tests
make stop        # Stop services
```

### Running Tests
```bash
pytest tests/ -v
# Or with coverage
pytest tests/ --cov=src --cov-report=html
```

## Configuration

### Adjust Response Speed
In UI sidebar → "⚙️ Advanced":
- **Temperature**: 0.1 (focused) to 1.0 (creative)
- **Max Length**: 128 (fast) to 2048 (detailed)

Recommended for speed: Temperature 0.7, Length 512

### Agent Modes
- **💬 General**: Everyday questions
- **🔢 Math**: Step-by-step problem solving  
- **💻 Code**: Programming help, debugging
- **✍️ Writing**: Essays, emails, creative content
- **🎨 Design**: UI/UX guidance

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
Edit `docker-compose.yml` - comment out GPU section under `ollama:` service (lines with `deploy:`, `nvidia`, `gpu`)

### Memory not working
```bash
# Check ChromaDB
curl http://localhost:8001/api/v1/collections

# Should show "conversations" collection
```

### Slow responses
- Use smaller model (Llama 3.2 3B vs 8B)
- Reduce max_tokens in sidebar settings
- Ensure Docker has 4GB+ RAM allocated

## Development

### Local Setup (without Docker)
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Start Ollama separately
ollama serve

# Run components
uvicorn src.api.main:app --reload --port 8000
streamlit run src/ui/streamlit_app.py --server.port 8501
```

### Using Make Commands
```bash
make setup       # Initial setup
make start       # Start all services
make logs        # View logs
make test        # Run tests
make stop        # Stop services
make clean       # Remove containers & volumes
```

### Running Tests
```bash
./test_features.sh

# Or individual tests
pytest tests/ -v
```

## Performance Benchmarks

| Model | Size | Response Time | Memory | Quality |
|-------|------|--------------|--------|---------|
| Llama 3.2 3B | 2.0 GB | 1.5s | 3.2 GB | Good |
| Llama 3.2 8B | 4.7 GB | 3.2s | 6.2 GB | Excellent |
| Phi-3 Mini | 2.3 GB | 1.1s | 3.8 GB | Very Good |
| Mistral 7B | 4.1 GB | 2.8s | 5.9 GB | Excellent |

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