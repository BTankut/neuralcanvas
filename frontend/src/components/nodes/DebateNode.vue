<script setup lang="ts">
import { Handle, Position, useNode, useNodeId } from '@vue-flow/core'
import { ref, watch, computed, onMounted, onUnmounted } from 'vue'
import { useWorkflowStore } from '../../stores/workflow'
import { PhArrowsOutSimple, PhX } from '@phosphor-icons/vue'
import ModelSelector from '../ui/ModelSelector.vue'

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
const rounds = ref(node.data?.node_config?.rounds || 3)
const model = ref(node.data?.node_config?.model || 'openai/gpt-3.5-turbo')
const debaters = ref(node.data?.node_config?.debaters || 2)
const temperature = ref(node.data?.node_config?.temperature || 0.8)

// Sync changes back to node data
watch([rounds, model, debaters, temperature], ([newRounds, newModel, newDebaters, newTemp]) => {
    node.data = {
        ...node.data,
        node_config: {
            ...node.data?.node_config,
            rounds: newRounds,
            model: newModel,
            debaters: newDebaters,
            temperature: newTemp
        }
    }
})

// Sync node data -> local state
watch(() => node.data?.node_config?.rounds, (newVal) => { if (newVal !== undefined && newVal !== rounds.value) rounds.value = newVal })
watch(() => node.data?.node_config?.model, (newVal) => { if (newVal !== undefined && newVal !== model.value) model.value = newVal })
watch(() => node.data?.node_config?.debaters, (newVal) => { if (newVal !== undefined && newVal !== debaters.value) debaters.value = newVal })
watch(() => node.data?.node_config?.temperature, (newVal) => { if (newVal !== undefined && newVal !== temperature.value) temperature.value = newVal })

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

    <!-- Expand Button -->
    <button @click="isExpanded = true" class="absolute top-2 right-2 text-slate-500 hover:text-neon-red transition-colors z-30">
        <PhArrowsOutSimple weight="bold" />
    </button>

    <!-- Header -->
    <div class="node-header bg-neon-red/20 border-b border-neon-red/30 text-neon-red flex justify-center items-center min-h-[40px] relative pl-6">
        <span class="font-bold text-xs tracking-wider uppercase">Debate Room</span>
        <span v-if="status.status === 'success'" class="absolute right-8 text-[9px] font-bold text-neon-green">FINISHED</span>
    </div>

    <div class="node-body p-3 space-y-3">
        <!-- Live Stream Display -->
        <div v-if="streamText" class="bg-black/50 border border-neon-red/50 rounded h-40 flex flex-col">
            <div class="bg-slate-800/50 px-2 py-1 border-b border-slate-700 flex justify-between items-center">
                <span class="text-[9px] text-neon-red font-bold uppercase tracking-wider truncate pr-2">
                    {{ selectedModelName }}
                </span>
                <div class="flex gap-2 items-center">
                     <span v-if="status.status === 'success'" class="text-[9px] text-neon-green">DEBATE OVER</span>
                </div>
            </div>

            <div class="p-2 text-[10px] font-mono text-slate-300 overflow-y-auto custom-scrollbar flex-1 nodrag cursor-text select-text">
                {{ streamText }}<span v-if="isRunning" class="animate-pulse text-neon-red">_</span>
            </div>
        </div>

        <!-- Configuration -->
        <div v-else class="space-y-3">
            <div>
                <label class="text-[10px] text-slate-400 mb-1 block uppercase">Debate Model</label>
                <ModelSelector
                    v-model="model"
                    :options="store.categorizedModels"
                    :loading="store.isLoadingModels"
                />
            </div>

            <div>
                <label class="text-[10px] text-slate-400 mb-1 block uppercase">Number of Debaters</label>
                <input
                    v-model.number="debaters"
                    type="number"
                    min="2"
                    max="5"
                    class="w-full bg-black/50 border border-slate-700 rounded text-xs text-slate-200 p-2 focus:border-neon-red outline-none"
                />
                <span class="text-[9px] text-slate-500">Pro, Con, Neutral...</span>
            </div>

            <div>
                <label class="text-[10px] text-slate-400 mb-1 block uppercase">Debate Rounds</label>
                <input
                    v-model.number="rounds"
                    type="number"
                    min="1"
                    max="10"
                    class="w-full bg-black/50 border border-slate-700 rounded text-xs text-slate-200 p-2 focus:border-neon-red outline-none"
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
                    class="w-full accent-neon-red"
                />
                <span class="text-[9px] text-slate-500">{{ temperature }} (higher = more creative)</span>
            </div>
        </div>
    </div>

    <Handle type="target" :position="Position.Left" class="neural-handle" />
    <Handle type="source" :position="Position.Right" class="neural-handle" />

    <!-- Expanded Modal -->
    <Teleport to="body">
        <div v-if="isExpanded" class="fixed inset-0 z-[100] flex items-center justify-center p-8 bg-black/80 backdrop-blur-sm" @click="isExpanded = false">
            <div class="bg-slate-900 border border-neon-red rounded-lg w-full max-w-4xl h-[80vh] flex flex-col shadow-2xl relative" @click.stop>
                <div class="flex justify-between items-center p-4 border-b border-slate-700">
                    <h2 class="text-neon-red font-mono font-bold text-lg">DEBATE TRANSCRIPT</h2>
                    <button @click="isExpanded = false" class="text-slate-400 hover:text-white">
                        <PhX weight="bold" class="text-xl" />
                    </button>
                </div>
                <div class="w-full h-full bg-black/50 text-slate-200 p-6 overflow-y-auto custom-scrollbar font-mono text-sm leading-relaxed whitespace-pre-wrap">
                    {{ streamText || 'No debate transcript yet.' }}
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
.debate-node {
    border: 2px solid rgba(239, 68, 68, 0.3);
}
</style>