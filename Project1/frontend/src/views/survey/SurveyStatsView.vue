<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { getQuestionStatsApi, getSurveyStatsApi } from '../../api/survey'

const route = useRoute()
const router = useRouter()
const surveyId = route.params.id

const loading = ref(false)
const errorMessage = ref('')
const surveyStats = ref(null)
const selectedQuestionId = ref('')
const singleQuestionStats = ref(null)

const selectedQuestionSummary = computed(() => {
  const stat = singleQuestionStats.value
  if (!stat) return null

  const optionEntries = Object.entries(stat.option_counts || {})
  const totalOptionCount = optionEntries.reduce((sum, [, count]) => sum + Number(count || 0), 0)
  const totalAnswered = stat.type === 'single_choice' ? Number(stat.total_answered || totalOptionCount) : totalOptionCount

  return {
    ...stat,
    optionEntries,
    totalOptionCount,
    totalAnswered
  }
})

const getPercentage = (count, total) => {
  if (!total) return 0
  return Math.round((Number(count || 0) / total) * 100)
}

const loadStats = async () => {
  loading.value = true
  errorMessage.value = ''
  try {
    surveyStats.value = await getSurveyStatsApi(surveyId)
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    loading.value = false
  }
}

const loadSingleQuestionStats = async () => {
  if (!selectedQuestionId.value) {
    singleQuestionStats.value = null
    return
  }
  errorMessage.value = ''
  try {
    singleQuestionStats.value = await getQuestionStatsApi(selectedQuestionId.value)
  } catch (error) {
    errorMessage.value = error.message
  }
}

onMounted(loadStats)
</script>

<template>
  <section class="space-y-5">
    <button class="btn-secondary" @click="router.push('/surveys')">返回问卷列表</button>

    <div v-if="loading" class="card text-center text-slate-500">统计加载中...</div>

    <template v-else-if="surveyStats">
      <div class="card">
        <h2 class="font-display text-2xl font-extrabold">{{ surveyStats.survey.title }} · 统计总览</h2>
        <p class="mt-2 text-slate-600">总提交次数：{{ surveyStats.submission_count }}</p>
      </div>

      <div class="card">
        <h3 class="font-display text-lg font-bold">单题统计</h3>
        <select v-model="selectedQuestionId" class="input mt-3" @change="loadSingleQuestionStats">
          <option value="">请选择题目</option>
          <option v-for="item in surveyStats.questions" :key="item.question_id" :value="item.question_id">{{ item.title
            }}</option>
        </select>

        <div v-if="selectedQuestionSummary" class="mt-4 space-y-3">
          <div class="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3">
            <p class="text-sm text-slate-500">题目类型</p>
            <p class="font-semibold text-ink">{{ selectedQuestionSummary.type }}</p>
          </div>

          <div v-if="selectedQuestionSummary.type === 'single_choice'"
            class="space-y-2 rounded-xl border border-slate-200 bg-white p-4">
            <p class="text-sm text-slate-600">回答人数：{{ selectedQuestionSummary.totalAnswered }}</p>
            <div v-for="([key, count]) in selectedQuestionSummary.optionEntries" :key="key" class="space-y-1">
              <div class="flex items-center justify-between text-sm">
                <span class="font-medium">{{ key }}</span>
                <span>{{ count }}（{{ getPercentage(count, selectedQuestionSummary.totalAnswered) }}%）</span>
              </div>
              <div class="h-2 rounded-full bg-slate-100">
                <div class="h-2 rounded-full bg-ocean"
                  :style="{ width: `${getPercentage(count, selectedQuestionSummary.totalAnswered)}%` }"></div>
              </div>
            </div>
          </div>

          <div v-else-if="selectedQuestionSummary.type === 'multi_choice'"
            class="space-y-2 rounded-xl border border-slate-200 bg-white p-4">
            <p class="text-sm text-slate-600">总选择次数：{{ selectedQuestionSummary.totalOptionCount }}</p>
            <div v-for="([key, count]) in selectedQuestionSummary.optionEntries" :key="key" class="space-y-1">
              <div class="flex items-center justify-between text-sm">
                <span class="font-medium">{{ key }}</span>
                <span>{{ count }}（{{ getPercentage(count, selectedQuestionSummary.totalOptionCount) }}%）</span>
              </div>
              <div class="h-2 rounded-full bg-slate-100">
                <div class="h-2 rounded-full bg-sky-500"
                  :style="{ width: `${getPercentage(count, selectedQuestionSummary.totalOptionCount)}%` }"></div>
              </div>
            </div>
          </div>

          <div v-else class="space-y-3 rounded-xl border border-slate-200 bg-white p-4">
            <p class="text-sm text-slate-600">填空条目：{{ selectedQuestionSummary.values?.length || 0 }}</p>
            <p class="text-sm text-slate-600">平均值：{{ selectedQuestionSummary.average ?? 'N/A' }}</p>
            <div class="max-h-48 space-y-1 overflow-auto rounded-xl bg-slate-50 p-2">
              <div v-for="(val, idx) in selectedQuestionSummary.values" :key="idx"
                class="rounded-lg bg-white px-2 py-1 text-sm text-slate-700">
                {{ val }}
              </div>
              <p v-if="!selectedQuestionSummary.values || selectedQuestionSummary.values.length === 0"
                class="px-2 py-1 text-sm text-slate-500">
                暂无填空数据
              </p>
            </div>
          </div>
        </div>
      </div>

      <div class="space-y-4">
        <div v-for="item in surveyStats.questions" :key="item.question_id" class="card">
          <h4 class="font-semibold">{{ item.title }} <span class="text-xs text-slate-500">({{ item.type }})</span></h4>

          <div v-if="item.type === 'single_choice'" class="mt-2 space-y-1">
            <p class="text-sm text-slate-600">回答人数：{{ item.total_answered }}</p>
            <div v-for="(count, key) in item.option_counts" :key="key"
              class="flex items-center justify-between rounded-lg bg-slate-100 px-3 py-2 text-sm">
              <span>{{ key }}</span>
              <span>{{ count }}</span>
            </div>
          </div>

          <div v-else-if="item.type === 'multi_choice'" class="mt-2 space-y-1">
            <div v-for="(count, key) in item.option_counts" :key="key"
              class="flex items-center justify-between rounded-lg bg-slate-100 px-3 py-2 text-sm">
              <span>{{ key }}</span>
              <span>{{ count }}</span>
            </div>
          </div>

          <div v-else class="mt-2">
            <p class="text-sm text-slate-600">平均值：{{ item.average ?? 'N/A' }}</p>
            <div class="mt-2 max-h-40 space-y-1 overflow-auto rounded-xl bg-slate-100 p-2">
              <div v-for="(val, idx) in item.values" :key="idx" class="rounded-md bg-white px-2 py-1 text-sm">{{ val }}
              </div>
              <p v-if="!item.values || item.values.length === 0" class="text-sm text-slate-500">暂无填空数据</p>
            </div>
          </div>
        </div>
      </div>
    </template>

    <p v-if="errorMessage" class="card text-coral">{{ errorMessage }}</p>
  </section>
</template>
