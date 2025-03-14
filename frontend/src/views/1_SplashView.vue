<script setup lang="ts">
import { RouterLink, useRouter } from 'vue-router'
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { constants, setPrompt } from "@/utils/utils";

const router = useRouter()

function submit() {
  router.push("/prompt")
}

let handlerEnter: any;
onMounted(() => {
  handlerEnter = (e: any) => {
    if (e.key === 'Enter') {
        submit()
    }
  };
  window.addEventListener('keypress', handlerEnter);
});

onBeforeUnmount(() => {
  if (handlerEnter) {
    window.removeEventListener('keypress', handlerEnter);
  }
});
</script>

<template>
  <main>
    <p class="buttons">
      <button @click="submit()">ENTER<br>to begin</button>
    </p>
  </main>
</template>
