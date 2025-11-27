# 🏗️ NeuralCanvas Architecture

## 📋 Overview
Single-user, self-hosted local application for visual AI workflow orchestration.

## 💻 Tech Stack

### Frontend (The Canvas)
| Technology | Purpose |
|------------|---------|
| **Vue 3** | Composition API, reactive UI |
| **Vue Flow** | Node-based graph interaction, zooming, panning |
| **Tailwind CSS** | Utility-first styling + custom glassmorphism |
| **Pinia** | Global state management (graph state, settings) |
| **Phosphor Icons** | Consistent icon set |

### Backend (The Brain)
| Technology | Purpose |
|------------|---------|
| **FastAPI** | High-performance async Python server |
| **SQLite** | Local database (zero config, portable) |
| **WebSocket** | Real-time streaming & graph sync |
| **asyncio** | Parallel node execution |
| **OpenRouter API** | LLM provider (multi-model access) |

### Project Structure
```
neuralcanvas/
├── frontend/                # Vue 3 application
│   ├── src/
│   │   ├── components/      # Vue components
│   │   │   ├── canvas/      # Canvas & node components
│   │   │   ├── nodes/       # Individual node type components
│   │   │   └── ui/          # Reusable UI components
│   │   ├── stores/          # Pinia stores
│   │   ├── composables/     # Vue composables
│   │   └── types/           # TypeScript types
│   └── package.json
├── backend/                 # FastAPI application
│   ├── app/
│   │   ├── api/             # API routes
│   │   ├── core/            # Config, settings
│   │   ├── engine/          # Execution engine
│   │   ├── models/          # SQLAlchemy models
│   │   └── services/        # Business logic
│   └── requirements.txt
└── data/                    # SQLite DB & user data
```

## 🧩 Core Components

### 1. Node System
Every entity on the canvas is a "Node" with common properties:
- `id`: Unique identifier
- `type`: Node type (llm, input, output, etc.)
- `position`: {x, y} on canvas
- `data`: Type-specific configuration
- `status`: idle | running | success | error

#### Node Types

| Node | Description | Config |
|------|-------------|--------|
| **Input Node** | User entry point | Text input, file upload |
| **LLM Node** | AI model container | Model, temperature, system prompt |
| **Coordinator Node** | Smart router | Routing rules, connected experts |
| **Tool Node** | Utilities | Web search, calculator |
| **Conditional Node** | If/Else branching | Condition expression |
| **Loop Node** | Iteration | Max iterations, break condition |
| **Variable Node** | Store/retrieve data | Variable name, scope |
| **Merge Node** | Combine parallel branches | Merge strategy |
| **Output Node** | Final result | Display format |

### 2. Execution Engine
```
┌─────────────────────────────────────────────────────┐
│                  Execution Flow                      │
├─────────────────────────────────────────────────────┤
│  1. User clicks "Run"                               │
│  2. Backend receives graph JSON via WebSocket       │
│  3. Engine validates graph (DAG check)              │
│  4. Topological sort determines execution order     │
│  5. Nodes execute (parallel where possible)         │
│  6. Each node streams status via WebSocket          │
│  7. Results flow to connected nodes                 │
│  8. Final output displayed                          │
└─────────────────────────────────────────────────────┘
```

**Key Behaviors:**
- **Graph Traversal:** DAG (Directed Acyclic Graph) - no circular dependencies
- **Data Flow:** Output from Node A → Input context for Node B
- **Parallelism:** Independent branches run via `asyncio.gather`
- **Error Handling:** Node failure stops downstream nodes, others continue

### 3. Live Inspection Layer
WebSocket events streamed during execution:

| Event | Payload | UI Behavior |
|-------|---------|-------------|
| `node_start` | node_id | Highlight node, show spinner |
| `token_stream` | node_id, token | Append to live preview bubble |
| `node_finish` | node_id, result, tokens_used | Show success, update cost |
| `node_error` | node_id, error | Show error state, message |
| `execution_complete` | total_cost, duration | Summary notification |

### 4. Data Persistence (SQLite)

**Tables:**
```sql
workflows       -- Saved workflow graphs
├── id, name, description, graph_json, created_at, updated_at

templates       -- Reusable templates
├── id, name, category, graph_json, is_builtin

settings        -- App configuration
├── key, value  -- (openrouter_api_key, default_model, theme, etc.)

execution_history  -- Past runs (optional, for debugging)
├── id, workflow_id, started_at, finished_at, total_tokens, total_cost, status
```

## 🔄 Data Flow Example
```
[User Input]
     ↓
[Coordinator Node] ──decides──→ [Math Expert Node]
     │                                   ↓
     └──────────────────────→ [History Expert Node]
                                         ↓
                              [Merge Node] ← ─ ─ ┘
                                         ↓
                              [Output Node]
```

## 🔐 Security Considerations
- **API Key Storage:** Encrypted in SQLite or system keychain
- **No arbitrary code execution:** Tool nodes are predefined, sandboxed
- **Local only:** No external network exposure by default
