<script setup>
import { computed, reactive, ref, watch } from 'vue'

import { createJumpRuleApi, deleteJumpRuleApi } from '../../api/survey'

const props = defineProps({
  surveyId: {
    type: String,
    required: true
  },
  questions: {
    type: Array,
    default: () => []
  },
  rules: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['changed'])

const form = reactive({
  question_id: '',
  operator: '',
  target_question_id: '',
  target_order: '',
  priority: 100,
  singleValue: '',
  selectedValues: [],
  numberValue: '',
  rangeMin: '',
  rangeMax: ''
})

const loading = ref(false)
const errorMessage = ref('')
const message = ref('')

const questionMap = computed(() => {
  const map = {}
  for (const item of props.questions) {
    map[item.id] = item
  }
  return map
})

const sourceQuestion = computed(() => questionMap.value[form.question_id] || null)

const ruleType = computed(() => {
  if (!sourceQuestion.value) return ''
  if (sourceQuestion.value.type === 'single_choice') return 'single_choice'
  if (sourceQuestion.value.type === 'multi_choice') return 'multi_choice'
  if (sourceQuestion.value.type === 'fill_blank' && sourceQuestion.value.validation?.value_type === 'number') return 'number'
  return ''
})

const operatorOptions = computed(() => {
  if (ruleType.value === 'single_choice') {
    return [
      { value: 'eq', label: '等于某个选项' },
      { value: 'in', label: '属于多个选项' }
    ]
  }
  if (ruleType.value === 'multi_choice') {
    return [
      { value: 'contains_any', label: '包含任意一个选项' },
      { value: 'contains_all', label: '包含所有选项' },
      { value: 'in', label: '答案精确匹配集合' }
    ]
  }
  if (ruleType.value === 'number') {
    return [
      { value: 'eq', label: '等于' },
      { value: 'gt', label: '大于' },
      { value: 'gte', label: '大于等于' },
      { value: 'lt', label: '小于' },
      { value: 'lte', label: '小于等于' },
      { value: 'range', label: '介于区间' }
    ]
  }
  return []
})

const sourceOptions = computed(() => sourceQuestion.value?.options || [])

watch(ruleType, (nextRuleType) => {
  const first = operatorOptions.value[0]
  form.operator = first ? first.value : ''
  form.singleValue = ''
  form.selectedValues = []
  form.numberValue = ''
  form.rangeMin = ''
  form.rangeMax = ''

  if (nextRuleType === 'single_choice' && sourceOptions.value.length > 0) {
    form.singleValue = sourceOptions.value[0].key
  }
})

const toggleSelectedValue = (value, checked) => {
  if (checked && !form.selectedValues.includes(value)) {
    form.selectedValues.push(value)
  }
  if (!checked) {
    form.selectedValues = form.selectedValues.filter((item) => item !== value)
  }
}

const buildRuleValue = () => {
  if (ruleType.value === 'single_choice') {
    if (form.operator === 'eq') {
      if (!form.singleValue) throw new Error('请选择触发选项')
      return form.singleValue
    }
    if (form.selectedValues.length < 1) throw new Error('请至少选择一个触发选项')
    return form.selectedValues
  }

  if (ruleType.value === 'multi_choice') {
    if (form.selectedValues.length < 1) throw new Error('请至少选择一个触发选项')
    return form.selectedValues
  }

  if (ruleType.value === 'number') {
    if (form.operator === 'range') {
      if (form.rangeMin === '' || form.rangeMax === '') {
        throw new Error('请输入完整的区间范围')
      }
      return [Number(form.rangeMin), Number(form.rangeMax)]
    }
    if (form.numberValue === '') {
      throw new Error('请输入数字阈值')
    }
    return Number(form.numberValue)
  }

  throw new Error('当前题目类型不支持跳转规则')
}

const createRule = async () => {
  loading.value = true
  errorMessage.value = ''
  message.value = ''

  try {
    if (!form.question_id) {
      throw new Error('请先选择源题目')
    }
    if (!ruleType.value) {
      throw new Error('该题目不支持跳转规则，仅支持单选/多选/数字填空')
    }

    const payload = {
      question_id: form.question_id,
      rule_type: ruleType.value,
      operator: form.operator,
      value: buildRuleValue(),
      target_question_id: form.target_question_id || null,
      target_order: form.target_order ? Number(form.target_order) : null,
      priority: Number(form.priority)
    }

    await createJumpRuleApi(props.surveyId, payload)
    message.value = '跳转规则已创建'
    emit('changed')
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    loading.value = false
  }
}

const removeRule = async (ruleId) => {
  loading.value = true
  errorMessage.value = ''
  message.value = ''
  try {
    await deleteJumpRuleApi(ruleId)
    message.value = '跳转规则已删除'
    emit('changed')
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    loading.value = false
  }
}

const questionText = (questionId) => {
  const question = questionMap.value[questionId]
  if (!question) return questionId
  return `Q${question.order} ${question.title}`
}

const targetText = (rule) => {
  if (rule.target_question_id) {
    return questionText(rule.target_question_id)
  }
  if (rule.target_order) {
    return `Q${rule.target_order}`
  }
  return '-'
}
</script>

<template>
  <div class="card">
    <h3 class="font-display text-lg font-bold">跳转规则配置</h3>
    <p class="mt-1 text-xs text-slate-500">选择题可直接勾选选项，数字题可直接填写阈值或区间。</p>

    <div class="mt-4 grid gap-3 md:grid-cols-2">
      <select v-model="form.question_id" class="input md:col-span-2">
        <option value="">选择源题目</option>
        <option v-for="item in questions" :key="item.id" :value="item.id">
          Q{{ item.order }} · {{ item.title }}
        </option>
      </select>

      <div class="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-700 md:col-span-2">
        规则类型：{{ ruleType || '未选择或不支持' }}
      </div>

      <select v-model="form.operator" class="input md:col-span-2" :disabled="!ruleType">
        <option value="" disabled>选择比较方式</option>
        <option v-for="op in operatorOptions" :key="op.value" :value="op.value">{{ op.label }}</option>
      </select>

      <div v-if="ruleType === 'single_choice' && form.operator === 'eq'" class="md:col-span-2">
        <select v-model="form.singleValue" class="input">
          <option value="">选择触发选项</option>
          <option v-for="opt in sourceOptions" :key="opt.key" :value="opt.key">{{ opt.label }}</option>
        </select>
      </div>

      <div v-if="(ruleType === 'single_choice' && form.operator === 'in') || ruleType === 'multi_choice'" class="space-y-2 md:col-span-2">
        <p class="text-sm text-slate-600">触发选项（可多选）</p>
        <label v-for="opt in sourceOptions" :key="opt.key" class="flex items-center gap-2 rounded-lg border border-slate-200 px-3 py-2">
          <input
            type="checkbox"
            :checked="form.selectedValues.includes(opt.key)"
            @change="toggleSelectedValue(opt.key, $event.target.checked)"
          />
          {{ opt.label }}
        </label>
      </div>

      <div v-if="ruleType === 'number' && form.operator !== 'range'" class="md:col-span-2">
        <input v-model="form.numberValue" class="input" type="number" placeholder="数字阈值" />
      </div>

      <div v-if="ruleType === 'number' && form.operator === 'range'" class="grid gap-3 md:col-span-2 md:grid-cols-2">
        <input v-model="form.rangeMin" class="input" type="number" placeholder="区间最小值" />
        <input v-model="form.rangeMax" class="input" type="number" placeholder="区间最大值" />
      </div>

      <select v-model="form.target_question_id" class="input">
        <option value="">按题号跳转</option>
        <option v-for="item in questions" :key="item.id" :value="item.id">Q{{ item.order }} · {{ item.title }}</option>
      </select>
      <input v-model="form.target_order" class="input" type="number" min="1" placeholder="或输入目标题号" />

      <input v-model="form.priority" class="input md:col-span-2" type="number" min="1" placeholder="优先级，越小越先匹配" />
    </div>

    <button class="btn-primary mt-4" :disabled="loading" @click="createRule">新增规则</button>

    <p v-if="message" class="mt-3 rounded-xl bg-ocean/10 px-3 py-2 text-sm text-ocean">{{ message }}</p>
    <p v-if="errorMessage" class="mt-3 rounded-xl bg-coral/10 px-3 py-2 text-sm text-coral">{{ errorMessage }}</p>

    <div class="mt-5 space-y-3">
      <div v-for="item in rules" :key="item.id" class="flex items-start justify-between gap-3 rounded-xl border border-slate-200 p-3">
        <div>
          <p class="font-semibold">{{ questionText(item.question_id) }}</p>
          <p class="text-xs text-slate-500">{{ item.rule_type }} / {{ item.operator }} / {{ JSON.stringify(item.value) }}</p>
          <p class="text-xs text-slate-500">跳转到：{{ targetText(item) }} / 优先级：{{ item.priority }}</p>
        </div>
        <button class="btn-secondary" @click="removeRule(item.id)">删除</button>
      </div>
    </div>
  </div>
</template>
