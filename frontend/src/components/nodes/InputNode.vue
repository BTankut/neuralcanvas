<script setup lang="ts">
import { Handle, Position, useNode } from '@vue-flow/core'
import { ref, watch, onMounted, onUnmounted } from 'vue'
import { PhArrowsOutSimple, PhX } from '@phosphor-icons/vue'

const { node } = useNode()
const inputValue = ref(node.data?.inputValue || '')
const isExpanded = ref(false)

// Close on ESC
const handleKeydown = (e: KeyboardEvent) => {
    if (isExpanded.value && e.key === 'Escape') {
        isExpanded.value = false
    }
}

onMounted(() => window.addEventListener('keydown', handleKeydown))
onUnmounted(() => window.removeEventListener('keydown', handleKeydown))

// Sync local input -> node data
watch(inputValue, (val) => {
    node.data = { ...node.data, inputValue: val }
})

// Sync node data -> local input (Fix for loading templates)
watch(() => node.data?.inputValue, (newVal) => {
    if (newVal !== undefined && newVal !== inputValue.value) {
        inputValue.value = newVal
    }
})
</script>

<template>
  <div class="neural-node-base input-node group relative">
    <!-- Expand Button -->
    <button @click="isExpanded = true" class="absolute top-2 right-2 text-slate-500 hover:text-neon-blue transition-colors z-30">
        <PhArrowsOutSimple weight="bold" />
    </button>

    <!-- Glowing Icon Badge -->
    <div class="absolute -top-6 -left-4 w-12 h-12 bg-slate-900 rounded-xl border border-neon-blue/50 shadow-[0_0_15px_rgba(59,130,246,0.5)] flex items-center justify-center z-20 transform group-hover:scale-110 transition-all duration-300">
        <img src="/assets/icons/input-source.png" class="w-8 h-8 object-contain" alt="Input" />
    </div>

    <div class="node-header bg-neon-blue/20 border-b border-neon-blue/30 text-neon-blue flex items-center justify-center min-h-[40px]">
      <span class="font-bold text-xs tracking-wider uppercase">Input Source</span>
    </div>
    
    <div class="node-body p-3">
        <label class="text-[10px] text-slate-400 mb-1 block uppercase">User Prompt</label>
        <textarea 
            v-model="inputValue"
            class="w-full bg-black/50 border border-slate-700 rounded text-xs text-slate-200 p-2 focus:border-neon-blue outline-none resize-none h-20 font-mono nodrag"
            placeholder="Enter your prompt here..."
        ></textarea>
    </div>

    <!-- Expanded Modal -->
    <Teleport to="body">
        <div v-if="isExpanded" class="fixed inset-0 z-[100] flex items-center justify-center p-8 bg-black/80 backdrop-blur-sm" @click="isExpanded = false">
            <div class="bg-slate-900 border border-neon-blue rounded-lg w-full max-w-4xl h-[80vh] flex flex-col shadow-2xl relative" @click.stop>
                <div class="flex justify-between items-center p-4 border-b border-slate-700">
                    <h2 class="text-neon-blue font-mono font-bold text-lg">FULL SCREEN INPUT</h2>
                    <button @click="isExpanded = false" class="text-slate-400 hover:text-white">
                        <PhX weight="bold" class="text-xl" />
                    </button>
                </div>
                <textarea 
                    v-model="inputValue"
                    class="w-full h-full bg-black/50 text-slate-200 p-6 focus:outline-none font-mono text-sm resize-none leading-relaxed"
                    placeholder="Enter your detailed prompt here..."
                ></textarea>
                <div class="p-2 bg-slate-800/50 text-center text-[10px] text-slate-500">
                    Press ESC to close
                </div>
            </div>
        </div>
    </Teleport>

    <Handle type="source" :position="Position.Right" class="neural-handle" />
  </div>
</template>
<style scoped>
/* These classes rely on global styles or Tailwind, ensuring consistency */
</style>
