<script setup lang="ts">
import { Handle, Position, useNodeId } from '@vue-flow/core'
import { computed } from 'vue'
import { useWorkflowStore } from '../../stores/workflow'
import { PhTerminalWindow } from '@phosphor-icons/vue'

defineProps(['data'])
const nodeId = useNodeId()
const store = useWorkflowStore()

const status = computed(() => store.nodeStatus[nodeId] || { status: 'idle' } as any)
const result = computed(() => status.value.result)
</script>

<template>
  <div 
    class="neural-node-base output-node w-64 transition-all duration-300"
    :class="{
        'border-neon-green shadow-[0_0_20px_rgba(16,185,129,0.4)]': status.status === 'success'
    }"
  >
    <div class="node-header bg-neon-green/20 border-b border-neon-green/30 text-neon-green flex justify-between items-center">
        <div class="flex items-center">
            <PhTerminalWindow weight="bold" class="text-lg mr-2" />
            <span class="font-bold text-xs tracking-wider uppercase">Result Output</span>
        </div>
    </div>
    
    <div class="node-body p-3 min-h-[80px] bg-black/30 flex items-start justify-start overflow-auto max-h-60 custom-scrollbar">
      <div v-if="result" class="text-xs font-mono text-slate-300 whitespace-pre-wrap">{{ result }}</div>
      <span v-else class="text-xs text-slate-500 italic m-auto">Waiting for execution...</span>
    </div>

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
