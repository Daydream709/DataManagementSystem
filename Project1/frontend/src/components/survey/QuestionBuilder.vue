<script setup>
import { reactive, ref } from 'vue'

import { createQuestionApi, deleteQuestionApi, updateQuestionApi } from '../../api/survey'

const props = defineProps({
  surveyId: {
    type: String,
    required: true
  },
  questions: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['changed'])

const loading = ref(false)
const errorMessage = ref('')
const message = ref('')
const editingId = ref('')

const createDefaultForm = () => ({
  order: 1,
  type: 'single_choice',
  title: '',
  required: false,
  optionLabels: ['选项1', '选项2'],
  multiMin: '',
  multiMax: '',
  fillValueType: 'text',
  textMin: '',
  textMax: '',
  numberMin: '',
  numberMax: '',
  numberInteger: false
})

const form = reactive(createDefaultForm())
const editForm = reactive(createDefaultForm())

const resetForm = () => {
  Object.assign(form, createDefaultForm())
  form.order = props.questions.length + 1
}

const normalizeOptionLabels = (labels) => labels.map((item) => item.trim()).filter((item) => item)

const buildOptions = (labels) => {
  const normalized = normalizeOptionLabels(labels)
  return normalized.map((label, index) => ({
    key: index < 26 ? String.fromCharCode(65 + index) : `OPT_${index + 1}`,
    label
  }))
}

const parseNumber = (value) => {
  if (value === '' || value === null || value === undefined) return null
  return Number(value)
}

const buildPayload = (source) => {
  const payload = {
    order: Number(source.order),
    type: source.type,
    title: source.title.trim(),
    required: Boolean(source.required)
  }

  if (!payload.title) {
    throw new Error('题目标题不能为空')
  }

  if (payload.type === 'single_choice' || payload.type === 'multi_choice') {
    payload.options = buildOptions(source.optionLabels)
    if (payload.options.length < 2) {
      throw new Error('选择题至少需要 2 个选项')
    }
  }

  if (payload.type === 'multi_choice') {
    const minSelect = parseNumber(source.multiMin)
    const maxSelect = parseNumber(source.multiMax)
    payload.validation = {}
    if (minSelect !== null) payload.validation.min_select = minSelect
    if (maxSelect !== null) payload.validation.max_select = maxSelect
  }

  if (payload.type === 'fill_blank') {
    payload.options = []
    payload.validation = {
      value_type: source.fillValueType
    }

    if (source.fillValueType === 'text') {
      const minLength = parseNumber(source.textMin)
      const maxLength = parseNumber(source.textMax)
      if (minLength !== null) payload.validation.min_length = minLength
      if (maxLength !== null) payload.validation.max_length = maxLength
    }

    if (source.fillValueType === 'number') {
      const minValue = parseNumber(source.numberMin)
      const maxValue = parseNumber(source.numberMax)
      if (minValue !== null) payload.validation.min_value = minValue
      if (maxValue !== null) payload.validation.max_value = maxValue
      payload.validation.is_integer = Boolean(source.numberInteger)
    }
  }

  return payload
}

const applyQuestionToForm = (question, target) => {
  target.order = question.order
  target.type = question.type
  target.title = question.title
  target.required = question.required

  target.optionLabels = (question.options || []).map((item) => item.label)
  if (target.optionLabels.length < 2) {
    target.optionLabels = ['选项1', '选项2']
  }

  const validation = question.validation || {}
  target.multiMin = validation.min_select ?? ''
  target.multiMax = validation.max_select ?? ''

  target.fillValueType = validation.value_type || 'text'
  target.textMin = validation.min_length ?? ''
  target.textMax = validation.max_length ?? ''
  target.numberMin = validation.min_value ?? ''
  target.numberMax = validation.max_value ?? ''
  target.numberInteger = Boolean(validation.is_integer)
}

const addOption = (target) => {
  target.optionLabels.push(`选项${target.optionLabels.length + 1}`)
}

const removeOption = (target, index) => {
  if (target.optionLabels.length <= 2) return
  target.optionLabels.splice(index, 1)
}

const createQuestion = async () => {
  loading.value = true
  errorMessage.value = ''
  message.value = ''
  try {
    const payload = buildPayload(form)
    await createQuestionApi(props.surveyId, payload)
    message.value = '题目已创建'
    resetForm()
    emit('changed')
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    loading.value = false
  }
}

const startEdit = (item) => {
  editingId.value = item.id
  applyQuestionToForm(item, editForm)
}

const cancelEdit = () => {
  editingId.value = ''
  Object.assign(editForm, createDefaultForm())
}

const submitEdit = async () => {
  if (!editingId.value) return
  loading.value = true
  errorMessage.value = ''
  message.value = ''
  try {
    const payload = buildPayload(editForm)
    await updateQuestionApi(editingId.value, payload)
    message.value = '题目已更新'
    cancelEdit()
    emit('changed')
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    loading.value = false
  }
}

const removeQuestion = async (id) => {
  loading.value = true
  errorMessage.value = ''
  message.value = ''
  try {
    await deleteQuestionApi(id)
    message.value = '题目已删除'
    emit('changed')
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    loading.value = false
  }
}

const summarizeValidation = (item) => {
  if (item.type === 'single_choice') {
    return `选项数 ${item.options?.length || 0}`
  }
  if (item.type === 'multi_choice') {
    const min = item.validation?.min_select
    const max = item.validation?.max_select
    return `选项数 ${item.options?.length || 0}，最少 ${min ?? '-'}，最多 ${max ?? '-'}`
  }
  if (item.validation?.value_type === 'number') {
    return `数字，最小 ${item.validation?.min_value ?? '-'}，最大 ${item.validation?.max_value ?? '-'}，整数 ${item.validation?.is_integer ? '是' : '否'}`
  }
  return `文本，最短 ${item.validation?.min_length ?? '-'}，最长 ${item.validation?.max_length ?? '-'}`
}

resetForm()
</script>

<template>
  <div class="card">
    <h3 class="font-display text-lg font-bold">题目配置</h3>
    <p class="mt-1 text-xs text-slate-500">使用可视化表单添加题目，不再需要手写 JSON。</p>

    <div class="mt-4 grid gap-3 md:grid-cols-2">
      <input v-model="form.title" class="input md:col-span-2" placeholder="题目标题" />
      <input v-model.number="form.order" class="input" type="number" min="1" placeholder="顺序" />
      <select v-model="form.type" class="input">
        <option value="single_choice">单选题</option>
        <option value="multi_choice">多选题</option>
        <option value="fill_blank">填空题</option>
      </select>
      <label class="flex items-center gap-2 text-sm md:col-span-2">
        <input v-model="form.required" type="checkbox" /> 必答题
      </label>
    </div>

    <div v-if="form.type === 'single_choice' || form.type === 'multi_choice'" class="mt-4 space-y-2">
      <p class="text-sm font-semibold">选项配置</p>
      <div v-for="(option, index) in form.optionLabels" :key="index" class="flex items-center gap-2">
        <input v-model="form.optionLabels[index]" class="input" :placeholder="`选项 ${index + 1}`" />
        <button class="btn-secondary" type="button" @click="removeOption(form, index)">删除</button>
      </div>
      <button class="btn-secondary" type="button" @click="addOption(form)">新增选项</button>
    </div>

    <div v-if="form.type === 'multi_choice'" class="mt-4 grid gap-3 md:grid-cols-2">
      <input v-model="form.multiMin" class="input" type="number" min="0" placeholder="最少选择数量（可选）" />
      <input v-model="form.multiMax" class="input" type="number" min="1" placeholder="最多选择数量（可选）" />
    </div>

    <div v-if="form.type === 'fill_blank'" class="mt-4 space-y-3">
      <select v-model="form.fillValueType" class="input">
        <option value="text">文本填空</option>
        <option value="number">数字填空</option>
      </select>

      <div v-if="form.fillValueType === 'text'" class="grid gap-3 md:grid-cols-2">
        <input v-model="form.textMin" class="input" type="number" min="0" placeholder="最少字数（可选）" />
        <input v-model="form.textMax" class="input" type="number" min="1" placeholder="最多字数（可选）" />
      </div>

      <div v-else class="grid gap-3 md:grid-cols-2">
        <input v-model="form.numberMin" class="input" type="number" placeholder="最小值（可选）" />
        <input v-model="form.numberMax" class="input" type="number" placeholder="最大值（可选）" />
        <label class="flex items-center gap-2 text-sm md:col-span-2">
          <input v-model="form.numberInteger" type="checkbox" /> 仅允许整数
        </label>
      </div>
    </div>

    <button class="btn-primary mt-4" :disabled="loading" @click="createQuestion">新增题目</button>

    <p v-if="message" class="mt-3 rounded-xl bg-ocean/10 px-3 py-2 text-sm text-ocean">{{ message }}</p>
    <p v-if="errorMessage" class="mt-3 rounded-xl bg-coral/10 px-3 py-2 text-sm text-coral">{{ errorMessage }}</p>

    <div class="mt-5 space-y-3">
      <div v-for="item in questions" :key="item.id" class="rounded-xl border border-slate-200 p-3">
        <div class="flex items-start justify-between gap-3">
          <div>
            <p class="font-semibold">Q{{ item.order }} · {{ item.title }}</p>
            <p class="text-xs text-slate-500">{{ item.type }} / {{ item.required ? '必答' : '非必答' }}</p>
            <p class="mt-1 text-xs text-slate-500">{{ summarizeValidation(item) }}</p>
          </div>
          <div class="flex gap-2">
            <button class="btn-secondary" @click="startEdit(item)">编辑</button>
            <button class="btn-secondary" @click="removeQuestion(item.id)">删除</button>
          </div>
        </div>
      </div>
    </div>

    <div v-if="editingId" class="mt-5 rounded-xl border border-ocean/30 bg-ocean/5 p-4">
      <h4 class="font-semibold">编辑题目</h4>
      <div class="mt-3 grid gap-3 md:grid-cols-2">
        <input v-model="editForm.title" class="input md:col-span-2" placeholder="题目标题" />
        <input v-model.number="editForm.order" class="input" type="number" min="1" />
        <select v-model="editForm.type" class="input">
          <option value="single_choice">单选题</option>
          <option value="multi_choice">多选题</option>
          <option value="fill_blank">填空题</option>
        </select>
        <label class="flex items-center gap-2 text-sm md:col-span-2">
          <input v-model="editForm.required" type="checkbox" /> 必答题
        </label>
      </div>

      <div v-if="editForm.type === 'single_choice' || editForm.type === 'multi_choice'" class="mt-4 space-y-2">
        <p class="text-sm font-semibold">选项配置</p>
        <div v-for="(option, index) in editForm.optionLabels" :key="index" class="flex items-center gap-2">
          <input v-model="editForm.optionLabels[index]" class="input" :placeholder="`选项 ${index + 1}`" />
          <button class="btn-secondary" type="button" @click="removeOption(editForm, index)">删除</button>
        </div>
        <button class="btn-secondary" type="button" @click="addOption(editForm)">新增选项</button>
      </div>

      <div v-if="editForm.type === 'multi_choice'" class="mt-4 grid gap-3 md:grid-cols-2">
        <input v-model="editForm.multiMin" class="input" type="number" min="0" placeholder="最少选择数量（可选）" />
        <input v-model="editForm.multiMax" class="input" type="number" min="1" placeholder="最多选择数量（可选）" />
      </div>

      <div v-if="editForm.type === 'fill_blank'" class="mt-4 space-y-3">
        <select v-model="editForm.fillValueType" class="input">
          <option value="text">文本填空</option>
          <option value="number">数字填空</option>
        </select>

        <div v-if="editForm.fillValueType === 'text'" class="grid gap-3 md:grid-cols-2">
          <input v-model="editForm.textMin" class="input" type="number" min="0" placeholder="最少字数（可选）" />
          <input v-model="editForm.textMax" class="input" type="number" min="1" placeholder="最多字数（可选）" />
        </div>

        <div v-else class="grid gap-3 md:grid-cols-2">
          <input v-model="editForm.numberMin" class="input" type="number" placeholder="最小值（可选）" />
          <input v-model="editForm.numberMax" class="input" type="number" placeholder="最大值（可选）" />
          <label class="flex items-center gap-2 text-sm md:col-span-2">
            <input v-model="editForm.numberInteger" type="checkbox" /> 仅允许整数
          </label>
        </div>
      </div>

      <div class="mt-4 flex gap-2">
        <button class="btn-primary" @click="submitEdit">保存修改</button>
        <button class="btn-secondary" @click="cancelEdit">取消</button>
      </div>
    </div>
  </div>
</template>
