<script setup lang="ts">
import FlowCanvas from './components/canvas/FlowCanvas.vue'
</script>

<template>
  <div class="h-screen w-screen overflow-hidden bg-void">
    <header class="absolute top-0 left-0 z-10 p-4 w-full flex justify-between items-center pointer-events-none">
      <div class="pointer-events-auto flex flex-col leading-tight">
        <h1 class="text-2xl font-bold text-neon-blue font-mono tracking-wider">
          NEURAL<span class="text-slate-200">CANVAS</span>
        </h1>
        <span class="text-[10px] text-slate-500 italic font-mono pl-1">powered by OpenRouter</span>
      </div>
      <div class="pointer-events-auto">
        <!-- Right side controls are injected via Teleport from FlowCanvas -->
      </div>
    </header>

    <main class="h-full w-full">
      <FlowCanvas />
    </main>
  </div>
</template>