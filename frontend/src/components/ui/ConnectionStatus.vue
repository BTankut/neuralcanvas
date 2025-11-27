<script setup lang="ts">
import { useWorkflowStore } from '../../stores/workflow'
import { PhWifiHigh, PhWifiSlash } from '@phosphor-icons/vue'

const store = useWorkflowStore()
</script>

<template>
  <div 
    class="fixed bottom-4 left-4 z-50 px-3 py-1.5 rounded-full border flex items-center gap-2 text-xs font-mono backdrop-blur-md transition-colors duration-300"
    :class="store.isConnected ? 'bg-neon-green/10 border-neon-green text-neon-green' : 'bg-neon-red/10 border-neon-red text-neon-red'"
  >
    <PhWifiHigh v-if="store.isConnected" weight="bold" />
    <PhWifiSlash v-else weight="bold" />
    
    <span>{{ store.isConnected ? 'BRAIN ONLINE' : 'BRAIN OFFLINE' }}</span>
  </div>
</template>
