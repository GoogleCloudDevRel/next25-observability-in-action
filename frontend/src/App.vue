<script setup lang="ts">
import { RouterView } from 'vue-router'
import { constants } from "@/utils/utils";
</script>

<template>
  <!-- <header>
    <h1>{{ constants.demoTitle }}</h1>
    <h2>{{ constants.demoSubtitle }}</h2>
  </header> -->
  
  <RouterView />
</template>

<style scoped>
/* body {
  background-color: white;
  color: black;
} */
</style>
