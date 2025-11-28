<script setup lang="ts">
import { Handle, Position, useNode, useNodeId } from '@vue-flow/core'
import { ref, watch, computed } from 'vue'
import { useWorkflowStore } from '../../stores/workflow'

const { node } = useNode()
const nodeId = useNodeId()
const store = useWorkflowStore()

// Configuration - array of models
const selectedModels = ref<string[]>(node.data?.node_config?.models || ['openai/gpt-3.5-turbo', 'anthropic/claude-3-haiku', 'openai/gpt-4-turbo'])
const temperature = ref(node.data?.node_config?.temperature || 0.7)

// Sync changes back to node data
watch([selectedModels, temperature], ([newModels, newTemp]) => {
    node.data = {
        ...node.data,
        node_config: {
            ...node.data?.node_config,
            models: newModels,
            temperature: newTemp
        }
    }
}, { deep: true })

// Sync node data -> local state (for loading templates)
watch(() => node.data?.node_config?.models, (newVal) => {
    if (newVal !== undefined && JSON.stringify(newVal) !== JSON.stringify(selectedModels.value)) {
        selectedModels.value = newVal
    }
}, { deep: true })
watch(() => node.data?.node_config?.temperature, (newVal) => {
    if (newVal !== undefined && newVal !== temperature.value) temperature.value = newVal
})

const status = computed(() => store.nodeStatus[nodeId] || { status: 'idle' } as any)
const isRunning = computed(() => status.value.status === 'running')
const streamText = computed(() => status.value.stream || '')

// Add/remove models
const newModel = ref('')
function addModel() {
    if (newModel.value && !selectedModels.value.includes(newModel.value)) {
        selectedModels.value.push(newModel.value)
        newModel.value = ''
    }
}
function removeModel(index: number) {
    selectedModels.value.splice(index, 1)
}

// Quick add from available models
const availableModelsShort = computed(() => {
    return store.availableModels.slice(0, 20).map(m => m.id)
})
</script>

<template>
  <div
    class="neural-node-base moa-proposer-node w-72 relative transition-all duration-300 group"
    :class="{
        'ring-2 ring-purple-500 shadow-[0_0_30px_rgba(168,85,247,0.6)]': isRunning,
        'border-neon-green': status.status === 'success',
        'border-neon-red': status.status === 'error'
    }"
  >
    <!-- Status Pulse -->
    <div v-if="isRunning" class="absolute -inset-1 bg-purple-500/20 blur-lg rounded-lg animate-pulse z-0"></div>

    <!-- Icon Badge -->
    <div class="absolute -top-6 -left-4 w-12 h-12 bg-slate-900 rounded-xl border border-purple-500/50 shadow-[0_0_15px_rgba(168,85,247,0.5)] flex items-center justify-center z-20 transform group-hover:scale-110 transition-all duration-300">
        <span class="text-2xl">🎭</span>
    </div>

    <div class="relative z-10 bg-slate-900/90 rounded-lg">
        <div class="node-header bg-purple-500/20 border-b border-purple-500/30 text-purple-500 flex justify-center items-center min-h-[40px]">
            <span class="font-bold text-xs tracking-wider uppercase">MoA Proposers</span>
            <div v-if="isRunning" class="w-2 h-2 bg-purple-500 rounded-full animate-ping ml-2"></div>
        </div>

        <div class="node-body p-3 space-y-3">
            <!-- Live Stream Display -->
            <div v-if="streamText" class="bg-black/50 border border-purple-500/50 rounded p-2 min-h-[100px]">
                <div class="text-[10px] font-mono text-slate-300 whitespace-pre-wrap">
                    {{ streamText }}
                </div>
            </div>

            <!-- Configuration -->
            <div v-else class="space-y-3">
                <div>
                    <label class="text-[10px] text-slate-400 mb-1 block uppercase">Proposer Models ({{ selectedModels.length }})</label>
                    <div class="space-y-1 max-h-32 overflow-y-auto custom-scrollbar">
                        <div v-for="(model, index) in selectedModels" :key="index"
                             class="flex items-center gap-1 bg-black/30 rounded px-2 py-1">
                            <span class="text-[9px] text-purple-400 flex-1 truncate">{{ model }}</span>
                            <button @click="removeModel(index)"
                                    class="text-red-400 hover:text-red-300 text-xs px-1">×</button>
                        </div>
                    </div>
                </div>

                <div>
                    <label class="text-[10px] text-slate-400 mb-1 block uppercase">Add Model</label>
                    <div class="flex gap-1">
                        <select v-model="newModel"
                                class="flex-1 bg-black/50 border border-slate-700 rounded text-[10px] text-slate-200 p-1 focus:border-purple-500 outline-none">
                            <option value="">Select model...</option>
                            <option v-for="m in availableModelsShort" :key="m" :value="m">{{ m }}</option>
                        </select>
                        <button @click="addModel"
                                class="bg-purple-500/20 hover:bg-purple-500/30 text-purple-400 px-2 rounded text-xs">
                            +
                        </button>
                    </div>
                </div>

                <div>
                    <label class="text-[10px] text-slate-400 mb-1 block uppercase">Temperature</label>
                    <input
                        v-model.number="temperature"
                        type="range"
                        min="0"
                        max="2"
                        step="0.1"
                        class="w-full accent-purple-500"
                    />
                    <span class="text-[9px] text-slate-500">{{ temperature }}</span>
                </div>
            </div>
        </div>
    </div>

    <Handle type="target" :position="Position.Left" class="neural-handle" />
    <Handle type="source" :position="Position.Right" class="neural-handle" />
  </div>
</template>

<style scoped>
.moa-proposer-node {
    border: 2px solid rgba(168, 85, 247, 0.3);
}
</style>
