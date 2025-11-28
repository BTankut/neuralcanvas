<script setup lang="ts">
import { ref, markRaw, watch, nextTick } from 'vue'
import { VueFlow, useVueFlow } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import { Controls } from '@vue-flow/controls'
import { useWorkflowStore } from '../../stores/workflow'
import InputNode from '../nodes/InputNode.vue'
import LLMNode from '../nodes/LLMNode.vue'
import OutputNode from '../nodes/OutputNode.vue'
import ConditionalNode from '../nodes/ConditionalNode.vue'
import LoopNode from '../nodes/LoopNode.vue'
import SearchNode from '../nodes/SearchNode.vue'
import SplitterNode from '../nodes/SplitterNode.vue'
import ReduceNode from '../nodes/ReduceNode.vue'
import SelfConsistencyNode from '../nodes/SelfConsistencyNode.vue'
import MoAProposerNode from '../nodes/MoAProposerNode.vue'
import MoAAggregatorNode from '../nodes/MoAAggregatorNode.vue'
import DebateNode from '../nodes/DebateNode.vue'
import VotingNode from '../nodes/VotingNode.vue'
import SettingsModal from '../ui/SettingsModal.vue'
import ConnectionStatus from '../ui/ConnectionStatus.vue'
import CostDisplay from '../ui/CostDisplay.vue'
import ContextMenu from '../ui/ContextMenu.vue'
import PersistenceModal from '../ui/PersistenceModal.vue'
import { PhGearSix, PhSpinner, PhFloppyDisk, PhFolderOpen, PhArrowUUpLeft, PhArrowUUpRight, PhBroom, PhArrowCounterClockwise, PhInfo } from '@phosphor-icons/vue'
import { useMagicKeys, whenever } from '@vueuse/core'

import '@vue-flow/core/dist/style.css'
import '@vue-flow/core/dist/theme-default.css'
import '@vue-flow/controls/dist/style.css'

const store = useWorkflowStore()
const { onConnect, addEdges, toObject, setNodes, setEdges } = useVueFlow()
const settingsModal = ref()
const persistenceModal = ref()

// --- History Management (Undo/Redo) ---
const history = ref<string[]>([])
const historyIndex = ref(-1)
const isUndoRedoOperation = ref(false)

function saveState() {
    if (isUndoRedoOperation.value) return

    const currentState = JSON.stringify(toObject())
    
    // If we are in the middle of history, discard future states
    if (historyIndex.value < history.value.length - 1) {
        history.value = history.value.slice(0, historyIndex.value + 1)
    }
    
    // Avoid duplicate consecutive saves
    if (history.value[historyIndex.value] !== currentState) {
        history.value.push(currentState)
        historyIndex.value++
        
        // Limit history size
        if (history.value.length > 50) {
            history.value.shift()
            historyIndex.value--
        }
    }
}

async function undo() {
    if (historyIndex.value > 0) {
        isUndoRedoOperation.value = true
        historyIndex.value--
        const stateJson = history.value[historyIndex.value]
        if (stateJson) {
            const state = JSON.parse(stateJson)
            setNodes(state.nodes)
            setEdges(state.edges)
            await nextTick()
        }
        isUndoRedoOperation.value = false
    }
}

async function redo() {
    if (historyIndex.value < history.value.length - 1) {
        isUndoRedoOperation.value = true
        historyIndex.value++
        const stateJson = history.value[historyIndex.value]
        if (stateJson) {
            const state = JSON.parse(stateJson)
            setNodes(state.nodes)
            setEdges(state.edges)
            await nextTick()
        }
        isUndoRedoOperation.value = false
    }
}

function resetCanvas() {
    if (confirm('Are you sure you want to clear the entire canvas?')) {
        nodes.value = []
        edges.value = []
        store.currentTemplate = null // Reset template info
        saveState()
    }
}

function reloadTemplate() {
    if (store.currentTemplate && persistenceModal.value) {
        if (confirm(`Reload template "${store.currentTemplate.name}"? All changes will be lost.`)) {
            // We need to find the template object from the registry inside PersistenceModal.
            // Since that registry is private to that component, we can either move it to store or just trigger a reload method on the modal.
            // Easier way: Expose a 'reload' method on PersistenceModal.
            persistenceModal.value.reload(store.currentTemplate.id)
        }
    }
}

// Keyboard Shortcuts
const { Meta_Z, Ctrl_Z, Meta_Shift_Z, Ctrl_Y } = useMagicKeys()

if (Meta_Z) whenever(Meta_Z, () => undo())
if (Ctrl_Z) whenever(Ctrl_Z, () => undo())
if (Meta_Shift_Z) whenever(Meta_Shift_Z, () => redo())
if (Ctrl_Y) whenever(Ctrl_Y, () => redo())

// --- End History ---

const nodeTypes = {
  'neural-input': markRaw(InputNode),
  'neural-llm': markRaw(LLMNode),
  'neural-output': markRaw(OutputNode),
  'neural-condition': markRaw(ConditionalNode),
  'neural-loop': markRaw(LoopNode),
  'neural-search': markRaw(SearchNode),
  'neural-splitter': markRaw(SplitterNode),
  'neural-reduce': markRaw(ReduceNode),
  'neural-self-consistency': markRaw(SelfConsistencyNode),
  'neural-moa-proposer': markRaw(MoAProposerNode),
  'neural-moa-aggregator': markRaw(MoAAggregatorNode),
  'neural-debate': markRaw(DebateNode),
  'neural-voting': markRaw(VotingNode),
}

// Initial nodes
const nodes = ref([
  {
    id: '1',
    type: 'neural-input',
    position: { x: 50, y: 200 },
    data: { label: 'Start', inputValue: 'Loop Test Start' }
  },
  {
    id: '2',
    type: 'neural-loop',
    position: { x: 400, y: 200 },
    data: { label: 'Iterator', node_config: { max_iterations: 3 } }
  },
  {
    id: '3',
    type: 'neural-llm',
    position: { x: 800, y: 50 },
    data: { label: 'Looped Worker' }
  },
  {
    id: '4',
    type: 'neural-output',
    position: { x: 800, y: 350 },
    data: { label: 'Final Result' }
  },
])

const edges = ref([
  { id: 'e1-2', source: '1', target: '2', animated: true },
  // Loop Path: Loop Node -> AI Node
  { id: 'e2-3', source: '2', target: '3', sourceHandle: 'loop', animated: true, style: { stroke: '#06b6d4' } },
  // Loop Back: AI Node -> Loop Node (This closes the cycle)
  { id: 'e3-2', source: '3', target: '2', animated: true, style: { stroke: '#06b6d4', strokeDasharray: '5,5' } },
  // Done Path: Loop Node -> Output
  { id: 'e2-4', source: '2', target: '4', sourceHandle: 'done', animated: true, style: { stroke: '#10b981' } },
])

// Sync with store
// Watch local changes -> update store
watch(nodes, (newNodes) => {
    store.setNodes(newNodes)
    saveState() // Save for Undo
}, { deep: true })

watch(edges, (newEdges) => {
    store.setEdges(newEdges)
    saveState() // Save for Undo
}, { deep: true })

// Watch store changes (e.g. LOAD) -> update local
watch(() => store.nodes, (newNodes) => {
    if (JSON.stringify(newNodes) !== JSON.stringify(nodes.value)) {
        nodes.value = [...newNodes] as any
    }
}, { deep: true })

watch(() => store.edges, (newEdges) => {
    if (JSON.stringify(newEdges) !== JSON.stringify(edges.value)) {
        edges.value = [...newEdges] as any
    }
}, { deep: true })

onConnect((params) => addEdges(params))

</script>

<template>
  <div class="h-full w-full bg-void text-slate-200 relative">
    
    <!-- Header Toolbar -->
    <div class="absolute top-4 right-4 z-50 flex gap-3 items-center">
        
        <!-- Template Info (if loaded) -->
        <div v-if="store.currentTemplate" class="flex items-center gap-2 bg-slate-900/80 border border-slate-700 rounded-full px-3 py-1.5 backdrop-blur-md mr-2 group relative">
            <span class="text-xs font-bold text-neon-yellow tracking-wide">{{ store.currentTemplate.name }}</span>
            <PhInfo weight="bold" class="text-slate-400 cursor-help" />
            
            <!-- Tooltip -->
            <div class="absolute top-full right-0 mt-2 w-48 p-2 bg-slate-800 border border-slate-600 rounded text-[10px] text-slate-300 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50 shadow-xl">
                {{ store.currentTemplate.description }}
            </div>

            <!-- Reload Template -->
            <button @click="reloadTemplate" class="ml-2 p-1 hover:bg-slate-700 rounded-full text-slate-400 hover:text-white transition-colors" title="Reset Template">
                <PhArrowCounterClockwise weight="bold" />
            </button>
        </div>

        <!-- Status Indicators -->
        <div class="flex gap-2 mr-4 border-r border-slate-700 pr-4">
            <ConnectionStatus />
            <CostDisplay />
        </div>

        <!-- Main Controls -->
        <div class="flex gap-1 mr-4 border-r border-slate-700 pr-4">
            <button 
                @click="undo"
                class="w-10 h-10 flex items-center justify-center bg-slate-900/50 border border-slate-700 text-slate-400 rounded-full hover:bg-slate-800 hover:text-neon-blue transition-all backdrop-blur-md disabled:opacity-30"
                :disabled="historyIndex <= 0"
                title="Undo (Ctrl+Z)"
            >
                <PhArrowUUpLeft weight="bold" class="text-xl" />
            </button>
            <button 
                @click="redo"
                class="w-10 h-10 flex items-center justify-center bg-slate-900/50 border border-slate-700 text-slate-400 rounded-full hover:bg-slate-800 hover:text-neon-blue transition-all backdrop-blur-md disabled:opacity-30"
                :disabled="historyIndex >= history.length - 1"
                title="Redo (Ctrl+Y)"
            >
                <PhArrowUUpRight weight="bold" class="text-xl" />
            </button>
            <button 
                @click="resetCanvas"
                class="w-10 h-10 flex items-center justify-center bg-slate-900/50 border border-slate-700 text-slate-400 rounded-full hover:bg-slate-800 hover:text-neon-red transition-all backdrop-blur-md ml-2"
                title="Clear Canvas"
            >
                <PhBroom weight="bold" class="text-xl" />
            </button>
        </div>

        <!-- Persistence Controls -->
        <div class="flex gap-1 mr-4 border-r border-slate-700 pr-4">
            <button 
                @click="persistenceModal.open('save')"
                class="w-10 h-10 flex items-center justify-center bg-slate-900/50 border border-slate-700 text-slate-400 rounded-full hover:bg-slate-800 hover:text-neon-blue transition-all backdrop-blur-md"
                title="Save Workflow"
            >
                <PhFloppyDisk weight="bold" class="text-xl" />
            </button>
            <button 
                @click="persistenceModal.open('load')"
                class="w-10 h-10 flex items-center justify-center bg-slate-900/50 border border-slate-700 text-slate-400 rounded-full hover:bg-slate-800 hover:text-neon-green transition-all backdrop-blur-md"
                title="Load Workflow"
            >
                <PhFolderOpen weight="bold" class="text-xl" />
            </button>
        </div>

        <button 
            @click="settingsModal.open()"
            class="w-10 h-10 flex items-center justify-center bg-slate-900/50 border border-slate-700 text-slate-400 rounded-full hover:bg-slate-800 hover:text-white transition-all backdrop-blur-md"
            title="Settings"
        >
            <PhGearSix weight="bold" class="text-xl" />
        </button>

        <button 
            @click="store.runWorkflow"
            :disabled="store.isExecuting"
            class="px-6 py-2 bg-neon-blue/20 border border-neon-blue text-neon-blue rounded-full hover:bg-neon-blue hover:text-black transition-all font-bold shadow-[0_0_15px_rgba(59,130,246,0.5)] disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 backdrop-blur-md"
        >
            <PhSpinner v-if="store.isExecuting" class="animate-spin w-4 h-4" />
            <span v-if="!store.isExecuting">RUN FLOW</span>
            <span v-else>EXECUTING...</span>
        </button>
    </div>

    <SettingsModal ref="settingsModal" />
    <PersistenceModal ref="persistenceModal" />
    
    <VueFlow
      v-model="nodes"
      v-model:edges="edges"
      :node-types="nodeTypes as any"
      class="neural-flow"
      :default-zoom="1"
      :min-zoom="0.2"
      :max-zoom="4"
      fit-view-on-init
    >
      <Background pattern-color="#3b82f6" :gap="20" :size="1" class="opacity-10" />
      <Controls class="bg-slate-900 border border-slate-700 text-slate-200" />
      <ContextMenu />
    </VueFlow>
  </div>
</template>

<style>
@reference "../../style.css";

.neural-flow .vue-flow__edge-path {
  @apply stroke-neon-blue;
  stroke-width: 2;
  filter: drop-shadow(0 0 3px rgba(59, 130, 246, 0.5));
}

/* Global styles for node components to share */
.neural-node-base {
  @apply bg-slate-900/80 border border-slate-700 rounded-lg shadow-lg backdrop-blur-md transition-all duration-300;
  font-family: 'Inter', sans-serif;
}

.neural-node-base:hover {
  @apply border-neon-blue shadow-[0_0_15px_rgba(59,130,246,0.3)];
}

.neural-node-base.selected {
  @apply border-neon-purple shadow-[0_0_20px_rgba(139,92,246,0.4)];
}

.node-header {
  @apply px-3 py-2 rounded-t-lg flex items-center;
}

.neural-handle {
  @apply !bg-black !border-2 !border-white !w-3 !h-3;
  transition: all 0.2s;
}

.neural-handle:hover {
  @apply !bg-neon-blue !border-neon-blue !transform !scale-125;
}
</style>