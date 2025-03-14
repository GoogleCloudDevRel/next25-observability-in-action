<script setup lang="ts">
import { RouterLink, useRouter } from 'vue-router'
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { constants, getPrompt, callModel } from "@/utils/utils";

var router = useRouter()

var prompt = ref(getPrompt())
var response = ref("")

var selection = ref(0)

function foo() {
  response.value = callModel("model-name")
}

function sendToModel() {
  response.value = "Generating..."
  setTimeout(foo, 1500)
  // response.value = callModel("model-name")
}

function returnHome() {
  router.push("/")
}

let handlerEnter: any;
let handlerOne: any;
let handlerTwo: any;
let handlerThree: any;
onMounted(() => {
  handlerEnter = (e: any) => {
    if (e.key === 'Enter') {
      if (response.value !== "") {
        returnHome()
      } else {
        sendToModel()
      }
    }
  };
  window.addEventListener('keypress', handlerEnter);
  handlerOne = (e: any) => {
    if (e.key === '1') {
      selection.value = 1
    }
  };
  window.addEventListener('keypress', handlerOne);
  handlerTwo = (e: any) => {
    if (e.key === '2') {
      selection.value = 2
    }
  };
  window.addEventListener('keypress', handlerTwo);
  handlerThree = (e: any) => {
    if (e.key === '3') {
      selection.value = 3
    }
  };
  window.addEventListener('keypress', handlerThree);
});

onBeforeUnmount(() => {
  if (handlerEnter) {
    window.removeEventListener('keypress', handlerEnter);
  }
  if (handlerOne) {
    window.removeEventListener('keypress', handlerOne);
  }
  if (handlerTwo) {
    window.removeEventListener('keypress', handlerTwo);
  }
  if (handlerThree) {
    window.removeEventListener('keypress', handlerThree);
  }
});
</script>

<template>
  <main>
    <p>
      Pick a model to run your prompt
    </p>
    <p id="prompt">
      {{ prompt }}
    </p>
    <p v-if="response">
      {{ response }}<br>
      <p class="buttons">
        <button @click="returnHome()">ENTER<br>to restart</button>
      </p>
    </p>
    <p class="buttons" v-else>
      <button @click="sendToModel()" :disabled="selection !== 1">Gemma</button>
      <button @click="sendToModel()" :disabled="selection !== 2">Gemini Flash</button>
      <button @click="sendToModel()" :disabled="selection !== 3">Gemini Pro</button>
      <button @click="sendToModel()" :disabled="selection === 0">ENTER<br>to confirm</button>
    </p>
  </main>
</template>
