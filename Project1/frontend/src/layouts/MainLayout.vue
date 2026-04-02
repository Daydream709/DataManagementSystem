<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'

import { useAuthStore } from '../stores/auth'

const authStore = useAuthStore()
const router = useRouter()

const registerTimeText = computed(() => {
  const createdAt = authStore.user?.created_at
  if (!createdAt) return '注册时间未知'

  const parsed = new Date(createdAt)
  if (Number.isNaN(parsed.getTime())) return '注册时间未知'
  return `注册于 ${parsed.toLocaleString()}`
})

const logout = () => {
  authStore.logout()
  router.push('/login')
}
</script>

<template>
  <div class="min-h-screen">
    <header class="sticky top-0 z-20 border-b border-slate-200/80 bg-white/80 backdrop-blur">
      <div class="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 md:px-6">
        <div>
          <h1 class="font-display text-xl font-extrabold tracking-tight text-ink">问卷系统</h1>
        </div>
        <div class="flex items-center gap-3">
          <div class="hidden text-right md:block">
            <p class="text-sm text-slate-700">{{ authStore.user?.username }}</p>
            <p class="text-xs text-slate-500">{{ registerTimeText }}</p>
          </div>
          <button class="btn-secondary" @click="logout">退出登录</button>
        </div>
      </div>
    </header>

    <main class="mx-auto max-w-7xl px-4 py-6 md:px-6">
      <router-view />
    </main>
  </div>
</template>
