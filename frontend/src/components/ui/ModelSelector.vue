<script setup lang="ts">
import { ref, computed, nextTick } from 'vue'
import { PhCaretDown, PhMagnifyingGlass, PhCheck } from '@phosphor-icons/vue'

const props = defineProps<{
    modelValue: string
    options: { category: string; models: { id: string; name: string }[] }[]
    placeholder?: string
    disabled?: boolean
    loading?: boolean
    error?: string | null
}>()

const emit = defineEmits(['update:modelValue'])

const isOpen = ref(false)
const searchQuery = ref('')
const searchInput = ref<HTMLInputElement | null>(null)

// Toggle Dropdown
const toggle = () => {
    if (props.disabled) return
    isOpen.value = !isOpen.value
    if (isOpen.value) {
        searchQuery.value = ''
        nextTick(() => searchInput.value?.focus())
    }
}

// Select Model
const selectModel = (id: string) => {
    emit('update:modelValue', id)
    isOpen.value = false
}

// Flatten and Filter Options
const filteredOptions = computed(() => {
    const query = searchQuery.value.toLowerCase()
    
    if (!query) return props.options

    return props.options.map(group => {
        return {
            category: group.category,
            models: group.models.filter(m => 
                m.name.toLowerCase().includes(query) || 
                m.id.toLowerCase().includes(query)
            )
        }
    }).filter(group => group.models.length > 0)
})

// Find selected model name for display
const selectedName = computed(() => {
    if (!props.modelValue) return ''
    for (const group of props.options) {
        const found = group.models.find(m => m.id === props.modelValue)
        if (found) return found.name
    }
    return props.modelValue // Fallback to ID if name not found
})
</script>

<template>
    <div class="relative w-full font-mono text-xs nodrag">
        <!-- Trigger Button -->
        <div 
            @click="toggle"
            class="w-full bg-black/50 border rounded p-1.5 flex justify-between items-center cursor-pointer transition-colors relative"
            :class="[
                isOpen ? 'border-neon-blue ring-1 ring-neon-blue/50' : 'border-slate-700 hover:border-slate-500',
                disabled ? 'opacity-50 cursor-not-allowed' : ''
            ]"
        >
            <div class="truncate pr-2 text-slate-200">
                <span v-if="loading">Loading models...</span>
                <span v-else-if="error" class="text-neon-red">{{ error }}</span>
                <span v-else-if="selectedName">{{ selectedName }}</span>
                <span v-else class="text-slate-500 italic">{{ placeholder || 'Select a model...' }}</span>
            </div>
            <PhCaretDown class="text-slate-500 flex-shrink-0" />
        </div>

        <!-- Dropdown Menu -->
        <div v-if="isOpen" class="absolute left-0 top-full mt-1 w-full bg-slate-900 border border-slate-600 rounded shadow-2xl z-[100] max-h-60 flex flex-col nodrag">
            
            <!-- Search Bar -->
            <div class="p-2 border-b border-slate-700 bg-slate-800/50 sticky top-0 z-10">
                <div class="relative">
                    <PhMagnifyingGlass class="absolute left-2 top-1.5 text-slate-500" />
                    <input 
                        ref="searchInput"
                        v-model="searchQuery"
                        type="text" 
                        placeholder="Search model..." 
                        class="w-full bg-black/50 border border-slate-700 rounded pl-7 pr-2 py-1 text-slate-200 focus:border-neon-blue outline-none text-xs"
                    />
                </div>
            </div>

            <!-- List -->
            <div class="overflow-y-auto custom-scrollbar flex-1">
                <div v-if="filteredOptions.length === 0" class="p-3 text-center text-slate-500 italic">
                    No models found.
                </div>

                <div v-for="group in filteredOptions" :key="group.category">
                    <div class="px-2 py-1 bg-slate-800/30 text-[10px] font-bold text-slate-500 uppercase tracking-wider sticky top-0">
                        {{ group.category }}
                    </div>
                    <div 
                        v-for="model in group.models" 
                        :key="model.id"
                        @click="selectModel(model.id)"
                        class="px-2 py-1.5 hover:bg-neon-blue/10 hover:text-neon-blue cursor-pointer flex justify-between items-center group transition-colors"
                        :class="modelValue === model.id ? 'text-neon-blue bg-neon-blue/5' : 'text-slate-300'"
                    >
                        <span class="truncate">{{ model.name }}</span>
                        <PhCheck v-if="modelValue === model.id" weight="bold" />
                    </div>
                </div>
            </div>
        </div>

        <!-- Backdrop to close -->
        <div v-if="isOpen" class="fixed inset-0 z-[90]" @click="isOpen = false"></div>
    </div>
</template>
