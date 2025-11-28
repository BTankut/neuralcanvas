<script setup lang="ts">
import { Handle, Position, useNodeId } from '@vue-flow/core'
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { useWorkflowStore } from '../../stores/workflow'
import { PhArrowsOutSimple, PhX } from '@phosphor-icons/vue'

defineProps(['data'])
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

const status = computed(() => store.nodeStatus[nodeId] || { status: 'idle' } as any)
const result = computed(() => status.value.result)
</script>

<template>
  <div 
    class="neural-node-base output-node w-64 transition-all duration-300 group relative"
    :class="{
        'border-neon-green shadow-[0_0_20px_rgba(16,185,129,0.4)]': status.status === 'success',
        'opacity-50 border-slate-700 grayscale': status.status === 'skipped'
    }"
  >
    <!-- Expand Button -->
    <button @click="isExpanded = true" class="absolute top-2 right-2 text-slate-500 hover:text-neon-green transition-colors z-30">
        <PhArrowsOutSimple weight="bold" />
    </button>

    <!-- Glowing Icon Badge -->
    <div class="absolute -top-6 -left-4 w-12 h-12 bg-slate-900 rounded-xl border border-neon-green/50 shadow-[0_0_15px_rgba(16,185,129,0.5)] flex items-center justify-center z-20 transform group-hover:scale-110 transition-all duration-300">
        <img src="/assets/icons/result-output.png" class="w-8 h-8 object-contain" alt="Output" />
    </div>

    <div class="node-header bg-neon-green/20 border-b border-neon-green/30 text-neon-green flex justify-center items-center min-h-[40px] relative"
         :class="{'!bg-slate-800 !text-slate-500 !border-slate-700': status.status === 'skipped'}">
        <div class="flex items-center">
            <span class="font-bold text-xs tracking-wider uppercase">Result Output</span>
        </div>
        <span v-if="status.status === 'skipped'" class="absolute right-8 text-[9px] font-bold">SKIPPED</span>
    </div>
    
    <div class="node-body p-3 min-h-[80px] bg-black/30 flex items-start justify-start overflow-auto max-h-60 custom-scrollbar nodrag cursor-text select-text">
        <div v-if="result" class="text-xs font-mono text-slate-300 whitespace-pre-wrap">{{ result }}</div>
        <span v-else-if="status.status === 'skipped'" class="text-xs text-slate-600 italic m-auto">Node execution skipped</span>
        <span v-else class="text-xs text-slate-500 italic m-auto">Waiting for execution...</span>
    </div>

    <!-- Expanded Modal -->
    <Teleport to="body">
        <div v-if="isExpanded" class="fixed inset-0 z-[100] flex items-center justify-center p-8 bg-black/80 backdrop-blur-sm" @click="isExpanded = false">
            <div class="bg-slate-900 border border-neon-green rounded-lg w-full max-w-4xl h-[80vh] flex flex-col shadow-2xl relative" @click.stop>
                <div class="flex justify-between items-center p-4 border-b border-slate-700">
                    <h2 class="text-neon-green font-mono font-bold text-lg">FULL SCREEN OUTPUT</h2>
                    <button @click="isExpanded = false" class="text-slate-400 hover:text-white">
                        <PhX weight="bold" class="text-xl" />
                    </button>
                </div>
                <div class="w-full h-full bg-black/50 text-slate-200 p-6 overflow-y-auto custom-scrollbar font-mono text-sm leading-relaxed whitespace-pre-wrap">
                    {{ result || 'No output content yet.' }}
                </div>
                <div class="p-2 bg-slate-800/50 text-center text-[10px] text-slate-500">
                    Press ESC to close
                </div>
            </div>
        </div>
    </Teleport>

    <Handle type="target" :position="Position.Left" class="neural-handle" />
  </div>
</template>
<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 4px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: #0f172a; 
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #10b981; 
  border-radius: 2px;
}
</style>
