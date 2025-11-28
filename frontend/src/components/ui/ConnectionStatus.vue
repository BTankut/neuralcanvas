<script setup lang="ts">
import { useWorkflowStore } from '../../stores/workflow'
import { PhWifiHigh, PhWifiSlash } from '@phosphor-icons/vue'

const store = useWorkflowStore()
</script>

<template>
  <div 
    class="px-3 py-2 rounded-full border flex items-center gap-2 text-xs font-mono backdrop-blur-md transition-colors duration-300 h-10 min-w-[140px] justify-center"
    :class="store.isConnected ? 'bg-neon-green/10 border-neon-green text-neon-green' : 'bg-neon-red/10 border-neon-red text-neon-red'"
  >
    <PhWifiHigh v-if="store.isConnected" weight="bold" class="text-lg" />
    <PhWifiSlash v-else weight="bold" class="text-lg" />
    
    <span class="font-bold">{{ store.isConnected ? 'BRAIN ONLINE' : 'BRAIN OFFLINE' }}</span>
  </div>
</template>
