import { defineStore } from "pinia";

export const useAuthStore = defineStore("auth", {
  state: () => ({
    token: localStorage.getItem("survey_token") || "",
    user: JSON.parse(localStorage.getItem("survey_user") || "null"),
  }),
  getters: {
    isAuthenticated: (state) => Boolean(state.token),
  },
  actions: {
    setAuth(payload) {
      this.token = payload.token;
      this.user = {
        id: payload.id,
        username: payload.username,
        created_at: payload.created_at,
      };
      localStorage.setItem("survey_token", payload.token);
      localStorage.setItem("survey_user", JSON.stringify(this.user));
    },
    logout() {
      this.token = "";
      this.user = null;
      localStorage.removeItem("survey_token");
      localStorage.removeItem("survey_user");
    },
  },
});
