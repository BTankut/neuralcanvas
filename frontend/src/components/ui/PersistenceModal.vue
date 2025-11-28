<script setup lang="ts">
import { ref } from 'vue'
import { useWorkflowStore } from '../../stores/workflow'
import { PhFloppyDisk, PhFolderOpen, PhTrash, PhX, PhSquaresFour } from '@phosphor-icons/vue'

const store = useWorkflowStore()
const isOpen = ref(false)
const mode = ref<'save' | 'load'>('save')
const loadTab = ref<'saved' | 'templates'>('saved') // Sub-tab for load mode
const saveName = ref('')
const savedWorkflows = ref<any[]>([])

// Hardcoded template registry with embedded data
const builtInTemplates = [
    {
        id: 'template-journalist',
        name: 'The Tech Journalist',
        description: 'An automated news reporting agent. It searches the web for the latest information on a topic, synthesizes key findings, and drafts a professional article. Perfect for content creators and researchers.',
        icon: 'PhNewspaper',
        data: {
            nodes: [
                { id: "1", type: "neural-input", position: { x: 50, y: 250 }, data: { label: "Topic", inputValue: "Recent breakthroughs in Quantum Computing 2024" } },
                { id: "2", type: "neural-search", position: { x: 400, y: 250 }, data: { label: "Web Research", node_config: { searchQuery: "" } } },
                { id: "3", type: "neural-llm", position: { x: 750, y: 250 }, data: { label: "Article Writer", node_config: { model: "openai/gpt-3.5-turbo", temperature: 0.7, systemPrompt: "You are a senior technology editor for Wired. Write a captivating, detailed news report based on the following search results. Use markdown formatting, headings, and a professional tone. Focus on the implications for the future." } } },
                { id: "4", type: "neural-output", position: { x: 1100, y: 250 }, data: { label: "Final Article" } }
            ],
            edges: [
                { id: "e1-2", source: "1", target: "2", animated: true },
                { id: "e2-3", source: "2", target: "3", animated: true },
                { id: "e3-4", source: "3", "target": "4", animated: true }
            ]
        }
    },
    {
        id: 'template-refiner',
        name: 'The Idea Refiner',
        description: 'A creative feedback loop that iteratively improves an initial concept. The AI acts as a consultant, refining the idea over multiple passes to enhance depth and feasibility.',
        icon: 'PhLightbulb',
        data: {
            nodes: [
                { id: "1", type: "neural-input", position: { x: 50, y: 200 }, data: { label: "Raw Idea", inputValue: "A mobile app that connects local farmers directly to consumers." } },
                { id: "2", type: "neural-loop", position: { x: 400, y: 200 }, data: { label: "Iterator", node_config: { max_iterations: 3 } } },
                { id: "3", type: "neural-llm", position: { x: 800, y: 50 }, data: { label: "Refiner AI", node_config: { model: "openai/gpt-3.5-turbo", temperature: 0.9, systemPrompt: "You are a world-class Product Strategist. Analyze the current iteration of the product concept. Critically evaluate its feasibility and add one 'Killer Feature' that would make it a unicorn startup. Be specific and bold." } } },
                { id: "4", type: "neural-output", position: { x: 800, y: 400 }, data: { label: "Polished Concept" } }
            ],
            edges: [
                { id: "e1-2", source: "1", target: "2", animated: true },
                { id: "e2-3", source: "2", target: "3", sourceHandle: "loop", animated: true, style: { stroke: "#06b6d4" } },
                { id: "e3-2", source: "3", target: "2", animated: true, style: { stroke: "#06b6d4", strokeDasharray: "5,5" } },
                { id: "e2-4", source: "2", target: "4", sourceHandle: "done", animated: true, style: { stroke: "#10b981" } }
            ]
        }
    },
    {
        id: 'template-router',
        name: 'The Support Router',
        description: 'An intelligent routing system that analyzes the sentiment of incoming messages. It directs angry customers to an empathetic support agent and standard queries to a general assistant.',
        icon: 'PhGitFork',
        data: {
            nodes: [
                { id: "1", type: "neural-input", position: { x: 50, y: 250 }, data: { label: "Customer Message", inputValue: "I've been waiting for my package for 3 weeks and nobody is answering me! This is unacceptable service." } },
                { id: "2", type: "neural-condition", position: { x: 400, y: 250 }, data: { label: "Sentiment Check", node_config: { conditionType: "contains", targetValue: "unacceptable" } } },
                { id: "3", type: "neural-llm", position: { x: 800, y: 50 }, data: { label: "Apology Bot", node_config: { model: "openai/gpt-3.5-turbo", temperature: 0.5, systemPrompt: "You are a Senior Customer Success Manager. Write a deeply empathetic, professional apology email. Offer a concrete solution (like a refund or discount) and assure the customer that you are personally taking over their case." } } },
                { id: "4", type: "neural-llm", position: { x: 800, y: 450 }, data: { label: "Support Bot", node_config: { model: "openai/gpt-3.5-turbo", temperature: 0.5, systemPrompt: "Write a standard, polite support acknowledgment email. Ask for the order number and provide typical shipping timelines." } } },
                { id: "5", type: "neural-output", position: { x: 1200, "y": 250 }, data: { label: "Final Response" } }
            ],
            edges: [
                { id: "e1-2", source: "1", target: "2", animated: true },
                { id: "e2-3", source: "2", target: "3", sourceHandle: "true", animated: true, style: { stroke: "#10b981" } },
                { id: "e2-4", source: "2", target: "4", sourceHandle: "false", animated: true, style: { stroke: "#ef4444" } },
                { id: "e3-5", source: "3", target: "5", animated: true },
                { id: "e4-5", source: "4", target: "5", animated: true }
            ]
        }
    },
    {
        id: 'template-board',
        name: 'The Executive Board',
        description: 'A multi-agent simulation where three specialized personas (Analyst, Creative, Finance) collaborate on a task. A final Coordinator agent synthesizes their reports into a master plan.',
        icon: 'PhSquaresFour',
        data: {
            nodes: [
                { id: "1", type: "neural-input", position: { x: 50, y: 300 }, data: { label: "Task", inputValue: "Launch a Cyberpunk Energy Drink targeting gamers." } },
                { id: "2", type: "neural-llm", position: { x: 500, y: 50 }, data: { label: "The Analyst", node_config: { model: "openai/gpt-3.5-turbo", temperature: 0.3, systemPrompt: "You are a Strategic Analyst. Identify potential risks, market competitors, and SWOT analysis for the given task. Be critical and factual." } } },
                { id: "3", type: "neural-llm", position: { x: 500, y: 300 }, data: { label: "The Creative", node_config: { model: "openai/gpt-3.5-turbo", temperature: 0.9, systemPrompt: "You are a Creative Director. Brainstorm 3 catchy slogans, a visual identity concept, and a viral marketing stunt for the task. Be wild and innovative." } } },
                { id: "4", type: "neural-llm", position: { x: 500, y: 550 }, data: { label: "The CFO", node_config: { model: "openai/gpt-3.5-turbo", temperature: 0.2, systemPrompt: "You are a strict CFO. Estimate a rough budget breakdown for a launch campaign. Focus on ROI and cost-cutting measures." } } },
                { id: "5", type: "neural-llm", position: { x: 1000, y: 300 }, data: { label: "The CEO (Boss)", node_config: { model: "openai/gpt-4-turbo", temperature: 0.5, systemPrompt: "You are the CEO. Review the reports from your Analyst, Creative Director, and CFO below. Synthesize them into a final, actionable Go-To-Market strategy. Resolve any conflicts between creativity and budget." } } },
                { id: "6", type: "neural-output", position: { x: 1400, y: 300 }, data: { label: "Master Plan" } }
            ],
            edges: [
                { id: "e1-2", source: "1", target: "2", animated: true },
                { id: "e1-3", source: "1", target: "3", animated: true },
                { id: "e1-4", source: "1", target: "4", animated: true },
                { id: "e2-5", source: "2", target: "5", animated: true },
                { id: "e3-5", source: "3", target: "5", animated: true },
                { id: "e4-5", source: "4", target: "5", animated: true },
                { id: "e5-6", source: "5", target: "6", animated: true }
            ]
        }
    },
    {
        id: 'template-automanager',
        name: 'The Auto-Manager (Dynamic)',
        description: 'A self-organizing team where a Manager agent dynamically assigns roles to sub-agents based on the task. Demonstrates prompt chaining and autonomous delegation capabilities.',
        icon: 'PhSquaresFour',
        data: {
            nodes: [
                { id: "1", type: "neural-input", position: { x: 50, y: 300 }, data: { label: "Mission Objective", inputValue: "Create a plot for a sci-fi movie set in Istanbul in the year 2099." } },
                { id: "2", type: "neural-llm", position: { x: 450, y: 300 }, data: { label: "The Manager", node_config: { model: "openai/gpt-4-turbo", temperature: 0.7, systemPrompt: "You are an autonomous Project Manager. You have 3 specialized AI agents at your disposal: AGENT_A, AGENT_B, and AGENT_C. \n\nAnalyze the user's input task. Break it down into 3 distinct components. Assign a specific Persona/Role and a Task to each agent.\n\nCRITICAL: You must output the instructions in this exact format so they can understand you:\n\n[[AGENT_A]]\n[Role Name]\n[Specific Instructions]\n\n[[AGENT_B]]\n[Role Name]\n[Specific Instructions]\n\n[[AGENT_C]]\n[Role Name]\n[Specific Instructions]" } } },
                { id: "3", type: "neural-llm", position: { x: 950, y: 50 }, data: { label: "Agent A", node_config: { model: "openai/gpt-3.5-turbo", temperature: 0.7, systemPrompt: "You are AGENT_A. Look at the input text provided by 'The Manager'. \nIgnore instructions for other agents. \nFind the section starting with [[AGENT_A]]. \nAdopt the Persona assigned to you in that section and execute the specific Task described there with high quality." } } },
                { id: "4", type: "neural-llm", position: { x: 950, y: 350 }, data: { label: "Agent B", node_config: { model: "openai/gpt-3.5-turbo", temperature: 0.7, systemPrompt: "You are AGENT_B. Look at the input text provided by 'The Manager'. \nIgnore instructions for other agents. \nFind the section starting with [[AGENT_B]]. \nAdopt the Persona assigned to you in that section and execute the specific Task described there with high quality." } } },
                { id: "5", type: "neural-llm", position: { x: 950, y: 650 }, data: { label: "Agent C", node_config: { model: "openai/gpt-3.5-turbo", temperature: 0.7, systemPrompt: "You are AGENT_C. Look at the input text provided by 'The Manager'. \nIgnore instructions for other agents. \nFind the section starting with [[AGENT_C]]. \nAdopt the Persona assigned to you in that section and execute the specific Task described there with high quality." } } },
                { id: "6", type: "neural-llm", position: { x: 1450, y: 350 }, data: { label: "Final Compiler", node_config: { model: "openai/gpt-4-turbo", temperature: 0.5, systemPrompt: "You are the Final Editor. You will receive outputs from 3 different agents (A, B, C) who performed parts of a larger task. \n\nCombine their works into a single, cohesive, polished final result. Ensure consistency in tone and style." } } },
                { id: "7", type: "neural-output", position: { x: 1850, y: 350 }, data: { label: "Final Product" } }
            ],
            edges: [
                { id: "e1-2", source: "1", target: "2", animated: true },
                { id: "e2-3", source: "2", target: "3", animated: true, style: { stroke: "#f472b6" } },
                { id: "e2-4", source: "2", target: "4", animated: true, style: { stroke: "#f472b6" } },
                { id: "e2-5", source: "2", target: "5", animated: true, style: { stroke: "#f472b6" } },
                { id: "e3-6", source: "3", target: "6", animated: true },
                { id: "e4-6", source: "4", target: "6", animated: true },
                { id: "e5-6", "source": "5", target: "6", animated: true },
                { id: "e6-7", source: "6", target: "7", animated: true }
            ]
        }
    },
    {
        id: 'template-coder',
        name: 'The Iterative Coder (Smart Loop)',
        description: 'A coding workflow where a Developer agent writes code and a Reviewer agent checks it. If issues are found, the loop sends it back for correction. The cycle repeats until the code is APPROVED.',
        icon: 'PhSquaresFour',
        data: {
            nodes: [
                { id: "1", type: "neural-input", position: { x: 50, y: 200 }, data: { label: "Coding Task", inputValue: "Write a Python function to check if a number is prime. Include error handling." } },
                { id: "2", type: "neural-loop", position: { x: 400, y: 200 }, data: { label: "Quality Gate", node_config: { max_iterations: 5, targetValue: "APPROVED" } } },
                { id: "3", type: "neural-llm", position: { x: 800, y: 50 }, data: { label: "Junior Developer", node_config: { model: "openai/gpt-3.5-turbo", temperature: 0.4, systemPrompt: "You are a Junior Python Developer. Write code based on the instructions. If you receive feedback, FIX the code based on that feedback." } } },
                { id: "4", type: "neural-llm", position: { x: 1200, y: 200 }, data: { label: "Senior Reviewer", node_config: { model: "openai/gpt-4-turbo", temperature: 0.2, systemPrompt: "You are a Senior Tech Lead. Review the code. \n1. If it is perfect and robust, output the word APPROVED, followed by the full final code block.\n2. If there are bugs or missing requirements, explain what needs to be fixed concisely." } } },
                { id: "5", type: "neural-output", position: { x: 1600, y: 200 }, data: { label: "Final Code" } }
            ],
            edges: [
                { id: "e1-2", source: "1", target: "2", animated: true },
                { id: "e2-3", source: "2", target: "3", sourceHandle: "loop", animated: true, style: { stroke: "#06b6d4" } },
                { id: "e3-4", source: "3", target: "4", animated: true },
                { id: "e4-2", source: "4", target: "2", animated: true, style: { stroke: "#ef4444", strokeDasharray: "5,5" } },
                { id: "e2-5", source: "2", target: "5", sourceHandle: "done", animated: true, style: { stroke: "#10b981" } }
            ]
        }
    },
    {
        id: 'template-parallel-test',
        name: '⚡ Parallel Speed Test',
        description: 'A benchmark workflow that executes 5 different AI models simultaneously. Useful for comparing speed and creative variety across different LLMs.',
        icon: 'PhSquaresFour',
        data: {
            nodes: [
                { id: "1", type: "neural-input", position: { x: 50, y: 450 }, data: { label: "Question", inputValue: "Write a haiku about artificial intelligence" } },
                { id: "2", type: "neural-llm", position: { x: 500, y: 50 }, data: { label: "Fast Model", node_config: { model: "openai/gpt-3.5-turbo", temperature: 0.8, systemPrompt: "You are a poet. Write a beautiful haiku." } } },
                { id: "3", type: "neural-llm", position: { x: 500, y: 250 }, data: { label: "Quality Model", node_config: { model: "openai/gpt-4-turbo", temperature: 0.7, systemPrompt: "You are a master poet. Write an exquisite haiku." } } },
                { id: "4", type: "neural-llm", position: { x: 500, y: 450 }, data: { label: "Creative Model", node_config: { model: "anthropic/claude-3.5-sonnet", temperature: 0.9, systemPrompt: "You are a creative poet. Write an innovative haiku." } } },
                { id: "5", type: "neural-llm", position: { x: 500, y: 650 }, data: { label: "Alternative Model", node_config: { model: "google/gemini-pro-1.5", temperature: 0.8, systemPrompt: "You are a unique poet. Write a distinctive haiku." } } },
                { id: "6", type: "neural-llm", position: { x: 500, y: 850 }, data: { label: "Open Source Model", node_config: { model: "meta-llama/llama-3.1-70b-instruct", temperature: 0.7, systemPrompt: "You are a poetic AI. Write a haiku." } } },
                { id: "7", type: "neural-output", position: { x: 1000, y: 450 }, data: { label: "All 5 Haikus" } }
            ],
            edges: [
                { id: "e1-2", source: "1", target: "2", animated: true },
                { id: "e1-3", source: "1", target: "3", animated: true },
                { id: "e1-4", source: "1", target: "4", animated: true },
                { id: "e1-5", source: "1", target: "5", animated: true },
                { id: "e1-6", source: "1", target: "6", animated: true },
                { id: "e2-7", source: "2", target: "7", animated: true },
                { id: "e3-7", source: "3", target: "7", animated: true },
                { id: "e4-7", source: "4", target: "7", animated: true },
                { id: "e5-7", source: "5", target: "7", animated: true },
                { id: "e6-7", source: "6", target: "7", animated: true }
            ]
        }
    },
    {
        id: 'template-diamond',
        name: '💎 The Diamond Pattern',
        description: 'A structured reasoning pattern where a topic is split into Pros and Cons by two separate agents, and then synthesized by a third agent into a balanced verdict.',
        icon: 'PhSquaresFour',
        data: {
            nodes: [
                { id: "1", type: "neural-input", position: { x: 50, y: 200 }, data: { label: "Topic", inputValue: "The future of renewable energy" } },
                { id: "2", type: "neural-llm", position: { x: 450, y: 50 }, data: { label: "Pros Analyst", node_config: { model: "openai/gpt-3.5-turbo", temperature: 0.5, systemPrompt: "List the TOP 3 advantages of this topic. Be concise and factual." } } },
                { id: "3", type: "neural-llm", position: { x: 450, y: 350 }, data: { label: "Cons Analyst", node_config: { model: "openai/gpt-3.5-turbo", temperature: 0.5, systemPrompt: "List the TOP 3 disadvantages or challenges of this topic. Be concise and critical." } } },
                { id: "4", type: "neural-llm", position: { x: 850, y: 200 }, data: { label: "Balanced Synthesizer", node_config: { model: "openai/gpt-4-turbo", temperature: 0.6, systemPrompt: "You will receive PROS and CONS for a topic. Write a balanced, nuanced analysis that acknowledges both sides. Conclude with your verdict." } } },
                { id: "5", type: "neural-output", position: { x: 1250, y: 200 }, data: { label: "Final Analysis" } }
            ],
            edges: [
                { id: "e1-2", source: "1", target: "2", animated: true },
                { id: "e1-3", source: "1", target: "3", animated: true },
                { id: "e2-4", source: "2", target: "4", animated: true },
                { id: "e3-4", source: "3", target: "4", animated: true },
                { id: "e4-5", source: "4", target: "5", animated: true }
            ]
        }
    },
    {
        id: 'template-research',
        name: '🔬 The Research Team',
        description: 'A comprehensive research workflow. It combines web search with multiple AI perspectives (Historical, Future, Expert) to produce a deep-dive report.',
        icon: 'PhSquaresFour',
        data: {
            nodes: [
                { id: "1", type: "neural-input", position: { x: 50, y: 350 }, data: { label: "Research Topic", inputValue: "Quantum Computing breakthroughs in 2024" } },
                { id: "2", type: "neural-search", position: { x: 400, y: 50 }, data: { label: "Web Search 1", node_config: { searchQuery: "" } } },
                { id: "3", type: "neural-search", position: { x: 400, y: 200 }, data: { label: "Web Search 2", node_config: { searchQuery: "" } } },
                { id: "4", type: "neural-llm", position: { x: 400, y: 350 }, data: { label: "Historical Context", node_config: { model: "openai/gpt-3.5-turbo", temperature: 0.3, systemPrompt: "Provide a brief history of this topic. Focus on key milestones." } } },
                { id: "5", type: "neural-llm", position: { x: 400, y: 500 }, data: { label: "Future Predictions", node_config: { model: "openai/gpt-3.5-turbo", temperature: 0.8, systemPrompt: "Make 3 bold predictions about the future of this topic in the next 5 years." } } },
                { id: "6", type: "neural-llm", position: { x: 400, y: 650 }, data: { label: "Expert Opinion", node_config: { model: "openai/gpt-4-turbo", temperature: 0.5, systemPrompt: "As a domain expert, provide your professional opinion on this topic. Be authoritative." } } },
                { id: "7", type: "neural-llm", position: { x: 850, y: 350 }, data: { label: "Master Compiler", node_config: { model: "openai/gpt-4-turbo", temperature: 0.6, systemPrompt: "Compile all research inputs into a comprehensive, well-structured report. Use markdown headings and bullet points." } } },
                { id: "8", type: "neural-output", position: { x: 1250, y: 350 }, data: { label: "Final Report" } }
            ],
            edges: [
                { id: "e1-2", source: "1", target: "2", animated: true },
                { id: "e1-3", source: "1", target: "3", animated: true },
                { id: "e1-4", source: "1", target: "4", animated: true },
                { id: "e1-5", source: "1", target: "5", animated: true },
                { id: "e1-6", source: "1", target: "6", animated: true },
                { id: "e2-7", source: "2", target: "7", animated: true },
                { id: "e3-7", source: "3", target: "7", animated: true },
                { id: "e4-7", source: "4", target: "7", animated: true },
                { id: "e5-7", source: "5", target: "7", animated: true },
                { id: "e6-7", source: "6", target: "7", animated: true },
                { id: "e7-8", source: "7", target: "8", animated: true }
            ]
        }
    },
    {
        id: 'template-fallback-test',
        name: '🛡️ Fallback System Test',
        description: 'Demonstrates system resilience. It purposely uses an invalid model ID to trigger the automatic fallback mechanism, ensuring workflow continuity.',
        icon: 'PhSquaresFour',
        data: {
            nodes: [
                { id: "1", type: "neural-input", position: { x: 50, y: 200 }, data: { label: "Prompt", inputValue: "Write a short poem about resilience" } },
                { id: "2", type: "neural-llm", position: { x: 450, y: 200 }, data: { label: "Broken Model → Auto Fallback", node_config: { model: "invalid/fake-model-that-will-fail", temperature: 0.7, systemPrompt: "You are a poet. Write a beautiful, short poem." } } },
                { id: "3", type: "neural-output", position: { x: 850, y: 200 }, data: { label: "Result (from fallback model)" } }
            ],
            edges: [
                { id: "e1-2", source: "1", target: "2", animated: true },
                { id: "e2-3", source: "2", target: "3", animated: true }
            ]
        }
    },
    {
        id: 'template-mapreduce',
        name: '📄 Document Analyzer (MapReduce)',
        description: 'A powerful method for processing large documents. The text is split into chunks, processed in parallel, and then summarized hierarchically to fit context windows.',
        icon: 'PhSquaresFour',
        data: {
            nodes: [
                {
                    id: "1",
                    type: "neural-input",
                    position: { x: 50, y: 300 },
                    data: {
                        label: "Long Document",
                        inputValue: "Artificial Intelligence has revolutionized numerous industries. In healthcare, AI systems can now diagnose diseases with accuracy rivaling human experts. Machine learning algorithms analyze medical images, patient records, and genetic data to identify patterns invisible to the human eye.\n\nIn finance, AI powers algorithmic trading, fraud detection, and personalized banking services. Natural language processing enables chatbots to handle customer service inquiries 24/7. Computer vision allows autonomous vehicles to navigate complex environments.\n\nThe education sector benefits from adaptive learning platforms that customize content to individual student needs. AI tutors provide instant feedback and identify knowledge gaps. In manufacturing, predictive maintenance systems prevent equipment failures before they occur.\n\nHowever, ethical concerns about AI bias, privacy, and job displacement remain critical challenges that society must address as the technology continues to advance at an unprecedented pace."
                    }
                },
                {
                    id: "2",
                    type: "neural-splitter",
                    position: { x: 450, y: 300 },
                    data: {
                        label: "Text Splitter",
                        node_config: {
                            chunk_size: 400,
                            overlap: 50,
                            strategy: "semantic"
                        }
                    }
                },
                {
                    id: "3",
                    type: "neural-reduce",
                    position: { x: 850, y: 300 },
                    data: {
                        label: "Hierarchical Reducer",
                        node_config: {
                            strategy: "hierarchical",
                            model: "openai/gpt-3.5-turbo",
                            temperature: 0.4,
                            prompt: "Summarize and synthesize the following content. Extract key insights and organize by topic."
                        }
                    }
                },
                {
                    id: "4",
                    type: "neural-output",
                    position: { x: 1250, y: 300 },
                    data: { label: "Final Summary" }
                }
            ],
            edges: [
                { id: "e1-2", source: "1", target: "2", animated: true },
                { id: "e2-3", source: "2", target: "3", animated: true },
                { id: "e3-4", source: "3", target: "4", animated: true }
            ]
        }
    },
    {
        id: 'template-self-consistency',
        name: '🎲 The Jury (Self-Consistency)',
        description: 'Enhances reliability by generating multiple answers to the same prompt and selecting the most consistent one via majority vote. Ideal for logic and math.',
        icon: 'PhSquaresFour',
        data: {
            nodes: [
                {
                    id: "1",
                    type: "neural-input",
                    position: { x: 50, y: 200 },
                    data: {
                        label: "Question",
                        inputValue: "If you flip a fair coin 3 times, what is the probability of getting exactly 2 heads?"
                    }
                },
                {
                    id: "2",
                    type: "neural-self-consistency",
                    position: { x: 450, y: 200 },
                    data: {
                        label: "Jury Deliberation",
                        node_config: {
                            model: "openai/gpt-3.5-turbo",
                            samples: 5,
                            voting: "majority",
                            temperature: 0.7
                        }
                    }
                },
                {
                    id: "3",
                    type: "neural-output",
                    position: { x: 850, y: 200 },
                    data: { label: "Consensus Answer" }
                }
            ],
            edges: [
                { id: "e1-2", source: "1", target: "2", animated: true },
                { id: "e2-3", source: "2", target: "3", animated: true }
            ]
        }
    },
    {
        id: 'template-moa',
        name: '🎭 The Think Tank (MoA)',
        description: 'Uses "Mixture-of-Agents" architecture. Several diverse models propose answers, and an aggregator model synthesizes them into a superior final response.',
        icon: 'PhSquaresFour',
        data: {
            nodes: [
                {
                    id: "1",
                    type: "neural-input",
                    position: { x: 50, y: 200 },
                    data: {
                        label: "Complex Question",
                        inputValue: "What are the most promising approaches to achieving Artificial General Intelligence (AGI) and what are the key challenges?"
                    }
                },
                {
                    id: "2",
                    type: "neural-moa-proposer",
                    position: { x: 450, y: 200 },
                    data: {
                        label: "Diverse Experts",
                        node_config: {
                            models: [
                                "openai/gpt-4-turbo",
                                "anthropic/claude-3.5-sonnet",
                                "openai/gpt-3.5-turbo"
                            ],
                            temperature: 0.7
                        }
                    }
                },
                {
                    id: "3",
                    type: "neural-moa-aggregator",
                    position: { x: 850, y: 200 },
                    data: {
                        label: "Master Synthesizer",
                        node_config: {
                            model: "openai/gpt-4-turbo",
                            temperature: 0.6,
                            strategy: "synthesis"
                        }
                    }
                },
                {
                    id: "4",
                    type: "neural-output",
                    position: { x: 1250, y: 200 },
                    data: { label: "Superior Answer" }
                }
            ],
            edges: [
                { id: "e1-2", source: "1", target: "2", animated: true },
                { id: "e2-3", source: "2", target: "3", animated: true },
                { id: "e3-4", source: "3", target: "4", animated: true }
            ]
        }
    },
    {
        id: 'template-debate',
        name: '⚔️ The Fact Checker (Debate)',
        description: 'Simulates a multi-round debate between opposing AI viewpoints. A Judge agent evaluates the arguments and declares a winner based on logic and evidence.',
        icon: 'PhSquaresFour',
        data: {
            nodes: [
                {
                    id: "1",
                    type: "neural-input",
                    position: { x: 50, y: 200 },
                    data: {
                        label: "Controversial Claim",
                        inputValue: "Remote work is more productive than office work for software development teams."
                    }
                },
                {
                    id: "2",
                    type: "neural-debate",
                    position: { x: 450, y: 200 },
                    data: {
                        label: "Debate Arena",
                        node_config: {
                            model: "openai/gpt-3.5-turbo",
                            debaters: 3,
                            rounds: 2,
                            temperature: 0.8
                        }
                    }
                },
                {
                    id: "3",
                    type: "neural-voting",
                    position: { x: 850, y: 200 },
                    data: {
                        label: "Supreme Judge",
                        node_config: {
                            model: "openai/gpt-4-turbo",
                            method: "judge",
                            temperature: 0.5
                        }
                    }
                },
                {
                    id: "4",
                    type: "neural-output",
                    position: { x: 1250, y: 200 },
                    data: { label: "Final Verdict" }
                }
            ],
            edges: [
                { id: "e1-2", source: "1", target: "2", animated: true },
                { id: "e2-3", source: "2", target: "3", animated: true },
                { id: "e3-4", source: "3", target: "4", animated: true }
            ]
        }
    },
    {
        id: 'template-moa-vs-debate',
        name: '⚔️ The Ultimate Battle: MoA vs Debate',
        description: 'A grand showcase comparing two advanced methodologies side-by-side. One path uses Mixture-of-Agents to synthesize an answer, while the other uses a Debate. A final Arbiter compares the results.',
        icon: 'PhSquaresFour',
        data: {
            nodes: [
                { id: "1", type: "neural-input", position: { x: 50, y: 400 }, data: { label: "The Big Question", inputValue: "Is Universal Basic Income (UBI) necessary for a post-AI economy? Analyze economic and social impacts." } },
                
                // Team MoA (Top)
                { id: "2", type: "neural-moa-proposer", position: { x: 500, y: 100 }, data: { label: "Team MoA: Proposers", node_config: { models: ["openai/gpt-4-turbo", "anthropic/claude-3.5-sonnet", "meta-llama/llama-3.1-70b-instruct"], temperature: 0.7 } } },
                { id: "3", type: "neural-moa-aggregator", position: { x: 900, y: 100 }, data: { label: "Team MoA: Aggregator", node_config: { model: "openai/gpt-4-turbo", temperature: 0.6, strategy: "synthesis" } } },
                
                // Team Debate (Bottom)
                { id: "4", type: "neural-debate", position: { x: 500, y: 600 }, data: { label: "Team Debate: Arena", node_config: { model: "openai/gpt-3.5-turbo", debaters: 3, rounds: 3, temperature: 0.8 } } },
                { id: "5", type: "neural-voting", position: { x: 900, y: 600 }, data: { label: "Team Debate: Judge", node_config: { model: "openai/gpt-4-turbo", method: "judge", temperature: 0.5 } } },
                
                // The Verdict
                { id: "6", type: "neural-llm", position: { x: 1350, y: 350 }, data: { label: "Grand Arbiter", node_config: { model: "openai/gpt-4-turbo", temperature: 0.5, systemPrompt: "You are the Grand Arbiter. You have received two high-quality analyses on the same topic from different AI methodologies (MoA and Debate).\n\n1. Compare the two approaches.\n2. Highlight the unique insights from each.\n3. Synthesize a final, definitive answer combining the best of both worlds." } } },
                { id: "7", type: "neural-output", position: { x: 1750, y: 350 }, data: { label: "Final Synthesis" } }
            ],
            edges: [
                // MoA Path
                { id: "e1-2", source: "1", target: "2", animated: true, style: { stroke: "#06b6d4" } },
                { id: "e2-3", source: "2", target: "3", animated: true, style: { stroke: "#06b6d4" } },
                { id: "e3-6", source: "3", target: "6", animated: true, style: { stroke: "#06b6d4" } },
                
                // Debate Path
                { id: "e1-4", source: "1", target: "4", animated: true, style: { stroke: "#ef4444" } },
                { id: "e4-5", source: "4", target: "5", animated: true, style: { stroke: "#ef4444" } },
                { id: "e5-6", source: "5", target: "6", animated: true, style: { stroke: "#ef4444" } },
                
                // Final
                { id: "e6-7", source: "6", target: "7", animated: true }
            ]
        }
    }
]

function open(initialMode: 'save' | 'load' = 'save') {
    mode.value = initialMode
    isOpen.value = true
    if (initialMode === 'load') {
        refreshList()
    }
}

function refreshList() {
    savedWorkflows.value = store.getSavedWorkflows().sort((a: any, b: any) => 
        new Date(b.savedAt).getTime() - new Date(a.savedAt).getTime()
    )
}

function handleSave() {
    if (!saveName.value.trim()) return
    store.saveWorkflow(saveName.value)
    isOpen.value = false
    saveName.value = ''
}

function handleLoad(id: string) {
    if (confirm('Loading a new workflow will overwrite the current canvas. Continue?')) {
        store.loadWorkflow(id)
        isOpen.value = false
    }
}

function handleLoadTemplate(template: any) {
    if (confirm(`Load template "${template.name}"? This will overwrite your canvas.`)) {
        try {
            // Use embedded data directly
            const flow = template.data
            
            // Deep copy to avoid reference issues
            const nodes = JSON.parse(JSON.stringify(flow.nodes))
            const edges = JSON.parse(JSON.stringify(flow.edges))

            store.setNodes(nodes)
            store.setEdges(edges)
            store.nodeStatus = {}
            store.isExecuting = false
            
            // Set current template info
            store.currentTemplate = {
                id: template.id,
                name: template.name,
                description: template.description
            }
            
            isOpen.value = false
        } catch (e) {
            console.error(e)
            alert('Error loading template: ' + e)
        }
    }
}

function handleDelete(id: string) {
    if (confirm('Are you sure you want to delete this workflow?')) {
        store.deleteWorkflow(id)
        refreshList()
    }
}

function reload(templateId: string) {
    const tpl = builtInTemplates.find(t => t.id === templateId)
    if (tpl) {
        try {
            const flow = tpl.data
            const nodes = JSON.parse(JSON.stringify(flow.nodes))
            const edges = JSON.parse(JSON.stringify(flow.edges))

            store.setNodes(nodes)
            store.setEdges(edges)
            store.nodeStatus = {}
            store.isExecuting = false
        } catch (e) {
            console.error(e)
        }
    }
}

defineExpose({ open, reload })
</script>

<template>
  <div v-if="isOpen" class="fixed inset-0 z-[100] flex items-center justify-center p-4">
    <div class="absolute inset-0 bg-black/60 backdrop-blur-sm" @click="isOpen = false"></div>
    
    <div class="relative bg-slate-900/90 border border-slate-700 rounded-lg p-6 w-full max-w-md shadow-2xl">
        <div class="flex justify-between items-center mb-6">
            <h2 class="text-xl font-bold text-slate-200 font-mono flex items-center gap-2">
                <PhFloppyDisk v-if="mode === 'save'" weight="bold" class="text-neon-blue" />
                <PhFolderOpen v-else weight="bold" class="text-neon-green" />
                {{ mode === 'save' ? 'SAVE WORKFLOW' : 'LOAD WORKFLOW' }}
            </h2>
            <button @click="isOpen = false" class="text-slate-500 hover:text-white">
                <PhX weight="bold" class="text-lg" />
            </button>
        </div>

        <!-- SAVE MODE -->
        <div v-if="mode === 'save'" class="space-y-4">
            <div>
                <label class="block text-xs text-slate-400 uppercase tracking-wider mb-2">Workflow Name</label>
                <input 
                    v-model="saveName"
                    type="text" 
                    placeholder="e.g. My Cooking Agent"
                    class="w-full bg-black/50 border border-slate-700 rounded text-sm text-slate-200 p-3 focus:border-neon-blue outline-none font-mono transition-all"
                    @keyup.enter="handleSave"
                />
            </div>
            <div class="flex justify-end">
                <button 
                    @click="handleSave"
                    class="px-6 py-2 bg-neon-blue/20 border border-neon-blue text-neon-blue rounded hover:bg-neon-blue hover:text-black transition-all font-bold text-xs"
                >
                    SAVE NOW
                </button>
            </div>
        </div>

        <!-- LOAD MODE -->
        <div v-else>
            <!-- Tabs -->
            <div class="flex gap-2 mb-4 border-b border-slate-700 pb-2">
                <button 
                    @click="loadTab = 'saved'"
                    class="px-3 py-1 text-xs font-bold rounded transition-colors"
                    :class="loadTab === 'saved' ? 'bg-slate-700 text-white' : 'text-slate-500 hover:text-slate-300'"
                >
                    SAVED
                </button>
                <button 
                    @click="loadTab = 'templates'"
                    class="px-3 py-1 text-xs font-bold rounded transition-colors flex items-center gap-1"
                    :class="loadTab === 'templates' ? 'bg-slate-700 text-neon-yellow' : 'text-slate-500 hover:text-slate-300'"
                >
                    <PhSquaresFour weight="bold" />
                    TEMPLATES
                </button>
            </div>

            <!-- SAVED LIST -->
            <div v-if="loadTab === 'saved'" class="space-y-3 max-h-[50vh] overflow-y-auto custom-scrollbar pr-2">
                <div v-if="savedWorkflows.length === 0" class="text-center text-slate-500 text-sm py-4 italic">
                    No saved workflows found.
                </div>
                
                <div v-for="flow in savedWorkflows" :key="flow.id" class="bg-black/30 border border-slate-800 rounded p-3 flex justify-between items-center hover:border-slate-600 transition-colors group">
                    <div>
                        <div class="font-bold text-slate-200 text-sm">{{ flow.name }}</div>
                        <div class="text-[10px] text-slate-500 mt-1">{{ new Date(flow.savedAt).toLocaleString() }} • {{ flow.nodes.length }} Nodes</div>
                    </div>
                    <div class="flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                        <button @click="handleLoad(flow.id)" class="px-3 py-1 bg-neon-green/10 border border-neon-green/50 text-neon-green rounded text-xs hover:bg-neon-green hover:text-black transition-colors">
                            LOAD
                        </button>
                        <button @click="handleDelete(flow.id)" class="p-1 text-slate-500 hover:text-neon-red transition-colors">
                            <PhTrash weight="bold" />
                        </button>
                    </div>
                </div>
            </div>

            <!-- TEMPLATES LIST -->
            <div v-else class="space-y-3 max-h-[50vh] overflow-y-auto custom-scrollbar pr-2">
                <div v-for="tpl in builtInTemplates" :key="tpl.id" class="bg-slate-800/30 border border-slate-700 rounded p-3 flex justify-between items-center hover:border-neon-yellow/50 transition-colors group cursor-pointer" @click="handleLoadTemplate(tpl)">
                    <div>
                        <div class="font-bold text-neon-yellow text-sm flex items-center gap-2">
                            {{ tpl.name }}
                        </div>
                        <div class="text-[10px] text-slate-400 mt-1 leading-snug">{{ tpl.description }}</div>
                    </div>
                    <button class="px-3 py-1 bg-neon-yellow/10 border border-neon-yellow/50 text-neon-yellow rounded text-xs group-hover:bg-neon-yellow group-hover:text-black transition-colors whitespace-nowrap">
                        USE
                    </button>
                </div>
            </div>
        </div>

    </div>
  </div>
</template>
