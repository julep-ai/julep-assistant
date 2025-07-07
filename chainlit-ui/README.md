# Julep Assistant Chainlit UI

An interactive chat interface for the Julep AI Assistant that helps developers with Julep platform questions, workflow development, and troubleshooting.

## Features

- **Interactive Chat**: Ask questions about Julep and get instant answers
- **RAG-Enabled**: Searches through indexed Julep documentation for accurate responses
- **Code Examples**: Get working examples in Python, YAML, and JavaScript
- **Workflow Assistance**: Help with writing and debugging Julep workflows
- **Real-time Streaming**: Responses stream in real-time for better UX
- **Feedback System**: Provide feedback on responses to improve the assistant over time

## Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your Julep API key
   ```

3. **Ensure the agent has indexed documentation**:
   - The agent should have been populated with Julep documentation using the crawler and indexer scripts
   - Check that documents exist: `client.agents.docs.list(agent_id=AGENT_UUID)`

## Running the Application

From the chainlit-ui directory:
```bash
chainlit run app.py -w
```

Or with specific host/port:
```bash
chainlit run app.py --host 0.0.0.0 --port 8000
```

The UI will be available at `http://localhost:8000`

## Usage

1. Open the UI in your browser
2. You'll see a welcome message explaining the assistant's capabilities
3. Type your question about Julep
4. The assistant will search through documentation and provide relevant answers
5. Code examples and workflow templates are available on request
6. Use the feedback buttons (👍/👎/💭) after each response to help improve the assistant

## Configuration Options

### Environment Variables

- `JULEP_API_KEY`: Your Julep API key (required)
- `JULEP_ENV`: Julep environment (`production` or `dev`)
- `AGENT_UUID`: The UUID of your Julep agent with indexed documentation

### RAG Search Parameters

The assistant uses these search parameters (configured in `app.py`):
- `mode`: "hybrid" - Uses both vector and text searches
- `confidence`: 0.7 - Confidence threshold for vector search
- `alpha`: 0.5 - Weight balance between vector and text search
- `mmr_strength`: 0.7 - Maximal Marginal Relevance for result diversity
- `limit`: 20 - Number of documents to retrieve

## Troubleshooting

1. **No response or errors**: Check that your JULEP_API_KEY is valid
2. **Empty responses**: Ensure the agent has indexed documentation
3. **Connection errors**: Verify the JULEP_ENV matches your API key environment
4. **Feedback not applying**: Check the logs - feedback must pass validation (confidence ≥ 0.7) to be applied

## Development

To modify the assistant behavior:
1. Edit `app.py` for main logic
2. Update `chainlit.md` for the welcome message
3. Adjust RAG parameters in the session creation