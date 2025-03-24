<script setup lang="ts">
import { RouterLink, useRouter } from 'vue-router'
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { constants, setPrompt } from "@/utils/utils";

const router = useRouter()

function submit() {
  router.push("/instructions")
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
  <video class="bg-video" autoplay loop muted playsinline>
    <source src="/vid_splash.mp4" type="video/mp4">
    Your browser does not support the video tag.
  </video>
  <!-- <main id="screen-splash"> -->
    <!-- splash
    <p class="buttons">
      <button @click="submit()">ENTER<br>to begin</button>
    </p> -->
  <!-- </main> -->
</template>
