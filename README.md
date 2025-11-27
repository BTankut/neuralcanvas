<div align="center">
  <img src="docs/images/banner.png" alt="NeuralCanvas Banner" width="100%" />

  # 🧠 NeuralCanvas
  ### The Visual AI Orchestration Engine
  
  **Design complex AI workflows visually. Execute them locally. Empowered by the Cloud.**

  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
  [![Vue 3](https://img.shields.io/badge/Frontend-Vue_3-42b883.svg)](https://vuejs.org/)
  [![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
  [![OpenRouter](https://img.shields.io/badge/AI-OpenRouter-blueviolet.svg)](https://openrouter.ai/)
</div>

---

## 🚀 Introduction

**NeuralCanvas** is a next-generation visual programming environment designed for building autonomous AI agents and complex workflows without writing a single line of glue code. 

It combines the intuitive "drag-and-drop" interface of **Vue Flow** with a powerful Python-based execution engine that supports **Loops**, **Conditional Logic**, and **External Tools**.

<div align="center">
  <img src="docs/images/interface.png" alt="NeuralCanvas Interface" width="800" style="border-radius: 10px; border: 1px solid #333;" />
</div>

---

## ✨ Key Features

### 🎨 Visual Workflow Builder
Create intricate logic chains using a beautiful, infinite canvas. Connect nodes, organize your thoughts, and see the big picture.

### 🤖 Multi-Model AI Support
Seamlessly integrate **GPT-4**, **Claude 3.5 Sonnet**, **Gemini 1.5 Pro**, and open-source models (Llama 3) via **OpenRouter**. Configure temperature and system prompts per node.

### 🔄 Logic & Loops (Turing Complete)
Unlike simple linear chat chains, NeuralCanvas supports:
- **Conditional Branching:** IF/ELSE logic based on AI analysis.
- **Iterative Loops:** Refine outputs by cycling through nodes multiple times.

### 🌍 Web Search & Tools
Give your AI agents access to the real world. The built-in **Web Search Node** (powered by DuckDuckGo) fetches live information for context-aware generation.

### 💾 Save, Load & Templates
- **Persistence:** Save your masterpieces to local storage.
- **Templates:** Start fast with built-in templates like *"The Tech Journalist"* or *"The Support Router"*.

### 💸 Real-Time Cost Tracking
Monitor token usage and estimated costs in real-time. Never get surprised by an API bill again.

---

## 🛠️ Tech Stack

*   **Frontend:** Vue 3, Vite, TypeScript, Tailwind CSS (v4), Vue Flow
*   **Backend:** Python 3.12, FastAPI, Uvicorn, WebSockets
*   **AI Engine:** OpenAI SDK (via OpenRouter), DuckDuckGo Search
*   **Design:** Custom Cyberpunk/Glassmorphism Theme, Phosphor Icons

---

## ⚡ Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- An [OpenRouter API Key](https://openrouter.ai/)

### 1. Clone the Repository
```bash
git clone https://github.com/BTankut/neuralcanvas.git
cd neuralcanvas
```

### 2. Setup Backend
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python3 -m uvicorn app.main:app --reload
```
*Backend runs at `http://localhost:8000`*

### 3. Setup Frontend
Open a new terminal window:
```bash
cd frontend
npm install
npm run dev
```
*Frontend runs at `http://localhost:5173`*

### 4. Launch!
Go to `http://localhost:5173`, click the **Settings (Gear)** icon, and enter your OpenRouter API Key. You are ready to create!

---

## 📖 How to Use

1.  **Add Nodes:** Right-click on the canvas to open the Context Menu.
2.  **Connect:** Drag from one node's handle to another to create a data flow.
3.  **Configure:** Click on a node to adjust settings (Model, Prompt, Search Query).
4.  **Run:** Click the "RUN FLOW" button in the top right.
5.  **Visualize:** Watch the execution flow in real-time with animated edges and status indicators.

---

## 📦 Templates

NeuralCanvas comes with powerful starter templates:
*   **The Tech Journalist:** Research -> Summarize -> Write Article.
*   **The Idea Refiner:** Iterative loop to improve a concept 3 times.
*   **The Support Router:** Sentiment analysis to route customer queries.

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

<div align="center">
  <sub>Built with ❤️ by <a href="https://github.com/BTankut">BTankut</a></sub>
</div>
