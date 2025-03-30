<script setup lang="ts">
import { RouterLink, useRouter } from 'vue-router'
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { constants, getPrompt, finalize, getAllQuestions } from "@/utils/utils";

var router = useRouter()

const showTransition = ref(true);
// var prompt = ref(getPrompt())
// var response = ref("")
var questions = []

var selection = ref(0)

const codeMap = new Map()
codeMap.set("GEMMA3", "Gemma on Cloud Run")
codeMap.set("FLASH", "Gemini 2.0 Flash on VertexAI")
codeMap.set("FLASHLITE", "Gemini 2.0 Flash-lite on VertexAI")

function reset() {
  router.push("/")
}

// function foo() {
//   response.value = callModel("model-name")
// }

// function sendToModel() {
//   response.value = "Generating..."
//   setTimeout(foo, 1500)
//   // response.value = callModel("model-name")
// }

function returnHome() {
  router.push("/")
}

let handlerEnter: any;
// let handlerOne: any;
// let handlerTwo: any;
// let handlerThree: any;
onMounted(() => {
  handlerEnter = (e: any) => {
    if (e.key === 'Enter') {
      returnHome()
    }
  };
  window.addEventListener('keypress', handlerEnter);
  // handlerOne = (e: any) => {
  //   if (e.key === '1') {
  //     selection.value = 1
  //   }
  // };
  // window.addEventListener('keypress', handlerOne);
  // handlerTwo = (e: any) => {
  //   if (e.key === '2') {
  //     selection.value = 2
  //   }
  // };
  // window.addEventListener('keypress', handlerTwo);
  // handlerThree = (e: any) => {
  //   if (e.key === '3') {
  //     selection.value = 3
  //   }
  // };
  // window.addEventListener('keypress', handlerThree);

  setTimeout(() => {
    showTransition.value = false;
    questions = getAllQuestions()
    console.log(questions)
    finalize()
  }, 1000);
});

onBeforeUnmount(() => {
  if (handlerEnter) {
    window.removeEventListener('keypress', handlerEnter);
  }
  // if (handlerOne) {
  //   window.removeEventListener('keypress', handlerOne);
  // }
  // if (handlerTwo) {
  //   window.removeEventListener('keypress', handlerTwo);
  // }
  // if (handlerThree) {
  //   window.removeEventListener('keypress', handlerThree);
  // }
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
      <div>
        <h1 class="yellow">Quiz Results</h1>
        <template v-for="(question, index) in questions">
          <div class="quiz-result" :class="question.code == question.tried_code ? 'green' : 'red'">
            <h3>{{ question.question }}</h3>
            <h4 v-if="question.code == question.tried_code">
              You selected the correct answer, <b>{{ codeMap.get(question.code) }}</b>!
            </h4>
            <h4 v-else class="white">
              You selected <b>{{ codeMap.get(question.tried_code) }}</b>,
              but the correct answer was <b>{{ codeMap.get(question.code) }}</b>.
            </h4>
          </div>
        </template>
        <h3 class="yellow">Press enter one last time to reset!</h3>
        <!-- <h3>{{ prompt }}</h3>
        <p v-if="response">
          {{ response }}<br>
          <p class="buttons">
            <button @click="returnHome()">ENTER<br>to restart</button>
          </p>
        </p>
        <p class="buttons" v-else>
          <button class="yellow" @click="sendToModel()" :disabled="selection !== 1">Gemma on Cloud Run</button>
          <button class="yellow" @click="sendToModel()" :disabled="selection !== 2">Gemini 2.0 Flash on VertexAI</button>
          <button class="yellow" @click="sendToModel()" :disabled="selection !== 3">Gemini 2.0 Flash-lite on VertexAI</button>
        </p> -->
      </div>
    </main>
  </template>
</template>
