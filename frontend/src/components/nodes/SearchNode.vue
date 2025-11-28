<script setup lang="ts">
import { Handle, Position, useNode, useNodeId } from '@vue-flow/core'
import { ref, watch, computed, onMounted, onUnmounted } from 'vue'
import { useWorkflowStore } from '../../stores/workflow'
import { PhArrowsOutSimple, PhX } from '@phosphor-icons/vue'

const { node } = useNode()
const nodeId = useNodeId()
const store = useWorkflowStore()
const isExpanded = ref(false)

// Close on ESC
const handleKeydown = (e: KeyboardEvent) => {
    if (isExpanded.value && e.key === 'Escape') {
        isExpanded.value = false
    }
}

onMounted(() => window.addEventListener('keydown', handleKeydown))
onUnmounted(() => window.removeEventListener('keydown', handleKeydown))

// Configuration
const searchQuery = ref(node.data?.node_config?.searchQuery || '')

// Sync changes back to node data
watch(searchQuery, (newQuery) => {
    node.data = {
        ...node.data,
        node_config: {
            ...node.data?.node_config,
            searchQuery: newQuery
        }
    }
})

// Sync node data -> local state
watch(() => node.data?.node_config?.searchQuery, (newVal) => { if (newVal !== undefined && newVal !== searchQuery.value) searchQuery.value = newVal })

const status = computed(() => store.nodeStatus[nodeId] || { status: 'idle' } as any)
const isRunning = computed(() => status.value.status === 'running')
const result = computed(() => status.value.result) // Search results usually come as final result, not stream
</script>

<template>
  <div 
    class="neural-node-base search-node w-64 relative transition-all duration-300 group"
    :class="{
        'ring-2 ring-cyan-500 shadow-[0_0_30px_rgba(6,182,212,0.6)]': isRunning,
        'border-cyan-500': true
    }"
  >
    <!-- Glowing Icon Badge -->
    <div class="absolute -top-6 -left-4 w-12 h-12 bg-slate-900 rounded-xl border border-cyan-500/50 shadow-[0_0_15px_rgba(6,182,212,0.5)] flex items-center justify-center z-20 transform group-hover:scale-110 transition-all duration-300">
        <img src="/assets/icons/web-search.png" class="w-8 h-8 object-contain" :class="{'animate-pulse': isRunning}" alt="Search" />
    </div>

    <!-- Expand Button -->
    <button @click="isExpanded = true" class="absolute top-2 right-2 text-slate-500 hover:text-cyan-500 transition-colors z-30">
        <PhArrowsOutSimple weight="bold" />
    </button>

    <!-- Header -->
    <div class="node-header bg-cyan-500/20 border-b border-cyan-500/30 text-cyan-500 flex justify-center items-center min-h-[40px] relative pl-6">
        <span class="font-bold text-xs tracking-wider uppercase">Web Search</span>
        <span v-if="status.status === 'success'" class="absolute right-2 text-[9px] font-bold text-neon-green">FOUND</span>
    </div>

    <div class="node-body p-3 space-y-3">
        <!-- Result Preview -->
        <div v-if="result" class="bg-black/50 border border-cyan-500/50 rounded h-24 overflow-hidden relative group/preview">
            <div class="absolute top-0 left-0 bg-cyan-500/20 text-cyan-500 text-[9px] font-bold px-1">RESULTS</div>
            <div class="p-2 text-[10px] font-mono text-slate-300 pt-4">
                {{ (typeof result === 'string' ? result : JSON.stringify(result, null, 2)).substring(0, 150) }}...
            </div>
        </div>

        <!-- Configuration -->
        <div v-else class="space-y-3">
            <div>
                <label class="text-[10px] text-slate-400 mb-1 block uppercase">Search Query</label>
                <textarea
                    v-model="searchQuery"
                    class="w-full bg-black/50 border border-slate-700 rounded text-xs text-slate-200 p-2 focus:border-cyan-500 outline-none resize-none h-16 font-mono"
                    placeholder="Leave empty to use input from previous node..."
                ></textarea>
            </div>
        </div>
    </div>

    <Handle type="target" :position="Position.Left" class="neural-handle" />
    <Handle type="source" :position="Position.Right" class="neural-handle" />

    <!-- Expanded Modal -->
    <Teleport to="body">
        <div v-if="isExpanded" class="fixed inset-0 z-[100] flex items-center justify-center p-8 bg-black/80 backdrop-blur-sm" @click="isExpanded = false">
            <div class="bg-slate-900 border border-cyan-500 rounded-lg w-full max-w-4xl h-[80vh] flex flex-col shadow-2xl relative" @click.stop>
                <div class="flex justify-between items-center p-4 border-b border-slate-700">
                    <h2 class="text-cyan-500 font-mono font-bold text-lg">SEARCH RESULTS</h2>
                    <button @click="isExpanded = false" class="text-slate-400 hover:text-white">
                        <PhX weight="bold" class="text-xl" />
                    </button>
                </div>
                <div class="w-full h-full bg-black/50 text-slate-200 p-6 overflow-y-auto custom-scrollbar font-mono text-sm leading-relaxed whitespace-pre-wrap">
                    {{ result ? (typeof result === 'string' ? result : JSON.stringify(result, null, 2)) : 'No search results yet.' }}
                </div>
                <div class="p-2 bg-slate-800/50 text-center text-[10px] text-slate-500">
                    Press ESC to close
                </div>
            </div>
        </div>
    </Teleport>
  </div>
</template>

<style scoped>
.search-node {
    border: 2px solid rgba(6, 182, 212, 0.3);
}
</style>