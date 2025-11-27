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

// Hardcoded template registry (since we can't fs.readdir in browser easily without build steps)
const builtInTemplates = [
    {
        id: 'template-journalist',
        name: 'The Tech Journalist',
        description: 'Searches web for news and writes an article.',
        file: '/templates/journalist.json',
        icon: 'PhNewspaper'
    },
    {
        id: 'template-refiner',
        name: 'The Idea Refiner',
        description: 'Iteratively improves an idea 3 times using a loop.',
        file: '/templates/refiner.json',
        icon: 'PhLightbulb'
    },
    {
        id: 'template-router',
        name: 'The Support Router',
        description: 'Routes messages based on sentiment (Angry vs Happy).',
        file: '/templates/router.json',
        icon: 'PhGitFork'
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

async function handleLoadTemplate(template: any) {
    if (confirm(`Load template "${template.name}"? This will overwrite your canvas.`)) {
        try {
            const res = await fetch(template.file)
            if (!res.ok) throw new Error('Failed to load template file')
            const flow = await res.json()
            
            // Reset store with template data
            store.setNodes(flow.nodes)
            store.setEdges(flow.edges)
            store.nodeStatus = {}
            store.isExecuting = false
            
            isOpen.value = false
        } catch (e) {
            console.error(e)
            alert('Error loading template.')
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
