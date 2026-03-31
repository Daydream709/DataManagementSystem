<script setup>
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { loginApi, registerApi } from '../../api/auth'
import { useAuthStore } from '../../stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const activeTab = ref('login')
const loading = ref(false)
const errorMessage = ref('')

const loginForm = reactive({
  username: '',
  password: ''
})

const registerForm = reactive({
  username: '',
  password: ''
})

const submitLogin = async () => {
  loading.value = true
  errorMessage.value = ''
  try {
    const data = await loginApi(loginForm)
    authStore.setAuth(data)
    router.push(route.query.redirect || '/surveys')
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    loading.value = false
  }
}

const submitRegister = async () => {
  loading.value = true
  errorMessage.value = ''
  try {
    const data = await registerApi(registerForm)
    authStore.setAuth(data)
    router.push('/surveys')
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="relative flex min-h-screen items-center justify-center overflow-hidden px-4 py-8">
    <div class="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_20%_20%,rgba(19,111,99,0.22),transparent_35%),radial-gradient(circle_at_85%_10%,rgba(255,113,91,0.2),transparent_40%),radial-gradient(circle_at_50%_80%,rgba(244,223,200,0.9),transparent_50%)]"></div>

    <div class="relative w-full max-w-md rounded-3xl border border-white/60 bg-white/80 p-6 shadow-2xl backdrop-blur md:p-8">
      <h1 class="font-display text-3xl font-extrabold">在线问卷系统</h1>
      <p class="mt-2 text-sm text-slate-600">第一阶段：支持创建、跳转、填写、统计</p>

      <div class="mt-6 grid grid-cols-2 rounded-xl bg-slate-100 p-1">
        <button
          class="rounded-lg py-2 text-sm font-semibold"
          :class="activeTab === 'login' ? 'bg-white text-ink shadow' : 'text-slate-500'"
          @click="activeTab = 'login'"
        >
          登录
        </button>
        <button
          class="rounded-lg py-2 text-sm font-semibold"
          :class="activeTab === 'register' ? 'bg-white text-ink shadow' : 'text-slate-500'"
          @click="activeTab = 'register'"
        >
          注册
        </button>
      </div>

      <form v-if="activeTab === 'login'" class="mt-5 space-y-4" @submit.prevent="submitLogin">
        <div>
          <label class="mb-1 block text-sm font-medium">用户名</label>
          <input v-model="loginForm.username" class="input" required placeholder="请输入用户名" />
        </div>
        <div>
          <label class="mb-1 block text-sm font-medium">密码</label>
          <input v-model="loginForm.password" type="password" class="input" required placeholder="请输入密码" />
        </div>
        <button class="btn-primary w-full" :disabled="loading">{{ loading ? '提交中...' : '登录' }}</button>
      </form>

      <form v-else class="mt-5 space-y-4" @submit.prevent="submitRegister">
        <div>
          <label class="mb-1 block text-sm font-medium">用户名</label>
          <input v-model="registerForm.username" class="input" required minlength="3" maxlength="50" placeholder="3-50位" />
        </div>
        <div>
          <label class="mb-1 block text-sm font-medium">密码</label>
          <input v-model="registerForm.password" type="password" class="input" required minlength="6" placeholder="至少6位" />
        </div>
        <button class="btn-primary w-full" :disabled="loading">{{ loading ? '提交中...' : '注册并登录' }}</button>
      </form>

      <p v-if="errorMessage" class="mt-4 rounded-xl bg-coral/10 px-3 py-2 text-sm text-coral">{{ errorMessage }}</p>
    </div>
  </div>
</template>
