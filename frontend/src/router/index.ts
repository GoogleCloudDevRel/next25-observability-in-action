import { createRouter, createWebHistory } from 'vue-router'
import SplashView from '../views/1_SplashView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'splash',
      component: SplashView,
    },
    {
      path: '/instructions',
      name: 'instructions',
      component: () => import('../views/2_InstructionsView.vue'),
    },
    {
      path: '/prompt',
      name: 'prompt',
      component: () => import('../views/3_PromptView.vue'),
    },
    {
      path: '/question',
      name: 'question',
      component: () => import('../views/4_QuestionView.vue'),
    },
    {
      path: '/model',
      name: 'model',
      component: () => import('../views/5_ModelView.vue'),
    },
  ],
})

export default router
