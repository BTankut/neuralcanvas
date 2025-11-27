# 🗺️ NeuralCanvas Roadmap

## Phase 1: Foundation (MVP Core)
Minimum viable product - basic working canvas with LLM execution.

### 1.1 Project Setup
- [ ] Initialize monorepo structure (`/frontend`, `/backend`, `/data`)
- [ ] Setup Vue 3 + Vite + TypeScript
- [ ] Configure Tailwind CSS with custom theme (dark mode, neon accents)
- [ ] Setup FastAPI with async support
- [ ] Configure SQLite with SQLAlchemy
- [ ] Setup WebSocket connection between frontend/backend
- [ ] Create `.env` configuration system

### 1.2 Canvas Foundation
- [ ] Integrate Vue Flow
- [ ] Implement infinite canvas with pan/zoom
- [ ] Create base node component (common structure)
- [ ] Implement edge connection system
- [ ] Add context menu (right-click to add nodes)
- [ ] Basic node drag-and-drop

### 1.3 Core Nodes (Basic)
- [ ] **Input Node:** Text input with submit
- [ ] **Output Node:** Markdown display
- [ ] **LLM Node:** Model selector, system prompt, temperature

### 1.4 Execution Engine v1
- [ ] Graph validation (check for cycles, required connections)
- [ ] Simple linear execution (A → B → C)
- [ ] WebSocket event streaming (`node_start`, `node_finish`)
- [ ] Basic error handling (show error on failed node)

### 1.5 Settings & Persistence
- [ ] Settings page (API key input)
- [ ] Encrypted API key storage in SQLite
- [ ] Save/Load single workflow
- [ ] Auto-save draft

### 1.6 Basic UI Polish
- [ ] Dark theme implementation
- [ ] Node status indicators (idle, running, success, error)
- [ ] Basic glassmorphism on panels

**MVP Milestone:** Can create Input → LLM → Output flow and execute it.

---

## Phase 2: Live Experience
Real-time streaming and better execution flow.

### 2.1 Token Streaming
- [ ] Implement `token_stream` WebSocket event
- [ ] Stream bubble component (live text above node)
- [ ] Typing animation effect

### 2.2 Parallel Execution
- [ ] Detect independent branches in graph
- [ ] Execute parallel branches with `asyncio.gather`
- [ ] Visual indication of parallel execution

### 2.3 Node Inspector
- [ ] Side panel for selected node
- [ ] Tabs: Config, Input, Output, Stats
- [ ] Token count display (input/output/total)
- [ ] Cost estimation per node

### 2.4 Cost Tracking
- [ ] Fetch OpenRouter pricing data
- [ ] Calculate per-node cost
- [ ] Execution summary with total cost
- [ ] Running session cost tracker

### 2.5 Edge Enhancements
- [ ] Animated edges during execution
- [ ] Edge labels (optional)
- [ ] Connection type validation

**Phase 2 Milestone:** Full streaming experience with cost visibility.

---

## Phase 3: Advanced Nodes
Expand node library for complex workflows.

### 3.1 Logic Nodes
- [ ] **Conditional Node:** If/Else branching (LLM-based decision)
- [ ] **Merge Node:** Combine parallel outputs
- [ ] **Variable Node:** Store/retrieve execution context

### 3.2 AI Nodes
- [ ] **Coordinator Node:** Smart routing to expert nodes
- [ ] **Evaluation Node:** Score outputs with criteria
- [ ] **Battle Node:** Two LLMs debate (configurable rounds)

### 3.3 Tool Nodes
- [ ] **Web Search Node:** (using free search API)
- [ ] **Calculator Node:** Math expression evaluator
- [ ] **Transform Node:** Text manipulation (regex, templates)

### 3.4 Utility Nodes
- [ ] **Note Node:** Documentation on canvas
- [ ] **Group Node:** Visual grouping
- [ ] **Delay Node:** Rate limiting

**Phase 3 Milestone:** Can build complex multi-branch workflows.

---

## Phase 4: UX Polish
Professional-grade user experience.

### 4.1 Canvas UX
- [ ] Undo/Redo system (command pattern)
- [ ] Multi-select nodes
- [ ] Copy/Paste nodes
- [ ] Keyboard shortcuts
- [ ] Mini-map navigation

### 4.2 Workflow Management
- [ ] Workflow list view (dashboard)
- [ ] Workflow metadata (name, description, tags)
- [ ] Duplicate workflow
- [ ] Delete with confirmation

### 4.3 Template System
- [ ] Save workflow as template
- [ ] Template library browser
- [ ] Template categories
- [ ] Built-in starter templates (3-5)

### 4.4 Import/Export
- [ ] JSON export (full graph)
- [ ] JSON import
- [ ] PNG export (canvas snapshot)

### 4.5 Visual Polish
- [ ] Custom Nanobanana node icons
- [ ] Refined glassmorphism effects
- [ ] Smooth animations (GSAP or CSS)
- [ ] Loading states and transitions

**Phase 4 Milestone:** Production-ready UX.

---

## Phase 5: Production Ready
Self-hosted deployment and documentation.

### 5.1 Deployment
- [ ] Dockerfile (multi-stage build)
- [ ] docker-compose.yml (frontend + backend)
- [ ] Environment configuration guide
- [ ] Health check endpoints

### 5.2 Documentation
- [ ] README with screenshots
- [ ] Installation guide
- [ ] Node reference documentation
- [ ] Example workflows

### 5.3 Quality
- [ ] Error boundaries (frontend)
- [ ] Comprehensive error messages
- [ ] Basic logging system
- [ ] Performance optimization pass

**Phase 5 Milestone:** Ready for self-hosting.

---

## Future Considerations (Post v1.0)
Not in initial scope, but potential future additions:

- [ ] Light theme option
- [ ] Loop Node (iteration)
- [ ] HTTP Node (external API calls)
- [ ] Additional LLM providers (OpenAI direct, Anthropic direct)
- [ ] Execution history browser
- [ ] Workflow versioning
- [ ] Collaboration features (if multi-user added)
- [ ] Plugin system for custom nodes

---

## Success Metrics

### MVP (Phase 1)
- Can execute Input → LLM → Output
- Settings persist across sessions
- No crashes during normal use

### v1.0 (Phase 5)
- Can build 10+ node workflows reliably
- All core node types functional
- < 100ms UI response time
- Docker deployment works first try
