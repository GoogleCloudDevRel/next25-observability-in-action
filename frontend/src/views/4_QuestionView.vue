<script setup lang="ts">
import { RouterLink, useRouter } from 'vue-router'
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { constants, getQuestion, postResponse } from "@/utils/utils";

var router = useRouter()

const showTransition = ref(true);
var totalQuestions = constants.numQuestions
var currentQuestionNumber = ref(1)
var question = ref(null)
question.value = getQuestion();

var selection = ref(0)

const colorMap: { [key: string]: string } = {
  "1": "red",
  "2": "blue",
  "3": "green"
};

const possibleAnswers = ["Gemma on Cloud Run", "Gemini 2.0 Flash on VertexAI", "Gemini 2.0 Flash-lite on VertexAI"]
const possibleCodes = ["GEMMA3", "FLASH", "FLASHLITE"]

function currentColor() {
  return colorMap[String(currentQuestionNumber.value)]
}

function reset() {
  router.push("/")
}

async function submitResponse() {
  postResponse(question.value.qid, possibleCodes[selection.value-1])
  
  if (currentQuestionNumber.value == totalQuestions) {
    setTimeout(() => {
      router.push("/model")
    }, 500);
    
    return
  }

  selection.value = 0
  currentQuestionNumber.value++
  question.value = await getQuestion();
}

let handlerEnter: any;
let handlerOne: any;
let handlerTwo: any;
let handlerThree: any;
onMounted(() => {
  handlerEnter = async (e: any) => {
    if (e.key === 'Enter' && selection.value !== 0) {
      await submitResponse()
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

  setTimeout(() => {
    showTransition.value = false;
  }, 1000);
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
  <video v-if="showTransition" class="bg-video" autoplay loop muted playsinline>
    <source src="/transition.mp4#t=1" type="video/mp4">
    Your browser does not support the video tag.
  </video>
  <template v-else>
    <button id="reset-button" class="btn" :class="currentColor()" @click="reset()">Reset</button>
    <main :id="'screen-' + currentColor()">
      <div>
        <h1 :class="currentColor()">Question {{ currentQuestionNumber }}</h1>
        <h3 style="padding-left: 100px; padding-right: 100px">
          {{ question.question }}
        </h3>
        <p class="buttons">
          <template v-for="(option, index) in possibleAnswers">
            <button :class="currentColor()" @click="submitResponse()" :disabled="selection !== index+1">{{ option }}</button>
          </template>
        </p>
      </div>
    </main>
  </template>
</template>
