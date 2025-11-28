<script setup lang="ts">
import { ref } from 'vue'
import { useWorkflowStore } from '../../stores/workflow'

const store = useWorkflowStore()
const isOpen = ref(false)
const apiKey = ref(store.apiKey || '')

function open() {
    apiKey.value = store.apiKey || ''
    isOpen.value = true
}

function save() {
    store.setApiKey(apiKey.value)
    isOpen.value = false
}

defineExpose({ open })
</script>

<template>
    <div v-if="isOpen" class="fixed inset-0 z-[100] flex items-center justify-center p-4">
        <!-- Backdrop -->
        <div class="absolute inset-0 bg-black/60 backdrop-blur-sm" @click="isOpen = false"></div>
        
        <!-- Modal -->
        <div class="relative bg-slate-900/90 border border-neon-blue/50 rounded-lg p-6 w-full max-w-md shadow-[0_0_30px_rgba(59,130,246,0.3)]">
            <h2 class="text-xl font-bold text-neon-blue mb-4 font-mono">SYSTEM SETTINGS</h2>
            
            <div class="space-y-4">
            <div>
                <label class="block text-xs text-slate-400 uppercase tracking-wider mb-2">OpenRouter API Key</label>
                <input 
                    v-model="apiKey"
                    type="password" 
                    placeholder="sk-or-..."
                    class="w-full bg-black/50 border border-slate-700 rounded text-sm text-slate-200 p-3 focus:border-neon-blue outline-none font-mono transition-all"
                />
                <div v-if="apiKey && apiKey.length > 10" class="text-[10px] text-neon-blue mt-1 font-mono flex justify-between">
                    <span>Current Key: ••••••••{{ apiKey.slice(-4) }}</span>
                    <span class="text-slate-500">Key is stored locally.</span>
                </div>
                <p v-else class="text-[10px] text-slate-500 mt-1">
                    Key is stored in browser memory and sent securely to the local execution engine.
                </p>
            </div>

            </div>

            <div class="flex justify-end gap-3 mt-6">
                <button 
                    @click="isOpen = false"
                    class="px-4 py-2 text-xs text-slate-400 hover:text-white transition-colors"
                >
                    CANCEL
                </button>
                <button 
                    @click="save"
                    class="px-6 py-2 bg-neon-blue/20 border border-neon-blue text-neon-blue rounded hover:bg-neon-blue hover:text-black transition-all font-bold text-xs"
                >
                    SAVE CONFIG
                </button>
            </div>
        </div>
    </div>
</template>
