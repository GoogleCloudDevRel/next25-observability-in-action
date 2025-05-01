<script setup lang="ts">
import { useRouter } from 'vue-router'
import { ref, onMounted, onBeforeUnmount } from 'vue'

const router = useRouter()

const showTransition = ref(true);

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
  <video v-else class="bg-video" autoplay loop muted playsinline>
    <source src="/vid_splash.mp4" type="video/mp4">
    Your browser does not support the video tag.
  </video>
</template>
