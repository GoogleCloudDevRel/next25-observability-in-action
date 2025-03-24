<script setup lang="ts">
import { RouterLink, useRouter } from 'vue-router'
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { constants, setPrompt } from "@/utils/utils";

const router = useRouter()

var prompt = ref("")

function reset() {
  router.push("/")
}

function submit() {
  setPrompt(prompt.value)
  router.push("/question")
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
  <button id="reset-button" class="btn yellow" @click="reset()">Reset</button>
  <main id="screen-yellow">
    <section>
      <h1 class="yellow" style="max-width: 800px;">Submit a prompt to generate logs</h1>
      <input v-model="prompt" type="text" autocomplete="off" placeholder="How long does it take an apple tree to grow?" autofocus>
      <br>
      <button class="btn btn-md yellow" @click="submit()" :disabled="prompt.length === 0">enter</button>
    </section>
  </main>
</template>
