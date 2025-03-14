<script setup lang="ts">
import { RouterLink, useRouter } from 'vue-router'
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { constants, setPrompt } from "@/utils/utils";

const router = useRouter()

var prompt = ref("")

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
  <main>
    <p>
      Hello! Enter a prompt!<br><br>
      <input v-model="prompt" type="text" autocomplete="off" id="fprompt" name="fprompt" autofocus>
    </p>
    <p class="buttons">
      <button @click="submit()" :disabled="prompt.length === 0">ENTER<br>to submit</button>
    </p>
  </main>
</template>
