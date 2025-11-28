<script setup lang="ts">
import { Handle, Position, useNodeId, useNode } from '@vue-flow/core'
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useWorkflowStore } from '../../stores/workflow'
import { PhArrowsOutSimple, PhX } from '@phosphor-icons/vue'

const props = defineProps(['data'])
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

// Use node data model if exists, else default
const { node } = useNode()
const model = ref(node.data?.node_config?.model || 'openai/gpt-3.5-turbo')
const temp = ref(node.data?.node_config?.temperature || 0.7)

// Sync changes back to node data
watch([model, temp], ([newModel, newTemp]) => {
    node.data = {
        ...node.data,
        node_config: {
            ...node.data?.node_config,
            model: newModel,
            temperature: newTemp
        }
    }
})

// Sync node data -> local state (Fix for loading templates)
watch(() => node.data?.node_config?.model, (newVal) => {
    if (newVal !== undefined && newVal !== model.value) model.value = newVal
})
watch(() => node.data?.node_config?.temperature, (newVal) => {
    if (newVal !== undefined && newVal !== temp.value) temp.value = newVal
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
    class="neural-node-base llm-node w-64 relative transition-all duration-300 group"
    :class="{
        'ring-2 ring-neon-purple shadow-[0_0_30px_rgba(139,92,246,0.6)]': isRunning,
        'border-neon-green': status.status === 'success',
        'border-neon-red': status.status === 'error',
        'opacity-50 border-slate-700 grayscale': status.status === 'skipped'
    }"
  >
    <!-- Status Pulse -->
    <div v-if="isRunning" class="absolute -inset-1 bg-neon-purple/20 blur-lg rounded-lg animate-pulse z-0"></div>

    <!-- Expand Button -->
    <button v-if="streamText" @click="isExpanded = true" class="absolute top-2 right-2 text-slate-500 hover:text-neon-purple transition-colors z-30">
        <PhArrowsOutSimple weight="bold" />
    </button>

    <!-- Glowing Icon Badge -->
    <div class="absolute -top-6 -left-4 w-12 h-12 bg-slate-900 rounded-xl border border-neon-purple/50 shadow-[0_0_15px_rgba(139,92,246,0.5)] flex items-center justify-center z-20 transform group-hover:scale-110 transition-all duration-300">
        <img src="/assets/icons/brain-chip.png" class="w-8 h-8 object-contain" alt="AI" />
    </div>

    <div class="relative z-10 bg-slate-900/90 rounded-lg">
        <div class="node-header bg-neon-purple/20 border-b border-neon-purple/30 text-neon-purple flex justify-center items-center min-h-[40px]"
             :class="{'!bg-slate-800 !text-slate-500 !border-slate-700': status.status === 'skipped'}">
        <div class="flex items-center">
            <span class="font-bold text-xs tracking-wider uppercase">AI Processing</span>
        </div>
        <div v-if="isRunning" class="absolute right-2 w-2 h-2 bg-neon-purple rounded-full animate-ping"></div>
        <span v-if="status.status === 'skipped'" class="absolute right-2 text-[9px] font-bold">SKIPPED</span>
    </div>
    
    <div class="node-body p-3 space-y-3">
        <div v-if="streamText" class="bg-black/50 border border-neon-purple/50 rounded h-40 flex flex-col">
            <div class="bg-slate-800/50 px-2 py-1 border-b border-slate-700 flex justify-between items-center">
                <span class="text-[9px] text-neon-purple font-bold uppercase tracking-wider truncate pr-2">{{ selectedModelName }}</span>
                <div class="flex gap-2 items-center">
                    <span v-if="status.usage?.cost" class="text-[9px] text-yellow-400 font-mono">
                        ${{ status.usage.cost.toFixed(6) }}
                    </span>
                    <span v-if="status.status === 'success'" class="text-[9px] text-neon-green">DONE</span>
                </div>
            </div>
            
            <div class="p-2 text-[10px] font-mono text-slate-300 overflow-y-auto custom-scrollbar flex-1 nodrag cursor-text select-text">
                {{ streamText }}<span v-if="isRunning" class="animate-pulse text-neon-purple">_</span>
            </div>
        </div>

        <div v-else class="space-y-3">
            <div>
                <label class="text-[10px] text-slate-400 mb-1 block uppercase">Model</label>
                <select v-model="model" class="w-full bg-black/50 border border-slate-700 rounded text-xs text-slate-200 p-1 focus:border-neon-purple outline-none">
                    <option v-if="store.isLoadingModels" disabled value="">Loading models...</option>
                    <option v-else-if="store.modelFetchError" disabled value="">Error: {{ store.modelFetchError }}</option>
                    <optgroup v-for="cat in store.categorizedModels" :key="cat.category" :label="cat.category">
                        <option v-for="m in cat.models" :key="m.id" :value="m.id">
                            {{ m.name }}
                        </option>
                    </optgroup>
                </select>
            </div>

            <div>
                <div class="flex justify-between text-[10px] text-slate-400 mb-1">
                    <span class="uppercase">Temperature</span>
                    <span>{{ temp }}</span>
                </div>
                <input 
                    type="range" 
                    v-model="temp" 
                    min="0" max="1" step="0.1"
                    class="w-full h-1 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-neon-purple"
                />
            </div>
        </div>
    </div>

    <Handle type="target" :position="Position.Left" class="neural-handle" />
    <Handle type="source" :position="Position.Right" class="neural-handle" />
  </div>

    <!-- Expanded Modal -->
    <Teleport to="body">
        <div v-if="isExpanded" class="fixed inset-0 z-[100] flex items-center justify-center p-8 bg-black/80 backdrop-blur-sm" @click="isExpanded = false">
            <div class="bg-slate-900 border border-neon-purple rounded-lg w-full max-w-4xl h-[80vh] flex flex-col shadow-2xl relative" @click.stop>
                <div class="flex justify-between items-center p-4 border-b border-slate-700">
                    <h2 class="text-neon-purple font-mono font-bold text-lg">AI OUTPUT ({{ selectedModelName }})</h2>
                    <button @click="isExpanded = false" class="text-slate-400 hover:text-white">
                        <PhX weight="bold" class="text-xl" />
                    </button>
                </div>
                <div class="w-full h-full bg-black/50 text-slate-200 p-6 overflow-y-auto custom-scrollbar font-mono text-sm leading-relaxed whitespace-pre-wrap">
                    {{ streamText }}
                </div>
                <div class="p-2 bg-slate-800/50 text-center text-[10px] text-slate-500">
                    Press ESC to close
                </div>
            </div>
        </div>
    </Teleport>
</template>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 4px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: #0f172a; 
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #8b5cf6; 
  border-radius: 2px;
}
</style>
