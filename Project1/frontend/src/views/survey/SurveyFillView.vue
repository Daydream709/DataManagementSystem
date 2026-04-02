<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import FillQuestionCard from '../../components/survey/FillQuestionCard.vue'
import { getPublicSurveyApi, nextQuestionApi, submitSurveyApi } from '../../api/survey'

const route = useRoute()
const router = useRouter()

const slug = route.params.slug
const loading = ref(false)
const stepping = ref(false)
const submitting = ref(false)
const finalActionLocked = ref(false)
const message = ref('')
const errorMessage = ref('')

const survey = ref(null)
const currentQuestionId = ref('')
const pageMode = ref('intro')

const navigationHistory = ref([])
const historyCursor = ref(-1)

const answers = reactive({})
const submitMeta = reactive({
  is_anonymous: false
})

const hasAnswerValue = (value) => {
  if (value === undefined || value === null) return false
  if (typeof value === 'string') return value.trim() !== ''
  if (Array.isArray(value)) return value.length > 0
  return true
}

const questionMap = computed(() => {
  const map = {}
  if (!survey.value) return map
  for (const item of survey.value.questions) {
    map[item.id] = item
  }
  return map
})

const totalQuestionCount = computed(() => survey.value?.questions?.length || 0)

const answeredQuestionIds = computed(() => {
  if (!survey.value) return []
  return survey.value.questions.filter((item) => hasAnswerValue(answers[item.id])).map((item) => item.id)
})

const answeredQuestionIdSet = computed(() => new Set(answeredQuestionIds.value))

const requiredQuestionIds = computed(() => {
  if (!survey.value) return []
  return survey.value.questions.filter((item) => item.required).map((item) => item.id)
})

const requiredUnansweredIds = computed(() => {
  const answeredSet = answeredQuestionIdSet.value
  return requiredQuestionIds.value.filter((id) => !answeredSet.has(id))
})

const requiredUnansweredCount = computed(() => requiredUnansweredIds.value.length)
const answeredCount = computed(() => answeredQuestionIds.value.length)
const remainingCount = computed(() => Math.max(0, totalQuestionCount.value - answeredCount.value))
const canSubmit = computed(() => requiredUnansweredCount.value === 0)

const currentQuestion = computed(() => {
  if (!survey.value) return null
  return survey.value.questions.find((item) => item.id === currentQuestionId.value) || null
})

const canGoPrevious = computed(() => historyCursor.value > 0)

const questionCardClass = (question) => {
  const answered = answeredQuestionIdSet.value.has(question.id)
  if (answered && question.required) return 'border-ocean bg-ocean/10 text-ocean'
  if (answered && !question.required) return 'border-sky-300 bg-sky-50 text-sky-700'
  if (!answered && question.required) return 'border-coral bg-coral/10 text-coral'
  return 'border-slate-200 bg-white text-slate-500'
}

const formatQuestionStatus = (question) => {
  const answered = answeredQuestionIdSet.value.has(question.id)
  const requiredText = question.required ? '必答' : '非必答'
  const answeredText = answered ? '已填写' : '未填写'
  return `${requiredText} · ${answeredText}`
}

const resetNavigation = (firstQuestionId) => {
  navigationHistory.value = [firstQuestionId]
  historyCursor.value = 0
  currentQuestionId.value = firstQuestionId
}

const pushHistory = (questionId) => {
  const next = navigationHistory.value.slice(0, historyCursor.value + 1)
  next.push(questionId)
  navigationHistory.value = next
  historyCursor.value += 1
  currentQuestionId.value = questionId
}

const jumpToQuestion = (questionId) => {
  if (!questionId || !questionMap.value[questionId]) return
  pageMode.value = 'question'

  const existingIndex = navigationHistory.value.findIndex((id, index) => index <= historyCursor.value && id === questionId)
  if (existingIndex >= 0) {
    historyCursor.value = existingIndex
    currentQuestionId.value = questionId
    return
  }
  pushHistory(questionId)
}

const startFill = () => {
  if (!survey.value || !survey.value.questions.length) {
    errorMessage.value = '当前问卷暂无题目，无法填写'
    return
  }
  if (!currentQuestionId.value) {
    resetNavigation(survey.value.questions[0].id)
  }
  pageMode.value = 'question'
}

const goToFinalPage = () => {
  pageMode.value = 'final'
}

const backToQuestions = () => {
  if (!currentQuestionId.value && survey.value?.questions?.length) {
    resetNavigation(survey.value.questions[0].id)
  }
  pageMode.value = 'question'
}

const initialize = async () => {
  loading.value = true
  errorMessage.value = ''
  try {
    const data = await getPublicSurveyApi(slug)
    survey.value = data
    submitMeta.is_anonymous = false
    if (data.questions.length > 0) {
      resetNavigation(data.questions[0].id)
    }
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    loading.value = false
  }
}

const nextStep = async () => {
  if (!currentQuestion.value) return
  stepping.value = true
  errorMessage.value = ''
  try {
    const payload = {
      current_question_id: currentQuestion.value.id,
      answer: answers[currentQuestion.value.id] ?? null
    }
    const result = await nextQuestionApi(slug, payload)
    if (!result.next_question) {
      pageMode.value = 'final'
      return
    }

    const nextId = result.next_question.id
    const expectedNext = navigationHistory.value[historyCursor.value + 1]
    if (expectedNext === nextId) {
      historyCursor.value += 1
      currentQuestionId.value = nextId
    } else {
      pushHistory(nextId)
    }
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    stepping.value = false
  }
}

const previousStep = () => {
  if (!canGoPrevious.value) return
  historyCursor.value -= 1
  currentQuestionId.value = navigationHistory.value[historyCursor.value]
}

const submitSurvey = async () => {
  if (finalActionLocked.value) {
    return
  }

  if (!canSubmit.value) {
    errorMessage.value = '仍有必答题未完成，暂时无法提交'
    return
  }

  finalActionLocked.value = true
  submitting.value = true
  errorMessage.value = ''
  message.value = ''
  try {
    const answerPayload = (survey.value?.questions || [])
      .map((item) => item.id)
      .filter((id) => hasAnswerValue(answers[id]))
      .map((id) => ({
        question_id: id,
        answer: answers[id]
      }))

    const result = await submitSurveyApi(slug, {
      is_anonymous: submitMeta.is_anonymous,
      answers: answerPayload
    })

    message.value = `提交成功，记录ID：${result.submission_id}`
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    submitting.value = false
  }
}

onMounted(initialize)
</script>

<template>
  <section class="mx-auto max-w-6xl space-y-5 py-6">
    <button class="btn-secondary" @click="router.push('/surveys')">返回管理后台</button>

    <div v-if="loading" class="card text-center text-slate-500">问卷加载中...</div>

    <template v-else-if="survey">
      <div v-if="pageMode !== 'intro'" class="card">
        <h1 class="font-display text-2xl font-extrabold">{{ survey.title }}</h1>
        <p class="mt-2 text-slate-600">{{ survey.description || '暂无说明' }}</p>
        <p class="mt-2 text-xs text-slate-500">总题数：{{ totalQuestionCount }}</p>
      </div>

      <div v-if="pageMode === 'intro'" class="card space-y-4">
        <h2 class="font-display text-xl font-bold">开始填写前总览</h2>
        <div class="grid gap-3 md:grid-cols-2">
          <div class="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm">
            <span class="text-slate-500">问卷标题：</span>{{ survey.title }}
          </div>
          <div class="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm">
            <span class="text-slate-500">总题数：</span>{{ totalQuestionCount }}
          </div>
          <div class="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm md:col-span-2">
            <span class="text-slate-500">问卷描述：</span>{{ survey.description || '暂无说明' }}
          </div>
          <div class="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm md:col-span-2">
            <span class="text-slate-500">是否允许匿名：</span>{{ survey.allow_anonymous ? '是' : '否' }}
          </div>
        </div>

        <label v-if="survey.allow_anonymous" class="flex items-center gap-2 text-sm">
          <input v-model="submitMeta.is_anonymous" type="checkbox" />
          本次以匿名方式提交（仅隐藏展示身份，仍需登录填写）
        </label>

        <button class="btn-primary" @click="startFill">开始填写</button>
      </div>

      <div v-else-if="pageMode === 'final'" class="card space-y-4">
        <h2 class="font-display text-xl font-bold">填写情况总览</h2>
        <div class="grid gap-3 md:grid-cols-3">
          <div class="rounded-xl border border-slate-200 bg-slate-50 px-3 py-3 text-sm">
            <p class="text-slate-500">已填写</p>
            <p class="mt-1 text-2xl font-bold text-ocean">{{ answeredCount }}</p>
          </div>
          <div class="rounded-xl border border-slate-200 bg-slate-50 px-3 py-3 text-sm">
            <p class="text-slate-500">未填写</p>
            <p class="mt-1 text-2xl font-bold text-slate-700">{{ remainingCount }}</p>
          </div>
          <div class="rounded-xl border border-slate-200 bg-slate-50 px-3 py-3 text-sm">
            <p class="text-slate-500">未完成必答题</p>
            <p class="mt-1 text-2xl font-bold" :class="canSubmit ? 'text-ocean' : 'text-coral'">{{
              requiredUnansweredCount }}</p>
          </div>
        </div>

        <div v-if="requiredUnansweredCount > 0" class="rounded-xl bg-coral/10 px-3 py-2 text-sm text-coral">
          仍有必答题未填写：
          <span v-for="id in requiredUnansweredIds" :key="id" class="mr-2 inline-block">
            {{ questionMap[id]?.title || id }}
          </span>
        </div>

        <div class="flex flex-wrap gap-2">
          <button class="btn-secondary" :disabled="finalActionLocked" @click="backToQuestions">返回继续填写</button>
          <button class="btn-primary" :disabled="submitting || !canSubmit || finalActionLocked" @click="submitSurvey">
            {{ finalActionLocked ? '已提交' : submitting ? '提交中...' : '填写完成并提交' }}
          </button>
        </div>
      </div>

      <div v-else class="grid gap-5 lg:grid-cols-[1fr,320px]">
        <div class="space-y-4">
          <FillQuestionCard v-if="currentQuestion" :question="currentQuestion" v-model="answers[currentQuestion.id]" />

          <div class="card">
            <div class="grid gap-2 md:grid-cols-2">
              <button class="btn-secondary" :disabled="!canGoPrevious" @click="previousStep">上一题</button>
              <button class="btn-primary" :disabled="stepping" @click="nextStep">
                {{ stepping ? '校验并跳转中...' : '下一题' }}
              </button>
            </div>
          </div>
        </div>

        <aside class="card h-fit space-y-3 lg:sticky lg:top-20">
          <h3 class="font-display text-lg font-bold">填写情况总览</h3>
          <p class="text-xs text-slate-500">点击方框可跳转到对应题目</p>

          <div class="grid grid-cols-2 gap-2">
            <button v-for="question in survey.questions" :key="question.id" type="button"
              class="rounded-xl border px-2 py-2 text-left text-xs transition hover:shadow-sm"
              :class="questionCardClass(question)" @click="jumpToQuestion(question.id)">
              <p class="font-semibold">Q{{ question.order }}</p>
              <p class="mt-1 line-clamp-2 text-[11px]">{{ question.title }}</p>
              <p class="mt-1 text-[10px] opacity-90">{{ formatQuestionStatus(question) }}</p>
            </button>
          </div>

          <div class="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-600">
            已填写 {{ answeredCount }} / {{ totalQuestionCount }}，未完成必答 {{ requiredUnansweredCount }}
          </div>

          <button class="btn-primary w-full" @click="goToFinalPage">前往提交页</button>
        </aside>
      </div>

      <p v-if="message" class="rounded-xl bg-ocean/10 px-3 py-2 text-sm text-ocean">{{ message }}</p>
      <p v-if="errorMessage" class="rounded-xl bg-coral/10 px-3 py-2 text-sm text-coral">{{ errorMessage }}</p>
    </template>

    <p v-else-if="errorMessage" class="card text-coral">{{ errorMessage }}</p>
  </section>
</template>
