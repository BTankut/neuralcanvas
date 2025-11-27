<script setup lang="ts">
import FlowCanvas from './components/canvas/FlowCanvas.vue'
</script>

<template>
  <div class="h-screen w-screen overflow-hidden bg-void">
    <header class="absolute top-0 left-0 z-10 p-4 w-full flex justify-between items-center pointer-events-none">
      <h1 class="text-xl font-bold text-neon-blue pointer-events-auto font-mono tracking-wider">
        NEURAL<span class="text-slate-200">CANVAS</span>
      </h1>
      <div class="pointer-events-auto">
        <!-- Toolbar placeholder -->
      </div>
    </header>
    <main class="h-full w-full">
      <FlowCanvas />
    </main>
  </div>
</template>