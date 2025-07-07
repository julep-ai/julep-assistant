# Julep Assistant

An intelligent AI support assistant built with the Julep platform to help developers understand and use Julep effectively. This project demonstrates best practices for building AI applications with Julep, including web crawling, document indexing, and conversational AI capabilities.

## Features

- **Intelligent Documentation Crawling**: Automatically crawls and indexes Julep documentation
- **RAG-powered Conversations**: Uses Retrieval-Augmented Generation for accurate, context-aware responses
- **Interactive Chat Interface**: Built with Chainlit for a smooth user experience
- **Feedback System**: Collects and validates user feedback for continuous improvement
- **Workflow Examples**: Demonstrates complex Julep workflows including web crawling and document processing

## Project Structure

```
julep-assistant/
├── agent.yaml              # Agent configuration (name, instructions, model)
├── task/                   # Julep task definitions
│   ├── main.yaml          # Main workflow task
│   ├── crawl.yaml         # Web crawling sub-task
│   └── full_task.yaml     # Complete task with all steps
├── scripts/               # Utility scripts
│   ├── crawler.py         # Standalone web crawler
│   └── indexer.py         # Document indexing utility
├── chainlit-ui/           # Web interface
│   ├── app.py            # Main Chainlit application
│   ├── feedback/         # Feedback handling system
│   └── requirements.txt  # Python dependencies
└── julep-assistant-notebook.ipynb  # Interactive notebook demo
```

## Prerequisites

- Python 3.8+
- Julep API key (get one at [platform.julep.ai](https://platform.julep.ai))
- Spider API key for web crawling

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/julep-assistant.git
cd julep-assistant
```

2. Install dependencies:
```bash
pip install -r chainlit-ui/requirements.txt
```

3. Set up environment variables:
```bash
# Create a .env file in the project root
cp .env.example .env

# Edit .env and add your API keys:
# JULEP_API_KEY=your_julep_api_key_here
# AGENT_UUID=ce7be83e-db8b-4ba9-808e-7cade6812e98  # Or create your own
# SPIDER_API_KEY=your_spider_api_key_here  # Optional, for web crawling
```

## Usage

### Running the Chat Interface

```bash
cd chainlit-ui
chainlit run app.py
```

This will start the web interface at `http://localhost:8000`

### Using the Jupyter Notebook

Open `julep-assistant-notebook.ipynb` to explore:
- Creating and configuring Julep agents
- Defining and executing tasks
- Setting up RAG-powered conversations
- Monitoring task executions

### Running Scripts Directly

**Web Crawler:**
```bash
python scripts/crawler.py --url https://docs.julep.ai --max-pages 100
```

**Document Indexer:**
```bash
python scripts/indexer.py
```

## How It Works

1. **Agent Configuration**: The assistant is configured with specific instructions and knowledge about Julep
2. **Document Indexing**: Crawls and indexes Julep documentation for RAG
3. **Hybrid Search**: Uses both vector and text search for optimal retrieval
4. **Contextual Responses**: Generates accurate answers based on retrieved documentation

## Key Components

### Agent (agent.yaml)
- Defines the assistant's personality, capabilities, and instructions
- Uses Claude Sonnet 3.5 model for high-quality responses

### Tasks (task/*.yaml)
- **main.yaml**: Entry point workflow
- **crawl.yaml**: Web crawling sub-task with Spider integration
- **full_task.yaml**: Complete workflow including crawling and indexing

### Chainlit UI
- Interactive chat interface
- Session management
- Feedback collection and validation
- Real-time streaming responses

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `JULEP_API_KEY` | Your Julep API key | Yes |
| `AGENT_UUID` | UUID for the Julep agent | No (uses default) |
| `JULEP_ENV` | Julep environment (production/development) | No (defaults to production) |
| `SPIDER_API_KEY` | Spider API key for web crawling | No (only for crawling tasks) |

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built with [Julep AI](https://julep.ai) - The platform for building stateful AI applications
- UI powered by [Chainlit](https://chainlit.io)
- Web crawling by [Spider](https://spider.cloud)

## Support

For questions about this project, please open an issue on GitHub.

For Julep-specific questions, visit the [Julep Documentation](https://docs.julep.ai) or join the [Julep Discord](https://discord.com/invite/JTSBGRZrzj).