<script setup lang="ts">
import { Handle, Position, useNode, useNodeId } from '@vue-flow/core'
import { ref, watch, computed } from 'vue'
import { useWorkflowStore } from '../../stores/workflow'

const props = defineProps(['data'])
const nodeId = useNodeId()
const store = useWorkflowStore()
const { node } = useNode()

// Config State
const conditionType = ref(node.data?.node_config?.conditionType || 'contains')
const targetValue = ref(node.data?.node_config?.targetValue || '')

// Sync config
watch([conditionType, targetValue], ([newType, newTarget]) => {
    node.data = {
        ...node.data,
        node_config: {
            ...node.data?.node_config,
            conditionType: newType,
            targetValue: newTarget
        }
    }
})

// Execution State
const status = computed(() => store.nodeStatus[nodeId] || { status: 'idle' } as any)
const isRunning = computed(() => status.value.status === 'running')
const result = computed(() => status.value.result) // "true" or "false"

</script>

<template>
  <div 
    class="neural-node-base conditional-node w-64 relative transition-all duration-300 group"
    :class="{
        'ring-2 ring-neon-yellow shadow-[0_0_30px_rgba(234,179,8,0.6)]': isRunning,
        'border-neon-yellow': true
    }"
  >
    <!-- Glowing Icon Badge -->
    <div class="absolute -top-6 -left-4 w-12 h-12 bg-slate-900 rounded-xl border border-neon-yellow/50 shadow-[0_0_15px_rgba(234,179,8,0.5)] flex items-center justify-center z-20 transform group-hover:scale-110 transition-all duration-300">
        <img src="/assets/icons/split-path.png" class="w-8 h-8 object-contain" alt="Condition" />
    </div>

    <!-- Header -->
    <div class="node-header bg-neon-yellow/20 border-b border-neon-yellow/30 text-neon-yellow flex justify-center items-center min-h-[40px] relative">
        <div class="flex items-center">
            <span class="font-bold text-xs tracking-wider uppercase">Condition</span>
        </div>
        <!-- Status Dot -->
        <div v-if="status.status === 'success'" class="absolute right-2 px-2 py-0.5 rounded text-[9px] font-bold uppercase"
             :class="result === 'true' ? 'bg-neon-green text-black' : 'bg-neon-red text-white'">
             {{ result === 'true' ? 'PASSED' : 'FAILED' }}
        </div>
    </div>
    
    <!-- Body -->
    <div class="node-body p-3 space-y-3">
        
        <div class="flex gap-2">
            <select v-model="conditionType" class="bg-black/50 border border-slate-700 rounded text-xs text-slate-200 p-1 focus:border-neon-yellow outline-none flex-1">
                <option value="contains">Contains</option>
                <option value="equals">Equals</option>
                <option value="not_contains">Not Contains</option>
            </select>
        </div>

        <input 
            type="text" 
            v-model="targetValue"
            placeholder="Value to check..."
            class="w-full bg-black/50 border border-slate-700 rounded text-xs text-slate-200 p-2 focus:border-neon-yellow outline-none font-mono"
        />

        <div class="text-[10px] text-slate-500 italic text-center">
            If input {{ conditionType.replace('_', ' ') }} "{{ targetValue }}"
        </div>
    </div>

    <!-- Input Handle -->
    <Handle type="target" :position="Position.Left" class="neural-handle !bg-slate-200" />

    <!-- Output Handles -->
    
    <!-- TRUE Path (Green) -->
    <div class="absolute -right-3 top-8 flex items-center">
        <span class="text-[9px] text-neon-green font-bold mr-1 bg-black/80 px-1 rounded backdrop-blur-sm">TRUE</span>
        <Handle 
            id="true" 
            type="source" 
            :position="Position.Right" 
            class="neural-handle !bg-neon-green !border-neon-green" 
            style="top: auto; right: 0; position: relative; transform: none;"
        />
    </div>

    <!-- FALSE Path (Red) -->
    <div class="absolute -right-3 bottom-8 flex items-center">
        <span class="text-[9px] text-neon-red font-bold mr-1 bg-black/80 px-1 rounded backdrop-blur-sm">FALSE</span>
        <Handle 
            id="false" 
            type="source" 
            :position="Position.Right" 
            class="neural-handle !bg-neon-red !border-neon-red" 
            style="top: auto; right: 0; position: relative; transform: none;"
        />
    </div>

  </div>
</template>

<style scoped>
@reference "../../style.css";

.neural-node-base.conditional-node {
    @apply border-yellow-500/50;
}
</style>
