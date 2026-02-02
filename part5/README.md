# Part 5: Agentic RAG

Building on the Baseline RAG from Part 4, this module extends the chatbot with **agentic capabilities** - the ability to use tools, make decisions, and take actions.

## What's Different from Part 4?

| Aspect | Part 4 (Baseline RAG) | Part 5 (Agentic RAG) |
|--------|----------------------|---------------------|
| Knowledge Source | Static KB only | KB + APIs + Databases |
| Capabilities | Answer questions | Answer + Take actions |
| Decision Making | None | Chooses tools dynamically |
| Multi-step | Single retrieve-generate | Loop until solved |
| Real-time Data | No | Yes (via tools) |

## Notebooks

1. **01_agentic_rag_concepts.ipynb** - Theory and motivation
   - Where baseline RAG fails
   - What makes RAG "agentic"
   - The ReAct pattern (Reason + Act)

2. **02_building_tools.ipynb** - Creating tools
   - Tool schemas (OpenAI function calling)
   - Mock tools for demo
   - Tool registry

3. **03_react_agent.ipynb** - Implementing the agent loop
   - ReAct agent implementation
   - Tool selection and execution
   - Multi-step reasoning

4. **04_agentic_chatbot.ipynb** - Complete agentic chatbot
   - Full integration
   - Comparison with baseline
   - Edge cases and error handling

5. **05_langgraph_agent.ipynb** - Same agent using LangGraph framework
   - LangGraph concepts (State, Nodes, Edges)
   - Comparison: Manual vs LangGraph
   - Memory with checkpointing
   - Streaming responses

## Tools Implemented

| Tool | Description |
|------|-------------|
| `search_knowledge_base` | Search FAQ/policies (real Bedrock KB) |
| `check_order_status` | Look up order status (mock) |
| `get_weather_alerts` | Check weather for shipping delays (mock) |
| `check_inventory` | Check product availability (mock) |
| `create_return_request` | Create a return ticket (mock) |

## Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your credentials
```

## Prerequisites

- Completed Part 4 (Baseline RAG)
- AWS credentials with Bedrock access
- OpenAI API key
- Knowledge Base ID from Part 4

## Architecture

```
User Query
    |
    v
+---------------------------+
|       AGENT LOOP          |
|  +---------------------+  |
|  |     REASONING       |  |
|  | What tool to use?   |  |
|  +----------+----------+  |
|             |             |
|             v             |
|  +---------------------+  |
|  |   TOOL SELECTION    |  |
|  | [KB] [Order] [Wthr] |  |
|  +----------+----------+  |
|             |             |
|             v             |
|  +---------------------+  |
|  |    OBSERVATION      |  |
|  | Process results     |  |
|  +---------------------+  |
+-------------+-------------+
              |
              v
         Response
```

## Example: Agentic RAG in Action

**User:** "What's the status of order #12345 and will it be delayed due to weather?"

**Baseline RAG would say:**
> "To check your order status, go to your account dashboard..."

**Agentic RAG does:**
1. Calls `check_order_status("ORD-12345")` → Gets shipping info
2. Calls `get_weather_alerts("New York")` → Checks weather
3. Combines results into personalized answer

**Response:**
> "Your order #12345 was shipped via FedEx and is expected to arrive Feb 3rd. Weather conditions in New York are clear, so no delays are expected."
