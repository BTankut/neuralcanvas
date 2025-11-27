<script setup lang="ts">
import { Handle, Position, useNode } from '@vue-flow/core'
import { ref, watch } from 'vue'

const { node } = useNode()
const inputValue = ref(node.data?.inputValue || '')

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
        class="w-full bg-black/50 border border-slate-700 rounded text-xs text-slate-200 p-2 focus:border-neon-blue outline-none resize-none h-20 font-mono"
        placeholder="Enter your prompt here..."
      ></textarea>
    </div>

    <Handle type="source" :position="Position.Right" class="neural-handle" />
  </div>
</template>

<style scoped>
/* These classes rely on global styles or Tailwind, ensuring consistency */
</style>
