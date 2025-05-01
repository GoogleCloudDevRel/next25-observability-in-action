<script setup lang="ts">
import { useRouter } from 'vue-router'
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { finalize, getAllQuestions } from "@/utils/utils";

var router = useRouter()

const showTransition = ref(true);
var questions = []

const codeMap = new Map()
codeMap.set("GEMMA3", "Gemma on Cloud Run")
codeMap.set("FLASH", "Gemini 2.0 Flash on VertexAI")
codeMap.set("FLASHLITE", "Gemini 2.0 Flash-lite on VertexAI")

function reset() {
  router.push("/")
}

function returnHome() {
  router.push("/")
}

let handlerEnter: any;
onMounted(() => {
  handlerEnter = (e: any) => {
    if (e.key === 'Enter') {
      returnHome()
    }
  };
  window.addEventListener('keypress', handlerEnter);

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
      </div>
    </main>
  </template>
</template>
