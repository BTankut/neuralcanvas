<script setup lang="ts">
import { ref, markRaw, watch } from 'vue'
import { VueFlow, useVueFlow } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import { Controls } from '@vue-flow/controls'
import { PhGearSix, PhSpinner } from '@phosphor-icons/vue'
import { useWorkflowStore } from '../../stores/workflow'
import InputNode from '../nodes/InputNode.vue'
import LLMNode from '../nodes/LLMNode.vue'
import OutputNode from '../nodes/OutputNode.vue'
import ConditionalNode from '../nodes/ConditionalNode.vue'
import LoopNode from '../nodes/LoopNode.vue'
import SearchNode from '../nodes/SearchNode.vue'
import SettingsModal from '../ui/SettingsModal.vue'
import ConnectionStatus from '../ui/ConnectionStatus.vue'
import CostDisplay from '../ui/CostDisplay.vue'
import ContextMenu from '../ui/ContextMenu.vue'

import '@vue-flow/core/dist/style.css'
import '@vue-flow/core/dist/theme-default.css'
import '@vue-flow/controls/dist/style.css'

const store = useWorkflowStore()
const { onConnect, addEdges } = useVueFlow()
const settingsModal = ref()

const nodeTypes = {
  'neural-input': markRaw(InputNode),
  'neural-llm': markRaw(LLMNode),
  'neural-output': markRaw(OutputNode),
  'neural-condition': markRaw(ConditionalNode),
  'neural-loop': markRaw(LoopNode),
  'neural-search': markRaw(SearchNode),
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
watch(nodes, (newNodes) => store.setNodes(newNodes), { deep: true, immediate: true })
watch(edges, (newEdges) => store.setEdges(newEdges), { deep: true, immediate: true })

onConnect((params) => addEdges(params))

</script>

<template>
  <div class="h-full w-full bg-void text-slate-200 relative">
    
    <!-- Floating Action Button for Run -->
    <div class="absolute top-4 right-4 z-50 flex gap-3">
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
    <ConnectionStatus />
    <CostDisplay />
    
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