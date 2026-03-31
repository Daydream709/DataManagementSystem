import { createRouter, createWebHistory } from "vue-router";

import MainLayout from "../layouts/MainLayout.vue";
import LoginView from "../views/auth/LoginView.vue";
import SurveyListView from "../views/survey/SurveyListView.vue";
import SurveyEditorView from "../views/survey/SurveyEditorView.vue";
import SurveyFillView from "../views/survey/SurveyFillView.vue";
import SurveyStatsView from "../views/survey/SurveyStatsView.vue";

const routes = [
  {
    path: "/login",
    name: "login",
    component: LoginView,
    meta: { public: true },
  },
  {
    path: "/",
    component: MainLayout,
    children: [
      {
        path: "",
        redirect: "/surveys",
      },
      {
        path: "surveys",
        name: "surveys",
        component: SurveyListView,
        meta: { requiresAuth: true },
      },
      {
        path: "surveys/:id/editor",
        name: "survey-editor",
        component: SurveyEditorView,
        meta: { requiresAuth: true },
      },
      {
        path: "surveys/:id/stats",
        name: "survey-stats",
        component: SurveyStatsView,
        meta: { requiresAuth: true },
      },
    ],
  },
  {
    path: "/survey/:slug",
    name: "survey-fill",
    component: SurveyFillView,
    meta: { requiresAuth: true },
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach((to) => {
  const token = localStorage.getItem("survey_token");
  if (to.meta.requiresAuth && !token) {
    return {
      path: "/login",
      query: { redirect: to.fullPath },
    };
  }
  if (to.path === "/login" && token) {
    return "/surveys";
  }
  return true;
});

export default router;
