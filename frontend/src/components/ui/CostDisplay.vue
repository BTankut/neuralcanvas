<script setup lang="ts">
import { useWorkflowStore } from '../../stores/workflow'
import { PhCoins } from '@phosphor-icons/vue'

const store = useWorkflowStore()
</script>

<template>
  <div 
    class="fixed bottom-4 right-4 z-50 px-4 py-2 rounded-full border border-slate-700 bg-slate-900/80 backdrop-blur-md flex items-center gap-2 shadow-lg transition-all duration-300"
    :class="{'border-yellow-500/50 text-yellow-400 shadow-yellow-500/10': store.totalCost > 0, 'text-slate-400': store.totalCost === 0}"
  >
    <PhCoins weight="fill" class="text-lg" />
    <div class="flex flex-col items-end leading-none">
        <span class="text-[10px] font-bold uppercase tracking-widest opacity-70">Session Cost</span>
        <span class="font-mono font-bold text-sm">${{ store.totalCost.toFixed(6) }}</span>
    </div>
  </div>
</template>
