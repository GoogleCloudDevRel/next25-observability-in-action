<script setup lang="ts">
import { useRouter } from 'vue-router'
import { ref, onMounted, onBeforeUnmount } from 'vue'

const router = useRouter()

const showTransition = ref(true);

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
  <main v-else>
    <div>
      <h1 class="yellow">Instructions</h1>
      <h3>Use the foot pedals to select from three different options and enter to confirm selection.</h3>
      <video class="bg-videoo" style="width: 800px" autoplay loop muted playsinline>
        <source src="/vid_instructions.mp4" type="video/mp4">
        Your browser does not support the video tag.
      </video>
      <h3>Hit enter to start!</h3>
    </div>
  </main>
</template>
