<script setup lang="ts">
import { RouterLink, useRouter } from 'vue-router'
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { constants, getQuestion, postResponse } from "@/utils/utils";

var router = useRouter()

var totalQuestions = constants.numQuestions
var currentQuestionNumber = ref(1)
var question = ref(getQuestion())

var selection = ref(0)

function submitResponse() {
  postResponse(question.value.id, "response")
  
  selection.value = 0
  currentQuestionNumber.value++
  question.value = getQuestion()

  if (currentQuestionNumber.value > totalQuestions) {
    router.push("/model")
  }
}

let handlerEnter: any;
let handlerOne: any;
let handlerTwo: any;
let handlerThree: any;
onMounted(() => {
  handlerEnter = (e: any) => {
    if (e.key === 'Enter' && selection.value !== 0) {
      submitResponse()
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
      Question #{{ currentQuestionNumber }}: {{ question.question }}
    </p>
    <p  class="buttons">
      <template v-for="(option, index) in question.options">
        <button @click="submitResponse()" :disabled="selection !== index+1">{{ option }}</button>
      </template>
      <button @click="submitResponse()" :disabled="selection === 0">ENTER<br>to confirm</button>
    </p>
  </main>
</template>
