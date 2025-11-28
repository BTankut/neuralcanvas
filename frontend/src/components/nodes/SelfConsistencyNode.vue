<script setup lang="ts">
import { Handle, Position, useNode, useNodeId } from '@vue-flow/core'
import { ref, watch, computed } from 'vue'
import { useWorkflowStore } from '../../stores/workflow'

const { node } = useNode()
const nodeId = useNodeId()
const store = useWorkflowStore()

// Configuration
const model = ref(node.data?.node_config?.model || 'openai/gpt-3.5-turbo')
const samples = ref(node.data?.node_config?.samples || 5)
const voting = ref(node.data?.node_config?.voting || 'majority')
const temperature = ref(node.data?.node_config?.temperature || 0.7)

// Sync changes back to node data
watch([model, samples, voting, temperature], ([newModel, newSamples, newVoting, newTemp]) => {
    node.data = {
        ...node.data,
        node_config: {
            ...node.data?.node_config,
            model: newModel,
            samples: newSamples,
            voting: newVoting,
            temperature: newTemp
        }
    }
})

// Sync node data -> local state (for loading templates)
watch(() => node.data?.node_config?.model, (newVal) => {
    if (newVal !== undefined && newVal !== model.value) model.value = newVal
})
watch(() => node.data?.node_config?.samples, (newVal) => {
    if (newVal !== undefined && newVal !== samples.value) samples.value = newVal
})
watch(() => node.data?.node_config?.voting, (newVal) => {
    if (newVal !== undefined && newVal !== voting.value) voting.value = newVal
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
    class="neural-node-base self-consistency-node w-64 relative transition-all duration-300 group"
    :class="{
        'ring-2 ring-indigo-500 shadow-[0_0_30px_rgba(99,102,241,0.6)]': isRunning,
        'border-neon-green': status.status === 'success',
        'border-neon-red': status.status === 'error'
    }"
  >
    <!-- Status Pulse -->
    <div v-if="isRunning" class="absolute -inset-1 bg-indigo-500/20 blur-lg rounded-lg animate-pulse z-0"></div>

    <!-- Icon Badge -->
    <div class="absolute -top-6 -left-4 w-12 h-12 bg-slate-900 rounded-xl border border-indigo-500/50 shadow-[0_0_15px_rgba(99,102,241,0.5)] flex items-center justify-center z-20 transform group-hover:scale-110 transition-all duration-300">
        <span class="text-2xl">🎲</span>
    </div>

    <div class="relative z-10 bg-slate-900/90 rounded-lg">
        <div class="node-header bg-indigo-500/20 border-b border-indigo-500/30 text-indigo-500 flex justify-center items-center min-h-[40px]">
            <span class="font-bold text-xs tracking-wider uppercase">Self-Consistency</span>
            <div v-if="isRunning" class="w-2 h-2 bg-indigo-500 rounded-full animate-ping ml-2"></div>
        </div>

        <div class="node-body p-3 space-y-3">
            <!-- Live Stream Display -->
            <div v-if="streamText" class="bg-black/50 border border-indigo-500/50 rounded h-40 flex flex-col">
                <div class="bg-slate-800/50 px-2 py-1 border-b border-slate-700 flex justify-between items-center">
                    <span class="text-[9px] text-indigo-500 font-bold uppercase tracking-wider truncate pr-2">
                        {{ selectedModelName }}
                    </span>
                    <div class="flex gap-2 items-center">
                         <span v-if="status.status === 'success'" class="text-[9px] text-neon-green">CONSENSUS</span>
                    </div>
                </div>

                <div class="p-2 text-[10px] font-mono text-slate-300 overflow-y-auto custom-scrollbar flex-1 nodrag cursor-text select-text">
                    {{ streamText }}<span v-if="isRunning" class="animate-pulse text-indigo-500">_</span>
                </div>
            </div>

            <!-- Configuration -->
            <div v-else class="space-y-3">
                <div>
                    <label class="text-[10px] text-slate-400 mb-1 block uppercase">Model</label>
                    <select v-model="model" class="w-full bg-black/50 border border-slate-700 rounded text-xs text-slate-200 p-1 focus:border-indigo-500 outline-none">
                        <option v-if="store.isLoadingModels" disabled value="">Loading models...</option>
                        <optgroup v-for="cat in store.categorizedModels" :key="cat.category" :label="cat.category">
                            <option v-for="m in cat.models" :key="m.id" :value="m.id">
                                {{ m.name }}
                            </option>
                        </optgroup>
                    </select>
                </div>

                <div>
                    <label class="text-[10px] text-slate-400 mb-1 block uppercase">Samples</label>
                    <input
                        v-model.number="samples"
                        type="number"
                        min="2"
                        max="10"
                        step="1"
                        class="w-full bg-black/50 border border-slate-700 rounded text-xs text-slate-200 p-1 focus:border-indigo-500 outline-none"
                    />
                    <span class="text-[9px] text-slate-500">Generate {{ samples }} diverse responses</span>
                </div>

                <div>
                    <label class="text-[10px] text-slate-400 mb-1 block uppercase">Voting Method</label>
                    <select v-model="voting" class="w-full bg-black/50 border border-slate-700 rounded text-xs text-slate-200 p-1 focus:border-indigo-500 outline-none">
                        <option value="majority">Majority Vote</option>
                        <option value="longest">Longest Response</option>
                        <option value="first">First Response</option>
                    </select>
                </div>

                <div>
                    <label class="text-[10px] text-slate-400 mb-1 block uppercase">Base Temperature</label>
                    <input
                        v-model.number="temperature"
                        type="range"
                        min="0"
                        max="2"
                        step="0.1"
                        class="w-full accent-indigo-500"
                    />
                    <span class="text-[9px] text-slate-500">{{ temperature }} (varies ±0.1 per sample)</span>
                </div>
            </div>
        </div>
    </div>

    <Handle type="target" :position="Position.Left" class="neural-handle" />
    <Handle type="source" :position="Position.Right" class="neural-handle" />
  </div>
</template>

<style scoped>
.self-consistency-node {
    border: 2px solid rgba(99, 102, 241, 0.3);
}
</style>
