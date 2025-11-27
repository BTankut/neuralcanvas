<script setup lang="ts">
import { Handle, Position, useNode } from '@vue-flow/core'
import { ref, watch } from 'vue'
import { PhTextT } from '@phosphor-icons/vue'

const { node } = useNode()
const inputValue = ref(node.data?.inputValue || '')

// Sync local input with node data for the store to pick up
watch(inputValue, (val) => {
    node.data = { ...node.data, inputValue: val }
})
</script>

<template>
  <div class="neural-node-base input-node group">
    <div class="node-header bg-neon-blue/20 border-b border-neon-blue/30 text-neon-blue flex items-center">
      <PhTextT weight="bold" class="text-lg mr-2" />
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
