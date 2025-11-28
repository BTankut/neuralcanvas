<script setup lang="ts">
import { Handle, Position, useNode, useNodeId } from '@vue-flow/core'
import { ref, watch, computed } from 'vue'
import { useWorkflowStore } from '../../stores/workflow'

const { node } = useNode()
const nodeId = useNodeId()
const store = useWorkflowStore()

// Configuration
const model = ref(node.data?.node_config?.model || 'openai/gpt-4-turbo')
const method = ref(node.data?.node_config?.method || 'judge')
const temperature = ref(node.data?.node_config?.temperature || 0.5)

// Sync changes back to node data
watch([model, method, temperature], ([newModel, newMethod, newTemp]) => {
    node.data = {
        ...node.data,
        node_config: {
            ...node.data?.node_config,
            model: newModel,
            method: newMethod,
            temperature: newTemp
        }
    }
})

// Sync node data -> local state (for loading templates)
watch(() => node.data?.node_config?.model, (newVal) => {
    if (newVal !== undefined && newVal !== model.value) model.value = newVal
})
watch(() => node.data?.node_config?.method, (newVal) => {
    if (newVal !== undefined && newVal !== method.value) method.value = newVal
})
watch(() => node.data?.node_config?.temperature, (newVal) => {
    if (newVal !== undefined && newVal !== temperature.value) temperature.value = newVal
})

const status = computed(() => store.nodeStatus[nodeId] || { status: 'idle' } as any)
const isRunning = computed(() => status.value.status === 'running')
const streamText = computed(() => status.value.stream || '')

const selectedModelName = computed(() => {
    const found = store.availableModels.find(m => m.id === model.value)
    return found ? found.name : model.value
})
</script>

<template>
  <div 
    class="neural-node-base voting-node w-64 relative transition-all duration-300 group"
    :class="{
        'ring-2 ring-neon-purple shadow-[0_0_30px_rgba(168,85,247,0.6)]': isRunning,
        'border-neon-purple': true
    }"
  >
    <!-- Glowing Icon Badge -->
    <div class="absolute -top-6 -left-4 w-12 h-12 bg-slate-900 rounded-xl border border-neon-purple/50 shadow-[0_0_15px_rgba(168,85,247,0.5)] flex items-center justify-center z-20 transform group-hover:scale-110 transition-all duration-300">
        <img src="/assets/icons/vote.png" class="w-8 h-8 object-contain" :class="{'animate-pulse': isRunning}" alt="Voting" />
    </div>

    <!-- Header -->
    <div class="node-header bg-neon-purple/20 border-b border-neon-purple/30 text-neon-purple flex justify-center items-center min-h-[40px] relative pl-6">
        <span class="font-bold text-xs tracking-wider uppercase">Judge / Voting</span>
        <span v-if="status.status === 'success'" class="absolute right-2 text-[9px] font-bold text-neon-green">DECIDED</span>
    </div>


        <div class="node-body p-3 space-y-3">
            <!-- Live Stream Display -->
            <div v-if="streamText" class="bg-black/50 border border-amber-500/50 rounded h-40 flex flex-col">
                <div class="bg-slate-800/50 px-2 py-1 border-b border-slate-700 flex justify-between items-center">
                    <span class="text-[9px] text-amber-500 font-bold uppercase tracking-wider truncate pr-2">
                        {{ selectedModelName }}
                    </span>
                    <div class="flex gap-2 items-center">
                         <span v-if="status.status === 'success'" class="text-[9px] text-neon-green">VERDICT</span>
                    </div>
                </div>

                <div class="p-2 text-[10px] font-mono text-slate-300 overflow-y-auto custom-scrollbar flex-1 nodrag cursor-text select-text">
                    {{ streamText }}<span v-if="isRunning" class="animate-pulse text-amber-500">_</span>
                </div>
            </div>

            <!-- Configuration -->
            <div v-else class="space-y-3">
                <div>
                    <label class="text-[10px] text-slate-400 mb-1 block uppercase">Judge Model</label>
                    <select v-model="model" class="w-full bg-black/50 border border-slate-700 rounded text-xs text-slate-200 p-1 focus:border-amber-500 outline-none">
                        <option v-if="store.isLoadingModels" disabled value="">Loading models...</option>
                        <optgroup v-for="cat in store.categorizedModels" :key="cat.category" :label="cat.category">
                            <option v-for="m in cat.models" :key="m.id" :value="m.id">
                                {{ m.name }}
                            </option>
                        </optgroup>
                    </select>
                    <span class="text-[9px] text-slate-500">Use strong model for best judgment</span>
                </div>

                <div>
                    <label class="text-[10px] text-slate-400 mb-1 block uppercase">Voting Method</label>
                    <select v-model="method" class="w-full bg-black/50 border border-slate-700 rounded text-xs text-slate-200 p-1 focus:border-amber-500 outline-none">
                        <option value="judge">Judge (Evaluate Debate)</option>
                        <option value="consensus">Consensus Finding</option>
                        <option value="count">Simple Count</option>
                    </select>
                </div>

                <div>
                    <label class="text-[10px] text-slate-400 mb-1 block uppercase">Temperature</label>
                    <input
                        v-model.number="temperature"
                        type="range"
                        min="0"
                        max="2"
                        step="0.1"
                        class="w-full accent-amber-500"
                    />
                    <span class="text-[9px] text-slate-500">{{ temperature }}</span>
                </div>
            </div>
        </div>

    <Handle type="target" :position="Position.Left" class="neural-handle" />
    <Handle type="source" :position="Position.Right" class="neural-handle" />
  </div>
</template>

<style scoped>
.voting-node {
    border: 2px solid rgba(245, 158, 11, 0.3);
}
</style>
