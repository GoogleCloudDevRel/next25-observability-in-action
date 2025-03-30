<script setup lang="ts">
import { RouterLink, useRouter } from 'vue-router'
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { constants, setPrompt } from "@/utils/utils";

const router = useRouter()

const showTransition = ref(true);
var prompt = ref("")

function reset() {
  router.push("/")
}

function submit() {
  setPrompt(prompt.value)

  setTimeout(() => {
    router.push("/question")
  }, 500);
}

let handlerEnter: any;
onMounted(() => {
  handlerEnter = (e: any) => {
    if (e.key === 'Enter') {
      submit()
    }
  };
  window.addEventListener('keypress', handlerEnter);

  setTimeout(() => {
    showTransition.value = false;
  }, 1000);
});

onBeforeUnmount(() => {
  if (handlerEnter) {
    window.removeEventListener('keypress', handlerEnter);
  }
});
</script>

<template>
  <video v-if="showTransition" class="bg-video" autoplay loop muted playsinline>
    <source src="/transition.mp4#t=1" type="video/mp4">
    Your browser does not support the video tag.
  </video>
  <template v-else>
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
</template>
