<script setup lang="ts">
import { Handle, Position, useNode, useNodeId } from '@vue-flow/core'
import { ref, watch, computed } from 'vue'
import { useWorkflowStore } from '../../stores/workflow'

const { node } = useNode()
const nodeId = useNodeId()
const store = useWorkflowStore()

// Configuration
const model = ref(node.data?.node_config?.model || 'openai/gpt-3.5-turbo')
const debaters = ref(node.data?.node_config?.debaters || 3)
const rounds = ref(node.data?.node_config?.rounds || 2)
const temperature = ref(node.data?.node_config?.temperature || 0.8)

// Sync changes back to node data
watch([model, debaters, rounds, temperature], ([newModel, newDebaters, newRounds, newTemp]) => {
    node.data = {
        ...node.data,
        node_config: {
            ...node.data?.node_config,
            model: newModel,
            debaters: newDebaters,
            rounds: newRounds,
            temperature: newTemp
        }
    }
})

// Sync node data -> local state (for loading templates)
watch(() => node.data?.node_config?.model, (newVal) => {
    if (newVal !== undefined && newVal !== model.value) model.value = newVal
})
watch(() => node.data?.node_config?.debaters, (newVal) => {
    if (newVal !== undefined && newVal !== debaters.value) debaters.value = newVal
})
watch(() => node.data?.node_config?.rounds, (newVal) => {
    if (newVal !== undefined && newVal !== rounds.value) rounds.value = newVal
})
watch(() => node.data?.node_config?.temperature, (newVal) => {
    if (newVal !== undefined && newVal !== temperature.value) temperature.value = newVal
})

const status = computed(() => store.nodeStatus[nodeId] || { status: 'idle' } as any)
const isRunning = computed(() => status.value.status === 'running')
const streamText = computed(() => status.value.stream || '')
</script>

<template>
  <div 
    class="neural-node-base debate-node w-64 relative transition-all duration-300 group"
    :class="{
        'ring-2 ring-neon-red shadow-[0_0_30px_rgba(239,68,68,0.6)]': isRunning,
        'border-neon-red': true
    }"
  >
    <!-- Glowing Icon Badge -->
    <div class="absolute -top-6 -left-4 w-12 h-12 bg-slate-900 rounded-xl border border-neon-red/50 shadow-[0_0_15px_rgba(239,68,68,0.5)] flex items-center justify-center z-20 transform group-hover:scale-110 transition-all duration-300">
        <img src="/assets/icons/debate.png" class="w-8 h-8 object-contain" :class="{'animate-pulse': isRunning}" alt="Debate" />
    </div>

    <!-- Header -->
    <div class="node-header bg-neon-red/20 border-b border-neon-red/30 text-neon-red flex justify-center items-center min-h-[40px] relative pl-6">
        <span class="font-bold text-xs tracking-wider uppercase">Debate Room</span>
        <div v-if="status.round" class="absolute right-2 px-2 py-0.5 bg-black/50 rounded text-[9px] font-mono border border-neon-red/50">
             R: {{ status.round }}
        </div>
    </div>

        <div class="node-body p-3 space-y-3">
            <!-- Live Stream Display -->
            <div v-if="streamText" class="bg-black/50 border border-red-500/50 rounded h-40 flex flex-col">
                <div class="bg-slate-800/50 px-2 py-1 border-b border-slate-700 flex justify-between items-center">
                    <span class="text-[9px] text-red-500 font-bold uppercase tracking-wider truncate pr-2">
                        {{ debaters }} Debaters × {{ rounds }} Rounds
                    </span>
                    <div class="flex gap-2 items-center">
                         <span v-if="status.status === 'success'" class="text-[9px] text-neon-green">COMPLETE</span>
                    </div>
                </div>

                <div class="p-2 text-[10px] font-mono text-slate-300 overflow-y-auto custom-scrollbar flex-1 nodrag cursor-text select-text">
                    {{ streamText }}<span v-if="isRunning" class="animate-pulse text-red-500">_</span>
                </div>
            </div>

            <!-- Configuration -->
            <div v-else class="space-y-3">
                <div>
                    <label class="text-[10px] text-slate-400 mb-1 block uppercase">Debate Model</label>
                    <select v-model="model" class="w-full bg-black/50 border border-slate-700 rounded text-xs text-slate-200 p-1 focus:border-red-500 outline-none">
                        <option v-if="store.isLoadingModels" disabled value="">Loading models...</option>
                        <optgroup v-for="cat in store.categorizedModels" :key="cat.category" :label="cat.category">
                            <option v-for="m in cat.models" :key="m.id" :value="m.id">
                                {{ m.name }}
                            </option>
                        </optgroup>
                    </select>
                </div>

                <div>
                    <label class="text-[10px] text-slate-400 mb-1 block uppercase">Number of Debaters</label>
                    <input
                        v-model.number="debaters"
                        type="number"
                        min="2"
                        max="5"
                        step="1"
                        class="w-full bg-black/50 border border-slate-700 rounded text-xs text-slate-200 p-1 focus:border-red-500 outline-none"
                    />
                    <span class="text-[9px] text-slate-500">Pro, Con, Neutral...</span>
                </div>

                <div>
                    <label class="text-[10px] text-slate-400 mb-1 block uppercase">Debate Rounds</label>
                    <input
                        v-model.number="rounds"
                        type="number"
                        min="1"
                        max="5"
                        step="1"
                        class="w-full bg-black/50 border border-slate-700 rounded text-xs text-slate-200 p-1 focus:border-red-500 outline-none"
                    />
                    <span class="text-[9px] text-slate-500">More rounds = deeper analysis</span>
                </div>

                <div>
                    <label class="text-[10px] text-slate-400 mb-1 block uppercase">Temperature</label>
                    <input
                        v-model.number="temperature"
                        type="range"
                        min="0"
                        max="2"
                        step="0.1"
                        class="w-full accent-red-500"
                    />
                    <span class="text-[9px] text-slate-500">{{ temperature }} (higher = more creative)</span>
                </div>
            </div>
        </div>

    <Handle type="target" :position="Position.Left" class="neural-handle" />
    <Handle type="source" :position="Position.Right" class="neural-handle" />
  </div>
</template>

<style scoped>
.debate-node {
    border: 2px solid rgba(239, 68, 68, 0.3);
}
</style>
