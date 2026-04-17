<script setup>
import { onMounted, ref } from 'vue'

import {
  createNewBankVersionApi,
  deleteQuestionBankApi,
  getBankCrossStatsApi,
  getBankUsageApi,
  importQuestionFromBankApi,
  listBankVersionsApi,
  listQuestionBankApi,
  listSharedBankApi,
  restoreBankVersionApi,
  shareBankItemApi,
  updateBankItemApi
} from '../../api/survey'

const props = defineProps({
  surveyId: {
    type: String,
    required: true
  },
  currentQuestionCount: {
    type: Number,
    default: 0
  }
})

const emit = defineEmits(['changed'])

const activeTab = ref('mine')
const loading = ref(false)
const message = ref('')
const errorMessage = ref('')

const myItems = ref([])
const sharedItems = ref([])

// Detail panel state
const detailMode = ref(null)
const detailItem = ref(null)
const detailData = ref(null)

// Share form
const shareUsernames = ref('')

// New version form
const newVersionForm = ref({ title: '', version_note: '' })

// Edit form
const editForm = ref({ title: '', version_note: '' })
const editVersions = ref([])
const editSelectedVersion = ref(null)

// Cross-stats version selector
const crossStatsVersions = ref([])
const crossStatsSelectedVersion = ref(null)

const typeLabel = (type) => {
  const map = { single_choice: '单选', multi_choice: '多选', fill_blank: '填空' }
  return map[type] || type
}

const summarizeOptions = (item) => {
  if (item.type === 'fill_blank') {
    const v = item.validation || {}
    if (v.value_type === 'number') return '数字'
    return '文本'
  }
  return `${(item.options || []).length} 个选项`
}

const fetchMine = async () => {
  try {
    myItems.value = await listQuestionBankApi()
  } catch (e) { /* ignore */ }
}

const fetchShared = async () => {
  try {
    sharedItems.value = await listSharedBankApi()
  } catch (e) { /* ignore */ }
}

const fetchCurrentTab = () => {
  if (activeTab.value === 'mine') return fetchMine()
  return fetchShared()
}

const switchTab = (tab) => {
  activeTab.value = tab
  closeDetail()
  message.value = ''
  errorMessage.value = ''
  fetchCurrentTab()
}

const importItem = async (item) => {
  loading.value = true
  message.value = ''
  errorMessage.value = ''
  try {
    const order = props.currentQuestionCount + 1
    await importQuestionFromBankApi(props.surveyId, {
      item_id: item.id,
      order,
      required: false
    })
    message.value = `「${item.title}」已导入为第 ${order} 题`
    emit('changed')
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    loading.value = false
  }
}

const removeItem = async (itemId) => {
  loading.value = true
  message.value = ''
  errorMessage.value = ''
  try {
    await deleteQuestionBankApi(itemId)
    message.value = '已删除'
    closeDetail()
    await fetchCurrentTab()
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    loading.value = false
  }
}

const removeChain = async (itemId) => {
  loading.value = true
  message.value = ''
  errorMessage.value = ''
  try {
    await deleteQuestionBankApi(itemId, true)
    message.value = '已删除全部版本'
    closeDetail()
    await fetchCurrentTab()
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    loading.value = false
  }
}

const closeDetail = () => {
  detailMode.value = null
  detailItem.value = null
  detailData.value = null
}

const showVersions = async (item) => {
  detailMode.value = 'versions'
  detailItem.value = item
  detailData.value = null
  try {
    detailData.value = await listBankVersionsApi(item.id)
  } catch (error) {
    errorMessage.value = error.message
  }
}

const showShare = (item) => {
  detailMode.value = 'share'
  detailItem.value = item
  shareUsernames.value = ''
}

const showUsage = async (item) => {
  detailMode.value = 'usage'
  detailItem.value = item
  detailData.value = null
  try {
    detailData.value = await getBankUsageApi(item.id)
  } catch (error) {
    errorMessage.value = error.message
  }
}

const showCrossStats = async (item, versionItemId = null) => {
  detailMode.value = 'cross-stats'
  detailItem.value = item
  detailData.value = null
  crossStatsSelectedVersion.value = versionItemId
  try {
    const [stats, versions] = await Promise.all([
      getBankCrossStatsApi(item.id, versionItemId),
      listBankVersionsApi(item.id)
    ])
    detailData.value = stats
    crossStatsVersions.value = versions
  } catch (error) {
    errorMessage.value = error.message
  }
}

const changeCrossStatsVersion = async (versionItemId) => {
  if (!detailItem.value) return
  crossStatsSelectedVersion.value = versionItemId || null
  try {
    detailData.value = await getBankCrossStatsApi(detailItem.value.id, versionItemId || null)
  } catch (error) {
    errorMessage.value = error.message
  }
}

const showEdit = async (item) => {
  detailMode.value = 'edit'
  detailItem.value = item
  editForm.value = { title: item.title, version_note: item.version_note || '' }
  editSelectedVersion.value = item.id
  try {
    editVersions.value = await listBankVersionsApi(item.id)
  } catch (error) {
    errorMessage.value = error.message
  }
}

const selectEditVersion = (version) => {
  editSelectedVersion.value = version.id
  editForm.value = { title: version.title, version_note: version.version_note || '' }
}

const submitEdit = async () => {
  loading.value = true
  message.value = ''
  errorMessage.value = ''
  try {
    const payload = {}
    if (editForm.value.title.trim()) payload.title = editForm.value.title.trim()
    if (editForm.value.version_note.trim()) payload.version_note = editForm.value.version_note.trim()
    const result = await updateBankItemApi(editSelectedVersion.value, payload)
    message.value = result.version !== detailItem.value.version
      ? `版本已被使用，已自动创建新版本 v${result.version}`
      : '题目已更新'
    closeDetail()
    await fetchCurrentTab()
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    loading.value = false
  }
}

const showNewVersion = (item) => {
  detailMode.value = 'new-version'
  detailItem.value = item
  newVersionForm.value = { title: item.title, version_note: '' }
}

const submitShare = async () => {
  if (!shareUsernames.value.trim()) return
  loading.value = true
  message.value = ''
  errorMessage.value = ''
  try {
    const usernames = shareUsernames.value.split(/[,，\s]+/).filter((s) => s.trim())
    await shareBankItemApi(detailItem.value.id, usernames)
    message.value = '共享成功'
    closeDetail()
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    loading.value = false
  }
}

const submitNewVersion = async () => {
  loading.value = true
  message.value = ''
  errorMessage.value = ''
  try {
    const payload = {}
    if (newVersionForm.value.title.trim()) payload.title = newVersionForm.value.title.trim()
    if (newVersionForm.value.version_note.trim()) payload.version_note = newVersionForm.value.version_note.trim()
    await createNewBankVersionApi(detailItem.value.id, payload)
    message.value = '新版本已创建'
    closeDetail()
    await fetchCurrentTab()
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    loading.value = false
  }
}

const restoreVersion = async (versionItemId) => {
  loading.value = true
  message.value = ''
  errorMessage.value = ''
  try {
    await restoreBankVersionApi(detailItem.value.id, versionItemId)
    message.value = '版本已切换'
    await showVersions(detailItem.value)
    await fetchCurrentTab()
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchMine()
  fetchShared()
})
</script>

<template>
  <div class="card">
    <div class="flex items-center justify-between">
      <h3 class="font-display text-lg font-bold">常用题库</h3>
    </div>

    <!-- Tabs -->
    <div class="mt-3 flex gap-1 rounded-xl bg-slate-100 p-1">
      <button
        class="flex-1 rounded-lg px-3 py-1.5 text-sm font-medium transition-colors"
        :class="activeTab === 'mine' ? 'bg-white shadow-sm text-ocean' : 'text-slate-500 hover:text-slate-700'"
        @click="switchTab('mine')"
      >我的题库</button>
      <button
        class="flex-1 rounded-lg px-3 py-1.5 text-sm font-medium transition-colors"
        :class="activeTab === 'shared' ? 'bg-white shadow-sm text-ocean' : 'text-slate-500 hover:text-slate-700'"
        @click="switchTab('shared')"
      >共享题目</button>
    </div>

    <p v-if="message" class="mt-3 rounded-xl bg-ocean/10 px-3 py-2 text-sm text-ocean">{{ message }}</p>
    <p v-if="errorMessage" class="mt-3 rounded-xl bg-coral/10 px-3 py-2 text-sm text-coral">{{ errorMessage }}</p>

    <!-- Item List -->
    <div class="mt-3 space-y-2">
      <!-- Mine tab -->
      <template v-if="activeTab === 'mine'">
        <div v-if="myItems.length === 0" class="py-4 text-center text-sm text-slate-400">
          题库为空。点击题目旁边的「收藏」按钮可保存到题库。
        </div>
        <div v-for="item in myItems" :key="item.id" class="rounded-xl border border-slate-200 p-3">
          <div class="flex items-start justify-between gap-2">
            <div class="min-w-0 flex-1">
              <p class="truncate font-semibold">{{ item.title }}</p>
              <p class="text-xs text-slate-500">
                {{ typeLabel(item.type) }} · {{ summarizeOptions(item) }}
                <span class="ml-1 rounded bg-ocean/10 px-1.5 py-0.5 text-ocean">v{{ item.version }}</span>
              </p>
            </div>
            <button class="btn-primary shrink-0 text-xs" :disabled="loading" @click="importItem(item)">导入</button>
          </div>
          <div class="mt-2 flex flex-wrap gap-1.5">
            <button class="rounded-lg bg-emerald-100 px-2 py-1 text-xs text-emerald-700 hover:bg-emerald-200" @click="showEdit(item)">编辑</button>
            <button class="rounded-lg bg-slate-100 px-2 py-1 text-xs text-slate-600 hover:bg-slate-200" @click="showNewVersion(item)">新版本</button>
            <button class="rounded-lg bg-slate-100 px-2 py-1 text-xs text-slate-600 hover:bg-slate-200" @click="showVersions(item)">历史</button>
            <button class="rounded-lg bg-slate-100 px-2 py-1 text-xs text-slate-600 hover:bg-slate-200" @click="showShare(item)">共享</button>
            <button class="rounded-lg bg-slate-100 px-2 py-1 text-xs text-slate-600 hover:bg-slate-200" @click="showUsage(item)">使用情况</button>
            <button class="rounded-lg bg-slate-100 px-2 py-1 text-xs text-slate-600 hover:bg-slate-200" @click="showCrossStats(item)">跨问卷统计</button>
            <button class="rounded-lg bg-coral/10 px-2 py-1 text-xs text-coral hover:bg-coral/20" @click="removeItem(item.id)">删除</button>
            <button v-if="item.version > 1" class="rounded-lg bg-coral/10 px-2 py-1 text-xs text-coral hover:bg-coral/20" @click="removeChain(item.id)">删除全部版本</button>
          </div>
        </div>
      </template>

      <!-- Shared tab -->
      <template v-if="activeTab === 'shared'">
        <div v-if="sharedItems.length === 0" class="py-4 text-center text-sm text-slate-400">
          暂无他人共享的题目。
        </div>
        <div v-for="item in sharedItems" :key="item.id" class="rounded-xl border border-slate-200 p-3">
          <div class="flex items-start justify-between gap-2">
            <div class="min-w-0 flex-1">
              <p class="truncate font-semibold">{{ item.title }}</p>
              <p class="text-xs text-slate-500">
                {{ typeLabel(item.type) }} · {{ summarizeOptions(item) }} · v{{ item.version }}
                <span class="ml-1 text-slate-400">来自 {{ item.owner_username }}</span>
                <span class="ml-1 rounded bg-purple-100 px-1.5 py-0.5 text-purple-700">共享</span>
              </p>
            </div>
            <button class="btn-primary shrink-0 text-xs" :disabled="loading" @click="importItem(item)">导入</button>
          </div>
        </div>
      </template>
    </div>

    <!-- Detail Panels -->
    <div v-if="detailMode" class="mt-4 rounded-xl border border-ocean/30 bg-ocean/5 p-4">
      <div class="flex items-center justify-between">
        <h4 class="font-semibold text-sm">
          <template v-if="detailMode === 'versions'">版本历史</template>
          <template v-if="detailMode === 'share'">共享题目</template>
          <template v-if="detailMode === 'usage'">使用情况</template>
          <template v-if="detailMode === 'cross-stats'">跨问卷统计</template>
          <template v-if="detailMode === 'new-version'">创建新版本</template>
          <template v-if="detailMode === 'edit'">编辑题目</template>
        </h4>
        <button class="text-xs text-slate-500 hover:text-slate-700" @click="closeDetail">关闭</button>
      </div>

      <p v-if="detailItem" class="mt-1 text-xs text-slate-500">
        {{ detailItem.title }} · v{{ detailItem.version }}
      </p>

      <!-- Version History -->
      <div v-if="detailMode === 'versions' && detailData" class="mt-3 space-y-2">
        <div v-for="v in detailData" :key="v.id"
          class="rounded-lg border border-slate-200 bg-white p-2.5">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium">
                v{{ v.version }}
                <span v-if="v.is_latest" class="ml-1 rounded bg-ocean/10 px-1.5 py-0.5 text-xs text-ocean">最新</span>
              </p>
              <p class="text-xs text-slate-500">{{ v.title }}</p>
              <p v-if="v.version_note" class="text-xs text-slate-400">{{ v.version_note }}</p>
              <p class="text-xs text-slate-400">{{ v.created_at?.slice(0, 19).replace('T', ' ') }}</p>
            </div>
            <button v-if="!v.is_latest" class="rounded bg-ocean/10 px-2 py-1 text-xs text-ocean hover:bg-ocean/20"
              :disabled="loading" @click="restoreVersion(v.id)">切换到该版本</button>
          </div>
        </div>
        <div v-if="detailData.length === 0" class="text-sm text-slate-400">无版本记录</div>
      </div>

      <!-- Share Dialog -->
      <div v-if="detailMode === 'share'" class="mt-3 space-y-2">
        <p class="text-xs text-slate-500">共享给指定用户：输入用户名，多个用户用逗号或空格分隔。</p>
        <input v-model="shareUsernames" class="input" placeholder="如: alice, bob" />
        <div class="flex gap-2">
          <button class="btn-primary text-xs" :disabled="loading" @click="submitShare">确认共享</button>
          <button class="btn-secondary text-xs" @click="closeDetail">取消</button>
        </div>
      </div>

      <!-- Usage -->
      <div v-if="detailMode === 'usage' && detailData" class="mt-3 space-y-2">
        <div v-if="detailData.length === 0" class="text-sm text-slate-400">该题目尚未被任何问卷使用</div>
        <div v-for="u in detailData" :key="u.question_id" class="rounded-lg border border-slate-200 bg-white p-2.5">
          <p class="text-sm font-medium">{{ u.survey_title }}</p>
          <p class="text-xs text-slate-500">
            状态：{{ u.survey_status }} · 第 {{ u.question_order }} 题 · 导入版本 v{{ u.bank_version || '-' }}
          </p>
        </div>
      </div>

      <!-- Edit Panel -->
      <div v-if="detailMode === 'edit'" class="mt-3 space-y-3">
        <div v-if="editVersions.length > 0" class="space-y-1">
          <p class="text-xs font-semibold text-slate-600">选择要编辑的版本</p>
          <div class="flex flex-wrap gap-1.5">
            <button v-for="v in editVersions" :key="v.id"
              class="rounded-lg px-2 py-1 text-xs transition-colors"
              :class="editSelectedVersion === v.id ? 'bg-ocean text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'"
              @click="selectEditVersion(v)">
              v{{ v.version }}
              <span v-if="v.is_latest" class="ml-0.5">(最新)</span>
            </button>
          </div>
        </div>
        <div class="space-y-2">
          <input v-model="editForm.title" class="input" placeholder="题目标题" />
          <input v-model="editForm.version_note" class="input" placeholder="版本说明（可选）" />
          <p class="text-xs text-slate-400">
            提示：如果该版本已被问卷使用，系统会自动创建新版本；未使用的版本将直接修改。
          </p>
          <div class="flex gap-2">
            <button class="btn-primary text-xs" :disabled="loading" @click="submitEdit">保存</button>
            <button class="btn-secondary text-xs" @click="closeDetail">取消</button>
          </div>
        </div>
      </div>

      <!-- Cross Stats -->
      <div v-if="detailMode === 'cross-stats' && detailData" class="mt-3 space-y-3">
        <!-- Version selector for cross-stats -->
        <div v-if="crossStatsVersions.length > 1" class="space-y-1">
          <p class="text-xs font-semibold text-slate-600">选择统计版本范围</p>
          <div class="flex flex-wrap gap-1.5">
            <button
              class="rounded-lg px-2 py-1 text-xs transition-colors"
              :class="!crossStatsSelectedVersion ? 'bg-ocean text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'"
              @click="changeCrossStatsVersion(null)">
              全部版本
            </button>
            <button v-for="v in crossStatsVersions" :key="v.id"
              class="rounded-lg px-2 py-1 text-xs transition-colors"
              :class="crossStatsSelectedVersion === v.id ? 'bg-ocean text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'"
              @click="changeCrossStatsVersion(v.id)">
              v{{ v.version }}
            </button>
          </div>
        </div>
        <div class="rounded-lg border border-slate-200 bg-white p-3">
          <p class="text-sm font-medium">跨问卷汇总</p>
          <p class="text-xs text-slate-500">
            涉及 {{ detailData.total_surveys }} 个问卷 · {{ detailData.total_submissions }} 条回答
          </p>
        </div>

        <template v-if="detailData.stats">
          <div v-if="detailData.stats.option_counts" class="space-y-1">
            <p class="text-xs font-semibold text-slate-600">选项分布</p>
            <div v-for="(count, key) in detailData.stats.option_counts" :key="key"
              class="flex items-center gap-2 text-xs">
              <span class="w-12 font-medium">{{ key }}</span>
              <div class="flex-1 rounded-full bg-slate-100">
                <div class="rounded-full bg-ocean/40 text-right text-ocean" :style="`width: ${detailData.stats.total_answered ? Math.round(count / detailData.stats.total_answered * 100) : 0}%`"
                  :class="count > 0 ? 'px-2 py-0.5' : 'py-0.5'">
                  {{ count }}
                </div>
              </div>
            </div>
          </div>

          <div v-if="detailData.stats.average !== undefined" class="text-xs">
            <p class="font-semibold text-slate-600">数字统计</p>
            <p>平均值：{{ detailData.stats.average?.toFixed(2) ?? '-' }} · 有效回答：{{ detailData.stats.numeric_count ?? 0 }}</p>
          </div>

          <div v-if="detailData.stats.values && !detailData.stats.option_counts && detailData.stats.average === undefined" class="text-xs text-slate-500">
            回答值：{{ detailData.stats.values.join(', ') || '暂无' }}
          </div>
        </template>
      </div>

      <!-- New Version -->
      <div v-if="detailMode === 'new-version'" class="mt-3 space-y-2">
        <input v-model="newVersionForm.title" class="input" placeholder="新版本标题" />
        <input v-model="newVersionForm.version_note" class="input" placeholder="版本说明（可选）" />
        <div class="flex gap-2">
          <button class="btn-primary text-xs" :disabled="loading" @click="submitNewVersion">创建</button>
          <button class="btn-secondary text-xs" @click="closeDetail">取消</button>
        </div>
      </div>
    </div>
  </div>
</template>
