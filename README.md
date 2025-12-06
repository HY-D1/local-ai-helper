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
- Docker & Docker Compose
- NVIDIA GPU (optional, for faster inference)
- 8GB+ RAM

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/local-ai-helper.git
cd local-ai-helper

# Start services
docker-compose up -d

# Pull default model
docker exec -it ai-helper-ollama ollama pull llama3.2

# Access UI
# Navigate to http://localhost:8501
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

Edit `config/agent_configs.yaml` to customize:
- System prompts for each mode
- Temperature and generation parameters
- Memory retrieval settings
- Model preferences

## Key Technical Features

**For MSR Applications:**
- LLM-based agent orchestration with specialized modes
- RAG implementation using ChromaDB vector store
- Asynchronous API design with FastAPI
- Containerized microservices architecture
- Benchmarking framework for model comparison
- PostgreSQL for structured conversation storage
- Prompt engineering across multiple task domains

## Roadmap

- [ ] Multimodal support (image understanding via CLIP/BLIP)
- [ ] Voice input/output
- [ ] Plugin system for external tools
- [ ] Fine-tuning interface for custom models
- [ ] Collaborative features (shared conversations)

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

Project Link: https://github.com/yourusername/local-ai-helper

---

**Portfolio Project** | Demonstrates: LLM Agent Systems, RAG, Docker, Python, System Design