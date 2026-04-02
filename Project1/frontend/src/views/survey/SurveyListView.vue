<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

import {
  closeSurveyApi,
  createSurveyApi,
  deleteSurveyApi,
  listSurveysApi,
  publishSurveyApi
} from '../../api/survey'

const router = useRouter()

const loading = ref(false)
const actionLoadingId = ref('')
const surveys = ref([])
const message = ref('')
const errorMessage = ref('')

const createForm = reactive({
  title: '',
  description: '',
  allow_anonymous: false,
  allow_multiple_submissions: true,
  deadline: ''
})

const fetchSurveys = async () => {
  loading.value = true
  errorMessage.value = ''
  try {
    surveys.value = await listSurveysApi()
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    loading.value = false
  }
}

const createSurvey = async () => {
  errorMessage.value = ''
  message.value = ''
  try {
    const payload = {
      ...createForm,
      deadline: createForm.deadline ? new Date(createForm.deadline).toISOString() : null
    }
    await createSurveyApi(payload)
    createForm.title = ''
    createForm.description = ''
    createForm.allow_anonymous = false
    createForm.allow_multiple_submissions = true
    createForm.deadline = ''
    message.value = '问卷创建成功'
    await fetchSurveys()
  } catch (error) {
    errorMessage.value = error.message
  }
}

const runAction = async (surveyId, action) => {
  if (action === 'delete') {
    const confirmed = window.confirm('确认删除该问卷吗？删除后题目、跳转规则和填写记录将一并删除。')
    if (!confirmed) return
  }

  actionLoadingId.value = `${surveyId}-${action}`
  errorMessage.value = ''
  message.value = ''
  try {
    if (action === 'publish') await publishSurveyApi(surveyId)
    if (action === 'close') await closeSurveyApi(surveyId)
    if (action === 'delete') await deleteSurveyApi(surveyId)
    message.value = '操作成功'
    await fetchSurveys()
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    actionLoadingId.value = ''
  }
}

const canOpenFill = (survey) => survey.status === 'published'
const canEditSurvey = (survey) => survey.status === 'draft'

const getFillUrl = (survey) => {
  if (survey.link) return survey.link
  return `${window.location.origin}/survey/${survey.slug}`
}

const copyFillLink = async (survey) => {
  if (!canOpenFill(survey)) {
    errorMessage.value = '问卷仅在发布状态下可复制填写链接'
    message.value = ''
    return
  }

  const url = getFillUrl(survey)
  try {
    await navigator.clipboard.writeText(url)
    message.value = '填写链接已复制'
    errorMessage.value = ''
  } catch {
    errorMessage.value = '复制失败，请检查浏览器剪贴板权限'
    message.value = ''
  }
}

onMounted(fetchSurveys)
</script>

<template>
  <section class="grid gap-6 lg:grid-cols-[360px,1fr]">
    <div class="card h-fit">
      <h2 class="font-display text-xl font-bold">创建新问卷</h2>
      <p class="mt-1 text-sm text-slate-500">创建后可在右侧继续编辑题目与跳转规则。</p>
      <div class="mt-4 space-y-3">
        <input v-model="createForm.title" class="input" placeholder="问卷标题" maxlength="200" />
        <textarea v-model="createForm.description" class="input min-h-24" placeholder="问卷说明"></textarea>
        <label class="flex items-center gap-2 text-sm">
          <input v-model="createForm.allow_anonymous" type="checkbox" class="h-4 w-4" />
          允许匿名提交
        </label>
        <label class="flex items-center gap-2 text-sm">
          <input v-model="createForm.allow_multiple_submissions" type="checkbox" class="h-4 w-4" />
          允许同一人多次填写
        </label>
        <div>
          <label class="mb-1 block text-sm text-slate-600">截止时间（可选）</label>
          <input v-model="createForm.deadline" type="datetime-local" class="input" />
        </div>
        <button class="btn-primary w-full" @click="createSurvey">创建问卷</button>
      </div>

      <p v-if="message" class="mt-4 rounded-xl bg-ocean/10 px-3 py-2 text-sm text-ocean">{{ message }}</p>
      <p v-if="errorMessage" class="mt-4 rounded-xl bg-coral/10 px-3 py-2 text-sm text-coral">{{ errorMessage }}</p>
    </div>

    <div class="space-y-4">
      <div class="flex items-center justify-between">
        <h2 class="font-display text-2xl font-extrabold">我的问卷</h2>
        <button class="btn-secondary" @click="fetchSurveys">刷新</button>
      </div>

      <div v-if="loading" class="card text-center text-slate-500">加载中...</div>
      <div v-else-if="surveys.length === 0" class="card text-center text-slate-500">暂无问卷，先创建一个吧。</div>

      <div v-for="item in surveys" :key="item.id" class="card">
        <div class="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h3 class="font-display text-lg font-bold">{{ item.title }}</h3>
            <p class="mt-1 text-sm text-slate-500">{{ item.description || '暂无说明' }}</p>
            <div class="mt-2 flex flex-wrap gap-2">
              <span class="badge"
                :class="item.status === 'published' ? 'bg-ocean/10 text-ocean' : item.status === 'closed' ? 'bg-slate-200 text-slate-600' : 'bg-sand text-ink'">
                {{ item.status }}
              </span>
              <span class="badge bg-slate-100 text-slate-500">匿名: {{ item.allow_anonymous ? '是' : '否' }}</span>
              <span class="badge bg-slate-100 text-slate-500">重复填写: {{ item.allow_multiple_submissions === false ? '否' :
                '是' }}</span>
            </div>
          </div>
          <div class="text-right text-xs text-slate-500">
            <div>创建于 {{ new Date(item.created_at).toLocaleString() }}</div>
            <div v-if="item.deadline">截止 {{ new Date(item.deadline).toLocaleString() }}</div>
          </div>
        </div>

        <div class="mt-4 grid gap-2 md:grid-cols-3 lg:grid-cols-5">
          <button class="btn-secondary" :disabled="!canEditSurvey(item)"
            :title="canEditSurvey(item) ? '编辑问卷' : '仅草稿状态可编辑'" @click="router.push(`/surveys/${item.id}/editor`)">
            编辑
          </button>
          <button class="btn-secondary" @click="router.push(`/surveys/${item.id}/stats`)">统计</button>
          <button class="btn-secondary" :disabled="!canOpenFill(item)"
            :title="canOpenFill(item) ? '复制填写链接' : '仅发布状态可填写'" @click="copyFillLink(item)">
            复制链接
          </button>
          <button class="btn-secondary" :disabled="actionLoadingId === `${item.id}-publish`"
            @click="runAction(item.id, 'publish')">发布</button>
          <button class="btn-secondary" :disabled="actionLoadingId === `${item.id}-close`"
            @click="runAction(item.id, 'close')">关闭</button>
        </div>
        <button class="mt-2 text-sm font-semibold text-coral" :disabled="actionLoadingId === `${item.id}-delete`"
          @click="runAction(item.id, 'delete')">删除问卷</button>
      </div>
    </div>
  </section>
</template>
