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
const selectedModels = ref<string[]>(node.data?.node_config?.models || [])
const temperature = ref(node.data?.node_config?.temperature || 0.7)
const addModelSelect = ref('')

// Helper to add model
const addModel = () => {
    if (addModelSelect.value && !selectedModels.value.includes(addModelSelect.value)) {
        selectedModels.value.push(addModelSelect.value)
        addModelSelect.value = ''
    }
}

const removeModel = (m: string) => {
    selectedModels.value = selectedModels.value.filter(x => x !== m)
}

// Sync changes back to node data
watch([selectedModels, temperature], ([newModels, newTemp]) => {
    // Deep check for array equality to prevent loops
    if (JSON.stringify(newModels) !== JSON.stringify(node.data?.node_config?.models) || newTemp !== node.data?.node_config?.temperature) {
         node.data = {
            ...node.data,
            node_config: {
                ...node.data?.node_config,
                models: newModels,
                temperature: newTemp
            }
        }
    }
}, { deep: true })

// Sync node data -> local state
watch(() => node.data?.node_config?.models, (newVal) => { 
    if (newVal && JSON.stringify(newVal) !== JSON.stringify(selectedModels.value)) {
        selectedModels.value = [...newVal]
    }
}, { deep: true })
watch(() => node.data?.node_config?.temperature, (newVal) => { if (newVal !== undefined && newVal !== temperature.value) temperature.value = newVal })

const status = computed(() => store.nodeStatus[nodeId] || { status: 'idle' } as any)
const isRunning = computed(() => status.value.status === 'running')
const result = computed(() => status.value.result) // MoA Proposer results usually come as final result object
</script>

<template>
  <div 
    class="neural-node-base moa-proposer-node w-72 relative transition-all duration-300 group"
    :class="{
        'ring-2 ring-neon-purple shadow-[0_0_30px_rgba(139,92,246,0.6)]': isRunning,
        'border-neon-purple': true
    }"
  >
    <!-- Glowing Icon Badge -->
    <div class="absolute -top-6 -left-4 w-12 h-12 bg-slate-900 rounded-xl border border-neon-purple/50 shadow-[0_0_15px_rgba(139,92,246,0.5)] flex items-center justify-center z-20 transform group-hover:scale-110 transition-all duration-300">
        <img src="/assets/icons/moa.png" class="w-8 h-8 object-contain" :class="{'animate-pulse': isRunning}" alt="MoA" />
    </div>

    <!-- Expand Button -->
    <button @click="isExpanded = true" class="absolute top-2 right-2 text-slate-500 hover:text-neon-purple transition-colors z-30">
        <PhArrowsOutSimple weight="bold" />
    </button>

    <!-- Header -->
    <div class="node-header bg-neon-purple/20 border-b border-neon-purple/30 text-neon-purple flex justify-center items-center min-h-[40px] relative pl-6">
        <span class="font-bold text-xs tracking-wider uppercase">MoA Proposers</span>
        <span v-if="status.status === 'success'" class="absolute right-8 text-[9px] font-bold text-neon-green">COMPLETE</span>
    </div>

    <div class="node-body p-3 space-y-3">
        <!-- Live Result Preview -->
        <div v-if="result" class="bg-black/50 border border-neon-purple/50 rounded h-32 overflow-hidden relative group/preview">
            <div class="absolute top-0 left-0 bg-neon-purple/20 text-neon-purple text-[9px] font-bold px-1">PROPOSALS</div>
            <div class="p-2 text-[10px] font-mono text-slate-300 pt-4 h-full overflow-y-auto custom-scrollbar">
                {{ typeof result === 'string' ? result : JSON.stringify(result, null, 2) }}
            </div>
        </div>

        <!-- Configuration -->
        <div v-else class="space-y-3">
            <div>
                <label class="text-[10px] text-slate-400 mb-1 block uppercase">Proposer Models ({{ selectedModels.length }})</label>
                
                <!-- Selected List -->
                <div class="flex flex-wrap gap-1 mb-2">
                    <div v-for="m in selectedModels" :key="m" class="bg-neon-purple/10 border border-neon-purple/30 rounded px-1 py-0.5 text-[9px] text-neon-purple flex items-center gap-1">
                        <span class="truncate max-w-[150px]">{{ m }}</span>
                        <button @click="removeModel(m)" class="hover:text-white"><PhX /></button>
                    </div>
                </div>

                <!-- Add Model -->
                <div class="flex gap-1 items-start">
                    <ModelSelector
                        v-model="addModelSelect"
                        :options="store.categorizedModels"
                        :loading="store.isLoadingModels"
                        placeholder="Add model..."
                        class="flex-1"
                    />
                    <button @click="addModel" class="bg-neon-purple/20 hover:bg-neon-purple/40 border border-neon-purple/50 text-neon-purple px-3 py-1.5 rounded h-full transition-colors font-bold text-lg leading-none flex items-center justify-center min-h-[28px]">+</button>
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
                    class="w-full accent-neon-purple nodrag cursor-pointer"
                />
                <span class="text-[9px] text-slate-500">{{ temperature }}</span>
            </div>
        </div>
    </div>

    <Handle type="target" :position="Position.Left" class="neural-handle" />
    <Handle type="source" :position="Position.Right" class="neural-handle" />

    <!-- Expanded Modal -->
    <Teleport to="body">
        <div v-if="isExpanded" class="fixed inset-0 z-[100] flex items-center justify-center p-8 bg-black/80 backdrop-blur-sm" @click="isExpanded = false">
            <div class="bg-slate-900 border border-neon-purple rounded-lg w-full max-w-4xl h-[80vh] flex flex-col shadow-2xl relative" @click.stop>
                <div class="flex justify-between items-center p-4 border-b border-slate-700">
                    <h2 class="text-neon-purple font-mono font-bold text-lg">PROPOSER OUTPUTS</h2>
                    <button @click="isExpanded = false" class="text-slate-400 hover:text-white">
                        <PhX weight="bold" class="text-xl" />
                    </button>
                </div>
                <div class="w-full h-full bg-black/50 text-slate-200 p-6 overflow-y-auto custom-scrollbar font-mono text-sm leading-relaxed whitespace-pre-wrap">
                    {{ result ? (typeof result === 'string' ? result : JSON.stringify(result, null, 2)) : 'No proposals generated yet.' }}
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
.moa-proposer-node {
    border: 2px solid rgba(139, 92, 246, 0.3);
}
</style>