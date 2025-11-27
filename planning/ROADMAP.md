# 🗺️ NeuralCanvas Roadmap

## Phase 1: Foundation (MVP Core)
Minimum viable product - basic working canvas with LLM execution.

### 1.1 Project Setup
- [x] Initialize monorepo structure (`/frontend`, `/backend`, `/data`)
- [x] Setup Vue 3 + Vite + TypeScript
- [x] Configure Tailwind CSS with custom theme (dark mode, neon accents)
- [x] Setup FastAPI with async support
- [x] Configure SQLite with SQLAlchemy
- [x] Setup WebSocket connection between frontend/backend
- [x] Create `.env` configuration system

### 1.2 Canvas Foundation
- [x] Integrate Vue Flow
- [x] Implement infinite canvas with pan/zoom
- [x] Create base node component (common structure)
- [x] Implement edge connection system
- [x] Add context menu (right-click to add nodes)
- [x] Basic node drag-and-drop

### 1.3 Core Nodes (Basic)
- [x] **Input Node:** Text input with submit
- [x] **Output Node:** Markdown display
- [x] **LLM Node:** Model selector, system prompt, temperature

### 1.4 Execution Engine v1
- [x] Graph validation (check for cycles, required connections)
- [x] Simple linear execution (A → B → C)
- [x] WebSocket event streaming (`node_start`, `node_finish`)
- [x] Basic error handling (show error on failed node)

### 1.5 Settings & Persistence
- [x] Settings page (API key input)
- [x] Encrypted API key storage in SQLite (Stored in LocalStorage for Phase 4.1)
- [x] Save/Load single workflow (Implemented via LocalStorage)
- [ ] Auto-save draft

### 1.6 Basic UI Polish
- [x] Dark theme implementation
- [x] Node status indicators (idle, running, success, error)
- [x] Basic glassmorphism on panels

**MVP Milestone:** Can create Input → LLM → Output flow and execute it.

---

## Phase 2: Live Experience
Real-time streaming and better execution flow.

### 2.1 Token Streaming
- [x] Implement `token_stream` WebSocket event
- [x] Stream bubble component (live text above node)
- [x] Typing animation effect

### 2.2 Parallel Execution
- [x] Detect independent branches in graph
- [x] Execute parallel branches with `asyncio.gather` (Handled via Dynamic Data-Driven Queue)
- [x] Visual indication of parallel execution

### 2.3 Node Inspector
- [ ] Side panel for selected node
- [ ] Tabs: Config, Input, Output, Stats
- [ ] Token count display (input/output/total)
- [ ] Cost estimation per node

### 2.4 Cost Tracking
- [x] Fetch OpenRouter pricing data
- [x] Calculate per-node cost
- [x] Execution summary with total cost
- [x] Running session cost tracker

### 2.5 Edge Enhancements
- [x] Animated edges during execution
- [ ] Edge labels (optional)
- [x] Connection type validation

**Phase 2 Milestone:** Full streaming experience with cost visibility.

---

## Phase 3: Advanced Nodes
Expand node library for complex workflows.

### 3.1 Logic Nodes
- [x] **Conditional Node:** If/Else branching (LLM-based decision)
- [ ] **Merge Node:** Combine parallel outputs
- [ ] **Variable Node:** Store/retrieve execution context

### 3.2 AI Nodes
- [ ] **Coordinator Node:** Smart routing to expert nodes
- [ ] **Evaluation Node:** Score outputs with criteria
- [ ] **Battle Node:** Two LLMs debate (configurable rounds)

### 3.3 Tool Nodes
- [x] **Web Search Node:** (using free search API)
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
- [x] Custom Nanobanana node icons
- [x] Refined glassmorphism effects
- [x] Smooth animations (GSAP or CSS)
- [x] Loading states and transitions

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
- [x] Loop Node (iteration) (Implemented in Phase 3.2)
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
