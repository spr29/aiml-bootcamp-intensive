# The ReAct Loop: Reasoning + Acting

## What is ReAct?

**ReAct** (Reasoning and Acting) is a paradigm for building AI agents that interleave:
- **Reasoning** - Thinking about what to do
- **Acting** - Executing tools/actions
- **Observing** - Processing results

This creates an iterative loop until the agent has enough information to respond.

---

## The ReAct Loop Diagram

```
                                    USER QUERY
                                        |
                                        v
                    +-------------------------------------------+
                    |                                           |
                    |              AGENT (LLM)                  |
                    |                                           |
                    |   "I need to check the order status"      |
                    |                                           |
                    +-------------------------------------------+
                                        |
                                        v
                              +------------------+
                              |     REASON       |
                              |                  |
                              | What tool do I   |
                              | need to answer   |
                              | this question?   |
                              +------------------+
                                        |
                                        v
                              +------------------+
                              |      ACT         |
                              |                  |
                              | Call tool:       |
                              | check_order_     |
                              | status("ORD-123")|
                              +------------------+
                                        |
                                        v
                              +------------------+
                              |    OBSERVE       |
                              |                  |
                              | Result:          |
                              | {status: shipped |
                              |  carrier: FedEx} |
                              +------------------+
                                        |
                                        v
                              +------------------+
                              | ENOUGH INFO?     |
                              +------------------+
                                   /        \
                                  /          \
                                 v            v
                              YES            NO
                               |              |
                               v              |
                    +------------------+      |
                    |    RESPOND       |      |
                    |                  |      |
                    | "Your order has  |      |
                    |  shipped via     |      |
                    |  FedEx..."       |      |
                    +------------------+      |
                               |              |
                               v              +-----> Back to REASON
                          FINAL RESPONSE
```

---

## Detailed Flow Diagram

```
+==============================================================================+
|                              ReAct AGENT LOOP                                 |
+==============================================================================+

    START
      |
      v
+-----------------------------------------------------------------------------+
|  STEP 1: RECEIVE QUERY                                                       |
|  User asks: "What is the status of my order #ORD-12345?"                    |
+-----------------------------------------------------------------------------+
      |
      v
+-----------------------------------------------------------------------------+
|  STEP 2: REASON (LLM thinks)                                                 |
|  "The user wants order status. I have a check_order_status tool.            |
|   I should use it with order_id = ORD-12345"                                |
+-----------------------------------------------------------------------------+
      |
      v
+-----------------------------------------------------------------------------+
|  STEP 3: ACT (Execute tool)                                                  |
|  Tool Call: check_order_status(order_id="ORD-12345")                        |
|  Execution: Your code runs the function                                      |
+-----------------------------------------------------------------------------+
      |
      v
+-----------------------------------------------------------------------------+
|  STEP 4: OBSERVE (Get result)                                                |
|  Result: {                                                                   |
|    "success": true,                                                          |
|    "status": "shipped",                                                      |
|    "carrier": "FedEx",                                                       |
|    "estimated_delivery": "2026-02-03"                                        |
|  }                                                                           |
+-----------------------------------------------------------------------------+
      |
      v
+-----------------------------------------------------------------------------+
|  STEP 5: DECIDE                                                              |
|  Do I have enough information to answer?                                     |
|                                                                              |
|  [YES] --> Go to STEP 6 (Respond)                                           |
|  [NO]  --> Go back to STEP 2 (Reason about what else is needed)             |
+-----------------------------------------------------------------------------+
      |
      v (YES)
+-----------------------------------------------------------------------------+
|  STEP 6: RESPOND                                                             |
|  "Your order ORD-12345 has been shipped via FedEx.                          |
|   Estimated delivery: February 3, 2026."                                     |
+-----------------------------------------------------------------------------+
      |
      v
     END
```

---

## Multi-Tool Query Example

```
USER: "Check order ORD-67890 and tell me if Miami weather will delay it"

+-----------------------------------------------------------------------------+
|                           ITERATION 1                                        |
+-----------------------------------------------------------------------------+

REASON: "User wants two things:
         1. Order status for ORD-67890
         2. Weather delay info for Miami
         I can call BOTH tools at once!"

ACT:    Tool 1: check_order_status(order_id="ORD-67890")
        Tool 2: get_weather_alerts(location="Miami")

OBSERVE:
        Result 1: {status: "processing", destination: "Miami, FL"}
        Result 2: {condition: "Hurricane Warning", delay_days: 3}

DECIDE: I have all the info I need. RESPOND.

+-----------------------------------------------------------------------------+
|                           FINAL RESPONSE                                     |
+-----------------------------------------------------------------------------+

"Your order ORD-67890 is currently processing and scheduled for delivery
to Miami, FL. However, there is a Hurricane Warning in Miami which may
cause a delay of approximately 3 days."
```

---

## The Loop in Code

```python
def react_loop(query: str, tools: list, max_iterations: int = 5) -> str:
    """
    The ReAct loop implementation
    """
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": query}
    ]

    for iteration in range(max_iterations):

        # =====================
        # REASON: LLM decides what to do
        # =====================
        response = llm.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=tools,
            tool_choice="auto"  # LLM decides
        )

        message = response.choices[0].message

        # =====================
        # CHECK: Tool call or final response?
        # =====================
        if message.tool_calls:

            # =====================
            # ACT: Execute the tool(s)
            # =====================
            messages.append(message)  # Add assistant's decision

            for tool_call in message.tool_calls:
                # Execute the tool
                result = execute_tool(
                    tool_call.function.name,
                    json.loads(tool_call.function.arguments)
                )

                # =====================
                # OBSERVE: Add result to context
                # =====================
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result)
                })

            # Loop continues - back to REASON

        else:
            # =====================
            # RESPOND: No more tools needed
            # =====================
            return message.content

    return "Max iterations reached"
```

---

## Visual: Message Flow

```
+------------------+     +------------------+     +------------------+
|                  |     |                  |     |                  |
|   USER MESSAGE   | --> |   LLM REASONS    | --> | TOOL CALL OUTPUT |
|                  |     |                  |     |                  |
| "What's my order |     | "I need to check |     | {name: "check_   |
|  status?"        |     |  order status"   |     |  order_status",  |
|                  |     |                  |     |  args: {...}}    |
+------------------+     +------------------+     +------------------+
                                                          |
                                                          v
+------------------+     +------------------+     +------------------+
|                  |     |                  |     |                  |
|  FINAL RESPONSE  | <-- |   LLM REASONS    | <-- |   TOOL RESULT    |
|                  |     |                  |     |                  |
| "Your order has  |     | "I have enough   |     | {status: shipped |
|  shipped..."     |     |  info to answer" |     |  carrier: FedEx} |
|                  |     |                  |     |                  |
+------------------+     +------------------+     +------------------+
```

---

## Message History Growth

Each iteration adds to the conversation:

```
INITIAL STATE:
+------------------------------------------------------------------+
| messages = [                                                      |
|   {role: "system", content: "You are a helpful agent..."},       |
|   {role: "user", content: "What's my order status?"}             |
| ]                                                                 |
+------------------------------------------------------------------+

AFTER ITERATION 1 (tool called):
+------------------------------------------------------------------+
| messages = [                                                      |
|   {role: "system", content: "You are a helpful agent..."},       |
|   {role: "user", content: "What's my order status?"},            |
|   {role: "assistant", tool_calls: [{...}]},          <-- NEW     |
|   {role: "tool", content: '{"status": "shipped"}'}   <-- NEW     |
| ]                                                                 |
+------------------------------------------------------------------+

AFTER ITERATION 2 (response generated):
+------------------------------------------------------------------+
| messages = [                                                      |
|   {role: "system", content: "You are a helpful agent..."},       |
|   {role: "user", content: "What's my order status?"},            |
|   {role: "assistant", tool_calls: [{...}]},                      |
|   {role: "tool", content: '{"status": "shipped"}'},              |
|   {role: "assistant", content: "Your order shipped..."} <-- NEW  |
| ]                                                                 |
+------------------------------------------------------------------+
```

---

## Key Insights

### 1. The LLM Never Executes Tools
```
+-------------+          +-------------+          +-------------+
|     LLM     |  ------> |  YOUR CODE  |  ------> |    TOOL     |
| "Call this  |          |  Executes   |          |  (Function) |
|  tool with  |          |  the tool   |          |             |
|  these args"|          |             |          |             |
+-------------+          +-------------+          +-------------+
```

The LLM only **decides** what to call. Your code **executes** it.

### 2. Tool Descriptions Guide Selection
```
GOOD DESCRIPTION:
"Check weather alerts and shipping delays for a location.
 Use when customer asks about weather impact on deliveries."

User: "Will my Miami package be delayed?"
LLM: "This matches 'weather impact on deliveries' --> use get_weather_alerts"
```

### 3. The Loop Enables Multi-Step Reasoning
```
Query: "Return my order if the replacement is in stock"

Iteration 1: check_order_status --> Get order details
Iteration 2: check_inventory --> Check replacement stock
Iteration 3: create_return --> Process the return (if in stock)
Iteration 4: RESPOND with combined result
```

---

## Comparison: Without vs With ReAct

### WITHOUT ReAct (Baseline RAG)
```
User Query --> Search Documents --> Generate Response

"What's my order status?"
     |
     v
Search KB: "How to check order status..."
     |
     v
Response: "To check your order, log into your account..."

PROBLEM: Can only answer from documents!
```

### WITH ReAct (Agentic RAG)
```
User Query --> Reason --> Act --> Observe --> Respond

"What's my order status?"
     |
     v
Reason: "Need to check order database"
     |
     v
Act: check_order_status("ORD-12345")
     |
     v
Observe: {status: "shipped", carrier: "FedEx"}
     |
     v
Response: "Your order shipped via FedEx!"

SOLUTION: Can query databases, APIs, take actions!
```

---

## Summary

| Step | What Happens | Who Does It |
|------|--------------|-------------|
| **REASON** | Decide what tool to use | LLM |
| **ACT** | Execute the tool | Your Code |
| **OBSERVE** | Process the result | Your Code |
| **DECIDE** | Check if done | LLM |
| **RESPOND** | Generate answer | LLM |

The ReAct pattern transforms a simple Q&A system into an intelligent agent that can:
- Query multiple data sources
- Call external APIs
- Take actions (create, update, delete)
- Handle complex multi-step tasks
