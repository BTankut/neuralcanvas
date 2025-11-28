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
        description: 'Searches web for news and writes an article.',
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
                { id: "e3-4", source: "3", "target": "4", "animated": true }
            ]
        }
    },
    {
        id: 'template-refiner',
        name: 'The Idea Refiner',
        description: 'Iteratively improves an idea 3 times using a loop.',
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
        description: 'Routes messages based on sentiment (Angry vs Happy).',
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
        description: 'Orchestrates 3 specialized agents (Analyst, Creative, Finance) to solve a task.',
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

defineExpose({ open })
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
                        <div class="text-[10px] text-slate-400 mt-1">{{ tpl.description }}</div>
                    </div>
                    <button class="px-3 py-1 bg-neon-yellow/10 border border-neon-yellow/50 text-neon-yellow rounded text-xs group-hover:bg-neon-yellow group-hover:text-black transition-colors">
                        USE
                    </button>
                </div>
            </div>
        </div>

    </div>
  </div>
</template>