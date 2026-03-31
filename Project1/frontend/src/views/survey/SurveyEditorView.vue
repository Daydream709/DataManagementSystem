<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import JumpRuleBuilder from '../../components/survey/JumpRuleBuilder.vue'
import QuestionBuilder from '../../components/survey/QuestionBuilder.vue'
import {
  getSurveyApi,
  listJumpRulesApi,
  listQuestionsApi,
  updateSurveyApi
} from '../../api/survey'

const route = useRoute()
const router = useRouter()

const surveyId = route.params.id
const loading = ref(false)
const saving = ref(false)
const message = ref('')
const errorMessage = ref('')

const survey = ref(null)
const questions = ref([])
const jumpRules = ref([])

const form = reactive({
  title: '',
  description: '',
  allow_anonymous: false,
  deadline: ''
})

const fetchData = async () => {
  loading.value = true
  errorMessage.value = ''
  try {
    const [surveyData, questionData, ruleData] = await Promise.all([
      getSurveyApi(surveyId),
      listQuestionsApi(surveyId),
      listJumpRulesApi(surveyId)
    ])
    survey.value = surveyData
    questions.value = questionData
    jumpRules.value = ruleData

    form.title = surveyData.title
    form.description = surveyData.description || ''
    form.allow_anonymous = surveyData.allow_anonymous
    form.deadline = surveyData.deadline ? new Date(surveyData.deadline).toISOString().slice(0, 16) : ''
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    loading.value = false
  }
}

const saveSurvey = async () => {
  saving.value = true
  errorMessage.value = ''
  message.value = ''
  try {
    await updateSurveyApi(surveyId, {
      title: form.title,
      description: form.description,
      allow_anonymous: form.allow_anonymous,
      deadline: form.deadline ? new Date(form.deadline).toISOString() : null
    })
    message.value = '问卷信息已更新'
    await fetchData()
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    saving.value = false
  }
}

onMounted(fetchData)
</script>

<template>
  <section class="space-y-5">
    <button class="btn-secondary" @click="router.push('/surveys')">返回问卷列表</button>

    <div v-if="loading" class="card text-center text-slate-500">加载中...</div>

    <template v-else>
      <div class="card">
        <div class="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 class="font-display text-2xl font-extrabold">问卷编辑器</h2>
            <p class="text-sm text-slate-500">ID: {{ surveyId }}</p>
          </div>
        </div>

        <div class="mt-4 grid gap-3 md:grid-cols-2">
          <input v-model="form.title" class="input md:col-span-2" placeholder="问卷标题" />
          <textarea v-model="form.description" class="input min-h-24 md:col-span-2" placeholder="问卷说明"></textarea>
          <label class="flex items-center gap-2 text-sm">
            <input v-model="form.allow_anonymous" type="checkbox" /> 允许匿名
          </label>
          <input v-model="form.deadline" type="datetime-local" class="input" />
        </div>

        <button class="btn-primary mt-3" :disabled="saving" @click="saveSurvey">保存问卷信息</button>

        <p v-if="message" class="mt-3 rounded-xl bg-ocean/10 px-3 py-2 text-sm text-ocean">{{ message }}</p>
        <p v-if="errorMessage" class="mt-3 rounded-xl bg-coral/10 px-3 py-2 text-sm text-coral">{{ errorMessage }}</p>
      </div>

      <div class="grid gap-5 lg:grid-cols-2">
        <QuestionBuilder :survey-id="surveyId" :questions="questions" @changed="fetchData" />
        <JumpRuleBuilder :survey-id="surveyId" :questions="questions" :rules="jumpRules" @changed="fetchData" />
      </div>
    </template>
  </section>
</template>
