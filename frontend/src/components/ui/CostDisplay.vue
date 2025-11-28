<script setup lang="ts">
import { useWorkflowStore } from '../../stores/workflow'
import { PhCoins } from '@phosphor-icons/vue'

const store = useWorkflowStore()
</script>

<template>
  <div 
    class="px-4 py-2 rounded-full border border-slate-700 bg-slate-900/50 backdrop-blur-md flex items-center gap-2 shadow-lg transition-all duration-300 h-10 min-w-[120px] justify-center"
    :class="{'border-yellow-500/50 text-yellow-400 shadow-yellow-500/10': store.totalCost > 0, 'text-slate-400': store.totalCost === 0}"
  >
    <PhCoins weight="fill" class="text-lg" />
    <span class="font-mono font-bold text-xs">${{ store.totalCost.toFixed(6) }}</span>
  </div>
</template>
