<script setup lang="ts">
import { Handle, Position, useNode, useNodeId } from '@vue-flow/core'
import { ref, watch, computed } from 'vue'
import { useWorkflowStore } from '../../stores/workflow'

const props = defineProps(['data'])
const nodeId = useNodeId()
const store = useWorkflowStore()
const { node } = useNode()

// Config State
const searchQuery = ref(node.data?.node_config?.searchQuery || '')

// Sync config local -> node
watch(searchQuery, (val) => {
    node.data = {
        ...node.data,
        node_config: {
            ...node.data?.node_config,
            searchQuery: val
        }
    }
})

// Sync node -> local (Fix for loading templates)
watch(() => node.data?.node_config?.searchQuery, (newVal) => {
    if (newVal !== undefined && newVal !== searchQuery.value) {
        searchQuery.value = newVal
    }
})

// Execution State
const status = computed(() => store.nodeStatus[nodeId] || { status: 'idle' } as any)
const isRunning = computed(() => status.value.status === 'running')
const result = computed(() => status.value.result)

</script>

<template>
  <div 
    class="neural-node-base search-node w-64 relative transition-all duration-300 group"
    :class="{
        'ring-2 ring-neon-orange shadow-[0_0_30px_rgba(249,115,22,0.6)]': isRunning,
        'border-neon-orange': true
    }"
  >
    <!-- Glowing Icon Badge -->
    <div class="absolute -top-6 -left-4 w-12 h-12 bg-slate-900 rounded-xl border border-neon-orange/50 shadow-[0_0_15px_rgba(249,115,22,0.5)] flex items-center justify-center z-20 transform group-hover:scale-110 transition-all duration-300">
        <img src="/assets/icons/web-search.png" class="w-8 h-8 object-contain" :class="{'animate-pulse': isRunning}" alt="Search" />
    </div>

    <!-- Header -->
    <div class="node-header bg-neon-orange/20 border-b border-neon-orange/30 text-neon-orange flex justify-center items-center min-h-[40px] relative">
        <div class="flex items-center">
            <span class="font-bold text-xs tracking-wider uppercase">Web Search</span>
        </div>
        <span v-if="status.status === 'success'" class="absolute right-2 text-[9px] text-neon-green font-bold">FOUND</span>
    </div>
    
    <!-- Body -->
    <div class="node-body p-3 space-y-3">
        <div v-if="result" class="max-h-32 overflow-y-auto custom-scrollbar text-[10px] font-mono text-slate-300">
            {{ result.slice(0, 150) }}...
        </div>
        <div v-else>
            <label class="text-[10px] text-slate-400 mb-1 block uppercase">Search Query</label>
            <input 
                type="text" 
                v-model="searchQuery"
                placeholder="Leave empty to use input..."
                class="w-full bg-black/50 border border-slate-700 rounded text-xs text-slate-200 p-2 focus:border-neon-orange outline-none"
            />
            <div class="text-[9px] text-slate-500 mt-1 italic">
                If empty, uses data from previous node.
            </div>
        </div>
    </div>

    <!-- Handles -->
    <Handle type="target" :position="Position.Left" class="neural-handle !bg-slate-200" />
    <Handle type="source" :position="Position.Right" class="neural-handle !bg-neon-orange !border-neon-orange" />

  </div>
</template>

<style scoped>
@reference "../../style.css";

.neural-node-base.search-node {
    @apply border-orange-500/50;
}
</style>
