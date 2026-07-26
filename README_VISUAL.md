# 🧠 NEXUS — Architecture & Flow Visualizations

## 1. High-Level Architecture
The C4-style diagram showing the system boundaries of the Nexus platform.

```mermaid
graph TD
    User([User / Researcher]) --> UI[Streamlit Frontend UI]
    UI <-->|HTTP/REST| API[FastAPI Gateway]
    UI <-->|WebSockets| WS[WebSocket Manager]
    API <--> Graph[LangGraph Orchestrator]
    WS <--> Graph
    Graph <--> DB[(PostgreSQL)]
    Graph <--> Cache[(Redis)]
    Graph <--> LLM[Gemini API]
    Graph <--> Tools[External APIs e.g. Tavily]
```

## 2. State Machine
Detailed state diagram with all transitions and conditions implemented in LangGraph.

```mermaid
stateDiagram-v2
    [*] --> PLANNER: new_task
    PLANNER --> RESEARCHER: plan_generated
    RESEARCHER --> ANALYST: findings_gathered
    ANALYST --> WRITER: synthesis_complete
    WRITER --> CRITIC: draft_generated
    
    state CRITIC_EVALUATION <<choice>>
    CRITIC --> CRITIC_EVALUATION
    
    CRITIC_EVALUATION --> WRITER: revise (score < 7 and revisions < 3)
    
    state HUMAN_EVALUATION <<choice>>
    CRITIC_EVALUATION --> HUMAN_EVALUATION: approve (score >= 7)
    
    HUMAN_EVALUATION --> HUMAN_REVIEW: requires_approval == true
    HUMAN_EVALUATION --> [*]: requires_approval == false
    
    state HUMAN_DECISION <<choice>>
    HUMAN_REVIEW --> HUMAN_DECISION
    
    HUMAN_DECISION --> WRITER: rejected_with_feedback
    HUMAN_DECISION --> [*]: approved
```

## 3. Tool Integration
How agents call tools and process the results.

```mermaid
sequenceDiagram
    participant Agent as Researcher Agent
    participant Graph as LangGraph Orchestrator
    participant Tool as ToolAgent (Web Search)
    participant API as External API
    
    Agent->>Graph: Yield tool_call("web_search", query)
    Graph->>Tool: Execute web_search(query)
    Tool->>API: HTTP GET
    API-->>Tool: JSON Response
    Tool-->>Graph: Tool Result
    Graph-->>Agent: Resume with Tool Result
    Agent->>Agent: Extract Findings
```

## 4. Human-in-the-Loop Flow
Detailed approval/rejection workflow pausing execution.

```mermaid
sequenceDiagram
    participant Critic
    participant Graph
    participant DB
    participant UI
    participant Human
    
    Critic->>Graph: Return approved=True
    Graph->>Graph: Check needs_human_approval()
    Graph->>DB: Save State (Status: WAITING_FOR_HUMAN)
    Graph->>UI: WebSocket: status=WAITING_FOR_HUMAN
    UI->>Human: Show Approval Panel
    
    alt Approves
        Human->>UI: Click "Approve"
        UI->>Graph: POST /approve
        Graph->>DB: Update State
        Graph->>Graph: Resume -> END
    else Rejects
        Human->>UI: Enter feedback + "Reject"
        UI->>Graph: POST /reject (feedback)
        Graph->>DB: Update State
        Graph->>Graph: Resume -> Route to Writer
    end
```
