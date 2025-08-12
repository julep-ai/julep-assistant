import chainlit as cl
from julep import AsyncJulep
import os
import dotenv
import uuid
from feedback import FeedbackHandler

dotenv.load_dotenv(override=True)

# Configuration
JULEP_API_KEY = os.getenv("JULEP_API_KEY")
AGENT_UUID = os.getenv("AGENT_UUID", "ce7be83e-db8b-4ba9-808e-7cade6812e98")
JULEP_ENV = os.getenv("JULEP_ENV", "production")

# Initialize Julep client
julep_client = AsyncJulep(api_key=JULEP_API_KEY, environment=JULEP_ENV)

# Initialize feedback handler
feedback_handler = None

# Store sessions per user
user_sessions = {}

@cl.on_chat_start
async def on_chat_start():
    """Initialize a new chat session"""
    # Welcome message
    await cl.Message(
        content="""**Welcome to Julep AI Assistant!**

This assistant demonstrates how to build an intelligent documentation helper using Julep's powerful features. It showcases:

• **RAG (Retrieval-Augmented Generation)**: Searches through Julep's documentation to provide accurate, context-aware answers
• **Self-Improving Feedback Loop**: The agent learns from your feedback, updating its knowledge base to provide better answers over time
• **Stateful Sessions**: Maintains conversation context across interactions
• **Intelligent Hybrid Search**: Combines vector embeddings with text search for optimal document retrieval

**📚 Resources:**
- [View the source code on GitHub](https://github.com/julep-ai/julep-assistant)
- [Follow the tutorial in our docs](https://docs.julep.ai/tutorials/julep-assistant)

**How I can help you:**
- Writing and debugging Julep workflows
- Understanding Julep concepts (agents, tasks, sessions, tools, etc.)
- Providing code examples
- Explaining API usage and best practices
- Troubleshooting and optimization tips

💡 **Tip**: Use the feedback buttons (👍/👎) on my responses to help me improve!

"""
    ).send()
    
    # Create a new session for this user
    session_id = str(uuid.uuid4())
    
    # Create session with search options
    session = await julep_client.sessions.create(
        agent=AGENT_UUID,
        # RAG search options
        recall_options={
            "mode": "hybrid",  # Uses both vector and text searches
            "confidence": 0.7,  # Confidence threshold for the vector search
            "alpha": 0.5,  # Weight of priority of the vector search (0-1)
            "mmr_strength": 0.7,  # Maximal Marginal Relevance strength
            "limit": 15,  # Number of documents to return
        }
    )
    
    # Store session in user session dict
    cl.user_session.set("session_id", session.id)
    cl.user_session.set("julep_client", julep_client)
    
    # Initialize feedback handler
    global feedback_handler
    if not feedback_handler:
        feedback_handler = FeedbackHandler(julep_client, AGENT_UUID)
    
    cl.user_session.set("feedback_handler", feedback_handler)
    
    # Create and send actions
    actions = [
        cl.Action(
            name="show_workflow_example",
            payload={"type": "workflow"},
            description="Show a workflow example",
            label="Show Workflow Example"
        ),
        cl.Action(
            name="show_agent_example", 
            payload={"type": "agent"},
            description="Show an agent creation example",
            label="Show Agent Example"
        )
    ]
    
    # Send initial status with actions
    await cl.Message(
        content=f"**You can ask me anything about Julep!**\n\nOr use the quick actions below:",
        author="System",
        actions=actions
    ).send()

@cl.on_message
async def on_message(message: cl.Message):
    """Handle incoming messages"""
    # Get session ID from user session
    session_id = cl.user_session.get("session_id")
    julep_client = cl.user_session.get("julep_client")
    
    if not session_id:
        await cl.Message(
            content="Session not found. Please refresh the page to start a new session.",
            author="System"
        ).send()
        return
    
    # Send typing indicator
    msg = cl.Message(content="", author="Julep Assistant")
    await msg.send()
    
    try:
        # Stream the response from Julep
        stream = await julep_client.sessions.chat(
            session_id=session_id,
            messages=[
                {
                    "role": "user",
                    "content": message.content
                }
            ],
            recall=True,  # Enable RAG search
            model="claude-sonnet-4",  # Use the model from agent config
            stream=True
        )
        
        # Stream the response
        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                await msg.stream_token(chunk.choices[0].delta.content)
        
        # Update the final message
        await msg.update()
        
        # Store the Q&A pair for feedback
        cl.user_session.set("last_question", message.content)
        cl.user_session.set("last_response", msg.content)
        
        # Add feedback actions to the response
        feedback_handler = cl.user_session.get("feedback_handler")
        if feedback_handler:
            feedback_actions = feedback_handler.create_feedback_actions(msg.id)
            msg.actions = feedback_actions
            await msg.update()
        
        # If documents were used, show them
        if hasattr(stream, 'docs') and stream.docs:
            docs_info = f"\n\n📚 **Referenced {len(stream.docs)} documentation sources**"
            await cl.Message(
                content=docs_info,
                author="System"
            ).send()
            
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        await cl.Message(
            content=error_msg,
            author="System"
        ).send()

@cl.on_chat_end
async def on_chat_end():
    """Clean up when chat ends"""
    session_id = cl.user_session.get("session_id")
    if session_id:
        # Optionally delete the session
        await julep_client.sessions.delete(session_id=session_id)
        # pass

# Custom actions for common tasks
@cl.action_callback("show_workflow_example")
async def show_workflow_example(action):
    """Show a workflow example"""
    example = """```yaml
name: Example Workflow
description: A simple workflow that demonstrates Julep capabilities

input_schema:
  type: object
  properties:
    message:
      type: string
  required:
    - message

tools:
- name: web_search
  type: integration
  integration:
    provider: web_search

main:
- prompt: Process the user message: {{_['message']}}
- tool: web_search
  arguments:
    query: {{_['message']}}
- prompt: Summarize the search results
```"""
    
    await cl.Message(content=example).send()

@cl.action_callback("show_agent_example")
async def show_agent_example(action):
    """Show an agent creation example"""
    example = """```python
from julep import Julep

client = Julep(api_key="your-api-key")

# Create an agent
agent = client.agents.create(
    name="My Assistant",
    about="A helpful AI assistant",
    instructions="You are a helpful assistant that answers questions clearly and concisely.",
    model="claude-sonnet-4",
    tools=[
        {
            "name": "web_search",
            "type": "integration",
            "integration": {
                "provider": "web_search"
            }
        }
    ]
)

print(f"Agent created with ID: {agent.id}")
```"""
    
    await cl.Message(content=example).send()

# Feedback action callbacks
@cl.action_callback("feedback_helpful")
async def feedback_helpful(action):
    """Handle positive feedback"""
    feedback_handler = cl.user_session.get("feedback_handler")
    last_question = cl.user_session.get("last_question")
    last_response = cl.user_session.get("last_response")
    
    if feedback_handler and last_question and last_response:
        await feedback_handler.handle_feedback_action(
            action, 
            last_question, 
            last_response
        )

@cl.action_callback("feedback_not_helpful")
async def feedback_not_helpful(action):
    """Handle negative feedback"""
    feedback_handler = cl.user_session.get("feedback_handler")
    last_question = cl.user_session.get("last_question")
    last_response = cl.user_session.get("last_response")
    
    if feedback_handler and last_question and last_response:
        await feedback_handler.handle_feedback_action(
            action,
            last_question,
            last_response
        )

@cl.action_callback("feedback_detailed")
async def feedback_detailed(action):
    """Handle detailed feedback request"""
    feedback_handler = cl.user_session.get("feedback_handler")
    last_question = cl.user_session.get("last_question")
    last_response = cl.user_session.get("last_response")
    
    if feedback_handler and last_question and last_response:
        await feedback_handler.handle_feedback_action(
            action,
            last_question,
            last_response
        )