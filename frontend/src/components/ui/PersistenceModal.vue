<script setup lang="ts">
import { ref } from 'vue'
import { useWorkflowStore } from '../../stores/workflow'
import { PhFloppyDisk, PhFolderOpen, PhTrash, PhX, PhSquaresFour, PhSpinner } from '@phosphor-icons/vue'

const store = useWorkflowStore()
const isOpen = ref(false)
const mode = ref<'save' | 'load'>('save')
const loadTab = ref<'saved' | 'templates'>('saved')
const saveName = ref('')
const savedWorkflows = ref<any[]>([])

// Template System State
const templates = ref<any[]>([])
const isLoadingTemplates = ref(false)
const templateError = ref<string | null>(null)

// Fetch template index from server
async function loadTemplateIndex() {
    if (templates.value.length > 0) return // Already loaded
    
    isLoadingTemplates.value = true
    templateError.value = null
    try {
        const res = await fetch('/templates/index.json')
        if (!res.ok) throw new Error('Failed to load template index')
        templates.value = await res.json()
    } catch (e: any) {
        console.error("Template Load Error:", e)
        templateError.value = "Failed to load templates. Please try again."
    } finally {
        isLoadingTemplates.value = false
    }
}

function open(initialMode: 'save' | 'load' = 'save') {
    mode.value = initialMode
    isOpen.value = true
    if (initialMode === 'load') {
        refreshList()
        if (loadTab.value === 'templates') {
            loadTemplateIndex()
        }
    }
}

function switchTab(tab: 'saved' | 'templates') {
    loadTab.value = tab
    if (tab === 'templates') {
        loadTemplateIndex()
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
            // Fetch the specific template file
            const res = await fetch(template.file)
            if (!res.ok) throw new Error(`Failed to load template file: ${template.file}`)
            
            const flow = await res.json()
            
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
        } catch (e: any) {
            console.error(e)
            alert('Error loading template: ' + e.message)
        }
    }
}

function handleDelete(id: string) {
    if (confirm('Are you sure you want to delete this workflow?')) {
        store.deleteWorkflow(id)
        refreshList()
    }
}

// External reload (used by Reset button in FlowCanvas)
async function reload(templateId: string) {
    // Ensure index is loaded
    if (templates.value.length === 0) {
        await loadTemplateIndex()
    }

    const tpl = templates.value.find(t => t.id === templateId)
    if (tpl) {
        handleLoadTemplate(tpl)
    } else {
        console.error(`Template ${templateId} not found`)
    }
}

defineExpose({ open, reload })
</script>

<template>
  <div v-if="isOpen" class="fixed inset-0 z-[100] flex items-center justify-center p-4">
    <div class="absolute inset-0 bg-black/60 backdrop-blur-sm" @click="isOpen = false"></div>
    
    <div class="relative bg-slate-900/90 border border-slate-700 rounded-lg p-6 w-full max-w-md shadow-2xl transition-all">
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
                    @click="switchTab('saved')"
                    class="px-3 py-1 text-xs font-bold rounded transition-colors"
                    :class="loadTab === 'saved' ? 'bg-slate-700 text-white' : 'text-slate-500 hover:text-slate-300'"
                >
                    SAVED
                </button>
                <button 
                    @click="switchTab('templates')"
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
                <!-- Loading State -->
                <div v-if="isLoadingTemplates" class="flex justify-center py-8 text-neon-yellow">
                    <PhSpinner class="animate-spin text-2xl" />
                </div>

                <!-- Error State -->
                <div v-else-if="templateError" class="text-center py-8 text-neon-red text-sm">
                    {{ templateError }}
                    <button @click="loadTemplateIndex" class="block mx-auto mt-2 text-xs underline">Try Again</button>
                </div>

                <!-- List State -->
                <div v-else>
                    <div v-for="tpl in templates" :key="tpl.id" class="bg-slate-800/30 border border-slate-700 rounded p-3 flex justify-between items-center hover:border-neon-yellow/50 transition-colors group cursor-pointer mb-3" @click="handleLoadTemplate(tpl)">
                        <div>
                            <div class="font-bold text-neon-yellow text-sm flex items-center gap-2">
                                {{ tpl.name }}
                            </div>
                            <div class="text-[10px] text-slate-400 mt-1 leading-snug">{{ tpl.description }}</div>
                        </div>
                        <button class="px-3 py-1 bg-neon-yellow/10 border border-neon-yellow/50 text-neon-yellow rounded text-xs group-hover:bg-neon-yellow group-hover:text-black transition-colors whitespace-nowrap ml-2">
                            USE
                        </button>
                    </div>
                </div>
            </div>
        </div>

    </div>
  </div>
</template>
