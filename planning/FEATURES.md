# ✨ NeuralCanvas Features

## 🎛️ The Canvas (Workspace)

### Core Interactions
| Feature | Description | Shortcut |
|---------|-------------|----------|
| **Infinite Canvas** | Pan and zoom freely | Scroll / Pinch |
| **Mini-map** | Quick navigation for large workflows | `M` |
| **Context Menu** | Right-click to add nodes | Right-click |
| **Multi-select** | Select multiple nodes | `Shift + Click` |
| **Copy/Paste** | Duplicate nodes | `Cmd+C / Cmd+V` |
| **Undo/Redo** | History navigation | `Cmd+Z / Cmd+Shift+Z` |

### Edge System
- **Animated edges:** Flow direction visualization during execution
- **Edge labels:** Optional labels showing data type
- **Smart routing:** Auto-avoids node overlap
- **Connection validation:** Prevents invalid connections

## 📦 Node Library

### Input/Output Nodes
| Node | Purpose | Features |
|------|---------|----------|
| **Input Node** | User entry point | Text, file upload, image |
| **Output Node** | Final result display | Markdown render, copy button |

### AI Nodes
| Node | Purpose | Features |
|------|---------|----------|
| **LLM Node** | Single model execution | Model selector, temperature, system prompt, max tokens |
| **Coordinator Node** | Smart router/manager | Routes to experts based on query analysis |
| **Battle Node** | Two LLMs debate | Rounds config, judge criteria |
| **Evaluation Node** | Score/critique output | Rubric definition, 1-10 scoring |

### Logic Nodes
| Node | Purpose | Features |
|------|---------|----------|
| **Conditional Node** | If/Else branching | LLM-based or rule-based conditions |
| **Loop Node** | Iterate over data | Max iterations, break condition |
| **Variable Node** | Store/retrieve values | Get/Set modes, scoped variables |
| **Merge Node** | Combine branches | Concatenate, summarize, or select |

### Tool Nodes
| Node | Purpose | Features |
|------|---------|----------|
| **Web Search Node** | Internet search | Query input, result count |
| **Calculator Node** | Math operations | Expression evaluator |
| **HTTP Node** | API calls | Method, headers, body |
| **Transform Node** | Text manipulation | Regex, JSON path, templates |

### Utility Nodes
| Node | Purpose | Features |
|------|---------|----------|
| **Note Node** | Documentation | Markdown support, colors |
| **Delay Node** | Rate limiting | Configurable wait time |
| **Group Node** | Visual grouping | Collapsible, labeled |

## ⚙️ Orchestration Modes

### 1. Manual Pipeline
```
[Input] → [LLM A] → [LLM B] → [Output]
```
- You define exact path: A → B → C
- Good for: Repetitive tasks (Summarize → Translate → Format)
- Predictable, debuggable

### 2. Auto-Orchestrator
```
                    ┌→ [Math Expert] ─┐
[Input] → [Coordinator] → [Code Expert] → [Merge] → [Output]
                    └→ [Writing Expert]┘
```
- Coordinator decides routing at runtime
- Analyzes query: "This is a math problem → route to Math Expert"
- Good for: General-purpose assistants, complex queries

## 👁️ Live Introspection

### During Execution
| Feature | Description |
|---------|-------------|
| **Node Glow** | Active node pulses with neon accent |
| **Stream Bubble** | Live token stream above working node |
| **Edge Animation** | Data flow visualization on connections |
| **Progress Indicator** | Overall execution progress bar |

### Node Inspector (Click to open)
| Tab | Content |
|-----|---------|
| **Config** | System prompt, model settings |
| **Input** | What this node received |
| **Output** | What this node produced |
| **Stats** | Tokens used, latency, cost |
| **History** | Previous execution results |

### Cost Tracking
- Per-node token counter (input/output)
- Real-time cost estimation (based on OpenRouter pricing)
- Execution summary with total cost

## 💾 Project Management

### Workflows
- **Save/Load:** Persist workflows to local database
- **Duplicate:** Clone existing workflow
- **Delete:** Remove with confirmation

### Templates
- **Save as Template:** Convert workflow to reusable template
- **Template Library:** Browse and instantiate templates
- **Categories:** Organize templates (Writing, Coding, Research, etc.)

### Import/Export
- **JSON Export:** Full graph structure
- **JSON Import:** Load external workflows
- **Image Export:** PNG snapshot of canvas (for documentation)

## ⚙️ Settings

### General
- Theme (Dark only for MVP, Light later)
- Language (English for MVP)
- Auto-save interval

### API Configuration
- OpenRouter API key (encrypted storage)
- Default model selection
- Default temperature

### Canvas Preferences
- Grid snap on/off
- Mini-map visibility
- Animation speed
