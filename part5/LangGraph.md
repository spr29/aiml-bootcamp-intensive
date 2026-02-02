# LangGraph Concepts: State, Nodes, and Edges

## Overview

LangGraph models your agent as a **graph** where:
- **State** = Data flowing through the graph
- **Nodes** = Functions that process/transform the data
- **Edges** = Connections that define flow between nodes

```
+------------------------------------------------------------------+
|                         LANGGRAPH                                 |
|                                                                   |
|    STATE (data)  flows through  NODES (functions)                |
|                  connected by   EDGES (flow control)              |
|                                                                   |
+------------------------------------------------------------------+
```

---

## 1. STATE: The Data Container

### What is State?

State is a **TypedDict** that holds ALL data flowing through your graph.

```python
from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]   # Conversation history
    user_name: str                             # User's name
    order_id: str                              # Current order being discussed
```

### Think of State as a Shared Notebook

```
+------------------------------------------------------------------+
|                          STATE                                    |
|                    (Shared Data Container)                        |
+------------------------------------------------------------------+
|                                                                   |
|  messages: [                                                      |
|    {role: "user", content: "Check my order"},                    |
|    {role: "assistant", content: "Your order shipped..."}         |
|  ]                                                                |
|                                                                   |
|  user_name: "Sarah"                                               |
|                                                                   |
|  order_id: "ORD-12345"                                           |
|                                                                   |
+------------------------------------------------------------------+
        |                    |                    |
        v                    v                    v
   [Node 1]             [Node 2]             [Node 3]
   can read             can read             can read
   and update           and update           and update
```

### How State Updates Work

Nodes return **partial updates** that get merged into the state:

```python
# Current state
state = {
    "messages": [msg1, msg2],
    "user_name": "Sarah"
}

# Node returns update
return {"messages": [msg3]}   # Only updating messages

# Result: messages are MERGED (because of add_messages reducer)
state = {
    "messages": [msg1, msg2, msg3],   # msg3 added!
    "user_name": "Sarah"               # unchanged
}
```

### Reducers: How Updates Merge

```python
class AgentState(TypedDict):
    # WITH reducer: new values are APPENDED
    messages: Annotated[list, add_messages]

    # WITHOUT reducer: new values REPLACE
    current_step: str
```

```
WITH REDUCER (add_messages):
+----------------+     +----------------+     +--------------------+
| messages: [A]  | --> | return [B]     | --> | messages: [A, B]   |
+----------------+     +----------------+     +--------------------+
                         (B is ADDED)

WITHOUT REDUCER:
+----------------+     +----------------+     +--------------------+
| step: "start"  | --> | return "end"   | --> | step: "end"        |
+----------------+     +----------------+     +--------------------+
                         (value REPLACED)
```

---

## 2. NODES: The Processing Functions

### What is a Node?

A node is a **function** that:
1. Takes the current state
2. Does some processing
3. Returns state updates

```python
def my_node(state: AgentState) -> AgentState:
    # Read from state
    messages = state["messages"]

    # Do something
    result = process(messages)

    # Return updates
    return {"messages": [result]}
```

### Types of Nodes

```
+------------------------------------------------------------------+
|                         NODE TYPES                                |
+------------------------------------------------------------------+

1. AGENT NODE (calls LLM)
+---------------------------+
|        agent_node         |
|---------------------------|
| - Reads messages          |
| - Calls LLM               |
| - Returns LLM response    |
+---------------------------+

2. TOOL NODE (executes tools)
+---------------------------+
|        tool_node          |
|---------------------------|
| - Reads tool_calls        |
| - Executes functions      |
| - Returns tool results    |
+---------------------------+

3. CUSTOM NODE (your logic)
+---------------------------+
|       custom_node         |
|---------------------------|
| - Any custom processing   |
| - Data transformation     |
| - External API calls      |
+---------------------------+
```

### Agent Node Example

```python
def agent_node(state: AgentState) -> AgentState:
    """
    The AGENT node - calls LLM to decide what to do
    """
    # Get current messages
    messages = state["messages"]

    # Add system prompt if not present
    if not any(isinstance(m, SystemMessage) for m in messages):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages

    # Call LLM with tools
    response = llm_with_tools.invoke(messages)

    # Return the response (will be added to messages)
    return {"messages": [response]}
```

```
+------------------------------------------------------------------+
|                        AGENT NODE                                 |
+------------------------------------------------------------------+
|                                                                   |
|  INPUT STATE:                                                     |
|  {                                                                |
|    messages: [user_message]                                       |
|  }                                                                |
|                                                                   |
|  PROCESSING:                                                      |
|  1. Read messages from state                                      |
|  2. Add system prompt                                             |
|  3. Call LLM with tools                                           |
|  4. Get response (might have tool_calls)                          |
|                                                                   |
|  OUTPUT:                                                          |
|  {                                                                |
|    messages: [llm_response]   <-- added to state                  |
|  }                                                                |
|                                                                   |
+------------------------------------------------------------------+
```

### Tool Node (Pre-built)

```python
from langgraph.prebuilt import ToolNode

# One line! LangGraph provides this
tool_node = ToolNode(tools)
```

```
+------------------------------------------------------------------+
|                        TOOL NODE                                  |
+------------------------------------------------------------------+
|                                                                   |
|  INPUT STATE:                                                     |
|  {                                                                |
|    messages: [..., assistant_msg_with_tool_calls]                |
|  }                                                                |
|                                                                   |
|  PROCESSING (automatic):                                          |
|  1. Read last message                                             |
|  2. Extract tool_calls                                            |
|  3. Execute each tool function                                    |
|  4. Collect results                                               |
|                                                                   |
|  OUTPUT:                                                          |
|  {                                                                |
|    messages: [tool_result_1, tool_result_2, ...]                 |
|  }                                                                |
|                                                                   |
+------------------------------------------------------------------+
```

---

## 3. EDGES: The Flow Control

### What is an Edge?

An edge defines **how nodes connect** - which node runs after which.

### Types of Edges

```
+------------------------------------------------------------------+
|                         EDGE TYPES                                |
+------------------------------------------------------------------+

1. NORMAL EDGE: Always go from A to B

   [Node A] -----------------> [Node B]

   graph.add_edge("node_a", "node_b")


2. CONDITIONAL EDGE: Choose path based on condition

   [Node A] ----> {condition?} ----> [Node B]
                       |
                       +-----------> [Node C]

   graph.add_conditional_edges("node_a", router_function, {
       "go_to_b": "node_b",
       "go_to_c": "node_c"
   })


3. ENTRY EDGE: Where the graph starts

   START -----------------> [First Node]

   graph.set_entry_point("first_node")
```

### Normal Edge

```python
# After tools node, ALWAYS go back to agent
graph.add_edge("tools", "agent")
```

```
+--------+                      +--------+
| tools  | -------------------> | agent  |
+--------+   (always)           +--------+
```

### Conditional Edge

```python
def should_continue(state: AgentState) -> str:
    """Router function - decides where to go next"""
    last_message = state["messages"][-1]

    # If LLM wants to use tools, go to tools node
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"

    # Otherwise, we're done
    return END

# Add the conditional edge
graph.add_conditional_edges(
    "agent",                    # From this node
    should_continue,            # Use this function to decide
    {
        "tools": "tools",       # If function returns "tools" -> go to tools
        END: END                # If function returns END -> finish
    }
)
```

```
                    +------------------+
                    |      agent       |
                    +------------------+
                            |
                            v
                    +------------------+
                    | should_continue? |
                    +------------------+
                      /            \
                     /              \
              "tools"                END
                   /                  \
                  v                    v
          +--------+              +--------+
          | tools  |              |  END   |
          +--------+              +--------+
```

---

## Complete Graph Example

### Building the Graph

```python
from langgraph.graph import StateGraph, END

# 1. Create graph with state type
workflow = StateGraph(AgentState)

# 2. Add nodes
workflow.add_node("agent", agent_node)
workflow.add_node("tools", tool_node)

# 3. Set entry point
workflow.set_entry_point("agent")

# 4. Add edges
workflow.add_conditional_edges("agent", should_continue, {
    "tools": "tools",
    END: END
})
workflow.add_edge("tools", "agent")

# 5. Compile
app = workflow.compile()
```

### Visual Representation

```
+==============================================================================+
|                              COMPLETE GRAPH                                   |
+==============================================================================+

                              START
                                |
                                | (entry point)
                                v
                        +---------------+
                        |     agent     |
                        |---------------|
                        | - Call LLM    |
                        | - Get response|
                        +---------------+
                                |
                                v
                      +-------------------+
                      | should_continue?  |
                      +-------------------+
                         /           \
                        /             \
                 has tool_calls?    no tool_calls
                      /                 \
                     v                   v
              +---------------+      +-------+
              |     tools     |      |  END  |
              |---------------|      +-------+
              | - Execute     |
              |   tool calls  |
              | - Return      |
              |   results     |
              +---------------+
                     |
                     | (always)
                     |
                     +-------------------> back to agent
```

---

## State Flow Through the Graph

### Example: "What is the status of order ORD-12345?"

```
STEP 1: START
+------------------------------------------------------------------+
| State: {messages: [HumanMessage("What is the status...")]}       |
+------------------------------------------------------------------+
                                |
                                v

STEP 2: AGENT NODE
+------------------------------------------------------------------+
| - Reads messages                                                  |
| - Calls LLM with tools                                           |
| - LLM returns: tool_calls=[check_order_status(order_id=...)]     |
| - Returns: {messages: [AIMessage with tool_calls]}               |
+------------------------------------------------------------------+
| State: {messages: [HumanMessage, AIMessage(tool_calls)]}         |
+------------------------------------------------------------------+
                                |
                                v

STEP 3: SHOULD_CONTINUE?
+------------------------------------------------------------------+
| - Checks last message                                             |
| - Has tool_calls? YES                                            |
| - Returns: "tools"                                               |
+------------------------------------------------------------------+
                                |
                                v

STEP 4: TOOLS NODE
+------------------------------------------------------------------+
| - Reads tool_calls from last message                             |
| - Executes: check_order_status("ORD-12345")                      |
| - Gets result: {status: "shipped", carrier: "FedEx"}             |
| - Returns: {messages: [ToolMessage(result)]}                     |
+------------------------------------------------------------------+
| State: {messages: [HumanMessage, AIMessage, ToolMessage]}        |
+------------------------------------------------------------------+
                                |
                                v

STEP 5: AGENT NODE (again)
+------------------------------------------------------------------+
| - Reads all messages (including tool result)                     |
| - Calls LLM                                                       |
| - LLM generates response: "Your order shipped via FedEx..."      |
| - Returns: {messages: [AIMessage(content)]}                      |
+------------------------------------------------------------------+
| State: {messages: [Human, AI(tools), Tool, AI(response)]}        |
+------------------------------------------------------------------+
                                |
                                v

STEP 6: SHOULD_CONTINUE?
+------------------------------------------------------------------+
| - Checks last message                                             |
| - Has tool_calls? NO                                             |
| - Returns: END                                                   |
+------------------------------------------------------------------+
                                |
                                v

STEP 7: END
+------------------------------------------------------------------+
| Final State: {messages: [all 4 messages]}                        |
| Response: "Your order shipped via FedEx..."                      |
+------------------------------------------------------------------+
```

---

## Summary Table

| Concept | What It Is | Example |
|---------|------------|---------|
| **State** | Shared data container | `{messages: [...], user_name: "Sarah"}` |
| **Node** | Function that processes state | `agent_node`, `tool_node` |
| **Edge** | Connection between nodes | `add_edge("tools", "agent")` |
| **Normal Edge** | Always go A -> B | After tools, go to agent |
| **Conditional Edge** | Choose path based on condition | Has tool_calls? Go to tools. Else END |
| **Entry Point** | Where graph starts | `set_entry_point("agent")` |
| **END** | Special node that finishes | `return END` from router |
| **Reducer** | How state updates merge | `add_messages` appends to list |

---

## Key Takeaways

1. **State** is the shared memory - all nodes read from and write to it

2. **Nodes** are functions that transform state - they do the actual work

3. **Edges** control flow - they decide which node runs next

4. **Conditional edges** enable branching - like if/else for graphs

5. **Reducers** control merging - `add_messages` appends, no reducer replaces

6. **The graph compiles** into a runnable app - `app.invoke(initial_state)`
