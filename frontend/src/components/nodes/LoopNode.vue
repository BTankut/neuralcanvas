<script setup lang="ts">
import { Handle, Position, useNode, useNodeId } from '@vue-flow/core'
import { ref, watch, computed } from 'vue'
import { useWorkflowStore } from '../../stores/workflow'

const props = defineProps(['data'])
const nodeId = useNodeId()
const store = useWorkflowStore()
const { node } = useNode()

// Config State
const maxIterations = ref(node.data?.node_config?.max_iterations || 3)

// Sync config local -> node
watch(maxIterations, (val) => {
    node.data = {
        ...node.data,
        node_config: {
            ...node.data?.node_config,
            max_iterations: val
        }
    }
})

// Sync node -> local (Fix for loading templates)
watch(() => node.data?.node_config?.max_iterations, (newVal) => {
    if (newVal !== undefined && newVal !== maxIterations.value) {
        maxIterations.value = newVal
    }
})

// Execution State
const status = computed(() => store.nodeStatus[nodeId] || { status: 'idle' } as any)
const isRunning = computed(() => status.value.status === 'running')
const currentIteration = computed(() => status.value.usage?.current_iteration || 0)

</script>

<template>
  <div 
    class="neural-node-base loop-node w-64 relative transition-all duration-300 group"
    :class="{
        'ring-2 ring-neon-cyan shadow-[0_0_30px_rgba(6,182,212,0.6)]': isRunning,
        'border-neon-cyan': true
    }"
  >
    <!-- Glowing Icon Badge -->
    <div class="absolute -top-6 -left-4 w-12 h-12 bg-slate-900 rounded-xl border border-neon-cyan/50 shadow-[0_0_15px_rgba(6,182,212,0.5)] flex items-center justify-center z-20 transform group-hover:scale-110 transition-all duration-300">
        <img src="/assets/icons/loop-cycle.png" class="w-8 h-8 object-contain" :class="{'animate-spin': isRunning}" alt="Loop" />
    </div>

    <!-- Header -->
    <div class="node-header bg-neon-cyan/20 border-b border-neon-cyan/30 text-neon-cyan flex justify-center items-center min-h-[40px] relative">
        <div class="flex items-center">
            <span class="font-bold text-xs tracking-wider uppercase">Iterator</span>
        </div>
        <div v-if="isRunning || status.status === 'success'" class="absolute right-2 px-2 py-0.5 bg-black/50 rounded text-[9px] font-mono border border-neon-cyan/50">
             {{ currentIteration }} / {{ maxIterations }}
        </div>
    </div>
    
    <!-- Body -->
    <div class="node-body p-3 space-y-3">
        <div class="flex justify-between text-[10px] text-slate-400 mb-1">
            <span class="uppercase">Loop Count</span>
            <span>{{ maxIterations }}</span>
        </div>
        <input 
            type="range" 
            v-model.number="maxIterations" 
            min="1" max="10" step="1"
            class="w-full h-1 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-neon-cyan"
        />
        
        <div class="text-[10px] text-slate-500 italic text-center">
            Repeats the flow {{ maxIterations }} times
        </div>
    </div>

    <!-- Input Handle -->
    <Handle type="target" :position="Position.Left" class="neural-handle !bg-slate-200" />

    <!-- Output Handles -->
    
    <!-- LOOP Path (Cyan) -->
    <div class="absolute -right-3 top-8 flex items-center">
        <span class="text-[9px] text-neon-cyan font-bold mr-1 bg-black/80 px-1 rounded backdrop-blur-sm">LOOP</span>
        <Handle 
            id="loop" 
            type="source" 
            :position="Position.Right" 
            class="neural-handle !bg-neon-cyan !border-neon-cyan" 
            style="top: auto; right: 0; position: relative; transform: none;"
        />
    </div>

    <!-- DONE Path (Green) -->
    <div class="absolute -right-3 bottom-8 flex items-center">
        <span class="text-[9px] text-neon-green font-bold mr-1 bg-black/80 px-1 rounded backdrop-blur-sm">DONE</span>
        <Handle 
            id="done" 
            type="source" 
            :position="Position.Right" 
            class="neural-handle !bg-neon-green !border-neon-green" 
            style="top: auto; right: 0; position: relative; transform: none;"
        />
    </div>

  </div>
</template>

<style scoped>
@reference "../../style.css";

.neural-node-base.loop-node {
    @apply border-cyan-500/50;
}
</style>
