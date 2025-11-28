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
const strategy = ref(node.data?.node_config?.strategy || 'hierarchical')
const model = ref(node.data?.node_config?.model || 'openai/gpt-3.5-turbo')
const temperature = ref(node.data?.node_config?.temperature || 0.7)
const prompt = ref(node.data?.node_config?.prompt || 'Summarize and synthesize the following content:')

// Sync changes back to node data
watch([strategy, model, temperature, prompt], ([newStrategy, newModel, newTemp, newPrompt]) => {
    node.data = {
        ...node.data,
        node_config: {
            ...node.data?.node_config,
            strategy: newStrategy,
            model: newModel,
            temperature: newTemp,
            prompt: newPrompt
        }
    }
})

// Sync node data -> local state (for loading templates)
watch(() => node.data?.node_config?.strategy, (newVal) => {
    if (newVal !== undefined && newVal !== strategy.value) strategy.value = newVal
})
watch(() => node.data?.node_config?.model, (newVal) => {
    if (newVal !== undefined && newVal !== model.value) model.value = newVal
})
watch(() => node.data?.node_config?.temperature, (newVal) => {
    if (newVal !== undefined && newVal !== temperature.value) temperature.value = newVal
})
watch(() => node.data?.node_config?.prompt, (newVal) => {
    if (newVal !== undefined && newVal !== prompt.value) prompt.value = newVal
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
    class="neural-node-base reduce-node w-64 relative transition-all duration-300 group"
    :class="{
        'ring-2 ring-neon-orange shadow-[0_0_30px_rgba(249,115,22,0.6)]': isRunning,
        'border-neon-orange': true
    }"
  >
    <!-- Glowing Icon Badge -->
    <div class="absolute -top-6 -left-4 w-12 h-12 bg-slate-900 rounded-xl border border-neon-orange/50 shadow-[0_0_15px_rgba(249,115,22,0.5)] flex items-center justify-center z-20 transform group-hover:scale-110 transition-all duration-300">
        <img src="/assets/icons/reduce.png" class="w-8 h-8 object-contain" :class="{'animate-pulse': isRunning}" alt="Reduce" />
    </div>

    <!-- Expand Button -->
    <button @click="isExpanded = true" class="absolute top-2 right-2 text-slate-500 hover:text-neon-orange transition-colors z-30">
        <PhArrowsOutSimple weight="bold" />
    </button>

    <!-- Header -->
    <div class="node-header bg-neon-orange/20 border-b border-neon-orange/30 text-neon-orange flex justify-center items-center min-h-[40px] relative pl-6">
        <span class="font-bold text-xs tracking-wider uppercase">Reducer / Summarizer</span>
        <span v-if="status.status === 'success'" class="absolute right-2 text-[9px] font-bold text-neon-green">COMPLETE</span>
    </div>

    <div class="node-body p-3 space-y-3">
        <!-- Live Stream Display -->
        <div v-if="streamText" class="bg-black/50 border border-cyan-500/50 rounded h-40 flex flex-col">
            <div class="bg-slate-800/50 px-2 py-1 border-b border-slate-700 flex justify-between items-center">
                <span class="text-[9px] text-cyan-500 font-bold uppercase tracking-wider truncate pr-2">
                    {{ selectedModelName }}
                </span>
                <div class="flex gap-2 items-center">
                        <span v-if="status.usage?.cost" class="text-[9px] text-yellow-400 font-mono">
                        ${{ status.usage.cost.toFixed(6) }}
                        </span>
                        <span v-if="status.status === 'success'" class="text-[9px] text-neon-green">DONE</span>
                </div>
            </div>

            <div class="p-2 text-[10px] font-mono text-slate-300 overflow-y-auto custom-scrollbar flex-1 nodrag cursor-text select-text">
                {{ streamText }}<span v-if="isRunning" class="animate-pulse text-cyan-500">_</span>
            </div>
        </div>

        <!-- Configuration -->
        <div v-else class="space-y-3">
            <div>
                <label class="text-[10px] text-slate-400 mb-1 block uppercase">Strategy</label>
                <select v-model="strategy" class="w-full bg-black/50 border border-slate-700 rounded text-xs text-slate-200 p-1 focus:border-cyan-500 outline-none">
                    <option value="hierarchical">Hierarchical</option>
                    <option value="concatenate">Concatenate</option>
                </select>
            </div>

            <div>
                <label class="text-[10px] text-slate-400 mb-1 block uppercase">Model</label>
                <select v-model="model" class="w-full bg-black/50 border border-slate-700 rounded text-xs text-slate-200 p-1 focus:border-cyan-500 outline-none">
                    <option v-if="store.isLoadingModels" disabled value="">Loading models...</option>
                    <optgroup v-for="cat in store.categorizedModels" :key="cat.category" :label="cat.category">
                        <option v-for="m in cat.models" :key="m.id" :value="m.id">
                            {{ m.name }}
                        </option>
                    </optgroup>
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
                    class="w-full accent-cyan-500"
                />
                <span class="text-[9px] text-slate-500">{{ temperature }}</span>
            </div>

            <div>
                <label class="text-[10px] text-slate-400 mb-1 block uppercase">Prompt</label>
                <textarea
                    v-model="prompt"
                    class="w-full bg-black/50 border border-slate-700 rounded text-xs text-slate-200 p-2 focus:border-cyan-500 outline-none resize-none h-16 font-mono"
                    placeholder="Enter reduction prompt..."
                ></textarea>
            </div>
        </div>
    </div>

    <Handle type="target" :position="Position.Left" class="neural-handle" />
    <Handle type="source" :position="Position.Right" class="neural-handle" />

    <!-- Expanded Modal -->
    <Teleport to="body">
        <div v-if="isExpanded" class="fixed inset-0 z-[100] flex items-center justify-center p-8 bg-black/80 backdrop-blur-sm" @click="isExpanded = false">
            <div class="bg-slate-900 border border-neon-orange rounded-lg w-full max-w-4xl h-[80vh] flex flex-col shadow-2xl relative" @click.stop>
                <div class="flex justify-between items-center p-4 border-b border-slate-700">
                    <h2 class="text-neon-orange font-mono font-bold text-lg">REDUCTION OUTPUT</h2>
                    <button @click="isExpanded = false" class="text-slate-400 hover:text-white">
                        <PhX weight="bold" class="text-xl" />
                    </button>
                </div>
                <div class="w-full h-full bg-black/50 text-slate-200 p-6 overflow-y-auto custom-scrollbar font-mono text-sm leading-relaxed whitespace-pre-wrap">
                    {{ streamText || 'No reduction output yet.' }}
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
.reduce-node {
    border: 2px solid rgba(6, 182, 212, 0.3);
}
</style>