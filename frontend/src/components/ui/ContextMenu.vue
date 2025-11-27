<script setup lang="ts">
import { ref } from 'vue'
import { useVueFlow } from '@vue-flow/core'

const { addNodes, project, onPaneContextMenu } = useVueFlow()

const isOpen = ref(false)
const position = ref({ x: 0, y: 0 })
const flowPosition = ref({ x: 0, y: 0 })

// Open menu on right click
onPaneContextMenu((event) => {
    console.log('Right click detected!', event)
    
    // Vue Flow event might be the raw event or wrapped
    const e = (event as any).event || event
    
    if (e && e.preventDefault) {
        e.preventDefault()
        isOpen.value = true
        position.value = { x: e.clientX, y: e.clientY }
        flowPosition.value = project({ x: e.clientX, y: e.clientY })
    }
})

// Close on click elsewhere
import { onMounted, onUnmounted } from 'vue'
const close = () => isOpen.value = false
onMounted(() => window.addEventListener('click', close))
onUnmounted(() => window.removeEventListener('click', close))

function addNode(type: string, label: string) {
    const id = crypto.randomUUID()
    const newNode = {
        id,
        type,
        position: flowPosition.value,
        data: { label }
    }
    addNodes([newNode])
    isOpen.value = false
}
</script>

<template>
  <div 
    v-if="isOpen" 
    class="fixed z-50 bg-slate-900 border border-slate-700 rounded shadow-[0_0_20px_rgba(0,0,0,0.5)] py-1 w-48 backdrop-blur-md overflow-hidden"
    :style="{ top: `${position.y}px`, left: `${position.x}px` }"
  >
    <div class="px-3 py-2 text-[10px] font-bold text-slate-500 uppercase tracking-widest border-b border-slate-800 bg-black/20">
        Add Node
    </div>
    
    <button @click="addNode('neural-input', 'Input')" class="w-full text-left px-4 py-2 text-xs text-slate-300 hover:bg-neon-blue/20 hover:text-neon-blue transition-colors flex items-center gap-2">
        <div class="w-2 h-2 rounded-full bg-neon-blue"></div>
        Input Source
    </button>
    
    <button @click="addNode('neural-llm', 'LLM')" class="w-full text-left px-4 py-2 text-xs text-slate-300 hover:bg-neon-purple/20 hover:text-neon-purple transition-colors flex items-center gap-2">
        <div class="w-2 h-2 rounded-full bg-neon-purple"></div>
        AI Processing
    </button>

    <button @click="addNode('neural-condition', 'Condition')" class="w-full text-left px-4 py-2 text-xs text-slate-300 hover:bg-neon-yellow/20 hover:text-neon-yellow transition-colors flex items-center gap-2">
        <div class="w-2 h-2 rounded-full bg-neon-yellow"></div>
        Conditional Logic
    </button>
    
    <button @click="addNode('neural-output', 'Output')" class="w-full text-left px-4 py-2 text-xs text-slate-300 hover:bg-neon-green/20 hover:text-neon-green transition-colors flex items-center gap-2">
        <div class="w-2 h-2 rounded-full bg-neon-green"></div>
        Result Output
    </button>
  </div>
</template>
