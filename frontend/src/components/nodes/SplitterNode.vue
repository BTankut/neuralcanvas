<script setup lang="ts">
import { Handle, Position, useNode, useNodeId } from '@vue-flow/core'
import { ref, watch, computed } from 'vue'
import { useWorkflowStore } from '../../stores/workflow'

const { node } = useNode()
const nodeId = useNodeId()
const store = useWorkflowStore()

// Configuration
const chunkSize = ref(node.data?.node_config?.chunk_size || 2000)
const overlap = ref(node.data?.node_config?.overlap || 200)
const strategy = ref(node.data?.node_config?.strategy || 'semantic')

// Sync changes back to node data
watch([chunkSize, overlap, strategy], ([newSize, newOverlap, newStrategy]) => {
    node.data = {
        ...node.data,
        node_config: {
            ...node.data?.node_config,
            chunk_size: newSize,
            overlap: newOverlap,
            strategy: newStrategy
        }
    }
})

// Sync node data -> local state (for loading templates)
watch(() => node.data?.node_config?.chunk_size, (newVal) => {
    if (newVal !== undefined && newVal !== chunkSize.value) chunkSize.value = newVal
})
watch(() => node.data?.node_config?.overlap, (newVal) => {
    if (newVal !== undefined && newVal !== overlap.value) overlap.value = newVal
})
watch(() => node.data?.node_config?.strategy, (newVal) => {
    if (newVal !== undefined && newVal !== strategy.value) strategy.value = newVal
})

const status = computed(() => store.nodeStatus[nodeId] || { status: 'idle' } as any)
const isRunning = computed(() => status.value.status === 'running')
const result = computed(() => {
    if (status.value.result && typeof status.value.result === 'object') {
        return status.value.result
    }
    return null
})
</script>

<template>
  <div 
    class="neural-node-base splitter-node w-64 relative transition-all duration-300 group"
    :class="{
        'ring-2 ring-neon-yellow shadow-[0_0_30px_rgba(234,179,8,0.6)]': isRunning,
        'border-neon-yellow': true
    }"
  >
    <!-- Glowing Icon Badge -->
    <div class="absolute -top-6 -left-4 w-12 h-12 bg-slate-900 rounded-xl border border-neon-yellow/50 shadow-[0_0_15px_rgba(234,179,8,0.5)] flex items-center justify-center z-20 transform group-hover:scale-110 transition-all duration-300">
        <img src="/assets/icons/split.png" class="w-8 h-8 object-contain" :class="{'animate-pulse': isRunning}" alt="Split" />
    </div>

    <!-- Header -->
    <div class="node-header bg-neon-yellow/20 border-b border-neon-yellow/30 text-neon-yellow flex justify-center items-center min-h-[40px] relative pl-6">
        <span class="font-bold text-xs tracking-wider uppercase">Text Splitter</span>
        <span v-if="status.chunks" class="absolute right-2 text-[9px] font-bold text-neon-blue">{{ status.chunks }} CHUNKS</span>
    </div>

        <div class="node-body p-3 space-y-3">
            <!-- Result Display -->
            <div v-if="result" class="bg-black/50 border border-orange-500/50 rounded p-2">
                <div class="text-[10px] text-slate-400 mb-1">Split Result</div>
                <div class="text-xs text-orange-400 font-mono">
                    📄 {{ result.num_chunks }} chunks created
                </div>
                <div class="text-[9px] text-slate-500 mt-1">
                    {{ result.chunk_size }} chars/chunk
                </div>
            </div>

            <!-- Configuration -->
            <div v-else class="space-y-3">
                <div>
                    <label class="text-[10px] text-slate-400 mb-1 block uppercase">Strategy</label>
                    <select v-model="strategy" class="w-full bg-black/50 border border-slate-700 rounded text-xs text-slate-200 p-1 focus:border-orange-500 outline-none">
                        <option value="semantic">Semantic (Paragraphs)</option>
                        <option value="sliding">Sliding Window</option>
                        <option value="fixed">Fixed Size</option>
                    </select>
                </div>

                <div>
                    <label class="text-[10px] text-slate-400 mb-1 block uppercase">Chunk Size</label>
                    <input
                        v-model.number="chunkSize"
                        type="number"
                        min="100"
                        max="10000"
                        step="100"
                        class="w-full bg-black/50 border border-slate-700 rounded text-xs text-slate-200 p-1 focus:border-orange-500 outline-none"
                    />
                </div>

                <div>
                    <label class="text-[10px] text-slate-400 mb-1 block uppercase">Overlap</label>
                    <input
                        v-model.number="overlap"
                        type="number"
                        min="0"
                        max="1000"
                        step="50"
                        class="w-full bg-black/50 border border-slate-700 rounded text-xs text-slate-200 p-1 focus:border-orange-500 outline-none"
                    />
                </div>
            </div>
        </div>

    <Handle type="target" :position="Position.Left" class="neural-handle" />
    <Handle type="source" :position="Position.Right" class="neural-handle" />
  </div>
</template>

<style scoped>
.splitter-node {
    border: 2px solid rgba(249, 115, 22, 0.3);
}
</style>
