<script setup>
import { computed } from 'vue'

const props = defineProps({
  question: {
    type: Object,
    required: true
  },
  modelValue: {
    type: [String, Number, Array, null],
    default: null
  }
})

const emit = defineEmits(['update:modelValue'])

const valueType = computed(() => props.question?.validation?.value_type || 'text')

const updateSingle = (value) => {
  emit('update:modelValue', value)
}

const updateMulti = (key, checked) => {
  const current = Array.isArray(props.modelValue) ? [...props.modelValue] : []
  if (checked && !current.includes(key)) current.push(key)
  if (!checked) {
    const idx = current.indexOf(key)
    if (idx >= 0) current.splice(idx, 1)
  }
  emit('update:modelValue', current)
}

const updateText = (event) => {
  emit('update:modelValue', event.target.value)
}

const updateNumber = (event) => {
  const raw = event.target.value
  emit('update:modelValue', raw === '' ? '' : Number(raw))
}
</script>

<template>
  <div class="card">
    <div class="mb-3 flex items-center justify-between">
      <h3 class="font-display text-xl font-bold">Q{{ question.order }}. {{ question.title }}</h3>
      <span v-if="question.required" class="badge bg-coral/15 text-coral">必答</span>
    </div>

    <div v-if="question.type === 'single_choice'" class="space-y-2">
      <label v-for="option in question.options" :key="option.key" class="flex cursor-pointer items-center gap-2 rounded-xl border border-slate-200 px-3 py-2 hover:border-ocean">
        <input
          type="radio"
          :name="`single-${question.id}`"
          :checked="modelValue === option.key"
          @change="updateSingle(option.key)"
        />
        <span>{{ option.label }}</span>
      </label>
    </div>

    <div v-else-if="question.type === 'multi_choice'" class="space-y-2">
      <label v-for="option in question.options" :key="option.key" class="flex cursor-pointer items-center gap-2 rounded-xl border border-slate-200 px-3 py-2 hover:border-ocean">
        <input
          type="checkbox"
          :checked="Array.isArray(modelValue) && modelValue.includes(option.key)"
          @change="updateMulti(option.key, $event.target.checked)"
        />
        <span>{{ option.label }}</span>
      </label>
      <p class="text-xs text-slate-500">min: {{ question.validation?.min_select ?? '-' }}, max: {{ question.validation?.max_select ?? '-' }}</p>
    </div>

    <div v-else>
      <input
        v-if="valueType === 'number'"
        class="input"
        type="number"
        :value="modelValue ?? ''"
        @input="updateNumber"
      />
      <textarea
        v-else
        class="input min-h-24"
        :value="modelValue ?? ''"
        @input="updateText"
      ></textarea>
      <p class="mt-2 text-xs text-slate-500">规则: {{ JSON.stringify(question.validation || {}) }}</p>
    </div>
  </div>
</template>
